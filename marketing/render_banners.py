from playwright.sync_api import sync_playwright
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "banners")
os.makedirs(OUT, exist_ok=True)
URL = "http://localhost:8080/marketing/banners.html"

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1200, "height": 675}, device_scale_factor=2)
    pg.goto(URL, wait_until="networkidle")
    pg.wait_for_timeout(1200)
    for i in (1, 2, 3):
        el = pg.query_selector(f"#b{i}")
        path = os.path.join(OUT, f"post-{i}.jpg")
        el.screenshot(path=path, type="jpeg", quality=92)
        print("saved", path, os.path.getsize(path) // 1024, "KB")
    b.close()
print("DONE")
