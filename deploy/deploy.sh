#!/usr/bin/env bash
# ============================================
# TIME VAULT: VPS deploy script (run ON the VPS as root/sudo)
# Idempotent. Isolated to /var/www/timevault + one nginx vhost.
# Usage: bash deploy.sh /path/to/timevault-site.tar.gz
# ============================================
set -euo pipefail

TAR="${1:?Usage: bash deploy.sh /path/to/timevault-site.tar.gz}"
SITE_DIR="/var/www/timevault"
VHOST_SRC="$(dirname "$0")/nginx-timevault.conf"
VHOST_DST="/etc/nginx/sites-available/timevault"

echo "==> Extracting site to $SITE_DIR"
mkdir -p "$SITE_DIR"
tar -xzf "$TAR" -C "$SITE_DIR"
chown -R www-data:www-data "$SITE_DIR" 2>/dev/null || chown -R nginx:nginx "$SITE_DIR" 2>/dev/null || true

echo "==> Installing nginx vhost (isolated, other sites untouched)"
cp "$VHOST_SRC" "$VHOST_DST"
ln -sf "$VHOST_DST" /etc/nginx/sites-enabled/timevault

echo "==> Testing nginx config"
nginx -t

echo "==> Reloading nginx"
systemctl reload nginx

echo "==> Done. Next (once DNS points here):"
echo "    certbot --nginx -d timevault.tv -d www.timevault.tv"
