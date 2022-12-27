import concurrent.futures as pool
import csv
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd

from kazantsev.currency_rates import CurrencyRates
from kazantsev.datetime_parser import parse_pd_datetime
from kazantsev.models import Vacancy
from kazantsev.salary_handler import unite_salaries
from kazantsev.year_separated import YearSeparated


class AvgCounter:
    """
    Класс для подсчета среднего арифметического значения

    Attributes:
        value (float): Среднее арифметическое значение
    """

    def __init__(self, *values):
        """
        Инициализирует объект счетчика среднего арифметического
        :param values: Значения для счетчика
        :type values: float
        """
        self._sum = sum(values)
        self._len = len(values)
        if self._len != 0:
            self.value = self._sum / self._len

    def add(self, value):
        """
        Добавляет значение для подсчета
        :param value: Значение
        :type value: float
        :return: None
        """
        self._sum += value
        self._len += 1
        self.value = self._sum / self._len

    @property
    def sum(self):
        return self._sum

    @property
    def len(self):
        return self._len

    def concat(self, other_counter):
        return AvgCounter.unite_many(self, other_counter)

    @staticmethod
    def unite_many(*counters):
        """
        Объединяет множество счетчиков среднее числа в один
        :param counters: счетчики
        :type counters: AvgCounter
        :return: Объединенный счетчик
        :rtype: AvgCounter
        """
        counter = AvgCounter()
        counter._sum = sum(c.sum for c in counters)
        counter._len = sum(c.len for c in counters)
        counter.value = counter.sum / counter.len
        return counter


class VacanciesStatistics(ABC):
    @property
    @abstractmethod
    def prof_name(self):
        pass

    @property
    @abstractmethod
    def salaries_by_year(self):
        pass

    @property
    @abstractmethod
    def counts_by_year(self):
        pass

    @property
    @abstractmethod
    def prof_salaries_by_year(self):
        pass

    @property
    @abstractmethod
    def prof_counts_by_year(self):
        pass

    @property
    @abstractmethod
    def vacancies_count(self):
        pass

    @property
    @abstractmethod
    def avg_counters_by_cities(self):
        pass

    @property
    @abstractmethod
    def top_10_salaries_by_cities(self):
        pass

    @property
    @abstractmethod
    def top_10_cities_shares(self):
        pass

    def get_top_10_percent_cities_shares(self, digits=None):
        """
        Возвращает топ 10 городов, где больше всего доля вакансий в процентах
        :return: Словарь город - доля (в процетах) с 10 значениями в порядке убывания
        :rtype: Dict[str, float]
        """
        handler = lambda n: 100 * n
        if digits is not None:
            handler = lambda n: round(100 * n, digits)

        return {k: handler(v) for k, v in self.top_10_cities_shares.items()}


class SingleProcessVacanciesStatistics(VacanciesStatistics):
    def __init__(self, path: Path, prof_name: str):
        """
        Инициализирует объект класса для определенной професии и прогружает вакансии
        :param path: Путь к файлу с таблицей
        :type path: Path
        :param prof_name: Название професии
        :type prof_name: str
        """
        self.path = path
        self._prof_name = prof_name

        self._salaries_by_year = {}
        self._counts_by_year = {}
        self._prof_salaries_by_year = {}
        self._prof_counts_by_year = {}
        self._salaries_by_cities = {}

        self._counts_by_cities = {}
        self._vacancies_count = 0
        self._init_data()

    @property
    def prof_name(self):
        return self._prof_name

    def _init_data(self):
        """
        Подгружает данные из файла и получает по нему статистику
        :return: None
        """
        with open(self.path.absolute(), 'r', encoding='utf_8_sig') as file:
            reader = csv.reader(file)
            title_row = None
            for row in reader:
                if title_row is None:
                    title_row = row
                    continue
                row_dict = self._to_row_dict(title_row, row)
                if row_dict is None:
                    continue
                vacancy = Vacancy.parse_from_dict(row_dict)
                self._update_statistics(vacancy)

    def _update_statistics(self, vacancy):
        """
        Обновляет статистику в объекте по данной вакансиий
        :param vacancy: Вакансия
        :type vacancy: Vacancy
        :return: None
        """

        def change_salary_and_count_stats(salaries: dict, counts: dict, key, salary):
            if key not in salaries:
                salaries[key] = AvgCounter(salary)
                counts[key] = 1
            else:
                salaries[key].add(salary)
                counts[key] += 1

        salary = vacancy.salary.avg_ruble_amount
        year = vacancy.year
        # Year stats
        change_salary_and_count_stats(self._salaries_by_year, self._counts_by_year, year, salary)

        # City stats
        self._vacancies_count += 1
        city = vacancy.area_name
        change_salary_and_count_stats(self._salaries_by_cities, self._counts_by_cities, city, salary)

        # Prof stats
        if self.prof_name not in vacancy.name:
            return
        change_salary_and_count_stats(self._prof_salaries_by_year, self._prof_counts_by_year, year, salary)

    @property
    def salaries_by_year(self):
        """
        Возвращает зарплаты по годам для всех профессий
        :return: Словарь год => средняя зарплата
        :rtype: Dict[int, float]
        """
        return dict(map(lambda item: (item[0], int(item[1].value)), self._salaries_by_year.items()))

    @property
    def counts_by_year(self):
        return self._counts_by_year

    @property
    def prof_salaries_by_year(self):
        """
        Возвращает зарплаты по годам для профессий self.prof_name
        :return: Словарь год => средняя зарплата
        :rtype: Dict[int, float]
        """
        if len(self._prof_salaries_by_year) == 0:
            return {datetime.now().year: 0}
        return dict(map(lambda item: (item[0], int(item[1].value)), self._prof_salaries_by_year.items()))

    @property
    def prof_counts_by_year(self):
        """
        Возвращает количество вакансий по годам для профессий self.prof_name
        :return: Словарь год => кол-во вакансий
        :rtype: Dict[int, int]
        """
        if len(self._prof_counts_by_year) == 0:
            return {datetime.now().year: 0}
        return self._prof_counts_by_year

    def _one_percent_filter(self, items_by_cities):
        """
        Фильтрует пары город и выдает только те, города которых занимают >= 1% от списка всех вакансий
        :param items_by_cities: Коллекция из кортежа (город, значение)
        :type items_by_cities: Iterable[Tuple[str, any]]
        :return: Пары, города которых занимают >= 1% от списка всех вакансий
        :rtype: Iterable[Tuple[str, any]]
        """
        one_percent = self._vacancies_count / 100
        for city, value in items_by_cities:
            if self._counts_by_cities[city] >= one_percent:
                yield city, value

    @property
    def top_10_salaries_by_cities(self):
        """
        Возвращает топ 10 пар город-зарплата
        :return: Словарь город - зарплата с 10 значениями в порядке убывания
        :rtype: Dict[str, int]
        """
        salaries = map(lambda item: (item[0], int(item[1].value)), self._salaries_by_cities.items())
        filtered_items = self._one_percent_filter(salaries)
        return dict(sorted(filtered_items, key=lambda item: -item[1])[:10])

    @property
    def top_10_cities_shares(self):
        """
        Возвращает топ 10 городов, где больше всего доля вакансий
        :return: Словарь город - доля (от 0 до 1) с 10 значениями в порядке убывания
        :rtype: Dict[str, float]
        """
        result = {}
        for city, count in self._one_percent_filter(self._counts_by_cities.items()):
            result[city] = round(count / self._vacancies_count, 4)
        return dict(sorted(result.items(), key=lambda item: -item[1])[:10])

    @staticmethod
    def _to_row_dict(title_row, row):
        """
        Преобразует заголовочную строку и строку со значениями в словарь вакансии
        :param title_row: Заголовочная строка
        :type title_row: List[str]
        :param row: Строка со значениями
        :type row: List[str]
        :return: Словарь вакансии
        :rtype: Dict[str, str]
        """
        if len(title_row) != len(row):
            return None
        row_dict = {}
        for i in range(len(row)):
            if row[i] == '':
                return None
            row_dict[title_row[i]] = row[i]
        return row_dict

    @property
    def vacancies_count(self):
        return self._vacancies_count

    @property
    def avg_counters_by_cities(self):
        return self._salaries_by_cities


# class MultiProcessVacanciesStatics(VacanciesStatistics):
#     def __init__(self, general_table: Path, chunk_paths: Iterable[Path], prof_name: str, preload_city_stats=False):
#         self._prof_name = prof_name
#         self._general_table = general_table
#
#         with multiprocessing.Manager() as manager:
#             chunk_dicts = manager.dict({
#                 'salaries': manager.dict(),
#                 'counts': manager.dict(),
#                 'prof_salaries': manager.dict(),
#                 'prof_counts': manager.dict(),
#             })
#
#             city_dicts = manager.dict({
#                 'top_10_salaries_by_cities': manager.dict(),
#                 'top_10_cities_shares': manager.dict(),
#             })
#
#             general_table_process = Process(target=self._handle_general_table,
#                                             args=(self._prof_name, general_table, city_dicts))
#             if preload_city_stats:
#                 general_table_process.start()
#
#             chunk_processes = []
#             for path in chunk_paths:
#                 process = Process(target=self._handle_one_chunk, args=(self._prof_name, path, chunk_dicts))
#                 process.start()
#                 chunk_processes.append(process)
#
#             for process in chunk_processes:
#                 process.join()
#
#             self._salaries_by_year = dict(chunk_dicts['salaries'])
#             self._counts_by_year = dict(chunk_dicts['counts'])
#             self._prof_salaries_by_year = dict(chunk_dicts['prof_salaries'])
#             self._prof_counts_by_year = dict(chunk_dicts['prof_counts'])
#
#             self._city_stats_loaded = preload_city_stats
#             if preload_city_stats:
#                 general_table_process.join()
#                 self._top_10_salaries_by_cities = dict(city_dicts['top_10_salaries_by_cities'])
#                 self._top_10_cities_shares = dict(city_dicts['top_10_cities_shares'])
#
#     def _load_city_stats(self):
#         with multiprocessing.Manager() as manager:
#             city_dicts = manager.dict({
#                 'top_10_salaries_by_cities': manager.dict(),
#                 'top_10_cities_shares': manager.dict(),
#             })
#             args = (self._prof_name, self._general_table, city_dicts)
#             general_table_process = Process(target=self._handle_general_table, args=args)
#             general_table_process.start()
#             general_table_process.join()
#             self._top_10_salaries_by_cities = dict(city_dicts['top_10_salaries_by_cities'])
#             self._top_10_cities_shares = dict(city_dicts['top_10_cities_shares'])
#             self._city_stats_loaded = True
#
#     @staticmethod
#     def _handle_one_chunk(prof_name, path: Path, dicts):
#         stats = SingleProcessVacanciesStatistics(path, prof_name)
#         dicts['salaries'].update(stats.salaries_by_year)
#         dicts['counts'].update(stats.counts_by_year)
#         dicts['prof_salaries'].update(stats.prof_salaries_by_year)
#         dicts['prof_counts'].update(stats.prof_counts_by_year)
#
#     @staticmethod
#     def _handle_general_table(prof_name, path: Path, dicts):
#         stats = SingleProcessVacanciesStatistics(path, prof_name)
#         dicts['top_10_salaries_by_cities'].update(stats.top_10_salaries_by_cities)
#         dicts['top_10_cities_shares'].update(stats.top_10_cities_shares)
#
#     @staticmethod
#     def from_chunk_folder(general_table: Path, chunk_folder: Path, prof_name: str):
#         return MultiProcessVacanciesStatics(general_table, (p for p in chunk_folder.rglob('*')), prof_name)
#
#     @staticmethod
#     def from_year_separated(year_separated: YearSeparated, prof_name: str):
#         return MultiProcessVacanciesStatics(year_separated.main_csv_path, year_separated.chunk_csv_paths, prof_name)
#
#     @property
#     def prof_name(self):
#         return self._prof_name
#
#     @property
#     def salaries_by_year(self):
#         if len(self._salaries_by_year) == 0:
#             return {datetime.now().year: 0}
#         return self._salaries_by_year
#
#     @property
#     def counts_by_year(self):
#         if len(self._counts_by_year) == 0:
#             return {datetime.now().year: 0}
#         return self._counts_by_year
#
#     @property
#     def prof_salaries_by_year(self):
#         if len(self._prof_salaries_by_year) == 0:
#             return {datetime.now().year: 0}
#         return self._prof_salaries_by_year
#
#     @property
#     def prof_counts_by_year(self):
#         if len(self._prof_counts_by_year) == 0:
#             return {datetime.now().year: 0}
#         return self._prof_counts_by_year
#
#     @property
#     def top_10_salaries_by_cities(self):
#         if not self._city_stats_loaded:
#             self._load_city_stats()
#         return self._top_10_salaries_by_cities
#
#     @property
#     def top_10_cities_shares(self):
#         if not self._city_stats_loaded:
#             self._load_city_stats()
#         return self._top_10_cities_shares


class ConcurrentFuturesVacanciesStatics(VacanciesStatistics):
    def __init__(self, chunk_paths: Iterable[Path], prof_name: str):
        self._prof_name = prof_name
        self._salaries_by_year = dict()
        self._counts_by_year = dict()
        self._prof_salaries_by_year = dict()
        self._prof_counts_by_year = dict()
        self._avg_counters_by_cities = dict()
        self._vacancies_count = 0

        with pool.ProcessPoolExecutor() as executor:
            for chunk_stats in executor.map(self._handle_one_chunk, chunk_paths, timeout=None):
                self._salaries_by_year.update(chunk_stats.salaries_by_year)
                self._counts_by_year.update(chunk_stats.counts_by_year)
                self._prof_salaries_by_year.update(chunk_stats.prof_salaries_by_year)
                self._prof_counts_by_year.update(chunk_stats.prof_counts_by_year)
                for city, counter in chunk_stats.avg_counters_by_cities.items():
                    if city in self._avg_counters_by_cities:
                        self._avg_counters_by_cities[city] = self._avg_counters_by_cities[city].concat(counter)
                    else:
                        self._avg_counters_by_cities[city] = counter
                    self._vacancies_count += counter.len

        self._init_counts_by_cities()
        self._init_city_salaries()

    def _init_counts_by_cities(self):
        counts = map(lambda item: (item[0], item[1].len), self.avg_counters_by_cities.items())
        one_percent = self.vacancies_count / 100
        accept_counts = filter(lambda x: x[1] >= one_percent, counts)
        top_10_counts = sorted(accept_counts, key=lambda item: -item[1])[:10]
        self._top_10_cities_shares = dict(map(lambda x: (x[0], round(x[1] / self.vacancies_count, 4)), top_10_counts))

    def _init_city_salaries(self):
        one_percent = self.vacancies_count / 100
        accepted_items = filter(lambda x: x[1].len >= one_percent, self.avg_counters_by_cities.items())
        salaries = map(lambda item: (item[0], int(item[1].value)), accepted_items)
        self._top_10_salaries_by_cities = dict(sorted(salaries, key=lambda item: -item[1])[:10])

    def _handle_one_chunk(self, path: Path):
        stats = SingleProcessVacanciesStatistics(path, self._prof_name)
        return stats

    @staticmethod
    def from_chunk_folder(chunk_folder: Path, prof_name: str):
        return ConcurrentFuturesVacanciesStatics((p for p in chunk_folder.rglob('*')), prof_name)

    @staticmethod
    def from_year_separated(year_separated: YearSeparated, prof_name: str):
        return ConcurrentFuturesVacanciesStatics(year_separated.chunk_csv_paths,
                                                 prof_name)

    @property
    def prof_name(self):
        return self._prof_name

    @property
    def vacancies_count(self):
        return self._vacancies_count

    @property
    def avg_counters_by_cities(self):
        return self._avg_counters_by_cities

    @property
    def salaries_by_year(self):
        if len(self._salaries_by_year) == 0:
            return {datetime.now().year: 0}
        return self._salaries_by_year

    @property
    def counts_by_year(self):
        if len(self._counts_by_year) == 0:
            return {datetime.now().year: 0}
        return self._counts_by_year

    @property
    def prof_salaries_by_year(self):
        if len(self._prof_salaries_by_year) == 0:
            return {datetime.now().year: 0}
        return self._prof_salaries_by_year

    @property
    def prof_counts_by_year(self):
        if len(self._prof_counts_by_year) == 0:
            return {datetime.now().year: 0}
        return self._prof_counts_by_year

    @property
    def top_10_salaries_by_cities(self):
        return self._top_10_salaries_by_cities

    @property
    def top_10_cities_shares(self):
        return self._top_10_cities_shares


class PandasVacanciesStatistics(VacanciesStatistics):
    def __init__(self, path: Path, prof_name: str, rates: CurrencyRates):
        self.path = path
        self._prof_name = prof_name
        # parse_dates=['published_at'] не работает, см.
        # https://stackoverflow.com/questions/74921547/how-to-parse-a-date-column-as-datetimes-not-objects-in-pandas
        df = pd.read_csv(path) \
            .pipe(parse_pd_datetime, 'published_at') \
            .pipe(unite_salaries, rates)
        self._vacancies_count = df.shape[0]

        df_by_year = df.groupby(df.published_at.dt.year)
        self._salaries_by_year = df_by_year['salary'].mean().astype(int).to_dict()
        self._counts_by_year = df_by_year.size().to_dict()

        prof_df_by_year = df[df['name'].str.contains(prof_name, case=True)] \
            .groupby(df.published_at.dt.year)
        self._prof_salaries_by_year = prof_df_by_year['salary'].mean().astype(int).to_dict()
        self._prof_counts_by_year = prof_df_by_year.size().to_dict()

        df_true_cities = df[df.groupby('area_name')['area_name'].transform('size') >= self._vacancies_count / 100]
        df_true_group = df_true_cities.groupby('area_name')

        # self._city_avg_counters = df_true_group['salary'].apply(list).apply(AvgCounter).to_dict()
        self._top_10_salaries_by_cities = df_true_group['salary']\
            .mean()\
            .astype(int)\
            .sort_values(ascending=False)\
            .iloc[:10]\
            .to_dict()
        self._top_10_cities_shares = df_true_group\
            .size()\
            .sort_values(ascending=False)\
            .apply(lambda x: x / self._vacancies_count) \
            .iloc[:10] \
            .to_dict()

    @staticmethod
    def _salary_to_rub(row, rates):
        """
        Переводит зарплату из заданной валюты в рубли
        :param row: Строка в таблица (pd.Series)
        :param rates: CurrencyRates
        :return: Значение ячейки
        """
        if row['salary_currency'] != 'RUR' and not pd.isnull(row['salary']):
            try:
                rate = rates.get_rate(row['salary_currency'], row['published_at'])
            except ValueError:
                return row
            if rate is None:
                return row
            row['salary'] = round(row['salary'] * rate, 0)
        return row

    @property
    def prof_name(self):
        return self._prof_name

    @property
    def salaries_by_year(self):
        return self._salaries_by_year

    @property
    def counts_by_year(self):
        return self._counts_by_year

    @property
    def prof_salaries_by_year(self):
        return self._prof_salaries_by_year

    @property
    def prof_counts_by_year(self):
        return self._prof_counts_by_year

    @property
    def top_10_salaries_by_cities(self):
        return self._top_10_salaries_by_cities
        # raise Exception('The method is not implemented')

    @property
    def top_10_cities_shares(self):
        return self._top_10_cities_shares
        # raise Exception('The method is not implemented')

    @property
    def vacancies_count(self):
        return self._vacancies_count

    @property
    def avg_counters_by_cities(self):
        # return self._city_avg_counters
        raise Exception('The method is not implemented')
