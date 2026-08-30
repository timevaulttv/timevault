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
vault, seven luminous figures rise behind it in an arc, and the mark resolves
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

8-14s: The camera stops orbiting and holds a slow, straight pull back. Seven
tall luminous figures fade up standing in a shallow arc behind the hourglass,
all facing the camera, all standing still. Three of them stand to the left of
the hourglass and four stand to the right. All seven are fully visible inside
the frame at the same time, none cropped by the edges, none hidden behind the
hourglass. Left group, left to right: @Image3, @Image4, @Image5. Right group,
left to right: @Image6, @Image7, @Image8, @Image9. Each carries a thin gold rim
light and a violet fill from below. Strings rise underneath.

14-18s: Still pulling back, the arc of figures dims to silhouette while the
hourglass brightens. Gold light spreads outward from the glass across the vault floor.

18-20s: The hourglass lifts slightly and the wordmark from @Image2 resolves
beneath it in clean gold letterforms. The particles settle. The score
resolves to one sustained low note.

NOTES
A vast dark vault interior throughout, near black, deep shadows, volumetric
haze catching every beam. Palette strictly deep black, violet and gold, no
other hues. Cinematic anamorphic look, shallow depth of field, fine film
grain. The hourglass stays centred in frame for the entire shot. Agent
appearances strictly match @Image3 to @Image9 and stay consistent, no face
changes. Once the figures appear, all seven stay in frame together until they
dim. All camera moves slow and smooth, no handheld shake. Orchestral score with
a low bass pulse and rising strings. No dialogue. No subtitles. --wm false
```

### Why the arc, and why the groups

The first version put the figures in a ring with the camera orbiting, and the
model returned six. It had not lost an agent: a ring means some figures sit
behind the hourglass or leave frame, and an orbiting camera guarantees it.

Video models are also weak at exact counts. Asking for seven reliably returns
six or eight. Asking for three on one side and four on the other does not,
because small groups are countable. That substitution is the actual fix; the
arc and the stilled camera just stop anything hiding.

`--wm false` at the end turns the watermark off. It is a documented parameter
under the legacy syntax, and loose validation means it is ignored rather than
fatal if the account does not allow it.

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

---

# Concept 2: "The Silence"

The film above sells the mark. This one sells the platform, and it is the one
to make first.

A video model cannot draw a working interface. Asked for a dashboard it returns
warped buttons and broken lettering, which is why the screen recordings in
`marketing/demo/` will always beat it at showing how Time Vault is used. What a
video model is genuinely better at is the thing a screen recording cannot do:
making an audience feel the problem before the product is mentioned.

So the split is: recordings show the how, this shows the why.

Twenty two seconds. The argument from the investor memo, told as pictures.

## Upload order

Far fewer assets than the brand film, because the human scene is generated
rather than referenced.

| # | File | Becomes |
|---|------|---------|
| 1 | `marketing/seedance/ref-hourglass.png` | `@Image1` |
| 2 | `marketing/seedance/ref-wordmark.png` | `@Image2` |

## Settings

    Mode        Ref-to-video
    Ratio       16:9
    Resolution  720P
    Duration    22s if settable, otherwise Smart length
    Sound       on

## The prompt

```
ASSET BINDINGS
@Image1 is the Time Vault emblem, a gold and violet hourglass. @Image2 is the
Time Vault wordmark. Both appear only in the final beat.

SUMMARY
A freelancer delivers work at night and is met with silence for days, then the
same moment replays with the payment already locked before the work begins.
Cinematic realistic short film, warm practical light against cold blue night,
locked-off camera with one slow push in.

PLOT
0-4s: Night. A freelancer sits at a cluttered desk in a small flat, face lit
only by a monitor. They click once to send a delivery, lean back, and let out a
small satisfied breath. Warm screen light on their face. A soft click, then room
tone.

4-9s: The camera holds the identical framing while time passes around them. Light
from the window cycles from night to day to night twice, coffee cups gather on
the desk, the room grows messier. Their posture sinks lower each cycle and the
satisfaction drains out of their face. The monitor glow stays constant and cold.

9-13s: Close on their hand picking up a phone, thumb hovering over an unanswered
message thread, then setting the phone face down without sending anything. They
rub their eyes. The room is silent apart from a clock.

13-15s: Hard cut to black. One thin horizontal line of gold light draws itself
across the centre of the darkness and holds.

15-20s: The same desk, the same person, but the order is reversed. Before they
begin working, a warm gold seal of light closes over a shape on the desk and
locks with a solid mechanical sound. They work, then click once to deliver.
Immediately the gold light releases and flows across the desk toward them. They
look up, caught off guard, and a real smile arrives. The room is warmer now, lit
gold rather than cold blue.

20-22s: The desk falls away into darkness. The hourglass emblem from @Image1
resolves at the centre with the wordmark from @Image2 beneath it, both in gold.
The score lands on one sustained low note.

NOTES
Cinematic realistic short film throughout, shot on a 35mm cinema lens, shallow
depth of field, fine film grain, authentic skin texture and natural performance,
no beautification. The first half is cold blue and grey, the second half is warm
gold; that colour turn is the point of the film and must be obvious. Camera is
locked off for the whole piece apart from one very slow push in during 15-20s.
Keep the same person, the same desk and the same framing across both halves so
the reversal reads. Score is sparse piano and low strings, quiet and patient in
the first half, opening up at the 15 second mark. Room tone and small practical
sounds only, no dialogue. No subtitles.
```

## Text to burn on afterwards

Timed to the turn, so the words land on the cut rather than over it:

| Time | Line |
|------|------|
| 5.0 to 8.5s | You delivered. |
| 9.5 to 12.5s | Then nothing. |
| 15.5 to 19.0s | Time Vault locks their money first. |
| 20.0 to end | timevault.tv |

Edit the `LINES` table at the top of `marketing/burn_text.py` to those values,
then:

```bash
python marketing/burn_text.py marketing/seedance/the-silence.mp4
```

## Why this one sells and the brand film does not

The brand film shows a logo and seven figures. A stranger finishes it knowing
Time Vault looks expensive and still not knowing what it does.

This one names the enemy in the first nine seconds, and every freelancer
watching has lived it. The reversal at 15 seconds is the product, shown rather
than claimed, and the only sentence needed is the one burned over it. Nothing
in it depends on rendering an interface, so nothing in it can come back warped.

Make this first. Make the brand film later, as a pinned header or an intro
sting, where atmosphere is the whole job.
