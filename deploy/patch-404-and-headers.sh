#!/usr/bin/env bash
# ============================================
# TIME VAULT: branded 404 + hardened headers on a LIVE server
#
# Patches the certbot-managed vhost IN PLACE (never overwrites it), so the
# `listen 443 ssl` block certbot owns is preserved:
#   - error_page 404 -> /404.html, so a wrong URL still looks like Time Vault
#   - /404 returns a real 404 instead of a 200 with 404 written on it
#   - adds Strict-Transport-Security and Permissions-Policy
#   - caches js/css for an hour, so a deploy is never more than an hour away
#   - drops the add_header inside the image location, which was silently
#     stripping every security header off every image the site serves
#
# Safe to run more than once. Backs up first, tests the config, and rolls back
# automatically if nginx rejects the result.
#
# Usage (on the VPS, as root):  bash patch-404-and-headers.sh
# ============================================
set -euo pipefail

VHOST="/etc/nginx/sites-available/timevault"
ROOT="/var/www/timevault"
BACKUP="/root/timevault-vhost.$(date +%Y%m%d-%H%M%S).bak"

[ -f "$VHOST" ] || { echo "ERROR: $VHOST not found"; exit 1; }
[ -f "$ROOT/404.html" ] || {
    echo "ERROR: $ROOT/404.html is missing. Deploy the site files first,"
    echo "       otherwise error_page would point at nothing."
    exit 1
}

echo "==> Backing up vhost to $BACKUP"
cp -a "$VHOST" "$BACKUP"

echo "==> Patching vhost"
python3 - "$VHOST" <<'PY'
import io, re, sys

path = sys.argv[1]
src = io.open(path, encoding="utf-8").read()
before = src
changes = []

# 1. Branded 404. Anchored to the try_files line so it lands in the block that
#    actually serves the site, not in certbot's port 80 redirect stub.
if "error_page 404" not in src:
    block = (
        "\n"
        "    # A wrong URL should still look like Time Vault rather than a bare\n"
        "    # nginx page. 404.html uses absolute asset paths, so it renders\n"
        "    # correctly however deep the address the visitor got wrong.\n"
        "    error_page 404 /404.html;\n"
        "\n"
        "    # Without this, try_files would find 404.html and serve the page\n"
        "    # with a 200, which lies to crawlers. Returning 404 hands it to\n"
        "    # error_page instead.\n"
        "    location = /404 {\n"
        "        return 404;\n"
        "    }\n"
    )
    # Close the enclosing `location / { ... }` first, then append.
    m = re.search(r"(?m)^([ \t]*)try_files\s+\$uri\s+\$uri\.html.*\n[ \t]*\}\n", src)
    if m:
        src = src[:m.end()] + block + src[m.end():]
        changes.append("added error_page 404 -> /404.html")
    else:
        print("   WARN: no clean-URL try_files block found.")
        print("         Run patch-clean-urls.sh first, then re-run this script.")

# 2. Security headers, placed beside the ones already there.
anchor = "add_header X-Content-Type-Options nosniff always;"
if anchor not in src:
    print("   WARN: existing security headers not found, new ones not added")
else:
    extra = ""
    if "Strict-Transport-Security" not in src:
        extra += ('    # Six months, and deliberately without `preload`: preload lists\n'
                  '    # are painful to leave, and this can be shortened again.\n'
                  '    add_header Strict-Transport-Security "max-age=15768000" always;\n')
        changes.append("added Strict-Transport-Security")
    if "Permissions-Policy" not in src:
        extra += ('    # The site asks for none of these, so nothing embedded in it can.\n'
                  '    add_header Permissions-Policy "camera=(), microphone=(), '
                  'geolocation=(), payment=(), usb=()" always;\n')
        changes.append("added Permissions-Policy")
    if extra:
        # After the last of the existing add_header lines, so they stay together.
        last = max(src.rfind("add_header X-Content-Type-Options"),
                   src.rfind("add_header X-Frame-Options"),
                   src.rfind("add_header Referrer-Policy"))
        eol = src.index("\n", last) + 1
        src = src[:eol] + extra + src[eol:]

# 3. One add_header inside a location discards every inherited one, so the
#    image block was serving pictures with no security headers at all.
new, n = re.subn(r'(?m)^[ \t]*add_header Cache-Control "public";[ \t]*\n', "", src)
if n:
    src = new
    changes.append("removed the add_header that was stripping headers off images")

# 4. Short cache for js/css. Long enough to help, short enough to not outlive
#    a deploy, since the filenames carry no content hash.
if not re.search(r"location\s+~\*\s+\\\.\(js\|css\)", src):
    blk = ("\n"
           "    # Scripts and styles ship on every deploy and carry no content\n"
           "    # hash, so a long cache would serve yesterday's code.\n"
           r"    location ~* \.(js|css)$ {" "\n"
           "        expires 1h;\n"
           "    }\n")
    m = re.search(r"(?m)^[ \t]*location\s+~\*\s+\\\.\([^)]*png[^)]*\)\$\s*\{"
                  r"(?:[^{}]|\n)*?\n[ \t]*\}\n", src)
    if m:
        src = src[:m.end()] + blk + src[m.end():]
        changes.append("added a 1 hour cache for js/css")
    else:
        print("   WARN: no static asset location found, js/css cache not added")

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
    echo "==> DONE"
    echo
    echo "Check it:"
    echo "  curl -s -o /dev/null -w '%{http_code}\n' https://timevault.tv/no-such-page"
    echo "  curl -sI https://timevault.tv/ | grep -i 'strict-transport\|permissions-policy'"
else
    echo "!! nginx rejected the config - ROLLING BACK"
    cp -a "$BACKUP" "$VHOST"
    nginx -t && systemctl reload nginx
    echo "!! Rolled back to $BACKUP. Nothing changed."
    exit 1
fi
