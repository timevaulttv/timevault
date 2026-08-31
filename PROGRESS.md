# Progress

One shipped thing at a time, each with a post and a banner. The rule that makes
it work: **every post links to something a stranger can check.** A verified
contract, a transaction hash, a page that loads, a commit. Progress nobody can
verify is just an announcement, and the account already has a reputation for
not making those.

## Where the roadmap actually stands

Phase 1 is complete. The live whitepaper is the source of truth; this is a
summary so a session can start without reading the HTML.

**Done**

- $TV token launched and the contract verified on the explorer
- Website and full platform interface
- All seven agents answering live on a hosted model, server-side key
- Live chain figures on every page, read at page load
- `timevault.tv/proof`, which lists what is not built
- Public repository

**Phase 2, the next real work**

1. Service NFT minting
2. Escrow contracts live
3. SOLON pricing written on chain
4. ATLAS matching against real listings
5. VORIAN arbitration binding on escrow

## Turning that into shippable units

The five items above are too big to ship in one go. Broken down, each becomes a
sequence where every step ends in something checkable:

| # | Ship | What the post links to |
|---|------|------------------------|
| 1 | Escrow contract written | the source file in the public repo |
| 2 | Escrow deployed to testnet | the contract on the explorer |
| 3 | Contract source verified | the verified tab, readable by anyone |
| 4 | First funded order on testnet | the transaction hash |
| 5 | Release path proven on testnet | the release transaction |
| 6 | Dispute path proven on testnet | the arbitration transaction |
| 7 | Service NFT contract written | the source file |
| 8 | Minting deployed to testnet | the contract |
| 9 | First Service NFT minted | the token on the explorer |
| 10 | Mint form wired to the contract | the app, working against testnet |

Work through those and Phase 2 is genuinely half deployed rather than half
announced. Every one of them has a link. None of them requires trusting anyone.

The order is a plan, not a schedule. Nothing public counts the days, because a
day counter turns a good run into a debt the first time one slips.

## What each one produces

**The thing itself.** Shipped, deployed, verified.

**A post.** Short. What shipped, what it means for a freelancer, and the link
that proves it. No hype, no price talk, no promises about what comes next
beyond what is already on the roadmap.

**A banner.** Square, 1080x1080, one format. Generated from the repo's brand
values so it never drifts, and from real source so the code on it is the code
that shipped.

All three land in `BUILD THE PROGRESS/`: `<slug>.jpg` and a `<slug>.txt` with
the title, the caption, and how it works written out in Indonesian. Open that
folder to post; nothing else needs reading first.

## Rules carried over

- No number that cannot be checked against the chain. This applies to progress
  posts as hard as it applies to the site.
- Never describe an unbuilt contract in the present tense. Future tense, or
  name the phase.
- No em dashes, no decorative emoji. `CONTRIBUTING.md` has the full voice note.
- Update `whitepaper.html`'s roadmap the same day a phase item lands, so the
  ticks and the posts never disagree.

## Log

Each entry: date, what shipped, the link, and the post that went out.

### 31 August 2026. The escrow contract is written.

`contracts/src/TimeVaultEscrow.sol`. 9,980 bytes deployed, compiles clean with
solc 0.8.24 and zero warnings, 31 tests passing. CI runs the compile and the
suite on every push, so the green check is the proof rather than a claim.

The design decision worth pointing at: in the normal path no address Time Vault
controls can move a token. Release happens because the buyer accepted, or
because the review window ran out and anyone at all called `settle`. The owner
has no function that touches an existing order, and `rescue` is capped at the
balance nobody is owed, so escrowed money is out of reach by arithmetic instead
of by promise.

Links: [the source](https://github.com/timevaulttv/timevault/blob/main/contracts/src/TimeVaultEscrow.sol),
[the tests](https://github.com/timevaulttv/timevault/blob/main/contracts/test/escrow.test.js),
[CI](https://github.com/timevaulttv/timevault/actions/workflows/contracts.yml).

`proof.html` updated: escrow still sits under "what is not built yet", now with
the source linked. Written is not deployed, and the site says so.

Ready to post in `BUILD THE PROGRESS/escrow-written.{jpg,txt}`.

Next: deploy it to a testnet. That needs the Robinhood Chain testnet RPC and
chain id, and a funded deployer key.
