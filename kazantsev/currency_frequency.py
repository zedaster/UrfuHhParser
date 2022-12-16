from pathlib import Path
from typing import Set

import pandas as pd


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


# get_local_path('./tests/vacancies_dif_currencies.csv')
def get_currency_frequencies(path: Path):
    """
    Возвращаем фрейм с валютами и количество вакансий с каждой
    :param path: Путь к CSV файлу
    :type path: Path
    :return: DataFrame
    """
    df = pd.read_csv(path).dropna()
    currency_counts = df['salary_currency'].value_counts()
    accepted_currencies = set(currency_counts[lambda x: x > 5000].keys())

    return df[df.salary_currency.isin(accepted_currencies)]
