from playwright.sync_api import sync_playwright
import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "banners")
os.makedirs(OUT, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1500, "height": 500}, device_scale_factor=2)
    pg.goto("http://localhost:8080/marketing/x-banner.html", wait_until="networkidle")
    pg.wait_for_timeout(1000)
    el = pg.query_selector("#xb")
    path = os.path.join(OUT, "x-header.jpg")
    el.screenshot(path=path, type="jpeg", quality=92)
    print("saved", path, os.path.getsize(path) // 1024, "KB")
    b.close()
