import concurrent.futures
from datetime import datetime
from itertools import repeat
from pathlib import Path
from typing import Set

import pandas as pd
import requests
from dateutil.relativedelta import relativedelta
from pandas import DataFrame


class CurrencyRates:
    """
    Класс для работы с курсами валют из ЦБ РФ

    Attributes:
        dataframe - Таблица с курсами в виде Pandas-датафрейма
    """

    def __init__(self, df: DataFrame):
        """
        Инициализацизирует данные из датафрейма
        :param df: DataFrame
        """
        self.dataframe = df

    @staticmethod
    def from_api(currencies: Set[str], min_date: datetime, max_date: datetime):
        """
        Инициализацизирует данные с частотой раз в месяц
        :param currencies: Сет из тикеров допустимых валют
        :type: Set[str]
        :param min_date: Минимальная дата выборки
        :type: datetime
        :param max_date: Предельная дата выборки
        :type: datetime
        """

        def get_days(min_date: datetime, max_date: datetime):
            current_date = min_date
            while current_date < max_date:
                yield current_date
                current_date += relativedelta(months=1)

        result = {}
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(CurrencyRates._get_day_rates, get_days(min_date, max_date), repeat(currencies), repeat(result))
        df = pd.DataFrame(result).transpose().sort_index()
        df.index.name = 'date'
        return CurrencyRates(df)

    @staticmethod
    def from_csv(path: Path):
        """
        Загружает данные из CSV файла
        :param path: Путь к CSV файлу
        :return: Экземпляр класа CurrencyRates
        """
        df = pd.read_csv(path)
        df['date'] = pd.to_datetime(df['date'])
        return CurrencyRates(df)

    def get_rate(self, currency: str, date: datetime):
        """
        Получает курс валюты за месяц и год данного числа
        :param currency: Тикер валюты (str)
        :param date: Дата (datetime)
        :return: Курс валюты (float)
        """
        if currency not in self.dataframe.columns:
            raise ValueError(f"Currency {currency} does not exist in the dataframe")
        first_date = self.dataframe['date'].iloc[0]
        if date < first_date:
            raise ValueError(f'Date {date} is less than date range of the rates')
        last_date = self.dataframe['date'].iloc[-1]
        if date > last_date:
            raise ValueError(f'Date {date} is bigger than date range of the rates')

        df = self.dataframe
        try:
            return df[(df['date'].dt.year == date.year) & (df['date'].dt.month == date.month)][currency].values[0]
        except IndexError:
            raise ValueError(f'No rates for {date}')

    @staticmethod
    def _get_day_rates(date: datetime, currencies, result_dict):
        url = f'https://www.cbr.ru/scripts/XML_daily.asp?date_req={date.day:02}/{date.month:02}/{date.year}'
        resp = requests.get(url)
        if resp.status_code != 200:
            raise Exception(f'Status code is {resp.status_code} for get from "{url}"')
        df = pd.read_xml(resp.text)
        df = df[df.CharCode.isin(currencies)][['CharCode', 'Nominal', 'Value']]
        df['Rate'] = df['Value'].map(lambda x: float(x.replace(',', '.'))) / df['Nominal']
        df = df[['CharCode', 'Rate']]
        series = df.set_index('CharCode')['Rate']
        result_dict[date] = series

    def save_to_csv(self, path: Path):
        """
        Сохраняет датафрейм в указанный CSV-файл
        :param path: Путь к CSV-файлу
        :type path: Path
        :return: None
        """
        self.dataframe.to_csv(path)


# path = get_local_path('./tests/vacancies_dif_currencies.csv')
# min_date, max_date = get_min_max_datetimes(path)
# currencies = get_most_frequency_currencies(path)
# rates = CurrencyRates.from_api(currencies, min_date, max_date)
# rates.save_to_csv(get_local_path('currency_rates.csv'))

# CurrencyRates._get_day_rates(datetime(2020, 1, 1))
