# -*- coding: utf-8 -*-
"""Burn the brand-film lines onto a generated clip.

Video models render lettering badly, so the Seedance prompt asks for no
subtitles and the type goes on afterwards, in a real font, here.

    python marketing/burn_text.py marketing/seedance/brand-film.mp4

Output: <input>-text.mp4 alongside the source.

Edit LINES to change the wording or timing. Times are seconds from the start of
the clip; anything past the end of the clip is dropped rather than clamped, so a
shorter generation simply shows fewer lines.
"""
import os
import subprocess
import sys

# (start, end, text, emphasis)  emphasis picks gold over white.
LINES = [
    (5.0,  8.5,  "Your hours, minted.",          False),
    (9.5,  13.0, "Their money, locked first.",   False),
    (14.0, 17.5, "Seven agents. One protocol.",  False),
    (18.0, 99.0, "timevault.tv",                 True),
]

GOLD = "#F0DA9B"
WHITE = "white@0.97"

# Cinzel is the brand display face but is a web font and rarely installed.
# Fall back through serifs that ship with Windows before giving up on the UI
# face, so the type at least stays in the right family.
FONT_CANDIDATES = [
    "C:/Windows/Fonts/Cinzel-SemiBold.ttf",
    "C:/Windows/Fonts/Cinzel-Regular.ttf",
    "C:/Windows/Fonts/constan.ttf",      # Constantia
    "C:/Windows/Fonts/georgia.ttf",
    "C:/Windows/Fonts/times.ttf",
    "C:/Windows/Fonts/seguisb.ttf",      # Segoe UI Semibold, last resort
]


def pick_font():
    for p in FONT_CANDIDATES:
        if os.path.isfile(p):
            return p
    sys.exit("FAIL: no usable font found. Add one to FONT_CANDIDATES.")


def esc(t):
    return t.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\u2019")


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python marketing/burn_text.py <video.mp4>")
    src = sys.argv[1]
    if not os.path.isfile(src):
        sys.exit("FAIL: %s not found" % src)

    dur = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", src],
        capture_output=True, text=True).stdout.strip())

    font = pick_font()
    print("  font: %s" % os.path.basename(font))
    print("  clip: %.1fs" % dur)

    # ffmpeg wants the drive colon escaped inside a filter string.
    fontfile = font.replace(":", "\\:")

    placed = []
    for start, end, text, gold in LINES:
        if start >= dur - 0.2:
            print("    skipped (past the end): %s" % text)
            continue
        placed.append((start, min(end, dur - 0.05), text, gold))

    if not placed:
        sys.exit("FAIL: the clip is too short for any of the lines")

    parts = []
    for start, end, text, gold in placed:
        parts.append(
            "drawtext=fontfile='%s':text='%s'"
            ":fontcolor=%s:fontsize=w/26"
            ":x=(w-text_w)/2:y=h-h/5"
            ":shadowcolor=black@0.55:shadowx=0:shadowy=2"
            ":enable='between(t,%.2f,%.2f)'"
            % (fontfile, esc(text), GOLD if gold else WHITE, start, end))
    chain = "[0:v]" + ",".join(parts) + "[out]"

    fpath = os.path.join(os.path.dirname(src) or ".", "_burn_filter.txt")
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(chain)

    root, _ = os.path.splitext(src)
    out = root + "-text.mp4"
    # Copy the audio through: the generated score is part of the deliverable.
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", src,
        "-filter_complex_script", fpath, "-map", "[out]", "-map", "0:a?",
        "-c:v", "libx264", "-preset", "slow", "-crf", "20",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        "-c:a", "aac", "-b:a", "192k",
        out,
    ], check=True)
    os.remove(fpath)

    print("  %s (%.1f MB)" % (out, os.path.getsize(out) / 1048576))
    for s, e, t, _ in placed:
        print("    %5.1f - %5.1f  %s" % (s, e, t))


if __name__ == "__main__":
    main()
