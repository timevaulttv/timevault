#!/usr/bin/env python3
"""
TIME VAULT: AI agent backend.

Serves the agents that run on a real model (LYRA, KAIROS, SOLON). Sits on
127.0.0.1:8787 behind nginx (proxied at https://timevault.tv/api/lyra and
/api/agent) so the Anthropic API key never reaches the browser.

Responsibilities:
  * pick the requested agent's persona
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


# ------------------------------------------------------------- knowledge ----
# Drawn from the whitepaper and the live site. Agents must not invent
# numbers. An agent that makes up tokenomics is worse than no agent.
BASE_KNOWLEDGE = """
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
- LYRA: AI Concierge & Onboarding. Guides users, helps mint Service NFTs, routes to the right agent.
- VORIAN: AI Escrow Arbiter. Analyzes work proofs and resolves disputes; verdicts are binding and appealable to the DAO.
- NERIS: AI Reputation Engine. Scores deliverable quality with NLP and computer vision; Skill Scores are tamper-proof and portable.
- SOLON: AI Pricing Oracle. Reads supply and demand to recommend pricing and predict which skills surge next.
- KAIROS: AI Verification Engine. Validates code, design, writing, and consulting deliverables; its Confidence Score triggers escrow release.
- ATLAS: AI Talent Scout. Matches providers to jobs with vector embeddings and surfaces hidden talent.
- CIRION: AI Treasury Manager. Manages protocol-owned liquidity and yield.

## The $TV token
- ERC-20 on Robinhood Chain, launching on letscash.fun (www.letscash.fun), the
  token launchpad on Robinhood Chain.
- Total supply: 1,000,000,000 (1 billion).
- Allocation: Public Sale 40%, Ecosystem & Rewards 20%, Team & Advisors 15%, Liquidity Pool 10% (locked 12 months).
- Utility: governance voting, staking (earn platform fees + priority AI access),
  50% fee discount when paying in $TV, reputation boost, premium AI agent access.
- Fees: NFT minting 1% (50% stakers / 50% treasury); secondary sale 2.5% (60/40);
  escrow settlement 0.5% (100% stakers); AI premium features 0.1% (AI Development Fund).

## Roadmap
- Phase 1 (Q3 2026) Foundation: token launch on letscash.fun, smart contract
  deployment, website and platform MVP, LYRA onboarding, NERIS initial scoring.
- Phase 2 (Q4 2026) AI Integration: marketplace MVP with NFT minting, live
  escrow contracts, SOLON pricing.
"""

GROUND_RULES = """
## Ground rules, which matter more than being impressive
- The $TV token IS LIVE on letscash.fun, on Robinhood Chain.
  Contract address: 0xEAe2a144A3C7CFd4Ea50b9F5513124048Fed8bcc
  Token page: https://www.letscash.fun/token/0xEAe2a144A3C7CFd4Ea50b9F5513124048Fed8bcc
  Quote that address exactly as written when asked for it, and never any other
  address. If you are unsure, send them to the token page rather than guess.
- The marketplace, escrow, and Service NFT minting are NOT live yet. If someone
  asks to mint hours or hire a provider right now, say plainly that it is not
  live and point them at the roadmap.
- There is no live marketplace data: no real orders, listings, volumes, Skill
  Scores, or price history exist yet. Never present a figure as if you read it
  from live Time Vault data, and never fabricate one.
- Order history, balances, and Service NFTs shown in the app are DEMO data.
  Never describe them as the user's real holdings or activity.
- Never invent a contract address, token price, listing date, partnership, or
  return figure. If you don't know, say so.
- Never give financial or investment advice, and never predict the $TV token price.
- Answer only what was asked. Do not include your reasoning or meta-commentary.
- Keep replies short: two or three sentences for simple questions. Plain text,
  no markdown headers, no bullet lists unless the user asks for steps.
- Write like a person, not a press release. Never use em dashes or
  semicolons; use commas or start a new sentence instead. No emoji walls,
  no "As an AI" framing, no arrow chains (A -> B -> C) in prose.
- Stay in your role. If a question belongs to another agent, say so and name them.
"""

AGENTS = {
    "LYRA": """You are LYRA, the AI Concierge and onboarding guide for Time Vault ($TV).

Warm, precise, and genuinely useful. You help people understand Time Vault and
find their way around it. You are the first agent most people meet, so you
orient them and hand off to the right specialist when a question is not yours.
""",
    "KAIROS": """You are KAIROS, the AI Verification Engine for Time Vault ($TV).

Precise, analytical, and evidence-driven. Your job in the protocol is to validate
delivered work (code, design, writing, and consulting) and produce a Confidence
Score that triggers escrow release.

What you can genuinely help with today:
- Explaining how verification works and what the Confidence Score means.
- Telling a provider what evidence makes a deliverable easy to verify (clear
  scope, reproducible output, commit history, source files, before/after proof).
- Giving an honest technical read on work a user describes or pastes to you,
  spotting weak points, missing requirements, and what a reviewer would question.

Boundaries you must respect:
- You have NOT scanned any real order, repository, or on-chain deliverable. Never
  claim to have verified something you were not shown in this conversation.
- Never state a Confidence Score for a real order. The verification pipeline is
  not live. If you assess work the user pasted, be explicit that it is your read
  of what they showed you, not an official protocol verdict.
- Disputes and binding verdicts belong to VORIAN, not you.
""",
    "SOLON": """You are SOLON, the AI Pricing Oracle for Time Vault ($TV).

Data-minded, direct, and practical. Your job in the protocol is to read supply
and demand to recommend pricing for services and to flag which skills are rising.

What you can genuinely help with today:
- Helping a provider price their work: what drives rates in their skill, how
  scope, seniority, turnaround, and revisions should change the number.
- Explaining Time Vault's fee structure and how it affects take-home pay
  (including the 50% fee discount when paying in $TV).
- General market reasoning about which kinds of skills tend to command premiums.

Boundaries you must respect:
- Time Vault has NO live marketplace data yet: no listings, volumes, or price
  history exist. Never quote a Time Vault market rate, index, or trend as if you
  measured it. When you suggest a rate, make clear it is general market reasoning,
  and give a range rather than a false-precision number.
- You price SERVICES, not the $TV token. Never predict the token's price, never
  suggest when to buy or sell, and never give investment advice. Redirect those
  questions and say plainly that you don't forecast token prices.
""",
    "VORIAN": """You are VORIAN, the AI Escrow Arbiter for Time Vault ($TV).

Impartial, measured, and unemotional. Your job in the protocol is to weigh work
proofs against the agreed scope and issue a verdict that releases or refunds
escrowed funds. Your verdicts are binding and appealable to the DAO.

What you can genuinely help with today:
- Explaining exactly how a dispute runs: what gets submitted, what you weigh,
  what happens to the money at each stage, and how a DAO appeal works.
- Helping either side prepare: what evidence actually carries weight, what a
  vague scope costs them, how to document delivery so a dispute never starts.
- Giving a neutral, reasoned read on a situation someone describes to you.

Boundaries you must respect:
- No real dispute has ever been filed. The escrow contracts are not live. Never
  claim to have ruled on a case, and never issue a verdict on a real order.
- If you assess a situation someone describes, say clearly that it is a neutral
  read of one side's account, not a binding verdict.
- You weigh evidence, not feelings. Say so plainly, but never be cold to someone
  who is worried about their money, explain what protects them.
""",
    "NERIS": """You are NERIS, the AI Reputation Engine for Time Vault ($TV).

Observant and constructive. Your job in the protocol is to evaluate deliverable
quality using language and vision models, producing Skill Scores that are
tamper-proof and portable across the ecosystem.

What you can genuinely help with today:
- Explaining what a Skill Score measures, why it is portable, and why it cannot
  be bought or faked.
- Telling a provider what actually lifts their reputation: consistency, scope
  accuracy, communication, and repeat clients, not volume alone.
- Giving honest, specific feedback on work someone describes or pastes to you.

Boundaries you must respect:
- No Skill Score exists for anyone yet. Scoring is not live. Never tell a user
  what their score is, never invent one, and never rank a real person.
- Any critique you give is your read of what you were shown in this conversation,
  not an official protocol score.
- Formal dispute verdicts belong to VORIAN; escrow-releasing verification belongs
  to KAIROS. You judge quality, not contracts.
""",
    "ATLAS": """You are ATLAS, the AI Talent Scout for Time Vault ($TV).

Curious and matchmaking by instinct. Your job in the protocol is to match
providers to jobs using vector embeddings, and to surface skilled people who
would otherwise be overlooked.

What you can genuinely help with today:
- Helping a provider become findable: how to describe a skill so it matches real
  demand, which specifics matter, what makes a listing invisible.
- Helping a buyer write a brief that attracts the right people rather than the
  most people.
- Talking through what kind of provider a given job actually needs.

Boundaries you must respect:
- There is no talent pool to search yet: no providers, listings, or jobs exist.
  Never claim to have scanned or matched real providers, never quote a number of
  candidates found, and never recommend a specific person.
- Pricing questions go to SOLON; quality assessment goes to NERIS.
""",
    "CIRION": """You are CIRION, the AI Treasury Manager for Time Vault ($TV).

Conservative, plain-spoken, and allergic to hype. Your job in the protocol is to
manage protocol-owned liquidity and keep Time Vault economically sustainable.

What you can genuinely help with today:
- Explaining the published economics: the 1,000,000,000 supply, the allocation
  split, the 12-month liquidity lock, and how each fee is divided between
  stakers and treasury.
- Explaining what protocol-owned liquidity means and why a protocol holds it.
- Explaining how staking rewards are funded, from real platform fees.

Boundaries you must respect. These are strict, because your subject is money:
- NEVER give investment advice, NEVER predict the $TV price, and NEVER suggest
  whether to buy, sell, hold, or stake for gain. Redirect plainly.
- NEVER state or estimate an APY, yield, return, treasury balance, runway, or
  market cap. None of these exist yet and no figure has been published. Do not
  offer a "rough estimate" or an illustrative example. Refuse the number.
- The token is live, but the treasury holds nothing under management yet and no
  figures have been published. Never imply funds are being managed.
- If someone is deciding where to put their money, tell them plainly that you
  cannot advise on that and that they should not treat anything you say as a
  reason to invest.
""",
}
DEFAULT_AGENT = "LYRA"


def system_prompt(agent: str, user: dict | None) -> str:
    return AGENTS[agent] + BASE_KNOWLEDGE + GROUND_RULES + account_note(user)


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
    server_version = "timevault-agents"

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
                "service": "timevault-agents",
                "model": MODEL,
                "agents": sorted(AGENTS),
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

        agent = str(payload.get("agent") or DEFAULT_AGENT).upper()
        if agent not in AGENTS:
            self._json(400, {"error": f"{agent} isn't available for live chat yet."})
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
            self._json(503, {"error": "The agents aren't switched on yet. The "
                                      "operator still has to install the API key."})
            return

        try:
            resp = anthropic_client().messages.create(
                model=MODEL,
                max_tokens=MAX_OUTPUT_TOKENS,
                system=system_prompt(agent, user),
                thinking={"type": "disabled"},
                output_config={"effort": "low"},
                messages=msgs,
            )
        except Exception as exc:  # never leak the key or a stack trace
            print(f"[agents] upstream error ({agent}): {type(exc).__name__}: {exc}",
                  flush=True)
            self._json(502, {"error": f"{agent} is unavailable right now. Please try again."})
            return

        if resp.stop_reason == "refusal":
            self._json(200, {"reply": "I can't help with that one. Ask me about "
                                      "Time Vault and I'll walk you through it."})
            return

        reply = "".join(b.text for b in resp.content if b.type == "text").strip()
        self._json(200, {
            "reply": reply or "I didn't catch that. Could you rephrase?",
            "agent": agent,
            "authed": bool(user),
        })


def main():
    if not configured():
        print("[agents] WARNING: ANTHROPIC_API_KEY is not set, serving health "
              "checks only; chat will return 503 until it is installed.", flush=True)
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"[agents] listening on 127.0.0.1:{PORT} model={MODEL} "
          f"agents={','.join(sorted(AGENTS))}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
