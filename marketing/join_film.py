# -*- coding: utf-8 -*-
"""Splice the real site footage onto the tail of a generated film.

The generated clip carries the story; this puts the actual product on screen at
the end, rather than letting a video model guess at an interface and warp it.

    python marketing/join_film.py marketing/seedance/the-silence.mp4

Output: <input>-joined.mp4

The two sources will not match in size, frame rate or audio layout, so both are
normalised to the same spec before concatenation. A straight concat demuxer
would produce a broken file otherwise.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TAIL = os.path.join(HERE, "seedance", "site-tail.mp4")
W, H, FPS = 1280, 720, 30
FADE = 0.6          # crossfade seconds between the film and the site footage


def probe(path, entries):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", entries,
         "-of", "default=nw=1:nk=1", path],
        capture_output=True, text=True).stdout.strip().split("\n")
    return [x for x in out if x]


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python marketing/join_film.py <generated-clip.mp4>")
    film = sys.argv[1]
    if not os.path.isfile(film):
        sys.exit("FAIL: %s not found" % film)
    if not os.path.isfile(TAIL):
        sys.exit("FAIL: %s missing. Run marketing/record_site_tail.py first." % TAIL)

    film_dur = float(probe(film, "format=duration")[0])
    tail_dur = float(probe(TAIL, "format=duration")[0])
    has_audio = bool(probe(film, "stream=codec_type") and
                     "audio" in probe(film, "stream=codec_type"))
    print("  film %.1fs  tail %.1fs  audio in film: %s"
          % (film_dur, tail_dur, "yes" if has_audio else "no"))

    offset = max(0.0, film_dur - FADE)

    # Normalise both to the same geometry and rate, then crossfade. Padding to
    # the target box preserves the generated aspect rather than stretching it.
    scale = ("scale=%d:%d:force_original_aspect_ratio=decrease,"
             "pad=%d:%d:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=%d" % (W, H, W, H, FPS))
    parts = [
        "[0:v]%s[a]" % scale,
        "[1:v]%s[b]" % scale,
        "[a][b]xfade=transition=fade:duration=%.2f:offset=%.2f[v]" % (FADE, offset),
    ]

    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", film, "-i", TAIL]
    if has_audio:
        # Hold the film's score under the tail rather than cutting it dead.
        parts.append("[0:a]afade=t=out:st=%.2f:d=%.2f,apad=whole_dur=%.2f[aud]"
                     % (max(0.0, film_dur + tail_dur - FADE - 1.2), 1.2,
                        film_dur + tail_dur - FADE))
        cmd += ["-filter_complex", ";".join(parts), "-map", "[v]", "-map", "[aud]",
                "-c:a", "aac", "-b:a", "192k"]
    else:
        cmd += ["-filter_complex", ";".join(parts), "-map", "[v]", "-an"]

    root, _ = os.path.splitext(film)
    out = root + "-joined.mp4"
    cmd += ["-c:v", "libx264", "-preset", "slow", "-crf", "20",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)

    dur = probe(out, "format=duration")[0]
    print("  %s (%.1f MB, %ss)" % (out, os.path.getsize(out) / 1048576, dur))


if __name__ == "__main__":
    main()
