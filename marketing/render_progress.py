# -*- coding: utf-8 -*-
"""Render the progress banners from marketing/progress-banner.html.

    python marketing/render_progress.py [slug]

Writes marketing/banners/<slug>-wide.jpg   (1600x900, for the timeline)
   and marketing/banners/<slug>-square.jpg (1080x1080, for anywhere square)

The slug comes from the POST object in the page, so the banner and its
filenames stay in step without being told twice. Pass one on the command line
to override it.

Loaded straight off disk with file://, so nothing needs to be served. Google
Fonts still come over the network, and the run waits for them, because a banner
that silently falls back to Arial is worse than no banner.
"""
import os
import sys

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = "file:///" + os.path.join(HERE, "progress-banner.html").replace("\\", "/")
OUT = os.path.join(HERE, "banners")

FRAMES = [("wide", 1600, 900), ("square", 1080, 1080)]


def main():
    os.makedirs(OUT, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": 1700, "height": 1200}, device_scale_factor=2)
        page.goto(PAGE, wait_until="networkidle")

        # Cinzel is the whole identity. If it did not arrive, stop rather than
        # ship a banner set in the fallback serif.
        page.wait_for_function("document.fonts.ready.then(() => true)")
        if not page.evaluate("document.fonts.check('700 64px Cinzel')"):
            browser.close()
            sys.exit("FAIL: Cinzel did not load. Check the network and run again.")

        slug = sys.argv[1] if len(sys.argv) > 1 else page.evaluate("POST.slug")
        if not slug:
            browser.close()
            sys.exit("FAIL: no slug. Set POST.slug in progress-banner.html.")

        page.wait_for_timeout(600)

        for name, w, h in FRAMES:
            el = page.query_selector("#" + name)
            path = os.path.join(OUT, "%s-%s.jpg" % (slug, name))
            el.screenshot(path=path, type="jpeg", quality=94)
            print("  %-40s %4dx%-4d  %d KB"
                  % (os.path.relpath(path, os.path.dirname(HERE)), w, h,
                     os.path.getsize(path) // 1024))

        browser.close()
    print("\n  Done. Both are 2x, so they stay sharp when X recompresses them.")


if __name__ == "__main__":
    main()
