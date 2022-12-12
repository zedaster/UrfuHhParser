import re
from unittest import TestCase

from kazantsev.local_path import LocalPath
from kazantsev.year_separated import YearSeparated


class YearSeparatedTest(TestCase):
    def test_100k_values(self):
        YearSeparated(LocalPath('./tests/vacancies_by_year_100k.csv'), 'published_at')
        name_regex = re.compile(r'^vacancies_by_year_100k_\d{4}.csv$')
        tables_list = [x.name for x in LocalPath('./year_separated').path.iterdir() if name_regex.match(x.name)]
        tables_set = set(tables_list)
        self.assertEqual(len(tables_set), len(tables_list))
        expected_set = set(f'vacancies_by_year_100k_{year}.csv' for year in range(2007, 2012))
        self.assertSetEqual(expected_set, tables_set)

    def test_many_values(self):
        YearSeparated(LocalPath('./tests/vacancies_by_year.csv'), 'published_at')
        name_regex = re.compile(r'^vacancies_by_year_\d{4}.csv$')
        tables_list = [x.name for x in LocalPath('./year_separated').path.iterdir() if name_regex.match(x.name)]
        tables_set = set(tables_list)
        self.assertEqual(len(tables_set), len(tables_list))
        expected_set = set(f'vacancies_by_year_{year}.csv' for year in range(2007, 2023))
        self.assertSetEqual(expected_set, tables_set)
