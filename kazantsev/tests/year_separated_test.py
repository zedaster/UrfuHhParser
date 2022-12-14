import re
from unittest import TestCase

from kazantsev.local_path import get_local_path
from kazantsev.year_separated import YearSeparated


class YearSeparatedTest(TestCase):
    def test_100k_values(self):
        YearSeparated(get_local_path('./tests/vacancies_by_year_100k.csv'), 'published_at')
        tables_list = [x.name for x in get_local_path('./year_separated').path.iterdir()]
        tables_set = set(tables_list)
        self.assertEqual(len(tables_set), len(tables_list))
        expected_set = set(f'vacancies_by_year_100k_{year}.csv' for year in range(2007, 2012))
        self.assertSetEqual(expected_set, tables_set)

    def test_many_values(self):
        YearSeparated(get_local_path('./tests/vacancies_by_year.csv'), 'published_at')
        tables_list = [x.name for x in get_local_path('./year_separated').path.iterdir()]
        tables_set = set(tables_list)
        self.assertEqual(len(tables_set), len(tables_list))
        expected_set = set(f'vacancies_by_year_{year}.csv' for year in range(2007, 2023))
        self.assertSetEqual(expected_set, tables_set)
