"""Audit the demo in isolated Chrome, with desktop/mobile evidence in output/qa."""
import functools
import http.server
import json
import os
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "output/qa"
EVIDENCE.mkdir(parents=True, exist_ok=True)


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


server = http.server.ThreadingHTTPServer(
    ("127.0.0.1", 0),
    functools.partial(Quiet, directory=str(ROOT / "examples/portfolio")),
)
threading.Thread(target=server.serve_forever, daemon=True).start()
checks = []
errors = []
try:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            **({"channel": "chrome"} if os.name == "nt" else {})
        )
        page = browser.new_page(viewport={"width": 1280, "height": 900}, reduced_motion="reduce")
        page.set_default_timeout(10000)
        page.on("pageerror", lambda error: errors.append(str(error)))
        url = os.environ.get("AUDIT_URL", f"http://127.0.0.1:{server.server_port}")
        page.goto(url, wait_until="networkidle")
        page.wait_for_function("window.__tfl?.ready")
        page.wait_for_function("!document.querySelector('#refresh').disabled")
        assert page.locator(".line").count() == 11
        assert page.locator("#history-chart polyline").count() == 11
        assert page.locator("#history-chart .data-blip").count() > 11
        assert page.evaluate("__tfl.rows.every(r => r.elo >= 100 && r.elo <= 3500)")
        assert page.locator("#leaderboard").bounding_box()["x"] < page.locator("#history").bounding_box()["x"]
        checks.append("Eleven authentic event-rated lines and chart; bounds preserved")
        page.screenshot(path=str(EVIDENCE / "desktop.png"), full_page=True)
        page.screenshot(path=str(ROOT / "examples/portfolio/preview.png"), full_page=True)
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), "Mobile overflow"
        page.screenshot(path=str(EVIDENCE / "mobile.png"), full_page=True)
        page.set_viewport_size({"width": 1280, "height": 900})
        checks.append("1280px / 390px layout without overflow")
        counts = []
        event_counts = []
        for hours in (1, 6, 24, 168, 720, 0):
            page.locator(f'#history [data-hours="{hours}"]').click()
            result = page.evaluate("window.__tflRange")
            assert result["hours"] == hours
            counts.append(result["count"])
            event_counts.append(result["events"])
        assert counts == sorted(counts), counts
        assert event_counts == sorted(event_counts), event_counts
        assert event_counts[-1] > 0 and counts[-1] >= event_counts[-1]
        page.locator(".line").first.click()
        assert page.locator("#history-chart polyline").count() == 1
        assert page.locator("#all-lines").is_visible()
        page.locator("#all-lines").click()
        assert page.locator("#history-chart polyline").count() == 11
        page.locator("#line-toggles input").first.uncheck()
        assert page.locator("#history-chart polyline").count() == 10
        page.locator("#all-lines").click()
        page.locator("details.tools summary").click()
        page.locator("#dataset").select_option("archive")
        page.wait_for_function("window.__tfl.dataset === 'archive'")
        assert page.locator("#history-chart polyline").count() == 11
        assert "archive" in page.locator("#updated").inner_text()
        page.screenshot(path=str(EVIDENCE / "archive.png"))
        page.locator("#dataset").select_option("live")
        with page.expect_download() as download:
            page.locator("#download").click()
        text = Path(download.value.path()).read_text()
        assert text.count("\n") == 11 and "on_time" in text
        page.get_by_text("Five-minute rating candles", exact=True).click()
        assert page.locator("#candle-chart svg").is_visible()
        page.locator("#candle-line").select_option("victoria")
        page.get_by_text("Recent sampled events", exact=True).click()
        assert page.locator(".event").count() > 0
        page.locator("#refresh").focus()
        page.keyboard.press("Tab")
        assert page.locator("#download").evaluate("el => getComputedStyle(el).outlineStyle") != "none"
        page.screenshot(path=str(EVIDENCE / "focus.png"))
        checks.append("Timeframes, focus/show-all, legend, archive, candles, events, CSV and keyboard focus")
        page.route("https://api.tfl.gov.uk/**", lambda route: route.abort())
        page.locator("#refresh").click()
        page.wait_for_function("!document.querySelector('#refresh').disabled")
        assert "unavailable" in page.locator("#connection").inner_text().lower()
        assert all("Status unavailable" in t for t in page.locator(".badge").all_inner_texts())
        page.screenshot(path=str(EVIDENCE / "service-unavailable.png"))
        checks.append("API outage clears stale service status and retains observations")
        fallback = browser.new_page(viewport={"width": 1280, "height": 900})
        fallback.on("pageerror", lambda error: errors.append(str(error)))
        fallback.route("https://raw.githubusercontent.com/**", lambda route: route.abort())
        fallback.route("https://api.tfl.gov.uk/**", lambda route: route.abort())
        fallback.goto(url, wait_until="networkidle")
        fallback.wait_for_function("window.__tfl?.ready")
        assert "bundled snapshot" in fallback.locator("#updated").inner_text()
        assert fallback.locator(".line").count() == 11
        fallback.screenshot(path=str(EVIDENCE / "bundled-fallback.png"), full_page=True)
        fallback.close()
        checks.append("Offline event snapshot retains its timestamp and explicit source label")
        failed = browser.new_page(viewport={"width": 390, "height": 844})
        failed.on("pageerror", lambda error: errors.append(str(error)))
        failed.route("https://raw.githubusercontent.com/**", lambda route: route.abort())
        failed.route("**/data/events.json", lambda route: route.abort())
        failed.route("https://api.tfl.gov.uk/**", lambda route: route.abort())
        failed.goto(url, wait_until="networkidle")
        failed.wait_for_function("!document.querySelector('#refresh').disabled")
        assert "unavailable" in failed.locator("#updated").inner_text()
        assert failed.locator("#download").is_disabled()
        assert "retry" in failed.locator("#notice").inner_text().lower()
        failed.screenshot(path=str(EVIDENCE / "load-failure.png"), full_page=True)
        failed.locator("details.tools summary").click()
        failed.locator("#dataset").select_option("archive")
        failed.wait_for_function("window.__tfl?.dataset === 'archive'")
        assert failed.locator(".line").count() == 11
        failed.close()
        checks.append("Total feed outage directs retry and archive recovery")
        assert not errors, errors
        assert page.evaluate("matchMedia('(prefers-reduced-motion: reduce)').matches")
        checks.append("No JavaScript errors; reduced motion enabled")
        (EVIDENCE / "audit.json").write_text(json.dumps({"checks": checks, "errors": errors, "viewports": [1280, 390]}, indent=2))
        print("PASS: " + "; ".join(checks))
        browser.close()
except Exception:
    raise
finally:
    server.shutdown()
