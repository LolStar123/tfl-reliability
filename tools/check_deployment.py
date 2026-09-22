"""Check the public feed after deployment, including CDN propagation."""
import json
import time
import urllib.request
from pathlib import Path
from audit_public import audit
expected = json.loads(Path('examples/portfolio/data/network.json').read_text())['updated']
url = 'https://lolstar123.github.io/tfl-reliability/data/network.json'
for attempt in range(6):
    try:
        req = urllib.request.Request(url + '?check=' + str(time.time_ns()), headers={'Cache-Control':'no-cache'})
        with urllib.request.urlopen(req, timeout=20) as response: feed = json.load(response)
        if feed['updated'] != expected: raise ValueError('Public deployment has not reached the collected timestamp')
        print(json.dumps(audit(feed), indent=2))
        break
    except Exception as exc:
        if attempt == 5: raise
        print(f'Public verification retry {attempt+1}: {exc}', flush=True)
        time.sleep(10)
