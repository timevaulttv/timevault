# Security Policy

## Reporting a vulnerability

If you find a security issue in this repository (XSS, a flaw in the wallet
connection, a dependency problem, or anything else that could put users at
risk), please **do not open a public issue**.

Use GitHub's private vulnerability reporting: open the repository's **Security**
tab and choose **Report a vulnerability**. That channel stays private between you
and the maintainers.

Please include:

- What the issue is and where it lives
- Steps to reproduce
- An impact assessment, if you have one

You will get a response as quickly as possible, and credit in the fix notes if
you want it.

## What is deployed, and what is not

This section exists because getting it wrong in either direction is a security
problem. Claiming something is live when it is not misleads buyers; claiming
something is a placeholder when it is real makes people distrust an address they
should be able to check.

**Deployed and real:**

| | |
|---|---|
| $TV token | [`0xEAe2a144A3C7CFd4Ea50b9F5513124048Fed8bcc`](https://www.letscash.fun/token/0xEAe2a144A3C7CFd4Ea50b9F5513124048Fed8bcc) |
| Source | verified on the explorer |
| Supply | 100% into the liquidity pool |
| Creator allocation | 0% |
| Liquidity | permanently locked |
| Trading tax | 3% |

That address is the only one. Anything else presented as $TV is not $TV. Check it
against the explorer link above before you send anything anywhere.

**Not deployed:**

- The escrow contract. No user funds move through this project today.
- Service NFT minting. The mint form in the app builds a preview and stops there.
- Any settlement, dispute, or verification contract.

The marketplace in `app.html` is a demonstration of the interface. Skill Scores
and order history shown there are demo data, not records of anything that
happened. `proof.html` on the live site says the same thing and is the canonical
version of it.

## Scope notes

- The wallet connector requests accounts only (`eth_requestAccounts`). It never
  asks for a signature and never builds a transaction.
- The Anthropic API key for the agent backend lives in `/etc/timevault-lyra.env`
  on the server, root-only, mode 600. It is not in this repository and never
  reaches the browser. The backend proxies every agent request.
- The agent backend rate-limits per client IP, and nginx rate-limits again in
  front of it.
- No analytics, no trackers, no third-party scripts beyond Three.js and Google
  Fonts.

## If you are doing diligence

Everything asserted above is checkable without trusting this file:

- [The contract on the explorer](https://www.letscash.fun/token/0xEAe2a144A3C7CFd4Ea50b9F5513124048Fed8bcc)
- [timevault.tv/proof](https://timevault.tv/proof), which reads its figures live
  from the chain rather than from anything typed in by hand
