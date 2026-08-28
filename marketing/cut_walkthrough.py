# -*- coding: utf-8 -*-
"""Burn the step captions into the dashboard walkthrough.

Captions are anchored to the beat marks the recorder writes into
demo/beats.json, not to fixed timestamps. Page loads vary by a few seconds
between takes, so hard-coded times drift out of sync with the picture; anchors
survive a re-record untouched.

No cutting. The take is paced to be followed, so all of it stays.

    python marketing/cut_walkthrough.py
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEMO = os.path.join(HERE, "demo")
RAW = os.path.join(DEMO, "walkthrough-raw.mp4")
BEATS = os.path.join(DEMO, "beats.json")
OUT = os.path.join(DEMO, "timevault-walkthrough.mp4")
FONT = "C\\:/Windows/Fonts/seguisb.ttf"

# (anchor beat, seconds after that beat, how long to hold, line)
CAPTIONS = [
    ("desk",     1.5,  4.0,  "Your desk. Live figures, straight off the chain."),
    ("signup",   0.6,  3.9,  "Step 1.  Open an account. Wallet or email, your choice."),
    ("listing",  2.0,  7.0,  "Step 2.  List the hours you want to sell."),
    ("listing",  9.5,  8.5,  "Name the job, then say what the buyer actually gets."),
    ("rate",     0.8,  7.5,  "Step 3.  Set your rate per hour."),
    ("rate",     9.5,  5.0,  "And how many hours you are putting up."),
    ("card",     1.0,  8.5,  "Your card builds as you type. That is what buyers see."),
    ("market",   2.0,  7.5,  "Step 4.  Your listing joins the marketplace."),
    ("market",  10.5,  7.5,  "Every card reads ESCROW LOCKED. The money is already in."),
    ("orders",   2.5,  7.5,  "Step 5.  Follow the money in My Orders."),
    ("orders",  11.0,  7.5,  "Escrowed, then In Progress, then KAIROS Verifying."),
    ("orders",  19.5,  7.0,  "Released. You get paid without having to ask."),
    ("disputes", 1.5,  5.0,  "If a buyer objects, VORIAN rules on it."),
    ("agents",   1.5,  5.0,  "Seven agents on call, any hour."),
    ("profile",  1.5,  4.5,  "Your record travels with you, not the platform."),
    ("close",    1.0,  6.5,  "Minting and escrow ship in Phase 2. This is the preview."),
]


def esc(t):
    return t.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’")


def main():
    if not os.path.isfile(RAW):
        sys.exit("FAIL: run marketing/record_walkthrough.py first")
    if not os.path.isfile(BEATS):
        sys.exit("FAIL: demo/beats.json missing, re-run the recorder")

    with open(BEATS, encoding="utf-8") as f:
        marks = {m["name"]: m["t"] for m in json.load(f)}

    # Playwright opens the video file slightly before the script starts timing,
    # so the file runs longer than the last mark. That difference is the lead-in,
    # and every mark has to be pushed by it or the captions land early.
    dur = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", RAW],
        capture_output=True, text=True).stdout.strip())
    # The closing line is the honest one and needs room to be read, so the
    # last frame is held rather than re-recording for a longer tail.
    PAD = 3.5
    lead = max(0.0, dur - marks.get("end", dur))
    marks = {k: v + lead for k, v in marks.items()}
    print("  lead-in %.2fs, applied to every mark" % lead)
    end = dur + PAD

    lines, skipped = [], 0
    for anchor, offset, hold, text in CAPTIONS:
        if anchor not in marks:
            skipped += 1
            continue
        s = marks[anchor] + offset
        e = min(s + hold, end - 0.3)
        if e <= s:
            skipped += 1
            continue
        lines.append((s, e, text))

    if not lines:
        sys.exit("FAIL: no captions could be placed")
    lines.sort()

    # Two captions share one position on screen, so an overlap renders them on
    # top of each other. Beats shift between takes, so rather than hand-tuning
    # every offset again, each line is clipped to end before the next begins.
    GAP = 0.4
    MIN = 1.8
    trimmed = []
    for i, (s, e, text) in enumerate(lines):
        if i + 1 < len(lines):
            e = min(e, lines[i + 1][0] - GAP)
        if e - s < MIN:
            print("    dropped (no room): %s" % text[:46])
            continue
        trimmed.append((s, e, text))
    lines = trimmed

    chain = "[0:v]tpad=stop_mode=clone:stop_duration=%.2f," % PAD
    for i, (s, e, text) in enumerate(lines):
        last = (i == len(lines) - 1)
        # The closing line is the honest one, so it gets the gold plate.
        colour = "#F0DA9B" if last else "white@0.97"
        chain += ("drawtext=fontfile='%s':text='%s'"
                  ":fontcolor=%s:fontsize=44"
                  ":box=1:boxcolor=black@0.62:boxborderw=26"
                  ":x=90:y=h-176"
                  ":enable='between(t,%.2f,%.2f)'" % (FONT, esc(text), colour, s, e))
        chain += "[out]" if last else ",\n"

    fpath = os.path.join(DEMO, "wt_filter.txt")
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(chain)

    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", RAW,
        "-filter_complex_script", fpath, "-map", "[out]",
        "-c:v", "libx264", "-preset", "slow", "-crf", "23",
        "-pix_fmt", "yuv420p", "-r", "30", "-movflags", "+faststart", "-an",
        OUT,
    ], check=True)
    os.remove(fpath)

    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", OUT],
                         capture_output=True, text=True).stdout.strip()
    print("  %s" % OUT)
    print("  %.1f MB, %ss, %d captions placed%s" %
          (os.path.getsize(OUT) / 1048576, dur, len(lines),
           (", %d skipped" % skipped) if skipped else ""))
    for s, e, t in lines:
        print("    %6.1f - %5.1f  %s" % (s, e, t[:52]))


if __name__ == "__main__":
    main()
