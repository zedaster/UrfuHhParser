import concurrent.futures
from datetime import datetime
from itertools import repeat
from pathlib import Path
from typing import Set

import pandas
import requests
from dateutil.relativedelta import relativedelta

from kazantsev.local_path import get_local_path


class CurrencyRates:
    """
    Класс для работы с курсами валют из ЦБ РФ

    Attributes:
        dataframe - Таблица с курсами в виде Pandas-датафрейма
    """
    def __init__(self, currencies: Set[str], min_date: datetime, max_date: datetime):
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
            executor.map(self._get_day_rates, get_days(min_date, max_date), repeat(currencies), repeat(result))
        df = pandas.DataFrame(result).transpose()
        df.index.name = 'date'
        self.dataframe = df

    @staticmethod
    def _get_day_rates(date: datetime, currencies, result_dict):
        url = f'https://www.cbr.ru/scripts/XML_daily.asp?date_req={date.day:02}/{date.month:02}/{date.year}'
        resp = requests.get(url)
        if resp.status_code != 200:
            raise Exception(f'Status code is {resp.status_code} for get from "{url}"')
        df = pandas.read_xml(resp.text)
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


# rates = CurrencyRates({'KZT', 'RUR', 'USD', 'UAH', 'EUR', 'BYR'}, datetime(2003, 1, 1), datetime(2020, 12, 1))
# rates.save_to_csv(get_local_path('currency_rates.csv'))

# CurrencyRates._get_day_rates(datetime(2020, 1, 1))
