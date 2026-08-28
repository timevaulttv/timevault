# -*- coding: utf-8 -*-
"""Record the 60 second platform demo against the live site.

Produces silent 1080p footage cut to the beats of marketing/demo-script.md, so
a voice track can be laid straight over the top without re-timing anything.

    python marketing/record_demo.py

Output: marketing/demo/timevault-demo.mp4
"""
import os
import shutil
import subprocess
import sys
import time

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "demo")
RAW = os.path.join(OUT, "raw")
SITE = "https://timevault.tv"
W, H = 1920, 1080

# Beat boundaries in seconds, matching the script. Each shot ends where the
# next line of voice over begins.
BEATS = [
    ("open",     8),   # the hourglass, the headline
    ("field",   10),   # cursor pushing the particle field
    ("live",    10),   # market cap, holders, real trades
    ("agents",  10),   # seven agents, one answering for real
    ("proof",   12),   # creator 0%, liquidity locked, explorer
    ("close",   10),   # contract address, copy, out
]


def glide(page, x1, y1, x2, y2, ms, steps=48):
    """Move the cursor along a line at a human-ish pace."""
    for i in range(steps + 1):
        t = i / steps
        ease = t * t * (3 - 2 * t)          # smoothstep, no robotic constant speed
        page.mouse.move(x1 + (x2 - x1) * ease, y1 + (y2 - y1) * ease)
        page.wait_for_timeout(int(ms / steps))


def creep(page, px, ms, steps=40):
    """Scroll slowly enough to read, rather than snapping down the page."""
    for _ in range(steps):
        page.mouse.wheel(0, px / steps)
        page.wait_for_timeout(int(ms / steps))


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(RAW, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--force-device-scale-factor=1",
                                          "--hide-scrollbars",
                                          "--autoplay-policy=no-user-gesture-required"])
        ctx = browser.new_context(viewport={"width": W, "height": H},
                                  record_video_dir=RAW,
                                  record_video_size={"width": W, "height": H},
                                  device_scale_factor=1)
        page = ctx.new_page()

        # Skip the intro overlay so the recording opens on the product itself.
        page.add_init_script("try{sessionStorage.setItem('tvIntroSeen','1')}catch(e){}")

        started = time.time()
        page.goto(SITE, wait_until="networkidle")
        page.wait_for_timeout(2200)          # let the live figures land

        # 1. OPEN. Hold on the hero so the hourglass and headline register.
        glide(page, 300, 820, 1350, 560, 3200)
        page.wait_for_timeout(1200)
        glide(page, 1350, 560, 1520, 700, 2200)

        # 2. FIELD. Drag through the particle field so it visibly gives way.
        glide(page, 1520, 700, 1180, 420, 2400, steps=60)
        glide(page, 1180, 420, 1600, 640, 2400, steps=60)
        glide(page, 1600, 640, 1300, 780, 2000, steps=50)
        glide(page, 1300, 780, 1450, 520, 1600, steps=40)

        # 3. LIVE. Down to the token section: market cap, chart, real trades.
        creep(page, 1500, 3000)
        page.wait_for_timeout(1200)
        creep(page, 1400, 2600)
        page.wait_for_timeout(1600)
        glide(page, 900, 600, 1200, 480, 1600)

        # 4. AGENTS. Open one card so a real answer appears on screen.
        page.evaluate("document.getElementById('agents').scrollIntoView({behavior:'smooth'})")
        page.wait_for_timeout(2200)
        cards = page.query_selector_all("#agentsGrid .tcg")
        if cards:
            box = cards[0].bounding_box()
            if box:
                glide(page, 700, 700, box["x"] + box["width"] / 2,
                      box["y"] + box["height"] / 2, 1400)
                cards[0].click()
                page.wait_for_timeout(4200)
                page.keyboard.press("Escape")
                page.wait_for_timeout(600)
        else:
            page.wait_for_timeout(6200)

        # 5. PROOF. The page that says what is true and what is not.
        page.goto(SITE + "/proof", wait_until="networkidle")
        page.wait_for_timeout(2600)          # live cells fill in
        creep(page, 1100, 3200)
        page.wait_for_timeout(1400)
        creep(page, 1200, 3200)
        page.wait_for_timeout(1600)

        # 6. CLOSE. Back to the contract plate, copy it, end on the mark.
        page.goto(SITE, wait_until="networkidle")
        page.wait_for_timeout(1800)
        btn = page.query_selector("#caCopy")
        if btn:
            box = btn.bounding_box()
            if box:
                glide(page, 600, 900, box["x"] + box["width"] / 2,
                      box["y"] + box["height"] / 2, 2200)
                btn.click()
                page.wait_for_timeout(2400)
        page.wait_for_timeout(3600)

        print("  captured %.1fs of footage" % (time.time() - started))
        ctx.close()
        browser.close()

    src = [f for f in os.listdir(RAW) if f.endswith(".webm")]
    if not src:
        sys.exit("FAIL: no video written")
    webm = os.path.join(RAW, src[0])

    mp4 = os.path.join(OUT, "timevault-demo.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", webm,
        "-c:v", "libx264", "-preset", "slow", "-crf", "19",
        "-pix_fmt", "yuv420p", "-r", "30", "-an", mp4,
    ], check=True)

    print("  mp4: %s (%.1f MB)" % (mp4, os.path.getsize(mp4) / 1048576))
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", mp4],
                         capture_output=True, text=True).stdout.strip()
    print("  duration: %ss" % dur)


if __name__ == "__main__":
    main()
