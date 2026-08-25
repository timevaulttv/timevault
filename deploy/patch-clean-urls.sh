#!/usr/bin/env bash
# ============================================
# TIME VAULT: enable extensionless URLs on a LIVE server
#
# Patches the certbot-managed vhost IN PLACE (never overwrites it), so the
# `listen 443 ssl` block certbot owns is preserved:
#   - try_files gains $uri.html  ->  /app serves app.html
#   - adds a 301 from /name.html -> /name
#
# Safe to run more than once. Backs up first, tests the config, and rolls back
# automatically if nginx rejects the result.
#
# Usage (on the VPS, as root):  bash patch-clean-urls.sh
# ============================================
set -euo pipefail

VHOST="/etc/nginx/sites-available/timevault"
BACKUP="/root/timevault-vhost.$(date +%Y%m%d-%H%M%S).bak"

[ -f "$VHOST" ] || { echo "ERROR: $VHOST not found"; exit 1; }

echo "==> Backing up vhost to $BACKUP"
cp -a "$VHOST" "$BACKUP"

echo "==> Patching vhost"
python3 - "$VHOST" <<'PY'
import io, re, sys

path = sys.argv[1]
src = io.open(path, encoding="utf-8").read()
before = src
changes = []

# 1. try_files: add the $uri.html fallback so /app resolves to app.html.
if "$uri.html" not in src:
    new, n = re.subn(r"try_files\s+\$uri\s+\$uri/\s*=404;",
                     "try_files $uri $uri.html $uri/ =404;", src)
    if n:
        src = new
        changes.append("try_files gained $uri.html (%d block%s)" % (n, "" if n == 1 else "s"))
    else:
        print("   WARN: no 'try_files $uri $uri/ =404;' found - check the vhost by hand")

# 2. Redirect /name.html -> /name, inserted inside the server block.
RULE_MARK = 'if ($request_uri ~ "^/([a-zA-Z0-9_-]+)\\.html")'
if RULE_MARK not in src:
    rule = ('    # Clean URLs: /name.html -> /name (loop-safe, the target has no .html)\n'
            '    if ($request_uri ~ "^/([a-zA-Z0-9_-]+)\\.html") {\n'
            '        return 301 /$1$is_args$args;\n'
            '    }\n\n')
    new, n = re.subn(r"(?m)^([ \t]*)location / \{", lambda m: rule + m.group(0), src, count=1)
    if n:
        src = new
        changes.append("added /name.html -> /name redirect")
    else:
        print("   WARN: no 'location / {' found - redirect not inserted")

if src == before:
    print("   Already patched - nothing to change.")
else:
    io.open(path, "w", encoding="utf-8", newline="").write(src)
    for c in changes:
        print("   " + c)
PY

echo "==> Testing nginx config"
if nginx -t; then
    echo "==> Config OK, reloading nginx"
    systemctl reload nginx
    echo "==> DONE - clean URLs are live"
else
    echo "!! nginx rejected the config - ROLLING BACK"
    cp -a "$BACKUP" "$VHOST"
    nginx -t && systemctl reload nginx
    echo "!! Rolled back to $BACKUP. Nothing changed."
    exit 1
fi
