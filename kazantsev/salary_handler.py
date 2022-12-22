from pathlib import Path

import pandas as pd

from kazantsev.currency_rates import CurrencyRates


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


def handle_salaries(in_path: Path, out_path: Path, rates: CurrencyRates, limit=None):
    """
    Преобразует входной csv в csv с отформатированной зарплатой
    :param in_path: Входной CSV
    :param out_path: Выходной CSV
    :param rates: Курсы валют
    :return: None
    """

    pd \
        .read_csv(in_path, nrows=limit) \
        .assign(published_at=lambda x: pd.to_datetime(x.published_at)) \
        .assign(salary=lambda x: x[['salary_from', 'salary_to']].mean(axis=1)) \
        .apply(lambda x: _salary_to_rub(x, rates), axis=1) \
        .loc[:, ['name', 'salary', 'area_name', 'published_at']] \
        .to_csv(out_path, index=False)
