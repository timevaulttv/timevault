# -*- coding: utf-8 -*-
"""Render the progress banner from marketing/progress-banner.html.

    python marketing/render_progress.py [slug]

Writes "BUILD THE PROGRESS/<slug>.jpg", 1080x1080 at 2x.

That folder is where every shipped thing lands: the square banner and a .txt
next to it holding the title, the caption, and a plain explanation of how the
thing works. One copy of each banner, so there is never a second version of an
announcement drifting away from the first.

Square only. It is the format that wins on a phone timeline, which is where
nearly all of this gets read, and one render means there can never be a wide
version saying something slightly different.

The slug comes from the POST object in the page, so the banner and its filename
stay in step without being told twice. Pass one on the command line to override.

Loaded straight off disk with file://, so nothing needs to be served. Google
Fonts still come over the network, and the run waits for them, because a banner
that silently falls back to Arial is worse than no banner.
"""
import os
import sys

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = "file:///" + os.path.join(HERE, "progress-banner.html").replace("\\", "/")
OUT = os.path.join(os.path.dirname(HERE), "BUILD THE PROGRESS")

SIZE = 1080


def main():
    os.makedirs(OUT, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": SIZE + 120, "height": SIZE + 120},
            device_scale_factor=2)
        page.goto(PAGE, wait_until="networkidle")

        # Cinzel is the whole identity. If it did not arrive, stop rather than
        # ship a banner set in the fallback serif.
        page.wait_for_function("document.fonts.ready.then(() => true)")
        if not page.evaluate("document.fonts.check('700 58px Cinzel')"):
            browser.close()
            sys.exit("FAIL: Cinzel did not load. Check the network and run again.")

        slug = sys.argv[1] if len(sys.argv) > 1 else page.evaluate("POST.slug")
        if not slug:
            browser.close()
            sys.exit("FAIL: no slug. Set POST.slug in progress-banner.html.")

        page.wait_for_timeout(600)

        path = os.path.join(OUT, slug + ".jpg")
        page.query_selector("#frame").screenshot(path=path, type="jpeg", quality=94)
        browser.close()

    print("  %s   %dx%d at 2x   %d KB"
          % (os.path.relpath(path, os.path.dirname(HERE)), SIZE, SIZE,
             os.path.getsize(path) // 1024))
    print("  Write %s.txt next to it: title, caption, and how it works." % slug)
    print("\n  2x on purpose, so it stays sharp after X recompresses it.")


if __name__ == "__main__":
    main()
