from datetime import datetime, timezone, timedelta
from unittest import TestCase

from kazantsev.currency_rates import CurrencyRates
from kazantsev.local_path import get_local_path


class CurrencyRatesTest(TestCase):
    def test_get_rate(self):
        rates = CurrencyRates.from_csv(get_local_path('./currency_rates.csv'))
        rate = rates.get_rate('USD', datetime(2006, 2, 3, tzinfo=timezone(timedelta(hours=4))))
        self.assertEqual(28.1994, rate)
