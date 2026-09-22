"""Collect real network observations and build the public reliability feed."""
import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tfl_line_elo import fetch_line_statuses, calculate_elo_for_line


def merge(history, payload, now):
    if not isinstance(payload, list) or len(payload) != 11:
        raise ValueError('Expected all eleven Tube lines; preserving the previous feed.')
    rows = []
    for line in payload:
        states = line.get('lineStatuses', [])
        if not states or any('statusSeverity' not in s for s in states):
            raise ValueError('Incomplete line status; preserving the previous feed.')
        # A closed service is a timetable state, not an observed failure.
        operational = [s for s in states if s['statusSeverity'] != 20]
        selected = min(operational, key=lambda s: s['statusSeverity']) if operational else states[0]
        rows.append({'id': line['id'], 'name': line['name'], 'severity': selected['statusSeverity'],
                     'status': selected['statusSeverityDescription'],
                     'reason': ' '.join(dict.fromkeys(s.get('reason', '').strip() for s in states)).strip()})
    timestamp = now.isoformat()
    cutoff = (now - timedelta(days=30)).isoformat()
    # At most one observation per ten-minute bucket, including manual dispatches.
    bucket = int(now.timestamp()) // 600
    snapshots = [s for s in history.get('snapshots', []) if s['at'] >= cutoff and int(datetime.fromisoformat(s['at']).timestamp()) // 600 != bucket]
    snapshots.append({'at': timestamp, 'lines': rows})
    return {'schema': 1, 'source': 'https://api.tfl.gov.uk/Line/Mode/tube/Status',
            'started': history.get('started', timestamp), 'updated': timestamp, 'cadence_minutes': 10,
            'snapshots': sorted(snapshots, key=lambda s: s['at'])}


def ranking(history):
    result = []
    latest = history['snapshots'][-1]
    for line in latest['lines']:
        observations = [r for s in history['snapshots'] for r in s['lines'] if r['id'] == line['id'] and r['severity'] != 20]
        events = [{'status_severity': r['severity'], 'reason': r['reason']} for r in observations]
        elo, stats, good_ratio = calculate_elo_for_line(events, 1500, 32)
        result.append({**line, 'elo': elo, 'observations': len(events), 'good_share': good_ratio if events else None})
    return sorted(result, key=lambda r: (-r['elo'], r['name']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--history', default='observations/history.json')
    parser.add_argument('--output', default='examples/portfolio/data/network.json')
    args = parser.parse_args()
    path = Path(args.history)
    history = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    payload = fetch_line_statuses('tube', None, None)
    history = merge(history, payload, datetime.now(timezone.utc))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(history, separators=(',', ':')), encoding='utf-8')
    output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({**history, 'rankings': ranking(history)}, separators=(',', ':')), encoding='utf-8')
    print(f"Published {len(history['snapshots'])} real network observations; latest {history['updated']}")


if __name__ == '__main__':
    main()
