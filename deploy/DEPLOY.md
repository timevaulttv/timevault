# Deploying timevault.tv: Namecheap VPS runbook

Everything deploy-related lives in this `deploy/` folder, fully separate from the site source.
The site on the VPS lives in **its own directory** (`/var/www/timevault`) with **its own nginx
vhost**, so other projects on the server are never touched.

## Live architecture (as deployed)

- **VPS**: Ubuntu 24.04, nginx serving `/var/www/timevault`. The origin IP is deliberately
  kept out of this repo, because publishing it lets attackers bypass Cloudflare. Keep it in your
  own notes or an `~/.ssh/config` host alias.
- **DNS + edge**: domain is on **Cloudflare** (proxied / orange cloud) → free CDN + DDoS + edge TLS
- **Cloudflare SSL mode**: Full, so CF connects to the origin over HTTPS (443)
- **Origin TLS**: Let's Encrypt cert (`certbot --nginx`), auto-renewing
- **Firewall (ufw)**: 22 open to all; **80/443 open only to Cloudflare IP ranges** so the origin
  can't be reached by bypassing Cloudflare. Refresh the CF ranges periodically from
  <https://www.cloudflare.com/ips-v4> and `.../ips-v6`.
- **Clean box**: this VPS previously hosted another project (a Cloudflare-Tunnel app); it and
  all of its infrastructure (app files, tunnel, PM2, Node) have been fully removed. Only
  Time Vault's stack remains: nginx, certbot, and the VPS's own system services.

## What gets deployed

`timevault-site.tar.gz`: the pages at the repo root, `robots.txt`,
`sitemap.xml` and `assets/`, around 5.3 MB total.

Rebuild it any time with:

```bash
git ls-files -z -- ':(glob)*.html' robots.txt sitemap.xml assets | xargs -0 tar -czf timevault-site.tar.gz
```

Read that as: ship what the repo tracks. It matters in both directions.

An earlier version of this line named every page by hand, and `proof.html` was
added to the site without being added here, so a rebuild would have shipped
without it. A plain `cp *.html` fixes that and breaks the other end, because it
also sweeps up whatever untracked files happen to be sitting in the folder.
Asking git avoids both: a new page ships on its own, and anything gitignored
cannot reach the server. `:(glob)` keeps `*` from crossing a slash, so the
render templates in `marketing/` stay out of it.

Check before you send:

```bash
tar -tzf timevault-site.tar.gz | grep -v '^assets/'
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
- [ ] `/app`, `/whitepaper` and `/proof` load; no console errors
- [ ] Any `/name.html` returns a 301 to `/name`
- [ ] A wrong URL returns 404 and shows the Time Vault page, not nginx's
- [ ] `/api/lyra/health` returns 200 with `"upstream": "ok"`
- [ ] Share preview: paste the URL into X/Discord, gold banner card appears
- [ ] `https://timevault.tv/sitemap.xml` reachable → submit in Google Search Console

Or all of it at once, from anywhere:

```bash
bash deploy/smoke.sh
```

## If the VPS runs cPanel instead of plain nginx

Namecheap VPS plans sometimes ship with cPanel/WHM. In that case skip the script:
create the account/domain in WHM, then upload the tar via cPanel File Manager into
`public_html` for the timevault.tv account and extract there. SSL: cPanel → SSL/TLS Status
→ Run AutoSSL. Isolation is per-account, so other projects remain untouched.

## Updating the live site later

> **Do not re-run `deploy.sh` on a live server.** It copies `nginx-timevault.conf` over the
> vhost, which deletes the `listen 443 ssl` block certbot added and takes HTTPS down.
> Cloudflare keeps serving cached pages, so the outage is easy to miss.

For a content update, rebuild the tar and extract it. nginx needs no reload for static files:

```bash
scp timevault-site.tar.gz <user>@<vps>:/tmp/
```

```bash
ssh <user>@<vps> 'tar -xzf /tmp/timevault-site.tar.gz -C /var/www/timevault && chown -R www-data:www-data /var/www/timevault && rm /tmp/timevault-site.tar.gz'
```

Then hard-refresh, and purge the Cloudflare cache if a change does not appear.

## Changing the live vhost

`deploy.sh` installs the vhost wholesale and is first-install only. To change the
config on a running server, use a patch script: each one edits the file in place,
backs it up first, runs `nginx -t`, and rolls back on its own if nginx objects.
Both are safe to run twice.

```bash
scp deploy/patch-clean-urls.sh deploy/patch-404-and-headers.sh <user>@<vps>:/tmp/
```

| Script | What it adds |
|--------|--------------|
| `patch-clean-urls.sh` | `/app` serves `app.html`; `/name.html` redirects to `/name` |
| `patch-404-and-headers.sh` | branded 404, HSTS, Permissions-Policy, js/css caching |

Run `patch-clean-urls.sh` first: the 404 patch anchors to the `try_files` line
that one installs.

## The agent backend

Seven agent personas served by `server/agents.py` on `127.0.0.1:8787`, proxied at
`/api/lyra`. The API key lives in `/etc/timevault-lyra.env` (root only, mode 600)
and never enters the repo.

```bash
scp server/agents.py <user>@<vps>:/tmp/
```

```bash
ssh <user>@<vps> 'install -m644 /tmp/agents.py /opt/timevault-lyra/agents.py && systemctl restart timevault-lyra && sleep 2 && curl -s localhost:8787/health'
```

`/health` answers with `"upstream"`, which is the field that matters:

| `upstream` | HTTP | Meaning |
|------------|------|---------|
| `ok` | 200 | the API accepted the key; agents can answer |
| `unauthorized` | 503 | the key is present but revoked or mistyped |
| `unreachable` | 503 | the API could not be reached |
| `unconfigured` | 503 | no key installed |

It is a live probe, cached five minutes, not a check that the variable is set.
The agents were down for weeks behind a health check that only looked for a
non-empty string, so this endpoint now answers the question that was actually
being asked.
