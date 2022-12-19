from datetime import datetime, timezone, timedelta
from unittest import TestCase

from kazantsev.currency_frequency import get_min_max_datetimes, get_most_frequency_currencies
from kazantsev.currency_rates import CurrencyRates
from kazantsev.local_path import get_local_path


class CurrencyRatesTest(TestCase):
    def test_loading_currency_rates(self):
        path = get_local_path('./tests/vacancies_dif_currencies.csv')
        min_date, max_date = get_min_max_datetimes(path)
        currencies = get_most_frequency_currencies(path)
        rates = CurrencyRates.from_api(currencies, min_date, max_date)
        rates.save_to_csv(get_local_path('currency_rates.csv'))

    def test_get_rate(self):
        rates = CurrencyRates.from_csv(get_local_path('./currency_rates.csv'))
        rate = rates.get_rate('USD', datetime(2006, 2, 3, tzinfo=timezone(timedelta(hours=4))))
        self.assertEqual(28.1994, rate)
