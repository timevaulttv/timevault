# Phase 2 posts

One post per thing shipped, each carrying a link a stranger can open.

Everything ready to post lives in `BUILD THE PROGRESS/` at the repo root: the
banner as `<slug>.jpg` and a `<slug>.txt` next to it holding the title, the
caption, and a plain-Indonesian explanation of how the thing works. That folder
is the one to open when it is time to post. This file is the working archive
and keeps the longer variants.

Square, 1080x1080, one format only. It is what wins on a phone timeline, which
is where nearly all of this gets read, and a single render means there is never
a second version saying something slightly different.

No day counters, in the banner or in the post. "Day 4 of 10" turns a run of good
work into a debt the moment a day slips, and it invites people to count the gaps
instead of reading the work. The shipping is the point, not the streak.

Same voice as `captions.md`: short lines, plain words, no hashtag wall, no press
release. No "I" and no "we". Time Vault is the subject, the reader is "you".

The rule that governs the series: **nothing goes in a post that a reader cannot
check.** Not one number, not one claim. It is what the account is for.

---

## The escrow contract is written

**Banner:** `BUILD THE PROGRESS/escrow-written.jpg`

> The escrow contract is written, and it is in the repo right now.
>
> Here is the part worth reading.
>
> When an order settles, the money does not pass through Time Vault. Either the
> buyer accepts, or the review window runs out and anyone at all can call
> settle(). There is no function anywhere in that file that lets Time Vault take
> a token out of an order. Not the owner. Not the agents.
>
> That is not a line in a pitch deck. It is a file you can open.
>
> A few of the details:
>
> The fee is stamped into an order the moment it is funded. Changing it later
> cannot reach backwards into money that is already escrowed.
>
> Dispute an order and VORIAN can split it. Only that order, only inside
> fourteen days, and it takes no cut. If VORIAN never answers, anyone can
> trigger a fifty-fifty split. Nobody gets paid for staying quiet.
>
> The owner's rescue function is capped at the balance nobody is owed. Escrowed
> funds sit out of reach by arithmetic instead of by promise.
>
> 31 tests, all passing. solc 0.8.24, zero warnings. CI compiles it and runs the
> suite on every push, so none of this needs taking on trust.
>
> Testnet next.
>
> github.com/timevaulttv/timevault/blob/main/contracts/src/TimeVaultEscrow.sol

### Short version, if the long one is too much for the slot

> The escrow contract is written.
>
> No function in it lets Time Vault take a token out of an order. Not the owner,
> not the agents. The buyer accepts, or the window runs out and anyone can
> settle it.
>
> 31 tests. Zero warnings. Read it yourself.
>
> Testnet next.
>
> github.com/timevaulttv/timevault

### Reply to hang under it

Post this as the first reply, not in the main body. It gives people a second
thing to click and it keeps the main post clean.

> The tests are the interesting read, honestly. Each one is named after the
> promise it checks, so the output is a list of things the contract will not let
> you do.
>
> "gives the owner no way to take escrowed money"
> "gives KAIROS no power beyond writing a number"
> "cannot freeze money that is already escrowed by pausing"
> "splits down the middle when VORIAN never answers, and charges nothing for it"
>
> github.com/timevaulttv/timevault/blob/main/contracts/test/escrow.test.js

### Notes on posting this one

- The main post has a URL in it. That is fine for an organic post. It is a hard
  blocker for a promoted one, so this is not ad material. See `x-ads.md`.
- Do not add "not audited" as a caveat in the post. It is already on the
  contracts README and on proof.html, which is where a caveat belongs. Saying it
  twice reads as nerves rather than as care.
- Best time to post is when the US wakes up, since that is where most of the
  crypto timeline is.
