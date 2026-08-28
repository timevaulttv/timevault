#!/usr/bin/env bash
# ============================================
# TIME VAULT: post-deploy smoke test
#
# Runs from anywhere with curl. Checks the things that have actually broken
# here before: a page that stopped being served, a .html path that stopped
# redirecting, and an agent backend reporting itself healthy while every reply
# came back 502.
#
#   bash deploy/smoke.sh                     # against production
#   bash deploy/smoke.sh http://localhost:8080   # against a local server
#
# The last check sends a real message to an agent, because a reply is the only
# thing that proves they work. It spends one anonymous slot of the hourly rate
# limit, so this is a deploy check, not something to run in a loop.
#
# Exits non-zero if any check fails, so CI or a cron job can use it.
# ============================================
set -uo pipefail

BASE="${1:-https://timevault.tv}"
BASE="${BASE%/}"
PASS=0
FAIL=0

# Colour only when a terminal is watching; logs and pipes stay plain.
if [ -t 1 ]; then G=$'\033[32m'; R=$'\033[31m'; D=$'\033[2m'; Z=$'\033[0m'
else G=""; R=""; D=""; Z=""; fi

ok()   { PASS=$((PASS+1)); printf '  %sPASS%s  %-34s %s%s%s\n' "$G" "$Z" "$1" "$D" "$2" "$Z"; }
bad()  { FAIL=$((FAIL+1)); printf '  %sFAIL%s  %-34s %s\n' "$R" "$Z" "$1" "$2"; }

# HTTP status of a URL, following nothing: a redirect is a result, not a detour.
code() { curl -s -o /dev/null -w '%{http_code}' --max-time 20 "$1"; }

expect_code() {  # label, path, expected
    local got; got="$(code "$BASE$2")"
    [ "$got" = "$3" ] && ok "$1" "$got" || bad "$1" "expected $3, got $got"
}

expect_redirect() {  # label, path, expected Location
    local out got loc
    out="$(curl -s -o /dev/null -D - --max-time 20 "$BASE$1")"
    got="$(printf '%s' "$out" | awk 'NR==1{print $2}')"
    loc="$(printf '%s' "$out" | tr -d '\r' | awk 'tolower($1)=="location:"{print $2}')"
    # nginx sends a relative Location; Cloudflare rewrites it to an absolute
    # URL. Both are correct, so compare the path.
    loc="${loc#"$BASE"}"
    if [ "$got" = "301" ] && [ "$loc" = "$2" ]; then
        ok "$1 redirects" "301 -> $loc"
    else
        bad "$1 redirects" "expected 301 -> $2, got $got -> ${loc:-none}"
    fi
}

printf '\nTime Vault smoke test  %s%s%s\n\n' "$D" "$BASE" "$Z"

# --- pages -----------------------------------------------------------------
expect_code "landing page"   "/"           200
expect_code "app"            "/app"        200
expect_code "whitepaper"     "/whitepaper" 200
expect_code "proof"          "/proof"      200
expect_code "sitemap"        "/sitemap.xml" 200
expect_code "robots"         "/robots.txt" 200
expect_code "share card"     "/assets/og.png" 200

# --- clean URLs ------------------------------------------------------------
expect_redirect "/app.html" "/app"

# --- the 404 is ours, not nginx's ------------------------------------------
body="$(curl -s --max-time 20 "$BASE/this-page-does-not-exist")"
status="$(code "$BASE/this-page-does-not-exist")"
if [ "$status" != "404" ]; then
    bad "missing page returns 404" "got $status"
elif printf '%s' "$body" | grep -qi 'time vault'; then
    ok "missing page returns 404" "branded"
else
    bad "missing page returns 404" "404 served, but it is not the Time Vault page"
fi

# --- security headers ------------------------------------------------------
head="$(curl -s -o /dev/null -D - --max-time 20 "$BASE/" | tr -d '\r' | tr 'A-Z' 'a-z')"
for h in x-content-type-options x-frame-options referrer-policy strict-transport-security permissions-policy; do
    if printf '%s' "$head" | grep -q "^$h:"; then
        ok "header $h" "present"
    else
        bad "header $h" "missing"
    fi
done

# --- the agents ------------------------------------------------------------
# The field that matters is `upstream`. `api_key_configured` only ever proved a
# string was set, which is how the agents stayed dead for weeks.
health="$(curl -s --max-time 25 "$BASE/api/lyra/health")"
up="$(printf '%s' "$health" | sed -n 's/.*"upstream"[: ]*"\([a-z]*\)".*/\1/p')"
case "$up" in
    ok)           ok  "agents upstream" "ok" ;;
    "")           bad "agents upstream" "no upstream field: ${health:-no response}" ;;
    *)            bad "agents upstream" "$up" ;;
esac

# A real question, answered. The only check that proves the agents work.
reply="$(curl -s --max-time 45 -X POST "$BASE/api/lyra" \
    -H 'Content-Type: application/json' \
    -d '{"agent":"LYRA","message":"In one short sentence, what is Time Vault?"}')"
if printf '%s' "$reply" | grep -q '"reply"'; then
    ok "agents answer" "$(printf '%s' "$reply" | cut -c1-46)..."
else
    bad "agents answer" "${reply:-no response}"
fi

# --- verdict ---------------------------------------------------------------
printf '\n'
if [ "$FAIL" -eq 0 ]; then
    printf '  %s%d checks passed%s\n\n' "$G" "$PASS" "$Z"
    exit 0
fi
printf '  %s%d of %d checks failed%s\n\n' "$R" "$FAIL" "$((PASS+FAIL))" "$Z"
exit 1
