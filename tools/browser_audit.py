import functools
import http.server
import os
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT/'examples/portfolio')))
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as p:
  b=p.chromium.launch(**({'channel':'chrome'} if os.name=='nt' else {}));page=b.new_page(viewport={'width':1280,'height':1000});errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(os.environ.get('AUDIT_URL',f'http://127.0.0.1:{server.server_port}'))
  page.wait_for_function('window.__tfl?.ready')
  page.wait_for_function('!document.querySelector("#refresh").disabled')
  assert page.locator('.line').count()==11
  assert page.evaluate('__tfl.rows.every(r=>r.elo>=100&&r.elo<=3500)')
  page.locator('#dataset').select_option('archive')
  page.locator('[data-view="history"]').click()
  assert page.locator('#history-chart polyline').count()==11
  page.locator('#line-toggles input').first.uncheck()
  assert page.locator('#history-chart polyline').count()==10
  page.locator('[data-view="candles"]').click()
  assert page.locator('#candle-chart rect').count()>1
  page.locator('#candle-line').select_option('victoria')
  page.locator('[data-view="leaderboard"]').click()
  page.locator('#dataset').select_option('live')
  with page.expect_download() as dl:page.locator('#download').click()
  assert dl.value.suggested_filename.endswith('.csv')
  page.set_viewport_size({'width':1280,'height':720})
  assert page.locator('.line').last.bounding_box()['y']+page.locator('.line').last.bounding_box()['height']<720,'all lines must fit landing viewport'
  page.screenshot(path=str(ROOT/'examples/portfolio/preview.png'))
  page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
  assert page.locator('.line').last.bounding_box()['y']+page.locator('.line').last.bounding_box()['height']<844,'all lines must fit phone landing viewport'
  page.route('https://api.tfl.gov.uk/**',lambda r:r.abort())
  page.locator('#refresh').click();page.wait_for_function('!document.querySelector("#refresh").disabled')
  assert page.locator('.line').count()==11
  assert not errors,errors
  print('PASS: 11 real lines, bounded ratings, selection, timeframe, export, mobile, API failure fallback')
  b.close()
finally:server.shutdown()
