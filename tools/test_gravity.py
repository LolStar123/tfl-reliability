import json
import subprocess
import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tfl_line_elo import calculate_elo_for_line

class BandGravity(unittest.TestCase):
    def test_long_runs_and_recovery(self):
        bad = [{'status_severity': 0, 'reason': 'cancelled'}] * 100000
        good = [{'status_severity': 10, 'reason': ''}] * 100000
        low = calculate_elo_for_line(bad, 1500, 32)[0]
        high = calculate_elo_for_line(good, 1500, 32)[0]
        self.assertTrue(100 < low < 1500 < high < 3500)
        self.assertGreater(calculate_elo_for_line(bad + good[:100], 1500, 32)[0], low + 100)
        self.assertLess(calculate_elo_for_line(good + bad[:100], 1500, 32)[0], high - 100)
        print(f'100,000 observations: cancellation equilibrium {low:.2f}; good service {high:.2f}')

    def test_browser_parity_under_extremes(self):
        events = [{'severity': (i * 7) % 11, 'reason': 'cancelled' if i % 3 == 0 else ''} for i in range(2000)]
        script = "import {rate} from './examples/portfolio/model.mjs';let s='';for await(const c of process.stdin)s+=c;console.log(JSON.stringify(rate(JSON.parse(s))));"
        result = json.loads(subprocess.run(['node','--input-type=module','-e',script],input=json.dumps(events),text=True,capture_output=True,check=True).stdout)
        py = calculate_elo_for_line([{'status_severity':e['severity'],'reason':e['reason']} for e in events],1500,32)[0]
        self.assertAlmostEqual(py,result['elo'],places=8)
        self.assertTrue(all(100 <= x <= 3500 for x in result['history']))

    def test_invalid_parameters(self):
        for base, k in [(float('nan'),32),(1500,float('inf')),(0,32),(3500,32),(1500,-1)]:
            with self.assertRaises(ValueError): calculate_elo_for_line([],base,k)


if __name__ == "__main__":
    unittest.main()
