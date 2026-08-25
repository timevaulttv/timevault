# Security Policy

## Reporting a vulnerability

If you discover a security issue in this repository (XSS, wallet-connection flaws, dependency issues, or anything that could put users at risk), please **do not open a public issue**.

Use GitHub's private vulnerability reporting instead: open the repository's
**Security** tab and choose **Report a vulnerability**. That channel is private
between you and the maintainers.

Please include:

- A description of the issue and where it lives
- Steps to reproduce
- Impact assessment if you have one

You will get a response as quickly as possible, and credit in the fix notes if you want it.

## Scope notes

- The on-chain layer is **in development**: marketplace data currently runs client-side and no user funds move anywhere yet.
- The wallet connector requests accounts only (`eth_requestAccounts`) and never asks for signatures or transactions.
- Smart contracts are not yet deployed; any contract addresses shown are placeholders until the audited contracts ship.
