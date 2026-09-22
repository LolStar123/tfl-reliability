"""Sample live train predictions; resolve near-stop evidence without inventing cancellations."""
import json
import math
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tfl_train_event_elo import ALL_TUBE_LINES, http_get_json, compute_event_delta, is_peak_london_time


def step(rating, outcome, peak=False, lateness=0):
    if not math.isfinite(rating): raise ValueError('Non-finite rating')
    rating=max(100,min(3500,rating));distance=rating-1500;span=2000 if distance>=0 else 1400
    return max(100,min(3500,rating+compute_event_delta(rating,outcome,peak,lateness)-32*(distance/span)**3))


def merge_predictions(state, line_id, predictions, at):
    now=datetime.fromisoformat(at).timestamp()
    if not isinstance(predictions,list):raise ValueError('Expected arrival prediction list')
    seen=state.setdefault('pending',{})
    for p in predictions:
        if p.get('lineId')!=line_id or not p.get('vehicleId') or not p.get('naptanId'):continue
        tts=p.get('timeToStation');expected=p.get('expectedArrival')
        if not isinstance(tts,(int,float)) or not expected:continue
        key='|'.join(str(p.get(k,'')) for k in ['lineId','vehicleId','naptanId','direction','destinationNaptanId'])
        old=seen.get(key)
        if old and now-old['last']>900: old=None
        rec=old or {'first_expected':expected,'first':now,'resolved':False,'sightings':0}
        rec.update(last=now,sightings=rec['sightings']+1);seen[key]=rec
        # A near-stop observation is an arrival estimate, not proof of a completed stop.
        # A disappearing prediction is NEVER classified as a cancellation.
        if rec['resolved'] or not 0<=tts<=30:continue
        drift=max(0,(datetime.fromisoformat(expected.replace('Z','+00:00'))-datetime.fromisoformat(rec['first_expected'].replace('Z','+00:00'))).total_seconds())
        if rec['sightings']<2:continue
        outcome='late' if drift>60 else 'arrived';row=state['lines'][line_id]
        row['elo']=step(row['elo'],outcome,is_peak_london_time(expected),drift)
        row['late' if outcome=='late' else 'on_time']+=1
        rec['resolved']=True
        state.setdefault('events',[]).append({'at':at,'line_id':line_id,'station':p.get('stationName',''),'outcome':outcome,'delay_seconds':round(drift),'elo':row['elo']})
    state['pending']={k:v for k,v in seen.items() if now-v['last']<1800}


def main():
    path=Path('observations/events.json');state=json.loads(path.read_text()) if path.exists() else {'started':datetime.now(timezone.utc).isoformat(),'lines':{i:{'id':i,'name':n,'elo':1500.,'on_time':0,'late':0,'cancelled':0} for i,n in ALL_TUBE_LINES},'history':[],'events':[],'pending':{}}
    failures=[]
    for cycle in range(3):
        def fetch(line):
            try:return line[0],http_get_json(f'https://api.tfl.gov.uk/Line/{line[0]}/Arrivals',timeout=15),None
            except Exception as e:return line[0],None,type(e).__name__
        with ThreadPoolExecutor(max_workers=4) as pool:
            for line_id,payload,error in pool.map(fetch,ALL_TUBE_LINES):
                if error:failures.append(line_id);continue
                merge_predictions(state,line_id,payload,datetime.now(timezone.utc).isoformat())
        if cycle<2:time.sleep(20)
    at=datetime.now(timezone.utc).isoformat();state['updated']=at
    state['history'].append({'at':at,'ratings':{i:r['elo'] for i,r in state['lines'].items()}})
    state['history']=state['history'][-4320:];state['events']=state['events'][-2000:]
    if len(failures)==33:raise RuntimeError('All arrival requests failed; refusing to stamp a successful collection')
    path.parent.mkdir(exist_ok=True);path.write_text(json.dumps(state,separators=(',',':')))
    public={k:v for k,v in state.items() if k!='pending'};public['failed_requests']=len(failures);public['sampling']='Three polls, 20 seconds apart, every ten minutes. Arrival estimates require two sightings and a prediction within 30 seconds. Late means ETA slipped over 60 seconds since first sighting. Missing trains are not assumed cancelled.'
    Path('examples/portfolio/data/events.json').write_text(json.dumps(public,separators=(',',':')))
    print(f"Resolved {sum(r['on_time']+r['late'] for r in state['lines'].values())} sampled stop calls; {len(failures)} failed requests")

if __name__=='__main__':main()
