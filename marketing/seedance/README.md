# Seedance 2.5 brand film

Everything needed to generate the Time Vault brand film on ModelArk with
Dreamina-Seedance-2.5. Written against the official prompt guide, not guessed.

## What the model actually does

Read from the BytePlus docs before any of this was written:

| | |
|---|---|
| Max duration | 30 seconds, single shot |
| Reference assets | 50 total: up to 30 images (4K max each), 10 videos, 10 audio |
| Video references | combined total no longer than 30 seconds |
| Audio references | combined total no longer than 30 seconds, used for voice timbre or music |
| Audio output | generated natively, including speech, in more than 10 languages |
| Asset naming | `@Image1`, `@Video1`, `@Audio1`, numbered by **upload order** |
| Negative control | only supported for subtitles and audio. Everything else must be phrased positively |

The guide asks for a four part prompt: asset bindings, a one sentence summary,
a timestamped plot, then notes for anything that stays constant. That is exactly
how the prompt below is built, so do not reorder it.

## Upload these, in this exact order

The numbering in the prompt is the upload order. Get this wrong and the agents
swap faces.

| # | File | Becomes | Why |
|---|------|---------|-----|
| 1 | `marketing/seedance/ref-hourglass.png` | `@Image1` | the mark |
| 2 | `marketing/seedance/ref-wordmark.png` | `@Image2` | the wordmark |
| 3 | `source/agents/lyra.png` | `@Image3` | LYRA |
| 4 | `source/agents/vorian.png` | `@Image4` | VORIAN |
| 5 | `source/agents/kairos.png` | `@Image5` | KAIROS |
| 6 | `source/agents/solon.png` | `@Image6` | SOLON |
| 7 | `source/agents/neris.png` | `@Image7` | NERIS |
| 8 | `source/agents/atlas.png` | `@Image8` | ATLAS |
| 9 | `source/agents/cirion.png` | `@Image9` | CIRION |
| 10 | `marketing/seedance/ref-particles-6s.mp4` | `@Video1` | particle motion, colour, lighting |
| 11 | `marketing/seedance/ref-mark-motion.mp4` | `@Video2` | how the mark turns and catches light |

`ref-hourglass.png` and `ref-wordmark.png` were resized to 2048px and given a
solid `#060309` background, because the originals are 6250px, above the 4K
ceiling, and transparent PNGs give the model nothing to read behind the mark.

Video references total about 11 seconds of the 30 second allowance, so there is
room to add another clip if a shot needs it.

## Settings in the console

    Mode        Ref-to-video
    Ratio       16:9
    Resolution  720P  (raise if the account allows it)
    Duration    20s if it can be set. Otherwise leave Smart length
    Sound       on
    Videos      1

## The prompt

Paste this whole block. Do not trim the last section, it is what keeps the look
consistent across the whole shot.

```
ASSET BINDINGS
@Image1 is the Time Vault emblem, a gold and violet hourglass. @Image2 is the
Time Vault wordmark. @Image3 to @Image9 are seven AI agents in this order:
LYRA, VORIAN, KAIROS, SOLON, NERIS, ATLAS, CIRION. Refer to @Video1 for
particle behaviour, colour and lighting only. Refer to @Video2 for how the
emblem turns and catches light.

SUMMARY
A gold hourglass forms out of a storm of violet particles inside a vast dark
vault, seven luminous figures rise around it in a ring, and the mark resolves
into the Time Vault wordmark. Cinematic brand film, deep blacks and gold rim
light, slow push in and then a wide pull back.

PLOT
0-4s: Total darkness. Fine violet and white particles drift in from every edge
of frame and spiral toward the centre, gathering speed. Slow push in. A low
ambient hum rises.

4-8s: The particles collapse into the hourglass emblem from @Image1, which
ignites with gold rim light. Sand inside the glass begins to fall and every
grain glows. The camera continues its slow push in. A single deep bass hit
lands the moment the mark ignites.

8-14s: The camera pulls back and orbits slowly to the left. Seven tall
luminous figures fade up in an evenly spaced ring around the hourglass, facing
inward, standing still. Clockwise from the left of frame they are @Image3,
@Image4, @Image5, @Image6, @Image7, @Image8, @Image9. Each carries a thin gold
rim light and a violet fill from below. Strings rise underneath.

14-18s: Still pulling back, the ring dims to silhouette while the hourglass
brightens. Gold light spreads outward from the glass across the vault floor.

18-20s: The hourglass lifts slightly and the wordmark from @Image2 resolves
beneath it in clean gold letterforms. The particles settle. The score
resolves to one sustained low note.

NOTES
A vast dark vault interior throughout, near black, deep shadows, volumetric
haze catching every beam. Palette strictly deep black, violet and gold, no
other hues. Cinematic anamorphic look, shallow depth of field, fine film
grain. The hourglass stays centred in frame for the entire shot. Agent
appearances strictly match @Image3 to @Image9 and stay consistent, no face
changes. All camera moves slow and smooth, no handheld shake. Orchestral
score with a low bass pulse and rising strings. No dialogue. No subtitles.
```

## Do not let the model draw your text

Video models render lettering badly, and garbled type on a brand film is worse
than no type at all. The prompt ends with `No subtitles` on purpose.

Add the text afterwards, in the real brand font, with the pipeline already in
this repo:

```bash
python marketing/burn_text.py marketing/seedance/brand-film.mp4
```

Three beats, timed to the shot:

| Time | Line |
|------|------|
| 5.0 to 8.5s | Your hours, minted. |
| 9.5 to 13.0s | Their money, locked first. |
| 14.0 to 17.5s | Seven agents. One protocol. |
| 18.0 to end | timevault.tv |

## If you want a voice instead of score

Seedance generates speech natively. Replace the last two lines of NOTES with:

```
Orchestral score with a low bass pulse and rising strings, kept low under the
voice. A calm male English voice with a London accent speaks the following,
unhurried, one line per beat: "Freelance work has one broken moment. You
deliver, and the money is still on their side of the table." then "Time Vault
moves it first." then "Seven agents. Every hour, sealed on chain." No
subtitles.
```

Around forty words is right for twenty seconds. Any more and it will rush.

To clone a specific voice instead, upload a 5 to 10 second clean recording as
`@Audio1` and add: `The narration uses the voice timbre from @Audio1.`

## Two things that may bite

**The agent portraits are figures with faces.** They are generated characters,
not photographs of anyone, but a face filter may still refuse them. If a
generation is rejected, drop the agent ring and run the 0-8s and 14-20s beats
alone as a pure mark film. It still works.

**Trial accounts are watermarked and rate limited.** Check the output for a
watermark before building anything else on top of it.

## Cost

The console quoted 0.0107 USD per thousand tokens. A single 720P run of this
length is small money, so generate three or four and pick. First attempts from
video models are rarely the best one.
