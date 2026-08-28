# -*- coding: utf-8 -*-
"""Record a short silent loop of the hero, with the cursor pushing the field.

Filler content. No captions, no claims, nothing to fact-check: it exists so a
posting schedule has something to run on the days there is nothing to announce,
and so the particle field gets seen by people who never open the site.

The cursor traces a slow lissajous around the hourglass and returns to where it
started, so the clip cuts back to its own first frame without a visible jump.

    python marketing/record_hero_loop.py

Output: marketing/demo/hero-loop.mp4
"""
import math
import os
import shutil
import subprocess
import sys
import time

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "demo")
RAW = os.path.join(OUT, "hero-raw")
SITE = "https://timevault.tv/"
W, H = 1280, 720
SECONDS = 16
FPS_MOVES = 50          # cursor updates per second; the field reads pointer velocity


def main():
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

        # The intro animation plays once on load and would dominate a 16 second
        # clip, so let it finish before the take starts.
        page.wait_for_timeout(4500)
        canvas = page.query_selector("canvas")
        if not canvas:
            sys.exit("FAIL: no particle canvas on the page")

        t0 = time.time()
        cx, cy = W * 0.5, H * 0.46          # the hourglass sits about here
        rx, ry = W * 0.30, H * 0.26

        # Drive the path from the wall clock, not from a step count. mouse.move
        # costs real milliseconds of its own, so stepping a fixed number of
        # times overruns the target length several times over.
        #
        # 2:3 lissajous over exactly one period, so the last point is the first
        # point and the clip cuts back to its own opening frame.
        while True:
            elapsed = time.time() - t0
            if elapsed >= SECONDS:
                break
            u = 2 * math.pi * (elapsed / SECONDS)
            page.mouse.move(cx + rx * math.sin(2 * u), cy + ry * math.sin(3 * u))
            page.wait_for_timeout(max(1, int(1000 / FPS_MOVES)))
        page.mouse.move(cx, cy)             # close the path exactly

        start_mark = time.time() - t0
        print("  captured %.1fs" % start_mark)
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
    # Everything before the cursor started moving is page load and the intro.
    start = max(0.0, dur - start_mark)
    out = os.path.join(OUT, "hero-loop.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error",
                    "-ss", "%.3f" % start, "-i", webm,
                    "-c:v", "libx264", "-preset", "slow", "-crf", "21",
                    "-pix_fmt", "yuv420p", "-r", "30", "-movflags", "+faststart", "-an",
                    out], check=True)
    shutil.rmtree(RAW, ignore_errors=True)

    final = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=nw=1:nk=1", out],
                           capture_output=True, text=True).stdout.strip()
    print("  %s (%.1f MB, %ss)" % (out, os.path.getsize(out) / 1048576, final))


if __name__ == "__main__":
    main()
