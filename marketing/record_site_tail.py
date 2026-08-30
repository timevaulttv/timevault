# -*- coding: utf-8 -*-
"""Record a short, clean pass of the live site to splice onto a generated film.

A video model cannot draw a working interface without warping it, so the
generated films never show the product. This records the real thing instead:
the hero with the particle field, then the agent console answering, then the
mark. Splice it onto the tail of a Seedance clip and the viewer sees the actual
site rather than a model's guess at one.

    python marketing/record_site_tail.py

Output: marketing/seedance/site-tail.mp4  (about 8 seconds, silent, 1280x720)
"""
import os
import shutil
import subprocess
import sys
import time

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "seedance")
RAW = os.path.join(OUT, "tail-raw")
SITE = "https://timevault.tv/"
W, H = 1280, 720


def glide(page, x1, y1, x2, y2, ms, steps=40):
    for i in range(steps + 1):
        t = i / steps
        e = t * t * (3 - 2 * t)
        page.mouse.move(x1 + (x2 - x1) * e, y1 + (y2 - y1) * e)
        page.wait_for_timeout(int(ms / steps))


def main():
    os.makedirs(OUT, exist_ok=True)
    if os.path.isdir(RAW):
        shutil.rmtree(RAW)
    os.makedirs(RAW, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--force-device-scale-factor=1", "--hide-scrollbars"])
        ctx = browser.new_context(viewport={"width": W, "height": H},
                                  record_video_dir=RAW,
                                  record_video_size={"width": W, "height": H},
                                  device_scale_factor=1)
        page = ctx.new_page()
        page.goto(SITE, wait_until="networkidle")
        page.wait_for_timeout(4200)          # let the intro animation finish

        t0 = time.time()

        # Push the particle field around the mark, which is the most cinematic
        # thing on the page and the only part that reads at a glance.
        glide(page, W * 0.30, H * 0.60, W * 0.72, H * 0.42, 1600)
        glide(page, W * 0.72, H * 0.42, W * 0.60, H * 0.70, 1400)
        glide(page, W * 0.60, H * 0.70, W * 0.80, H * 0.50, 1400)
        page.wait_for_timeout(900)

        # Then the live figures, so the tail carries a fact and not just mood.
        page.evaluate("() => window.scrollBy({top: 620, behavior: 'smooth'})")
        page.wait_for_timeout(2600)

        held = time.time() - t0
        print("  captured %.1fs of usable footage" % held)
        ctx.close()
        browser.close()

    src = [f for f in os.listdir(RAW) if f.endswith(".webm")]
    if not src:
        sys.exit("FAIL: no video written")
    webm = os.path.join(RAW, src[0])

    dur = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", webm],
        capture_output=True, text=True).stdout.strip())
    start = max(0.0, dur - held)

    # mouse.move costs real milliseconds of its own, so the scripted timings
    # above always overrun. Cap the tail rather than shipping whatever length
    # the machine happened to produce, and keep the end, where the live figures
    # are, because that is the part that proves the site is real.
    TARGET = 8.0
    if held > TARGET:
        start += held - TARGET
        print("  trimming to the last %.1fs" % TARGET)

    out = os.path.join(OUT, "site-tail.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error",
                    "-ss", "%.3f" % start, "-i", webm,
                    "-c:v", "libx264", "-preset", "slow", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-r", "30", "-movflags", "+faststart", "-an",
                    out], check=True)
    shutil.rmtree(RAW, ignore_errors=True)

    final = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=nw=1:nk=1", out],
                           capture_output=True, text=True).stdout.strip()
    print("  %s (%.1f MB, %ss)" % (out, os.path.getsize(out) / 1048576, final))
    print()
    print("  Splice it onto a generated film with:")
    print("    python marketing/join_film.py <seedance-clip.mp4>")


if __name__ == "__main__":
    main()
