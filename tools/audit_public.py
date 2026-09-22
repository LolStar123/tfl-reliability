"""Fail collection if real ratings are stale, unbounded, or disagree with the browser."""
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from collect_public import ranking


def audit(feed, now=None):
    now = now or datetime.now(timezone.utc)
    age = (now - datetime.fromisoformat(feed['updated'].replace('Z', '+00:00'))).total_seconds()
    if not -60 <= age <= 1800:
        raise ValueError(f'Feed timestamp is stale or in the future: {age:.0f}s')
    rows = ranking(feed)
    if len(rows) != 11 or len({r['id'] for r in rows}) != 11:
        raise ValueError('Expected eleven distinct lines')
    for row in rows:
        if not math.isfinite(row['elo']) or not 100 <= row['elo'] <= 3500:
            raise ValueError(f"Unbounded rating: {row['id']}")
    script = "import {leaderboard} from './examples/portfolio/live.mjs'; let s=''; for await (const c of process.stdin) s+=c; console.log(JSON.stringify(leaderboard(JSON.parse(s), 24*31)));"
    js = json.loads(subprocess.run(['node', '--input-type=module', '-e', script], input=json.dumps(feed), text=True, capture_output=True, check=True).stdout)
    for row in rows:
        browser = next(r for r in js if r['id'] == row['id'])
        if abs(browser['elo'] - row['elo']) > 1e-8:
            raise ValueError(f"Python/browser disagreement: {row['id']}")
    return {'checked_at': now.isoformat(), 'observation_at': feed['updated'], 'lines': len(rows),
            'min_rating': min(r['elo'] for r in rows), 'max_rating': max(r['elo'] for r in rows),
            'snapshots': len(feed['snapshots']), 'python_browser_agree': True, 'healthy': True}

if __name__ == '__main__':
    path = Path('examples/portfolio/data/network.json')
    result = audit(json.loads(path.read_text(encoding='utf-8')))
    Path('examples/portfolio/data/health.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
