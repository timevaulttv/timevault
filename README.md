# ⏳ Time Vault ($TV)

**Every Hour, Sealed on Chain.** · [**timevault.tv**](https://timevault.tv)

![License: MIT](https://img.shields.io/badge/license-MIT-D4AF37?labelColor=0A0512)
![Status](https://img.shields.io/badge/status-pre--launch-8B5CF6?labelColor=0A0512)
![Launch](https://img.shields.io/badge/launch-letscash.fun-C026D3?labelColor=0A0512)
![Stack](https://img.shields.io/badge/stack-vanilla%20HTML%2FCSS%2FJS-FAFAFA?labelColor=0A0512)
![Wallets](https://img.shields.io/badge/wallets-all%20EVM%20(EIP--6963)-34D399?labelColor=0A0512)
![PRs](https://img.shields.io/badge/PRs-welcome-F0DA9B?labelColor=0A0512)

Time Vault is an AI-powered **tokenized proof-of-service marketplace** concept built for
Robinhood Chain, launching on letscash.fun (www.letscash.fun). Freelance hours become tradable NFTs, buyer funds
lock in smart-contract escrow, and **7 specialized AI agents** handle pricing, verification,
matching, reputation, and disputes.

![Time Vault](assets/og.png)

## Highlights

- 🎬 **Cinematic landing**: brand intro, TCG-style agent cards with 3D tilt + holo glare, purple meteor sky
- 🛰️ **Vault Overview**: live protocol command center with an agent constellation map, streaming activity feed, counting stats
- 🛒 **Service marketplace**: 12 providers with photos, KAIROS-verified badges, live escrow/repricing simulation
- 🤖 **7 AI agents**: each with a portrait, personality, working action panel, and chat (typing indicators included)
- 📟 **Vault Notes**: a draggable terminal notepad on every page, per-wallet storage, `/ai` discussion built in
- 👛 **Universal EVM wallet connect**: EIP-6963 discovery picks up MetaMask, Rabby, OKX, Coinbase, Trust, and friends
- 📜 **Full whitepaper**: SVG technical flow diagrams, tokenomics donut, printable to PDF

## Pages

| Page | File | Description |
|------|------|-------------|
| **Landing** | `index.html` | Cinematic intro, TCG-style agent cards, live marketplace, purple meteor background |
| **App** | `app.html` | dApp shell: Vault Overview (live agent constellation), Browse, Mint Service NFT, My Orders, Dispute Center, Agent Console, My Profile |
| **Whitepaper** | `whitepaper.html` | Full whitepaper with SVG technical flow diagrams, tokenomics, and roadmap (printable to PDF) |

## The 7 AI Agents

| Agent | Role |
|-------|------|
| 💬 **LYRA** | Concierge & onboarding |
| 🛡️ **VORIAN** | Escrow arbiter & dispute resolution |
| ⭐ **NERIS** | Reputation engine (Skill Score) |
| ✦ **SOLON** | Pricing oracle |
| 🔍 **KAIROS** | Delivery verification (Confidence Score) |
| 🎯 **ATLAS** | Talent scout & matching |
| 🏦 **CIRION** | Treasury manager |

## Run locally

Any static server works:

```bash
npx http-server . -p 8080
# open http://localhost:8080
```

No build step. Everything is vanilla HTML/CSS/JS (Three.js and Google Fonts from CDN).

## Project structure

```
├── index.html            # Landing page
├── app.html              # dApp interface
├── whitepaper.html       # Whitepaper
├── assets/
│   ├── logo.png          # Emblem (web-optimized)
│   ├── logo-name.png     # Wordmark
│   ├── favicon.png       # Square favicon
│   ├── og.png            # Social share image (1200x630)
│   ├── agents/           # 7 agent portraits (web-optimized)
│   ├── video/            # Compressed brand animations (H.264)
│   └── js/agent-menu.js  # Landing agent-panel system
├── marketing/            # Social banner templates + render scripts
├── deploy/               # nginx vhost + deployment guide
├── server/               # LYRA agent backend (Python, stdlib HTTP)
└── source/
    ├── brand/            # Original brand masters (uncompressed)
    └── agents/           # Original agent art masters
```

## Status

**In active development toward launch on letscash.fun.** The frontend platform is complete.
marketplace data currently runs client-side while the on-chain layer is built out. Next
milestones, with the full roadmap in the [whitepaper](whitepaper.html):

1. **Smart contracts**: $TV (ERC-20), Service NFT (ERC-721), Escrow Vault to testnet, then audit
2. **Backend API**: persistent marketplace, orders, and disputes (Node/Express + MongoDB)
3. **$TV launch** on letscash.fun · Robinhood Chain integration as the network becomes publicly available

> **Disclaimer:** nothing here is financial advice. Always DYOR before participating in any token sale.

---
© 2026 Time Vault. Every Hour, Sealed on Chain.
