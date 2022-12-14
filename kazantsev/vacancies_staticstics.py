import csv
import multiprocessing
import concurrent.futures as pool
from abc import ABC, abstractmethod
from datetime import datetime
from multiprocessing import Process
from pathlib import Path
from typing import Iterable

from kazantsev.models import Vacancy
from kazantsev.year_separated import YearSeparated


class AvgCounter:
    """
    Класс для подсчета среднего арифметического значения

    Attributes:
        value (float): Среднее арифметическое значение
    """

    def __init__(self, first_value=None):
        """
        Инициализирует объект счетчика среднего арифметического
        :param first_value: Первое значение
        :type first_value: float
        """
        self.value = 0
        self._sum = 0
        self._len = 0
        if first_value is not None:
            self.add(first_value)

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
    def top_10_salaries_by_cities(self):
        pass

    @property
    @abstractmethod
    def top_10_cities_shares(self):
        pass

    @property
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


class MultiProcessVacanciesStatics(VacanciesStatistics):
    def __init__(self, general_table: Path, chunk_paths: Iterable[Path], prof_name: str, preload_city_stats=False):
        self._prof_name = prof_name
        self._general_table = general_table

        with multiprocessing.Manager() as manager:
            chunk_dicts = manager.dict({
                'salaries': manager.dict(),
                'counts': manager.dict(),
                'prof_salaries': manager.dict(),
                'prof_counts': manager.dict(),
            })

            city_dicts = manager.dict({
                'top_10_salaries_by_cities': manager.dict(),
                'top_10_cities_shares': manager.dict(),
            })

            general_table_process = Process(target=self._handle_general_table,
                                            args=(self._prof_name, general_table, city_dicts))
            if preload_city_stats:
                general_table_process.start()

            chunk_processes = []
            for path in chunk_paths:
                process = Process(target=self._handle_one_chunk, args=(self._prof_name, path, chunk_dicts))
                process.start()
                chunk_processes.append(process)

            for process in chunk_processes:
                process.join()

            self._salaries_by_year = dict(chunk_dicts['salaries'])
            self._counts_by_year = dict(chunk_dicts['counts'])
            self._prof_salaries_by_year = dict(chunk_dicts['prof_salaries'])
            self._prof_counts_by_year = dict(chunk_dicts['prof_counts'])

            self._city_stats_loaded = preload_city_stats
            if preload_city_stats:
                general_table_process.join()
                self._top_10_salaries_by_cities = dict(city_dicts['top_10_salaries_by_cities'])
                self._top_10_cities_shares = dict(city_dicts['top_10_cities_shares'])

    def _load_city_stats(self):
        with multiprocessing.Manager() as manager:
            city_dicts = manager.dict({
                'top_10_salaries_by_cities': manager.dict(),
                'top_10_cities_shares': manager.dict(),
            })
            args = (self._prof_name, self._general_table, city_dicts)
            general_table_process = Process(target=self._handle_general_table, args=args)
            general_table_process.start()
            general_table_process.join()
            self._top_10_salaries_by_cities = dict(city_dicts['top_10_salaries_by_cities'])
            self._top_10_cities_shares = dict(city_dicts['top_10_cities_shares'])
            self._city_stats_loaded = True

    @staticmethod
    def _handle_one_chunk(prof_name, path: Path, dicts):
        stats = SingleProcessVacanciesStatistics(path, prof_name)
        dicts['salaries'].update(stats.salaries_by_year)
        dicts['counts'].update(stats.counts_by_year)
        dicts['prof_salaries'].update(stats.prof_salaries_by_year)
        dicts['prof_counts'].update(stats.prof_counts_by_year)

    @staticmethod
    def _handle_general_table(prof_name, path: Path, dicts):
        stats = SingleProcessVacanciesStatistics(path, prof_name)
        dicts['top_10_salaries_by_cities'].update(stats.top_10_salaries_by_cities)
        dicts['top_10_cities_shares'].update(stats.top_10_cities_shares)

    @staticmethod
    def from_chunk_folder(general_table: Path, chunk_folder: Path, prof_name: str):
        return MultiProcessVacanciesStatics(general_table, (p for p in chunk_folder.rglob('*')), prof_name)

    @staticmethod
    def from_year_separated(year_separated: YearSeparated, prof_name: str):
        return MultiProcessVacanciesStatics(year_separated.main_csv_path, year_separated.chunk_csv_paths, prof_name)

    @property
    def prof_name(self):
        return self._prof_name

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
        if not self._city_stats_loaded:
            self._load_city_stats()
        return self._top_10_salaries_by_cities

    @property
    def top_10_cities_shares(self):
        if not self._city_stats_loaded:
            self._load_city_stats()
        return self._top_10_cities_shares


class ConcurrentFuturesVacanciesStatics(VacanciesStatistics):
    def __init__(self, general_table: Path, chunk_paths: Iterable[Path], prof_name: str, preload_city_stats=False):
        self._prof_name = prof_name
        self._general_table = general_table
        self._city_stats_loaded = preload_city_stats
        self._salaries_by_year = dict()
        self._counts_by_year = dict()
        self._prof_salaries_by_year = dict()
        self._prof_counts_by_year = dict()

        with pool.ProcessPoolExecutor() as executor:
            if preload_city_stats:
                future_general = executor.submit(self._handle_general_table)

            for chunk_dict in executor.map(self._handle_one_chunk, chunk_paths, timeout=None):
                self._salaries_by_year.update(chunk_dict['salaries'])
                self._counts_by_year.update(chunk_dict['counts'])
                self._prof_salaries_by_year.update(chunk_dict['prof_salaries'])
                self._prof_counts_by_year.update(chunk_dict['prof_counts'])

            if preload_city_stats:
                city_dicts = future_general.result()
                self._top_10_salaries_by_cities = city_dicts['top_10_salaries_by_cities']
                self._top_10_cities_shares = city_dicts['top_10_cities_shares']

    def _load_city_stats(self):
        with pool.ProcessPoolExecutor() as executor:
            future_general = executor.submit(self._handle_general_table)
            city_dicts = future_general.result()
            self._top_10_salaries_by_cities = city_dicts['top_10_salaries_by_cities']
            self._top_10_cities_shares = city_dicts['top_10_cities_shares']
            self._city_stats_loaded = True

    def _handle_one_chunk(self, path: Path):
        stats = SingleProcessVacanciesStatistics(path, self._prof_name)
        return {
            'salaries': stats.salaries_by_year,
            'counts': stats.counts_by_year,
            'prof_salaries': stats.prof_salaries_by_year,
            'prof_counts': stats.prof_counts_by_year,
        }

    def _handle_general_table(self):
        stats = SingleProcessVacanciesStatistics(self._general_table, self._prof_name)
        return {
            'top_10_salaries_by_cities': stats.top_10_salaries_by_cities,
            'top_10_cities_shares': stats.top_10_cities_shares
        }

    @staticmethod
    def from_chunk_folder(general_table: Path, chunk_folder: Path, prof_name: str):
        return ConcurrentFuturesVacanciesStatics(general_table, (p for p in chunk_folder.rglob('*')), prof_name)

    @staticmethod
    def from_year_separated(year_separated: YearSeparated, prof_name: str):
        return ConcurrentFuturesVacanciesStatics(year_separated.main_csv_path, year_separated.chunk_csv_paths, prof_name)

    @property
    def prof_name(self):
        return self._prof_name

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
        if not self._city_stats_loaded:
            self._load_city_stats()
        return self._top_10_salaries_by_cities

    @property
    def top_10_cities_shares(self):
        if not self._city_stats_loaded:
            self._load_city_stats()
        return self._top_10_cities_shares
