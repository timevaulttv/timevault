# -*- coding: utf-8 -*-
"""Cut the raw capture to 60 seconds and burn in the on-screen lines.

Six segments are lifted out of the raw take and joined, dropping the page
loads and the dead air the recorder could not avoid. Captions sit low left,
one line at a time, so they never fight the interface behind them.

    python marketing/cut_demo.py
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEMO = os.path.join(HERE, "demo")
RAW = os.path.join(DEMO, "timevault-demo.mp4")
OUT = os.path.join(DEMO, "timevault-demo-60s.mp4")
FONT = "C\\:/Windows/Fonts/seguisb.ttf"

# (start, end) in the raw take. Chosen from the contact sheets: the loads and
# the frozen stretches between them are simply not included.
SEGMENTS = [
    (2.0, 16.0),    # hero, headline, the field giving way under the cursor
    (24.0, 34.0),   # down the page, live figures land
    (34.0, 42.0),   # the seven agents
    (56.5, 62.5),   # one of them open and answering
    (66.0, 80.0),   # the proof page: figures, contract, what is and is not built
    (84.0, 92.0),   # back to the plate, address copied, out
]

# (start, end, line) in FINAL timeline seconds. Written to be read aloud, not
# to be admired: short sentences, plain words, nothing a person would not say.
CAPTIONS = [
    (1.2,  6.2,  "Freelancers get stiffed on payment. Constantly."),
    (7.5,  13.0, "So the money moves first."),
    (15.0, 22.0, "Every figure on this page is live from the chain."),
    (25.0, 31.0, "Seven agents run the protocol."),
    (32.6, 37.6, "Ask them anything. They answer for real."),
    (38.6, 44.5, "Creator holds nothing. Liquidity locked forever."),
    (46.0, 51.5, "And we tell you what is not built yet."),
    (53.5, 59.6, "$TV is live on letscash.fun"),
]


def esc(t):
    return t.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’")


def main():
    if not os.path.isfile(RAW):
        sys.exit("FAIL: run marketing/record_demo.py first")

    total = sum(b - a for a, b in SEGMENTS)
    print("  segments: %d, joined length %.1fs" % (len(SEGMENTS), total))

    # trim + concat in one graph so there is no intermediate re-encode
    inputs, parts = [], []
    for i, (a, b) in enumerate(SEGMENTS):
        inputs.append("[0:v]trim=start=%.2f:end=%.2f,setpts=PTS-STARTPTS[v%d]" % (a, b, i))
        parts.append("[v%d]" % i)
    graph = ";".join(inputs) + ";" + "".join(parts) + "concat=n=%d:v=1:a=0[joined]" % len(SEGMENTS)

    # captions: a soft plate behind each line keeps it readable over the field
    chain = "[joined]"
    for i, (s, e, text) in enumerate(CAPTIONS):
        tag = "[c%d]" % i
        chain += ("drawtext=fontfile='%s':text='%s'"
                  ":fontcolor=white@0.96:fontsize=46"
                  ":box=1:boxcolor=black@0.55:boxborderw=26"
                  ":x=96:y=h-190"
                  ":enable='between(t,%.2f,%.2f)'" % (FONT, esc(text), s, e)) + tag
        chain = chain if i == len(CAPTIONS) - 1 else chain + tag.replace("[c", "[c")
        chain = chain[:-len(tag)] + tag + ("" if i == len(CAPTIONS) - 1 else ";" + tag)

    # the loop above is fiddly to read; build it plainly instead
    chain = "[joined]"
    for i, (s, e, text) in enumerate(CAPTIONS):
        last = (i == len(CAPTIONS) - 1)
        chain += ("drawtext=fontfile='%s':text='%s'"
                  ":fontcolor=white@0.96:fontsize=46"
                  ":box=1:boxcolor=black@0.55:boxborderw=26"
                  ":x=96:y=h-190"
                  ":enable='between(t,%.2f,%.2f)'" % (FONT, esc(text), s, e))
        chain += "[out]" if last else ",\n"
    filt = graph + ";" + chain

    fpath = os.path.join(DEMO, "filter.txt")
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(filt)

    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", RAW,
        "-filter_complex_script", fpath, "-map", "[out]",
        "-c:v", "libx264", "-preset", "slow", "-crf", "21",
        "-pix_fmt", "yuv420p", "-r", "30", "-movflags", "+faststart", "-an",
        OUT,
    ], check=True)

    size = os.path.getsize(OUT) / 1048576
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", OUT],
                         capture_output=True, text=True).stdout.strip()
    print("  %s" % OUT)
    print("  %.1f MB, %ss, 1920x1080, silent" % (size, dur))
    os.remove(fpath)


if __name__ == "__main__":
    main()
