# Deploying timevault.tv — Namecheap VPS runbook

Everything deploy-related lives in this `deploy/` folder, fully separate from the site source.
The site on the VPS lives in **its own directory** (`/var/www/timevault`) with **its own nginx
vhost** — other projects on the server are never touched.

## Live architecture (as deployed)

- **VPS**: Ubuntu 24.04, nginx serving `/var/www/timevault`. The origin IP is deliberately
  kept out of this repo — publishing it lets attackers bypass Cloudflare. Keep it in your
  own notes or an `~/.ssh/config` host alias.
- **DNS + edge**: domain is on **Cloudflare** (proxied / orange cloud) → free CDN + DDoS + edge TLS
- **Cloudflare SSL mode**: Full — CF connects to the origin over HTTPS (443)
- **Origin TLS**: Let's Encrypt cert (`certbot --nginx`), auto-renewing
- **Firewall (ufw)**: 22 open to all; **80/443 open only to Cloudflare IP ranges** so the origin
  can't be reached by bypassing Cloudflare. Refresh the CF ranges periodically from
  <https://www.cloudflare.com/ips-v4> and `.../ips-v6`.
- **Clean box**: this VPS previously hosted another project (a Cloudflare-Tunnel app); it and
  all of its infrastructure (app files, tunnel, PM2, Node) have been fully removed. Only
  Time Vault's stack remains: nginx, certbot, and the VPS's own system services.

## What gets deployed

`timevault-site.tar.gz` (built from the repo root):
`index.html · app.html · whitepaper.html · robots.txt · sitemap.xml · assets/` — ~5.3 MB total.

Rebuild it any time with:

```bash
mkdir -p ../timevault-deploy && cp index.html app.html whitepaper.html robots.txt sitemap.xml ../timevault-deploy/ && cp -r assets ../timevault-deploy/ && tar -czf timevault-site.tar.gz -C ../timevault-deploy .
```

## 1. DNS (Namecheap dashboard)

Domain List → timevault.tv → **Advanced DNS**:

| Type | Host | Value | TTL |
|------|------|-------|-----|
| A | @ | `<VPS IP>` | Automatic |
| A | www | `<VPS IP>` | Automatic |

Wait for propagation (`nslookup timevault.tv` should return the VPS IP).

## 2. Upload + deploy (plain Ubuntu/Debian VPS with nginx)

From the local machine:

```bash
scp timevault-site.tar.gz deploy/deploy.sh deploy/nginx-timevault.conf <user>@<VPS-IP>:/tmp/
ssh <user>@<VPS-IP>
sudo bash /tmp/deploy.sh /tmp/timevault-site.tar.gz
```

The script extracts to `/var/www/timevault`, installs the vhost, tests and reloads nginx.

## 3. HTTPS (after DNS resolves)

```bash
sudo apt install -y certbot python3-certbot-nginx   # if not installed
sudo certbot --nginx -d timevault.tv -d www.timevault.tv --redirect -m <email> --agree-tos -n
```

Certbot auto-renews; verify with `sudo certbot renew --dry-run`.

## 4. Post-launch checklist

- [ ] `https://timevault.tv` loads, padlock valid, `www.` redirects to apex
- [ ] `/app.html` and `/whitepaper.html` load; no console errors
- [ ] Share preview: paste the URL into X/Discord — gold banner card appears
- [ ] `https://timevault.tv/sitemap.xml` reachable → submit in Google Search Console

## If the VPS runs cPanel instead of plain nginx

Namecheap VPS plans sometimes ship with cPanel/WHM. In that case skip the script:
create the account/domain in WHM, then upload the tar via cPanel File Manager into
`public_html` for the timevault.tv account and extract there. SSL: cPanel → SSL/TLS Status
→ Run AutoSSL. Isolation is per-account, so other projects remain untouched.

## Updating the live site later

> **Do not re-run `deploy.sh` on a live server.** It copies `nginx-timevault.conf` over the
> vhost, which deletes the `listen 443 ssl` block certbot added and takes HTTPS down.
> Cloudflare keeps serving cached pages, so the outage is easy to miss.

For a content update, rebuild the tar and extract it — nginx needs no reload for static files:

```bash
scp timevault-site.tar.gz <user>@<vps>:/tmp/
ssh <user>@<vps> 'tar -xzf /tmp/timevault-site.tar.gz -C /var/www/timevault \n  && chown -R www-data:www-data /var/www/timevault \n  && rm /tmp/timevault-site.tar.gz'
```

Then hard-refresh, and purge the Cloudflare cache if a change does not appear.
