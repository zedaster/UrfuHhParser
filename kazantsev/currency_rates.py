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

    @staticmethod
    def _str_to_dt(string):
        return datetime(int(string[:4]), int(string[5:7]), day=1)

    @staticmethod
    def _dt_to_str(dt):
        return f"{dt.year}-{dt.month:02}"

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
            current_date = min_date.replace(day=1)
            while current_date <= max_date:
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
        return CurrencyRates(df)

    def get_rate(self, currency: str, date: datetime):
        """
        Получает курс валюты за месяц и год данного числа
        :param currency: Тикер валюты (str)
        :param date: Дата (datetime)
        :return: Курс валюты (float)
        """
        date = date.replace(tzinfo=None)
        if currency not in self.dataframe.columns:
            raise ValueError(f"Currency {currency} does not exist in the dataframe")
        first_date = self._str_to_dt(self.dataframe['date'].iloc[0])
        if date < first_date:
            raise ValueError(f'Date {date} is less than date range of the rates')
        last_date = self._str_to_dt(self.dataframe['date'].iloc[-1])
        if date > last_date:
            raise ValueError(f'Date {date} is bigger than date range of the rates')

        df = self.dataframe
        try:
            return df[df['date'] == self._dt_to_str(date)][currency].values[0]
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
        df['Rate'] = df['Rate'].apply(lambda x: round(x, 7))
        df = df[['CharCode', 'Rate']]
        series = df.set_index('CharCode')['Rate']
        result_dict[CurrencyRates._dt_to_str(date)] = series

    def save_to_csv(self, path: Path):
        """
        Сохраняет датафрейм в указанный CSV-файл
        :param path: Путь к CSV-файлу
        :type path: Path
        :return: None
        """
        self.dataframe.to_csv(path)
