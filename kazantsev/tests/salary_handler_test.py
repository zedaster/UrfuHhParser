from unittest import TestCase

from kazantsev.currency_rates import CurrencyRates
from kazantsev.local_path import get_local_path
from kazantsev.salary_handler import handle_salaries


class SalaryHandlerTest(TestCase):
    def test_salary_handler(self):
        rates = CurrencyRates.from_csv(get_local_path('currency_rates.csv'))
        in_csv = get_local_path('./tests/vacancies_dif_currencies.csv')
        out_csv = get_local_path('./vacancies_one_currency.csv')
        handle_salaries(in_csv, out_csv, rates, limit=100)
