# -*- coding: utf-8 -*-
"""Record the dashboard walkthrough: open an account, list your hours, get paid.

This follows one provider through the desk rather than touring the website.
Pacing is deliberately slow: someone watching should be able to read every
field and follow the cursor without pausing.

    python marketing/record_walkthrough.py

Output: marketing/demo/walkthrough-raw.mp4
"""
import json
import os
import shutil
import subprocess
import sys
import time

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "demo")
RAW = os.path.join(OUT, "wt-raw")
APP = "https://timevault.tv/app"
W, H = 1920, 1080


def glide(page, x1, y1, x2, y2, ms, steps=50):
    """Cursor travel with easing, so it reads as a hand and not a teleport."""
    for i in range(steps + 1):
        t = i / steps
        e = t * t * (3 - 2 * t)
        page.mouse.move(x1 + (x2 - x1) * e, y1 + (y2 - y1) * e)
        page.wait_for_timeout(int(ms / steps))


def reach(page, sel, ms=1500, frm=(W * 0.45, H * 0.65)):
    el = page.query_selector(sel)
    if not el:
        return None
    b = el.bounding_box()
    if b:
        glide(page, frm[0], frm[1], b["x"] + b["width"] / 2, b["y"] + b["height"] / 2, ms)
    return el


def fill(page, sel, text, delay=70, settle=900):
    """Type slowly enough to be read, then pause on the result."""
    el = page.query_selector(sel)
    if not el:
        return
    b = el.bounding_box()
    if b:
        glide(page, W * 0.3, b["y"] + 240, b["x"] + 50, b["y"] + b["height"] / 2, 800, steps=26)
    el.click()
    # The mint form ships with default values, so typing straight in appends and
    # the rate reads 0.0500.085 on camera. Select the existing text first, then
    # type over it, which also looks like what a person actually does.
    page.keyboard.press("Control+A")
    page.wait_for_timeout(220)
    el.type(text, delay=delay)
    page.wait_for_timeout(settle)


def section(page, key, hold, mark=None):
    el = reach(page, '[data-section="%s"]' % key, 1300)
    if el:
        el.click()
    if mark:
        mark(key)          # stamped the moment the view actually swaps
    page.wait_for_timeout(hold)


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
        t0 = time.time()
        marks = []

        def mark(name):
            marks.append({"name": name, "t": round(time.time() - t0, 2)})

        page.goto(APP, wait_until="networkidle")
        page.wait_for_timeout(3000)          # let the live figures land

        mark("desk")
        # --- 1. THE DESK -------------------------------------------------
        # Open on the dashboard so the viewer knows where they are.
        page.wait_for_timeout(2600)

        # --- 2. OPEN AN ACCOUNT ------------------------------------------
        btn = reach(page, "#walletBtn, .wallet-btn", 1800)
        if btn:
            btn.click()
            mark("signup")                   # the overlay is up from here
            page.wait_for_timeout(4200)      # hold on Wallet / Email
            page.keyboard.press("Escape")
            page.wait_for_timeout(1200)

        # --- 3. LIST YOUR HOURS ------------------------------------------
        section(page, "mint", 2400, lambda k: mark("listing"))
        fill(page, "#mintName", "Brand Identity Sprint", 62, 1200)
        sel = page.query_selector("#mintCat")
        if sel:
            b = sel.bounding_box()
            if b:
                glide(page, W * 0.3, b["y"] + 160, b["x"] + 60, b["y"] + b["height"] / 2, 700, steps=22)
            sel.select_option(label="Design")
        page.wait_for_timeout(1400)
        fill(page, "#mintDesc", "Logo, palette and type system in five working days.", 34, 1300)

        # --- 4. SET YOUR RATE --------------------------------------------
        mark("rate")
        fill(page, "#mintRate", "0.085", 150, 1800)
        fill(page, "#mintHours", "20", 180, 1800)
        fill(page, "#mintTags", "Branding, Figma", 60, 2600)

        # hold on the card preview: this is the thing being sold
        mark("card")
        prev = page.query_selector(".mint-preview, #mintPreview, .tcg")
        if prev:
            b = prev.bounding_box()
            if b:
                glide(page, 700, 800, b["x"] + b["width"] / 2, b["y"] + b["height"] / 2, 1800)
                page.wait_for_timeout(3000)

        mint = page.query_selector("button:has-text('Mint Service NFT')")
        if mint:
            b = mint.bounding_box()
            if b:
                glide(page, W * 0.55, H * 0.55, b["x"] + b["width"] / 2, b["y"] + b["height"] / 2, 1500)
            mint.click()
            page.wait_for_timeout(3200)      # the wallet gate

        # --- 5. IT LANDS IN THE MARKET -----------------------------------
        section(page, "browse", 2600, lambda k: mark("market"))
        glide(page, 400, 380, 1500, 720, 3400, steps=70)
        page.wait_for_timeout(1600)
        card = page.query_selector(".service-card")
        if card:
            b = card.bounding_box()
            if b:
                glide(page, 1500, 720, b["x"] + b["width"] / 2, b["y"] + 50, 1800)
                page.wait_for_timeout(3400)  # the ESCROW LOCKED stamp

        # --- 6. FOLLOW THE MONEY -----------------------------------------
        section(page, "orders", 3000, mark)
        # the earnings figure first
        glide(page, 800, 700, 420, 400, 1600)
        page.wait_for_timeout(2800)
        # then down the status column, one state at a time
        glide(page, 420, 400, 1520, 520, 2200, steps=56)
        page.wait_for_timeout(2400)
        glide(page, 1520, 520, 1520, 600, 1400, steps=34)
        page.wait_for_timeout(2400)
        glide(page, 1520, 600, 1520, 680, 1400, steps=34)
        page.wait_for_timeout(3200)

        # --- 7. WHEN IT GOES WRONG ---------------------------------------
        section(page, "disputes", 4000, mark)

        # --- 8. THE AGENTS -----------------------------------------------
        section(page, "agents", 4400, mark)

        # --- 9. YOUR PROFILE ---------------------------------------------
        section(page, "profile", 3400, mark)

        # --- 10. BACK TO THE DESK ----------------------------------------
        section(page, "overview", 4200, lambda k: mark("close"))

        mark("end")
        print("  captured %.1fs" % (time.time() - t0))
        with open(os.path.join(OUT, "beats.json"), "w", encoding="utf-8") as f:
            json.dump(marks, f, indent=1)
        for m in marks:
            print("    %-9s %6.1fs" % (m["name"], m["t"]))
        ctx.close()
        browser.close()

    src = [f for f in os.listdir(RAW) if f.endswith(".webm")]
    if not src:
        sys.exit("FAIL: no video written")

    mp4 = os.path.join(OUT, "walkthrough-raw.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(RAW, src[0]),
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-r", "30", "-an", mp4], check=True)
    shutil.rmtree(RAW, ignore_errors=True)   # the webm has been transcoded; drop it

    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", mp4],
                         capture_output=True, text=True).stdout.strip()
    print("  %s (%.1f MB, %ss)" % (mp4, os.path.getsize(mp4) / 1048576, dur))


if __name__ == "__main__":
    main()
