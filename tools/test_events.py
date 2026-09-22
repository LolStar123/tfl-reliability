import unittest
from collect_events import step,merge_predictions
class Events(unittest.TestCase):
 def test_bounds_and_recovery(self):
  for outcome in ['arrived','late','cancelled']:
   rating=1500
   for _ in range(100000):
    rating=step(rating,outcome,True,900)
    self.assertTrue(100<=rating<=3500)
   if outcome!='arrived':self.assertGreater(step(rating,'arrived'),rating)
 def test_two_sightings_once_and_no_phantom_cancellations(self):
  s={'lines':{'central':{'elo':1500,'on_time':0,'late':0,'cancelled':0}}}
  p={'lineId':'central','vehicleId':'1','naptanId':'stop','expectedArrival':'2026-09-22T10:00:25Z','timeToStation':25}
  merge_predictions(s,'central',[p],'2026-09-22T10:00:00+00:00');self.assertEqual(s['lines']['central']['on_time'],0)
  merge_predictions(s,'central',[p],'2026-09-22T10:00:20+00:00');self.assertEqual(s['lines']['central']['on_time'],1)
  merge_predictions(s,'central',[p],'2026-09-22T10:00:25+00:00');self.assertEqual(s['lines']['central']['on_time'],1)
  merge_predictions(s,'central',[],'2026-09-22T11:00:00+00:00');self.assertEqual(s['lines']['central']['cancelled'],0)


if __name__ == "__main__":
    unittest.main()
