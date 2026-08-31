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

## Voice

`BUILD THE PROGRESS/README.txt` carries this in Indonesian for the user. The
short version, because the first draft of every one of these comes out sounding
like a machine wrote it:

**Never open with a status report.** "The escrow contract is written" is a
changelog entry. "Spent today writing a contract that makes it impossible for
us to touch the money. On purpose." is a post. The first sentence has one job:
earn the second.

**Say "we".** The earlier rule here banned it, and that was wrong. Avoiding
"we" is exactly what makes a post read as a press release. The no-first-person
rule belongs to the agents answering in the app, not to the account posting.

**Cut the signposting.** "Here is the part worth reading", "A few of the
details:", "It is worth noting". People do not announce that they are about to
explain something. Delete the announcement and keep the explanation.

**Fragments are good.** "Not the buyer, not us." is not a sentence, and that is
why it sounds like speech.

**One idea in the main post.** No bullet lists there. Detail goes in the reply,
which also gives people a second thing to click.

**Numbers dropped, not displayed.** "562 lines, 31 tests, zero warnings, all of
it public" beats a tidy line per statistic.

**Close with an invitation.** "Go break it." Not a summary of what was just
said.

**Never write "not yet" or "still".** Those read as apologising. Write what
comes next instead: "Testnet next." This is a rule about tone and nothing else.
Unbuilt things still may not be described as running, and the caveats still
live in the README and on `proof.html`.

**Read it aloud.** Any sentence you would not say to a friend gets rewritten.

Tells to hunt for and kill: three parallel items per sentence over and over,
every sentence the same length, repeated "not X but Y", relentless politeness
with no attitude anywhere, explaining something the reader already understood.

The rule that governs the series: **nothing goes in a post that a reader cannot
check.** Not one number, not one claim. It is what the account is for.

---

## The escrow contract is written

**Banner:** `BUILD THE PROGRESS/escrow-written.jpg`

> Spent today writing a contract that makes it impossible for us to touch the
> money. On purpose.
>
> Here's how it pays out. Buyer funds the job before you start. You deliver.
> Three days later the money is yours, and nobody has to press a button for
> that to happen. Not the buyer, not us. The clock does it, and once the clock
> runs out anyone on earth can trigger the payout.
>
> No approval queue. No "let me check with finance." No polite follow-up email
> three weeks later.
>
> 562 lines, 31 tests, zero warnings, all of it public. Go break it.
>
> Testnet next.
>
> github.com/timevaulttv/timevault/blob/main/contracts/src/TimeVaultEscrow.sol

### First reply, hung under it

> The part people always ask about: what happens when a buyer just claims the
> work is bad.
>
> VORIAN rules on it. But it only ever gets that one order, only for 14 days,
> and it takes zero cut either way. Go quiet past 14 days and anyone can split
> the escrow 50/50, and we get nothing.
>
> So we lose money by ignoring your dispute. Seemed like the right incentive.

### Second reply, if it is running

> The tests read like a list of things the contract won't let you do.
>
> "gives the owner no way to take escrowed money"
> "gives KAIROS no power beyond writing a number"
> "cannot freeze money that is already escrowed by pausing"
>
> Named that way on purpose. If something on the site can't be traced back to
> one of these, one of the two is wrong.
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
