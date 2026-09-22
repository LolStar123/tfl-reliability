import unittest
from datetime import datetime, timezone, timedelta
from collect_public import merge, ranking

class PublicFeed(unittest.TestCase):
    def payload(self, severity=10):
        return [{'id':str(i),'name':str(i),'lineStatuses':[{'statusSeverity':severity,'statusSeverityDescription':'status'}]} for i in range(11)]
    def test_bucket_replaces_not_inflates(self):
        now=datetime(2026,9,22,10,0,tzinfo=timezone.utc)
        a=merge({},self.payload(),now)
        b=merge(a,self.payload(6),now+timedelta(minutes=3))
        self.assertEqual(len(b['snapshots']),1)
        self.assertLess(ranking(b)[0]['elo'],1516.1)
        c=merge(b,self.payload(),now+timedelta(minutes=16))
        self.assertEqual(len(c['snapshots']),2)
    def test_closed_not_scored_and_partial_feed_rejected(self):
        now=datetime.now(timezone.utc)
        r=ranking(merge({},self.payload(20),now))
        self.assertEqual(r[0]['elo'],1500)
        self.assertIsNone(r[0]['good_share'])
        with self.assertRaises(ValueError):merge({},self.payload()[:3],now)

if __name__=='__main__':unittest.main()
