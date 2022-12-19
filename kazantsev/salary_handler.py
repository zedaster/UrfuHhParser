from pathlib import Path

import numpy as np
import pandas as pd

from kazantsev.currency_rates import CurrencyRates
from kazantsev.datetime_parser import parse_datetime


def _add_salary_column(row, rates):
    """
    Получает ячейку salary для определнной строки в таблице
    :param row: Строка в таблица (pd.Series)
    :param rates: CurrencyRates
    :return: Значение ячейки
    """
    amount = None
    if pd.isnull(row['salary_from']) and pd.isnull(row['salary_to']):
        return row
    if pd.isnull(row['salary_from']):
        amount = row['salary_to']
    elif pd.isnull(row['salary_to']):
        amount = row['salary_from']
    else:
        amount = (row['salary_from'] + row['salary_to']) / 2

    if row['salary_currency'] != 'RUR':
        date = parse_datetime(row['published_at'])
        try:
            rate = rates.get_rate(row['salary_currency'], date)
        except ValueError:
            return row
        if rate is None:
            return row
        amount *= rate
    row['salary'] = amount
    return row


def handle_salaries(in_path: Path, out_path: Path, rates: CurrencyRates, limit=None):
    """
    Преобразует входной csv в csv с отформатированной зарплатой
    :param in_path: Входной CSV
    :param out_path: Выходной CSV
    :param rates: Курсы валют
    :return: None
    """
    df = pd.read_csv(in_path, nrows=limit)
    df.insert(1, column='salary', value=[np.nan for _ in range(df.shape[0])])
    df = df.apply(lambda x: _add_salary_column(x, rates), axis=1)
    df = df.drop(['salary_from', 'salary_to', 'salary_currency'], axis=1)
    df.to_csv(out_path, index=False)
