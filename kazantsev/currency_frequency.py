from datetime import datetime
from pathlib import Path
from typing import Set, Tuple

import pandas as pd

from kazantsev.datetime_parser import parse_datetime
from kazantsev.local_path import get_local_path


def get_most_frequency_currencies(path: Path, more_than=5000) -> Set[str]:
    """
    Возвращает самые частые валюты в таблице вакансий
    :param path: путь к CSV файлу
    :type path: Path
    :param more_than: Нижний лимит вакансий для валют
    :type more_than: int
    :return: Set из самых частых валют
    """
    df = pd.read_csv(path).dropna()
    currency_counts = df['salary_currency'].value_counts()
    return set(currency_counts[lambda x: x > more_than].keys())


def get_min_max_datetimes(path: Path, datetime_column_name='published_at') -> Tuple[datetime, datetime]:
    """
    Получает минимальную и максимальную даты в CSV-таблице
    :param path: Путь к CSV-файлу
    :type path: Path
    :param datetime_column_name: Название колонки в CSV с датой
    :type datetime_column_name: str
    :return: Кортеж из минимальной и максимальной даты
    :rtype: Tuple[datetime, datetime]
    """
    df = pd.read_csv(path).dropna()
    min_date = parse_datetime(df[datetime_column_name].min())
    max_date = parse_datetime(df[datetime_column_name].max())
    return min_date, max_date


def get_currency_frequencies(path: Path):
    """
    Возвращает фрейм с валютами и количество вакансий с каждой
    :param path: Путь к CSV файлу
    :type path: Path
    :return: DataFrame
    """
    df = pd.read_csv(path).dropna()
    currency_counts = df['salary_currency'].value_counts()
    accepted_currencies = set(currency_counts[lambda x: x > 5000].keys())

    return df[df.salary_currency.isin(accepted_currencies)]


# path = get_local_path('./tests/vacancies_dif_currencies.csv')

# print(get_most_frequency_currencies(path))

# print(get_min_max_datetimes(path))
# (datetime.datetime(2005, 9, 16, 17, 26, 39, tzinfo=UTC+04:00),
# datetime.datetime(2022, 7, 18, 19, 35, 13, tzinfo=UTC+03:00))
