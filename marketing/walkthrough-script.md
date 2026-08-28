# Dashboard walkthrough: voice over script

Two minutes thirty seven, timed to `demo/timevault-walkthrough.mp4`. The
footage is silent, so the track drops straight on top.

This one is a how-to, not a trailer. The job is that someone watching knows
exactly what to click and exactly how the money reaches them. Explain, do not
sell.

**Voice:** London, native. Calm and unhurried. Think someone showing a
colleague round a tool they use every day, pausing where the other person
would need a second to catch up.

**Pace:** roughly 330 words across 157 seconds. That is slow. Leave the gaps.
The picture is doing half the work and the captions carry the step numbers.

---

## The script

**[0:07 - 0:14]** · dashboard, live figures across the top
> This is your desk. The numbers along the top are not decoration, they come
> straight off the chain and move on their own.

*(pause while the map settles)*

**[0:15 - 0:20]** · Enter Time Vault, wallet or email
> First, an account. Connect a wallet if you have one. If you do not, an email
> works just as well.

**[0:26 - 0:33]** · Mint Service NFT, the empty form
> Now you list the hours you want to sell. This is the part that earns.

**[0:33 - 0:41]** · name, category, description filling in
> Name the job the way a buyer would search for it. Pick a category, then say
> plainly what they get for their money.

**[0:42 - 0:49]** · rate field
> Your rate, per hour. You set it. Nobody sets it for you, and nobody takes a
> cut off the top.

**[0:50 - 0:55]** · hours field
> Then how many hours you are putting up. Twenty here.

**[0:56 - 1:05]** · the card preview
> And watch the right-hand side. Your card builds as you type. That is exactly
> what a buyer sees when they find you.

*(let it breathe)*

**[1:14 - 1:22]** · browse services
> Once it is minted, it sits in the marketplace next to everyone else.

**[1:22 - 1:30]** · the escrow stamp on the cards
> Look at the stamp on every card. Escrow locked. That means the buyer's money
> went in before the work started. Not after you deliver. Before.

**[1:37 - 1:45]** · my orders, the earnings figure
> My Orders is where you watch it. Total earned, jobs completed, what is still
> running.

**[1:46 - 1:53]** · the status column
> And every order carries a state. Escrowed, so the money is held. In progress
> while you work. Then KAIROS verifying, where the delivery gets checked.

**[1:54 - 2:01]** · released
> Then released. The funds land without you having to ask anyone for them.
> No invoice, no chasing, no polite follow-up three weeks later.

**[2:10 - 2:15]** · dispute centre
> If a buyer does object, VORIAN reads both sides and rules on it. The money
> stays locked until it does.

**[2:17 - 2:22]** · agent console
> Seven agents sit behind all of this, and you can talk to any of them.

**[2:24 - 2:29]** · profile
> And your record belongs to you. Your score travels with you, it is not
> trapped on the platform.

**[2:30 - 2:37]** · back to the dashboard
> One thing, straight. Minting and escrow ship in Phase Two. What you just
> watched is the interface, running, ahead of the contracts.
> Time Vault. Dollar T V is live on letscash dot fun today.

---

## Notes for the read

- "Dollar T V" spoken as letters. "letscash dot fun" spoken out.
- The line at 1:22 about escrow is the one that sells the whole thing. Slow
  down there. Land "Not after you deliver. Before." like a full stop.
- The closing admission is not an apology. Say it evenly. Being early is not
  the same as being dishonest, and the tone should carry that.
- Do not add energy the picture does not have. This is a walkthrough.

## Words to keep out

No "revolutionise", "seamless", "empower", "unlock", "effortless", "in just a
few clicks", "welcome to the future of". If a sentence would survive being
pasted onto any other product, rewrite it.

## Putting it together

```bash
ffmpeg -i demo/timevault-walkthrough.mp4 -i voiceover.wav \
  -c:v copy -c:a aac -b:a 192k -shortest \
  demo/timevault-walkthrough-final.mp4
```

## Rebuilding

```bash
python marketing/record_walkthrough.py    # records and writes demo/beats.json
python marketing/cut_walkthrough.py       # captions anchored to those beats
```

Captions are pinned to beat names rather than timestamps, so a re-record stays
in sync without touching the timings. Edit the `CAPTIONS` table at the top of
`cut_walkthrough.py` to change wording.
