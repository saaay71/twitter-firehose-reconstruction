import unittest
from datetime import datetime
import pytz
from snowflake import daysSinceEpoch

class SnowflakeTest(unittest.TestCase):
    def test(self):
        epochDay = datetime(1970,1,1, tzinfo=pytz.UTC).timestamp()
        self.assertEqual(daysSinceEpoch(epochDay), 0)

        oneYear = datetime(1971,1,1, tzinfo=pytz.UTC).timestamp()
        self.assertEqual(daysSinceEpoch(oneYear), 365)

        randomDate = datetime(1976,2,3, tzinfo=pytz.UTC).timestamp()
        self.assertEqual(daysSinceEpoch(randomDate), 6*365 + 1 + 31 + 2)