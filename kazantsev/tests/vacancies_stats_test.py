import io
from unittest import TestCase
from unittest.mock import patch

from kazantsev.hhparser import Report
from kazantsev.local_path import get_local_path
from kazantsev.vacancies_staticstics import *


class VacanciesStatsSpeedTest(TestCase):
    @classmethod
    def setUpClass(cls):
        YearSeparated(get_local_path('./tests/vacancies_by_year.csv'))

    year_salaries = {2007: 38916, 2008: 43646, 2009: 42492, 2010: 43846, 2011: 47451, 2012: 48243, 2013: 51510,
                     2014: 50658, 2015: 52696, 2016: 62675, 2017: 60935, 2018: 58335, 2019: 69467, 2020: 73431,
                     2021: 82690, 2022: 91795}
    year_counts = {2007: 2196, 2008: 17549, 2009: 17709, 2010: 29093, 2011: 36700, 2012: 44153, 2013: 59954,
                   2014: 66837, 2015: 70039, 2016: 75145, 2017: 82823, 2018: 131701, 2019: 115086, 2020: 102243,
                   2021: 57623, 2022: 18294}
    prof_salaries = {2007: 40936, 2008: 46417, 2009: 45030, 2010: 47242, 2011: 49111, 2012: 52382, 2013: 52385,
                     2014: 58169, 2015: 57032, 2016: 61834, 2017: 67484, 2018: 71551, 2019: 74633, 2020: 78800,
                     2021: 91625, 2022: 98050}
    prof_counts = {2007: 118, 2008: 1212, 2009: 1326, 2010: 2260, 2011: 2984, 2012: 3396, 2013: 4132, 2014: 4606,
                   2015: 4515, 2016: 6101, 2017: 6381, 2018: 7356, 2019: 6163, 2020: 4894, 2021: 2385, 2022: 653}

    def test_single_process_four_stats(self):
        stats = SingleProcessVacanciesStatistics(get_local_path('./tests/vacancies_by_year.csv'), 'программист')
        self.assertDictEqual(self.year_salaries, stats.salaries_by_year)
        self.assertDictEqual(self.year_counts, stats.counts_by_year)
        self.assertDictEqual(self.prof_salaries, stats.prof_salaries_by_year)
        self.assertDictEqual(self.prof_counts, stats.prof_counts_by_year)
        print(stats.top_10_salaries_by_cities)

    # def test_multi_process_four_stats(self):
    #     folder = get_local_path('./year_separated')
    #     stats = MultiProcessVacanciesStatics.from_chunk_folder(folder, 'программист')
    #     self.assertDictEqual(self.year_salaries, stats.salaries_by_year)
    #     self.assertDictEqual(self.year_counts, stats.counts_by_year)
    #     self.assertDictEqual(self.prof_salaries, stats.prof_salaries_by_year)
    #     self.assertDictEqual(self.prof_counts, stats.prof_counts_by_year)

    def test_concurrent_process_four_stats(self):
        folder = get_local_path('./year_separated')
        stats = ConcurrentFuturesVacanciesStatics.from_chunk_folder(folder, 'программист')
        self.assertDictEqual(self.year_salaries, stats.salaries_by_year)
        self.assertDictEqual(self.year_counts, stats.counts_by_year)
        self.assertDictEqual(self.prof_salaries, stats.prof_salaries_by_year)
        self.assertDictEqual(self.prof_counts, stats.prof_counts_by_year)

    #
    # def test_pandas_four_stats(self):
    #     rates = CurrencyRates.from_csv(get_local_path('currency_rates.csv'))
    #     stats = PandasVacanciesStatistics(get_local_path('./tests/vacancies_by_year.csv'), 'программист', rates)
    #     self.assertDictEqual(self.year_salaries, stats.salaries_by_year)
    #     self.assertDictEqual(self.year_counts, stats.counts_by_year)
    #     self.assertDictEqual(self.prof_salaries, stats.prof_salaries_by_year)
    #     self.assertDictEqual(self.prof_counts, stats.prof_counts_by_year)

    def test_pandas_four_stats(self):
        rates = CurrencyRates.from_csv(get_local_path('vacancies_one_currency.csv'))
        stats = PandasVacanciesStatistics(get_local_path('./tests/vacancies_by_year.csv'), 'программист', rates)
        self.assertDictEqual(self.year_salaries, stats.salaries_by_year)
        self.assertDictEqual(self.year_counts, stats.counts_by_year)
        self.assertDictEqual(self.prof_salaries, stats.prof_salaries_by_year)
        self.assertDictEqual(self.prof_counts, stats.prof_counts_by_year)


class VacanciesStatsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        YearSeparated(get_local_path('./tests/vacancies_by_year_100k.csv'))

    def _test_stats_print(self, stats, mock_stdout):
        Report(stats).print()
        with open(Path(__file__).with_name('coder_stats_test.txt'), mode='r', encoding='utf-8') as test_output:
            self.assertEqual(test_output.read(), mock_stdout.getvalue())

    def _test_zero_prof_salaries(self, stats):
        current_year = datetime.now().year
        self.assertDictEqual({current_year: 0}, stats.prof_salaries_by_year)

    def _test_zero_prof_counts(self, stats):
        current_year = datetime.now().year
        self.assertDictEqual({current_year: 0}, stats.prof_counts_by_year)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_single_stats_print(self, mock_stdout):
        main_csv = get_local_path('./tests/vacancies_by_year_100k.csv')
        stats = SingleProcessVacanciesStatistics(main_csv, 'Программист')
        self._test_stats_print(stats, mock_stdout)

    # @patch('sys.stdout', new_callable=io.StringIO)
    # def test_multi_stats_print(self, mock_stdout):
    #     main_csv = get_local_path('./tests/vacancies_by_year_100k.csv')
    #     folder = get_local_path('./year_separated/')
    #     stats = MultiProcessVacanciesStatics.from_chunk_folder(main_csv, folder, 'Программист')
    #     self._test_stats_print(stats, mock_stdout)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_concurrent_stats_print(self, mock_stdout):
        folder = get_local_path('./year_separated/')
        stats = ConcurrentFuturesVacanciesStatics.from_chunk_folder(folder, 'Программист')
        self._test_stats_print(stats, mock_stdout)

    def test_single_zero_prof_salaries(self):
        main_csv = get_local_path('./tests/empty.csv')
        stats = SingleProcessVacanciesStatistics(main_csv, 'Программист')
        self._test_zero_prof_salaries(stats)

    # def test_multi_zero_prof_salaries(self):
    #     main_csv = get_local_path('./tests/empty.csv')
    #     folder = get_local_path('./tests/empty_folder')
    #     stats = MultiProcessVacanciesStatics.from_chunk_folder(main_csv, folder, 'Программист')
    #     self._test_zero_prof_salaries(stats)

    def test_concurrent_zero_prof_salaries(self):
        folder = get_local_path('./tests/empty_folder')
        stats = ConcurrentFuturesVacanciesStatics.from_chunk_folder(folder, 'Программист')
        self._test_zero_prof_salaries(stats)

    def test_single_zero_prof_counts(self):
        main_csv = get_local_path('./tests/empty.csv')
        stats = SingleProcessVacanciesStatistics(main_csv, 'Программист')
        self._test_zero_prof_counts(stats)

    # def test_multi_zero_prof_counts(self):
    #     main_csv = get_local_path('./tests/empty.csv')
    #     folder = get_local_path('./tests/empty_folder')
    #     stats = MultiProcessVacanciesStatics.from_chunk_folder(main_csv, folder, 'Программист')
    #     self._test_zero_prof_counts(stats)

    def test_concurrent_zero_prof_counts(self):
        folder = get_local_path('./tests/empty_folder')
        stats = ConcurrentFuturesVacanciesStatics.from_chunk_folder(folder, 'Программист')
        self._test_zero_prof_counts(stats)
