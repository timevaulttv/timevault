# Demo video: voice over script

Sixty seconds, timed to `demo/timevault-demo-60s.mp4`. The footage is silent, so
the track drops straight on top with no re-cutting.

**Voice:** London, native. Male or female both work. Think the way someone
explains a thing they built to a mate in a pub, not a narrator reading ad copy.
Dry, quick, a bit fed up in the opening lines, warmer by the end.

**Pace:** roughly 155 words across 60 seconds. That is conversational, not
rushed. Leave the gaps where they are marked; the picture is doing work there.

---

## The script

**[0:00 - 0:07]** · hero, the hourglass, the field moving
> Freelancers get stiffed on payment. Constantly.
> You deliver, then the client goes quiet.

*(beat, let the particles move)*

**[0:08 - 0:14]** · cursor pushing through the field
> So we flipped it. The money moves first.
> It locks before you start the work.

**[0:15 - 0:24]** · scrolling down, live figures landing
> And everything you see here is live off the chain.
> Market cap, holders, every trade. Nothing typed in by hand.

**[0:25 - 0:32]** · the seven agent cards
> Seven agents run the protocol.
> Pricing, verification, disputes, the lot.

**[0:33 - 0:38]** · one agent, chat visible
> Ask them anything. They actually answer.
> That is a real model, not a script.

**[0:39 - 0:46]** · proof page, figures and contract
> Creator holds nothing. Not a single token.
> Liquidity is locked, and it cannot be pulled.

**[0:47 - 0:53]** · what is not built yet
> And we tell you straight what is not built yet.
> Because you would find out anyway.

**[0:54 - 1:00]** · back to the mark
> Time Vault. Every hour, sealed on chain.
> Dollar T V, live on letscash dot fun.

---

## Notes for the read

- "Dollar T V" is spoken, not "TV". Say the letters.
- "letscash dot fun" spoken out, no spelling.
- The opening two lines carry the whole thing. Flat and slightly annoyed beats
  enthusiastic every time.
- Do not smile through "Creator holds nothing." Say it like a fact, because it
  is one.
- The last line is the only place to lift.

## Words to keep out

No "revolutionise", "seamless", "empower", "unlock", "game changing",
"cutting edge", "in today's world", "imagine a place where". If a line sounds
like it was written to be impressive rather than understood, cut it.

## Where to get the voice

Any of these will return a London read inside a day:

- **Voice123** or **Voices.com** for a booked professional
- **Fiverr Pro**, filter to United Kingdom and listen to samples first
- A friend from London with a decent USB mic. This script is short and plain
  enough that a real accent beats a studio one.

Ask for a dry room, no music bed, and the raw WAV.

## Putting it together

```bash
ffmpeg -i demo/timevault-demo-60s.mp4 -i voiceover.wav \
  -c:v copy -c:a aac -b:a 192k -shortest \
  demo/timevault-demo-final.mp4
```

If you add a music bed, keep it under the voice by about 18 dB:

```bash
ffmpeg -i demo/timevault-demo-60s.mp4 -i voiceover.wav -i music.mp3 \
  -filter_complex "[2:a]volume=0.12[m];[1:a][m]amix=inputs=2:duration=first[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k \
  demo/timevault-demo-final.mp4
```

## Rebuilding the footage

The capture runs against the live site, so the figures in it are whatever the
chain said at the time. To refresh:

```bash
python marketing/record_demo.py    # raw take, about 95 seconds
python marketing/cut_demo.py       # cuts to 60s and burns the captions in
```

Segment boundaries and caption timings live at the top of `cut_demo.py`.
