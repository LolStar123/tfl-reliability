import functools
import http.server
import os
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


server = http.server.ThreadingHTTPServer(
    ("127.0.0.1", 0),
    functools.partial(Quiet, directory=str(ROOT / "examples/portfolio")),
)
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            **({"channel": "chrome"} if os.name == "nt" else {})
        )
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(os.environ.get("AUDIT_URL", f"http://127.0.0.1:{server.server_port}"))
        page.wait_for_function("window.__tfl?.ready")
        page.wait_for_function("!document.querySelector('#refresh').disabled")
        assert page.locator(".line").count() == 11
        assert page.locator("#history-chart polyline").count() == 11
        assert page.evaluate("__tfl.rows.every(r => r.elo >= 100 && r.elo <= 3500)")

        counts = []
        for hours in (1, 6, 24, 168, 720, 0):
            page.locator(f'#history [data-hours="{hours}"]').click()
            result = page.evaluate("window.__tflRange")
            assert result["hours"] == hours
            counts.append(result["count"])
        assert counts == sorted(counts), counts

        page.locator(".line").first.click()
        assert page.locator("#history-chart polyline").count() == 1
        page.locator(".line").first.click()
        assert page.locator("#history-chart polyline").count() == 11

        page.locator("details.tools summary").click()
        page.locator("#dataset").select_option("archive")
        assert page.locator("#history-chart polyline").count() == 11
        page.locator("#dataset").select_option("live")
        with page.expect_download() as download:
            page.locator("#download").click()
        assert download.value.suggested_filename.endswith(".csv")

        page.screenshot(path=str(ROOT / "examples/portfolio/preview.png"), full_page=True)
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")

        page.route("https://api.tfl.gov.uk/**", lambda route: route.abort())
        page.locator("#refresh").click()
        page.wait_for_function("!document.querySelector('#refresh').disabled")
        assert page.locator(".line").count() == 11
        assert not errors, errors
        print("PASS: 11 live lines, timeframe, focus, archive, export, mobile and API fallback")
        browser.close()
finally:
    server.shutdown()
