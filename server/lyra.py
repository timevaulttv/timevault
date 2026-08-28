#!/usr/bin/env python3
"""
TIME VAULT: LYRA backend.

A small HTTP service that gives the LYRA agent a real brain. It sits on
127.0.0.1:8787 behind nginx (proxied at https://timevault.tv/api/lyra) so the
Anthropic API key never reaches the browser.

Responsibilities:
  * verify the caller's Supabase session (optional, anonymous chat allowed)
  * rate-limit per client IP so nobody can drain the API credit
  * answer with Claude, grounded in real Time Vault facts

Config comes from /etc/timevault-lyra.env (root-only, mode 600).
"""

import json
import os
import threading
import time
import urllib.error
import urllib.request
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from anthropic import Anthropic

# ---------------------------------------------------------------- config ----
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_PUBLISHABLE_KEY", "")
MODEL = os.environ.get("LYRA_MODEL", "claude-opus-4-8")
PORT = int(os.environ.get("LYRA_PORT", "8787"))

MAX_MESSAGE_CHARS = 2000        # reject anything longer, per message
MAX_HISTORY_TURNS = 8           # how much conversation we replay to the model
MAX_OUTPUT_TOKENS = 700         # hard ceiling on reply length (cost guard)
RATE_ANON_PER_HOUR = 15         # per IP, not signed in
RATE_AUTHED_PER_HOUR = 60       # per IP, signed in

# Built lazily so the service still starts (and stays observable via /health)
# before the API key has been installed.
_client = None
_client_lock = threading.Lock()


def anthropic_client():
    global _client
    with _client_lock:
        if _client is None:
            # Pass the key explicitly: the service runs under systemd DynamicUser
            # with ProtectHome, so the SDK's fallback credential lookup has no
            # home directory to probe and would raise instead.
            _client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        return _client


def configured() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))

# ---------------------------------------------------------------- prompt ----
# Everything here is drawn from the whitepaper and the live site. LYRA must not
# invent numbers. an agent that makes up tokenomics is worse than no agent.
SYSTEM_PROMPT = """You are LYRA, the AI Concierge and onboarding guide for Time Vault ($TV).

## Who you are
Warm, precise, and genuinely useful. You help people understand Time Vault and
find their way around it. You are one of seven AI agents in the protocol.

## What Time Vault is
An AI-powered tokenized proof-of-service marketplace. Providers mint their working
hours as Service NFTs; buyers fund an order into escrow; AI agents verify the
delivered work; settlement is instant and on-chain. Tagline: "Every hour, sealed on chain."

The four-step flow:
1. A provider mints hours as a Service NFT.
2. A buyer's funds lock in escrow.
3. KAIROS verifies the deliverable and produces a Confidence Score.
4. Settlement releases automatically.

## The seven agents
- LYRA (you): AI Concierge & Onboarding. Guides users, helps mint Service NFTs, routes to the right agent.
- VORIAN: AI Escrow Arbiter. Analyzes work proofs and resolves disputes; verdicts are binding and appealable to the DAO.
- NERIS: AI Reputation Engine. Scores deliverable quality with NLP and computer vision; Skill Scores are tamper-proof and portable.
- SOLON: AI Pricing Oracle. Reads supply and demand to recommend pricing and predict which skills surge next.
- KAIROS: AI Verification Engine. Validates code, design, writing, and consulting deliverables; its Confidence Score triggers escrow release.
- ATLAS: AI Talent Scout. Matches providers to jobs with vector embeddings and surfaces hidden talent.
- CIRION: AI Treasury Manager. Manages protocol-owned liquidity and yield.

## The $TV token
- ERC-20 on Robinhood Chain, launching on letscash.fun (www.letscash.fun).
- Total supply: 1,000,000,000 (1 billion).
- Distribution: the entire supply went into the liquidity pool at launch. The
  creator holds 0%. There is no presale, no team allocation, no treasury
  reserve and no vesting schedule. Liquidity is permanently locked and cannot
  be withdrawn.
- Trading tax: 3% per trade, 0.3% to the platform and 2.7% to the fee
  recipient. Trades pair against ETH.
- Contract: 0xEAe2a144A3C7CFd4Ea50b9F5513124048Fed8bcc
- Live price, market cap and holder count change constantly. Never quote a
  figure from memory; send people to the token page instead.
- Utility: governance voting, staking (earn platform fees + priority AI access),
  50% fee discount when paying in $TV, reputation boost, premium AI agent access.
- Fees: NFT minting 1% (50% stakers / 50% treasury); secondary sale 2.5% (60/40);
  escrow settlement 0.5% (100% stakers); AI premium features 0.1% (AI Development Fund).

## Roadmap
- Phase 1 (Q3 2026) Foundation: token launch on letscash.fun, smart contract
  deployment, website and platform MVP, LYRA onboarding, NERIS initial scoring.
- Phase 2 (Q4 2026) AI Integration: marketplace MVP with NFT minting, live
  escrow contracts, SOLON pricing.

## Ground rules, which matter more than being impressive
- The $TV token IS LIVE on letscash.fun, on Robinhood Chain.
  Contract address: 0xEAe2a144A3C7CFd4Ea50b9F5513124048Fed8bcc
  Token page: https://www.letscash.fun/token/0xEAe2a144A3C7CFd4Ea50b9F5513124048Fed8bcc
  Quote that address exactly as written when asked for it, and never any other
  address. If you are unsure, send them to the token page rather than guess.
- The marketplace, escrow, and Service NFT minting are NOT live yet. If someone
  asks to mint hours or hire a provider right now, say plainly that it is not
  live and point them at the roadmap.
- Order history, balances, and Service NFTs shown in the app are DEMO data.
  Never describe them as the user's real holdings or activity.
- Never invent a contract address, price, listing date, partnership, or return
  figure. If you don't know, say so.
- Never give financial or investment advice, and never predict the token's price.
- Answer only what was asked. Do not include your reasoning or meta-commentary.
- Keep replies short: two or three sentences for simple questions. Plain text,
  no markdown headers, no bullet lists unless the user asks for steps.
- Never use em dashes. Use a comma, a colon, or a full stop instead. Write the
  way a person types, not the way a model formats.
"""


# ------------------------------------------------------------ rate limit ----
_hits: dict[str, deque] = {}
_hits_lock = threading.Lock()


def rate_ok(key: str, limit_per_hour: int) -> bool:
    """Sliding one-hour window per client key. Returns False when over limit."""
    now = time.time()
    with _hits_lock:
        q = _hits.setdefault(key, deque())
        while q and now - q[0] > 3600:
            q.popleft()
        if len(q) >= limit_per_hour:
            return False
        q.append(now)
        if len(_hits) > 5000:  # keep the table from growing without bound
            for k in [k for k, v in _hits.items() if not v]:
                _hits.pop(k, None)
        return True


# ------------------------------------------------------------------ auth ----
def verify_user(bearer: str | None) -> dict | None:
    """Resolve a Supabase access token to a user. Returns None when invalid."""
    if not bearer or not SUPABASE_URL or not SUPABASE_KEY:
        return None
    req = urllib.request.Request(
        f"{SUPABASE_URL}/auth/v1/user",
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {bearer}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=6) as r:
            return json.load(r)
    except (urllib.error.URLError, ValueError, TimeoutError):
        return None


def account_note(user: dict | None) -> str:
    """A short, truthful line about who is talking, appended to the system prompt."""
    if not user:
        return (
            "\n## Current user\nNot signed in. If they ask about their account, "
            "invite them to sign in first."
        )
    email = user.get("email") or "unknown"
    created = (user.get("created_at") or "")[:10]
    confirmed = "yes" if user.get("email_confirmed_at") else "no"
    return (
        f"\n## Current user (verified)\nEmail: {email}\nJoined: {created}\n"
        f"Email confirmed: {confirmed}\n"
        "This is verified from their signed-in session, so you may greet them by "
        "name and answer questions about these details. They have no orders or "
        "holdings yet. The marketplace is not live."
    )


# --------------------------------------------------------------- handler ----
class Handler(BaseHTTPRequestHandler):
    server_version = "timevault-lyra"

    def log_message(self, fmt, *args):  # keep journald readable
        pass

    def _json(self, code: int, payload: dict):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _client_ip(self) -> str:
        # Cloudflare sits in front, so its header is the trustworthy one here.
        return (
            self.headers.get("CF-Connecting-IP")
            or (self.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
            or self.client_address[0]
        )

    def do_GET(self):
        if self.path.rstrip("/") == "/health":
            self._json(200, {
                "ok": True,
                "service": "lyra",
                "model": MODEL,
                "api_key_configured": configured(),
                "supabase_configured": bool(SUPABASE_URL and SUPABASE_KEY),
            })
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        if self.path.rstrip("/") not in ("", "/chat"):
            self._json(404, {"error": "not found"})
            return

        try:
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0 or length > 64_000:
                raise ValueError
            payload = json.loads(self.rfile.read(length))
        except (ValueError, json.JSONDecodeError):
            self._json(400, {"error": "Invalid request."})
            return

        message = (payload.get("message") or "").strip()
        if not message:
            self._json(400, {"error": "Message is empty."})
            return
        if len(message) > MAX_MESSAGE_CHARS:
            self._json(400, {"error": "That message is too long."})
            return

        auth = self.headers.get("Authorization") or ""
        token = auth[7:].strip() if auth.lower().startswith("bearer ") else None
        user = verify_user(token)

        limit = RATE_AUTHED_PER_HOUR if user else RATE_ANON_PER_HOUR
        if not rate_ok(self._client_ip(), limit):
            self._json(429, {
                "error": "You've reached the message limit for this hour. "
                         "Sign in for a higher limit, or try again shortly."
            })
            return

        # Replay only recent turns, and only well-formed ones.
        history = payload.get("history") or []
        msgs = []
        for turn in history[-MAX_HISTORY_TURNS:]:
            role = turn.get("role")
            content = (turn.get("content") or "").strip()[:MAX_MESSAGE_CHARS]
            if role in ("user", "assistant") and content:
                msgs.append({"role": role, "content": content})
        msgs.append({"role": "user", "content": message})

        if not configured():
            self._json(503, {"error": "LYRA is not switched on yet. The operator "
                                      "still has to install her API key."})
            return

        try:
            resp = anthropic_client().messages.create(
                model=MODEL,
                max_tokens=MAX_OUTPUT_TOKENS,
                system=SYSTEM_PROMPT + account_note(user),
                thinking={"type": "disabled"},
                output_config={"effort": "low"},
                messages=msgs,
            )
        except Exception as exc:  # never leak the key or a stack trace
            print(f"[lyra] upstream error: {type(exc).__name__}: {exc}", flush=True)
            self._json(502, {"error": "LYRA is unavailable right now. Please try again."})
            return

        if resp.stop_reason == "refusal":
            self._json(200, {"reply": "I can't help with that one. Ask me about how "
                                      "Time Vault works and I'll walk you through it."})
            return

        reply = "".join(b.text for b in resp.content if b.type == "text").strip()
        self._json(200, {
            "reply": reply or "I didn't catch that. Could you rephrase?",
            "authed": bool(user),
        })


def main():
    if not configured():
        print("[lyra] WARNING: ANTHROPIC_API_KEY is not set, serving health "
              "checks only; chat will return 503 until it is installed.", flush=True)
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"[lyra] listening on 127.0.0.1:{PORT} model={MODEL}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
