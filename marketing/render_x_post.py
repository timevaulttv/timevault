from playwright.sync_api import sync_playwright
import os, sys

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "banners")
os.makedirs(OUT, exist_ok=True)
name = sys.argv[1] if len(sys.argv) > 1 else "x-post.html"
out  = sys.argv[2] if len(sys.argv) > 2 else "x-post.jpg"

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1200, "height": 675}, device_scale_factor=2)
    pg.goto("http://localhost:8123/marketing/" + name, wait_until="networkidle")
    pg.wait_for_timeout(1200)
    el = pg.query_selector("#xp")
    path = os.path.join(OUT, out)
    el.screenshot(path=path, type="jpeg", quality=94)
    print("saved", path, os.path.getsize(path) // 1024, "KB")
    b.close()
