# Time Vault contracts

[![contracts](https://github.com/timevaulttv/timevault/actions/workflows/contracts.yml/badge.svg)](https://github.com/timevaulttv/timevault/actions/workflows/contracts.yml)

## What is here, and what is not

| | Status |
|---|---|
| `src/TimeVaultEscrow.sol` | written, compiles, 31 tests passing |
| Deployed to a testnet | not yet |
| Deployed to Robinhood Chain | not yet |
| Audited | no |
| Service NFT minting | not written yet |

Nothing in this folder holds anyone's money. The escrow contract has never been
deployed. When it is, the address and the verified source will be linked from
this page and from `proof.html`, and until then the honest answer to "is escrow
live" is no.

The $TV token itself is live and verified. That is a separate contract, not one
of these:
`0xEAe2a144A3C7CFd4Ea50b9F5513124048Fed8bcc`

## Running it yourself

```
cd contracts
npm install
npm run check
```

`npm run check` compiles with solc and then runs the test suite. Both also run
in CI on every push, which is what the badge above points at.

## TimeVaultEscrow

A buyer funds an order in $TV before the work starts. The provider does the
work. The money leaves the contract only in ways written into it.

**The property worth checking first.** In the normal path, no address that Time
Vault controls can move a single token. Not the owner, not KAIROS, not VORIAN.
Release happens because the buyer accepted, or because the review window ran
out and anyone at all called `settle`. That is the reason to put this on chain
rather than hold funds in a company account, so it is the first thing to
verify, not a footnote.

The single exception is a disputed order. If, and only if, the buyer objects
during the review window, VORIAN may split that order. It cannot reach another
order, cannot pay out more than the order holds, cannot take a cut, and loses
the power when the arbitration window closes.

### The path an order takes

```
  fund ──▶ Escrowed ──start──▶ InProgress ──deliver──▶ Review ──▶ Released
             │                     │                     │
           cancel               reclaim                dispute
             │                (deadline passed)          │
             ▼                     ▼                     ▼
          Refunded              Refunded             Disputed ──▶ Settled
```

`Review` is what the interface labels KAIROS Verifying. It lasts 3 days. The
buyer can end it early by accepting. If the buyer says nothing, anyone can call
`settle` and the provider is paid.

### Who can do what

| | |
|---|---|
| buyer | fund, cancel before work starts, accept, dispute during review, reclaim after the deadline |
| provider | start, deliver, refund voluntarily at any point before release |
| anyone | settle an order whose review window ran out, resolve a dispute VORIAN never answered |
| KAIROS | write a confidence score and an evidence pointer. It cannot move money or change a state |
| VORIAN | split a disputed order, inside the arbitration window only |
| owner | set the fee (capped at 2%), set who receives it, rotate the agent keys, pause new funding |

The owner has no function that touches an order that already exists. Pausing
stops new orders and nothing else: every open order can still be released,
refunded and reclaimed while the contract is paused, and there is a test for
exactly that.

### Timings and limits

| | |
|---|---|
| Review window | 3 days |
| Arbitration window | 14 days |
| Delivery window | chosen by the buyer, between 1 hour and 365 days |
| Settlement fee | 0.5%, the published rate, capped in code at 2% |

The fee rate is snapshotted into each order when it is funded, so raising the
fee later cannot reach back into money that is already escrowed. No fee is
charged on a refund. No fee is charged when arbitration times out, because the
protocol should not get paid for failing to show up.

### The accounting invariant

`totalEscrowed` is the sum of every open order. The contract's token balance is
never allowed to fall below it, and `rescue` cannot reach past it, so escrowed
money is out of the owner's hands by arithmetic rather than by promise. Once
deployed, anyone can check it on the explorer:

```
balanceOf(escrow) >= escrow.totalEscrowed()
```

### Honest notes

KAIROS and VORIAN are AI agents. On chain they are ordinary addresses whose
keys Time Vault holds. VORIAN is a trusted arbiter with bounded powers, not
something trustless, and the bounds are the code: one order, one window, no
fee, and a 50/50 fallback if it never answers.

The escrow does not know about Service NFTs yet. The buyer names the provider
and the listing when funding. `listingId` is there so that wiring a minted NFT
into it later does not need a new escrow contract.

The contract has not been audited.

## Build settings

Anyone verifying the deployed bytecode needs these to match:

| | |
|---|---|
| solc | 0.8.24 |
| optimizer | enabled, 200 runs |
| evmVersion | paris |

`paris` rather than the 0.8.24 default of `shanghai`, because `shanghai` emits
the PUSH0 opcode and Robinhood Chain has not been confirmed to accept it. A
contract that deploys and then reverts on every call is a bad way to find out.

`build.js` writes `out/standard-input.json`, which is the exact JSON a
Blockscout verification form wants.
