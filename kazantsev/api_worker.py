import csv
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from dateutil.relativedelta import relativedelta

from kazantsev.datetime_parser import parse_datetime


class HhApiWorker:
    def load_vacancies_to_csv(self, csv_path: Path, date: datetime, swap_to_workday=True):
        """
        Выгружает IT-вакансии с API hh.ru в указанный CSV файл
        :param csv_path: Путь к выходному CSV-файлу
        :param date: День, по которому будут выгружены данные
        :param swap_to_workday: Заменять ли день на ближайший рабочий в прошлом
        :return: None
        """
        # Поменять день если надо
        start_date = datetime(date.year, date.month, date.day, 0, 0, 0, tzinfo=timezone(timedelta(hours=3)))
        if swap_to_workday:
            if date.weekday() == 5:
                start_date -= relativedelta(days=1)
            if date.weekday() == 6:
                start_date -= relativedelta(days=2)

        # Задать лимиты по датам
        end_date = start_date + relativedelta(days=1)
        # Потом по датам
        found = float('inf')
        rows = dict()
        while found > 2000:
            last_row = None
            try:
                for row in self._iterate_vacancies(start_date, end_date):
                    rows[row.id] = row.to_cortege()
                    last_row = row
                found = last_row.total_count
                end_date = parse_datetime(last_row.published_at) + relativedelta(seconds=1)
            except self.CaptchaException as ex:
                print(f'Слишком много запросов на API hh.ru. \n'
                      f'Пройдите капчу на {ex.captcha_url}\n'
                      f'Или по адресу {ex.fallback_url}\n'
                      f'Затем запустите программу снова.')
                return
            # Также можно обратать и другие не 200 ответы
            # except requests.exceptions.HTTPError as ex:

        with open(csv_path, 'w', encoding='utf_8_sig', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(self._VacancyRow.cortege_titles)
            for row_val in rows.values():
                writer.writerow(row_val)

    class _VacancyRow:
        """
        Класс для работы с вакансий из API hh.ru
        """
        cortege_titles = 'name', 'salary_from', 'salary_to', 'salary_currency', 'area_name', 'published_at'

        def __init__(self, total_count, v_id, name, salary_from, salary_to, salary_currency, area_name, published_at):
            """
            Создает объект с вакансией на hh.ru
            :param total_count: Общее количество вакансий, полученных вместе с данной
            :param v_id: Id вакансии
            :param name: Название вакансии
            :param salary_from: Зарплата от
            :param salary_to: Зарплата до
            :param salary_currency: Валюта зарплаты
            :param area_name: Название региона, где размещена вакансия
            :param published_at: Дата+время публикации
            """
            self.total_count = total_count
            self.id = v_id
            self.name = name
            self.salary_from = salary_from
            self.salary_to = salary_to
            self.salary_currency = salary_currency
            self.area_name = area_name
            self.published_at = published_at

        def to_cortege(self):
            """
            Преобразует параметры вакансии в кортеж. Полезен для формирования датасетов и таблиц
            :return:
            """
            return self.name, self.salary_from, self.salary_to, self.salary_currency, self.area_name, self.published_at

    class CaptchaException(Exception):
        """
        Ошибка, возникающая при запросе капчи с HH.RU API
        """
        def __init__(self, captcha_url, fallback_url):
            self.captcha_url = captcha_url
            self.fallback_url = fallback_url

    def _iterate_vacancies(self, start_date: datetime, end_date: datetime):
        """
        Запрашивает вакансии с API hh.ru в пределах указанных дат. Выдает до 2000 вакансий
        :param start_date: Начало диапазона дат
        :param end_date: Коней диапазона дат
        :return: Итератор объектов _VacancyRow в порядке убывания даты публикации. Выдает максимум 2000 объектов
        """
        page_count = 20
        page = 0
        while page < page_count:
            params = {
                'specialization': 1,
                'page': page,
                'per_page': 100,
                'order_by': 'publication_time',
                'date_from': self._date_to_string(start_date),
                'date_to': self._date_to_string(end_date)
            }
            resp = requests.get('https://api.hh.ru/vacancies', params)
            # Вернуть ошибку при капче
            if resp.status_code == 403:
                for error in resp.json()['errors']:
                    if error['value'] == 'captcha_required':
                        raise self.CaptchaException(error.get("captcha_url", None), error.get("fallback_url", None))
            # Вернуть ошибку при других случаях, когда ответ != 200
            resp.raise_for_status()
            json = resp.json()
            page_count = json['pages']
            found = json['found']
            for item in json['items']:
                v_id = item['id']
                name = item['name']
                salary_from = None
                salary_to = None
                salary_currency = None
                if item['salary'] is not None:
                    salary_from = item['salary']['from']
                    salary_to = item['salary']['to']
                    salary_currency = item['salary']['currency']
                area_name = item['area']['name']
                published_at = item['published_at']
                row = self._VacancyRow(found, v_id, name, salary_from, salary_to, salary_currency, area_name,
                                       published_at)
                yield row
            page += 1

    @staticmethod
    def _date_to_string(date: datetime):
        """
        Преобразует дату в строку, допустимую для API hh.ru
        :param date: datetime
        :return: str
        """
        return date.strftime('%Y-%m-%dT%H:%M:%S%z')
