import csv
import itertools
import re
from typing import List

from prettytable import PrettyTable, ALL

exp_naming = {
    "noExperience": "Нет опыта",
    "between1And3": "От 1 года до 3 лет",
    "between3And6": "От 3 до 6 лет",
    "moreThan6": "Более 6 лет"
}

cur_naming = {
    "AZN": "Манаты",
    "BYR": "Белорусские рубли",
    "EUR": "Евро",
    "GEL": "Грузинский лари",
    "KGS": "Киргизский сом",
    "KZT": "Тенге",
    "RUR": "Рубли",
    "UAH": "Гривны",
    "USD": "Доллары",
    "UZS": "Узбекский сум"
}

gross_naming = {
    False: 'С вычетом налогов',
    True: 'Без вычета налогов'
}

bool_naming = {
    True: 'Да',
    False: 'Нет'
}

reversed_bool_naming = {
    'Да': True,
    'Нет': False
}


def to_bool(str_val):
    if str_val == 'True':
        return True
    elif str_val == 'False':
        return False
    else:
        raise Exception(f'Failed to parse bool value "{str_val}"')


def format_sum(str_sum):
    return format(int(float(str_sum)), ',').replace(',', ' ')


def format_date(str_date):
    return f"{str_date[8:10]}.{str_date[5:7]}.{str_date[0:4]}"


class Salary:
    def __init__(self, salary_from: int, salary_to: int, salary_gross: bool, salary_currency: str):
        self.salary_from = salary_from
        self.salary_to = salary_to
        self.salary_gross = salary_gross
        self.salary_currency = salary_currency

    def get_ruble_avg_salary(self):
        currency_to_rub = {
            "AZN": 35.68,
            "BYR": 23.91,
            "EUR": 59.90,
            "GEL": 21.74,
            "KGS": 0.76,
            "KZT": 0.13,
            "RUR": 1,
            "UAH": 1.64,
            "USD": 60.66,
            "UZS": 0.0055,
        }

        avg = (self.salary_from + self.salary_to) / 2
        return avg * currency_to_rub[self.salary_currency]


class Vacancy:
    def __init__(self, name: str, description: str, key_skills: List[str], experience_id, premium: bool,
                 employer_name: str, salary: Salary,
                 area_name: str, published_at: str):
        self.name = name
        self.description = description
        self.key_skills = key_skills
        self.experience_id = experience_id
        self.premium = premium
        self.employer_name = employer_name
        self.salary = salary
        self.area_name = area_name
        self.published_at = published_at


class EmptyFileException(Exception):
    pass


class DataSet:
    def __init__(self, file_name):
        self.file_name = file_name

        # Read vacancies from csv file
        list_naming, rows = self._read_csv(file_name)
        if list_naming is None:
            raise EmptyFileException()
        row_dicts = self._get_row_dicts(rows, list_naming)
        self.vacancy_objects = self._get_vacancy_objects(row_dicts)

    @staticmethod
    def _transform_value(value: str):
        result = []
        for sub_value in value.split('\n'):
            no_tag_value = re.sub(r"<.*?>", '', sub_value)
            clean_value = re.sub(r"\s+", ' ', no_tag_value.strip())
            result.append(clean_value)
        if len(result) == 1:
            return result[0]
        elif len(result) > 1:
            return result
        else:
            return None

    # Returns header fields and list of other csv fields:
    @staticmethod
    def _read_csv(file_name):
        with open(file_name, 'r', encoding='utf_8_sig') as file:
            reader = csv.reader(file)
            rows = [row for row in reader]
            if len(rows) == 0:
                return None, None
            list_naming = rows.pop(0)
            return list_naming, rows

    @staticmethod
    def _get_row_dicts(rows, list_naming):
        for row_values in rows:
            row_dict = {}
            if len(row_values) != len(list_naming) or '' in row_values:
                continue
            for i in range(len(row_values)):
                row_dict[list_naming[i]] = DataSet._transform_value(row_values[i])
            yield row_dict

    @staticmethod
    def _get_vacancy_objects(row_dicts):
        def list_skills(skills):
            if type(skills) is list:
                return skills
            elif type(skills) is str:
                return [skills]
            else:
                raise Exception(f"Type ${type(skills)} is wrong for raw skills")

        objects = []
        for row_dict in row_dicts:
            salary = Salary(salary_from=int(float(row_dict['salary_from'])),
                            salary_to=int(float(row_dict['salary_to'])),
                            salary_gross=to_bool(row_dict['salary_gross']),
                            salary_currency=row_dict['salary_currency'])
            vacancy = Vacancy(name=row_dict['name'],
                              description=row_dict['description'],
                              key_skills=list_skills(row_dict['key_skills']),
                              experience_id=row_dict['experience_id'],
                              premium=to_bool(row_dict['premium']),
                              employer_name=row_dict['employer_name'],
                              salary=salary,
                              area_name=row_dict['area_name'],
                              published_at=row_dict['published_at']
                              )
            objects.append(vacancy)
        return objects


class FilterException(Exception):
    pass


class SortException(Exception):
    pass


class InputConect:
    def __init__(self):
        self._filters = {
            'Название': lambda vac, exp_val: vac.name == exp_val,
            'Описание': lambda vac, exp_val: vac.description == exp_val,
            'Компания': lambda vac, exp_val: vac.employer_name == exp_val,
            'Название региона': lambda vac, exp_val: vac.area_name == exp_val,
            'Оклад': lambda vac, exp_val: vac.salary.salary_from <= int(exp_val) <= vac.salary.salary_to,
            'Опыт работы': lambda vac, exp_val: exp_naming[vac.experience_id] == exp_val,
            'Премиум-вакансия': lambda vac, exp_val: bool_naming[vac.premium] == exp_val,
            'Идентификатор валюты оклада': lambda vac, exp_val: cur_naming[vac.salary.salary_currency] == exp_val,
            'Дата публикации вакансии': lambda vac, exp_val: format_date(vac.published_at) == exp_val,
            'Навыки': lambda vac, exp_val: all([s in vac.key_skills for s in exp_val.split(', ')]),
        }
        self._sorters = {
            'Название': lambda vac: vac.name,
            'Описание': lambda vac: vac.description,
            'Компания': lambda vac: vac.employer_name,
            'Название региона': lambda vac: vac.area_name,
            'Навыки': lambda vac: len(vac.key_skills),
            'Оклад': lambda vac: vac.salary.avg_ruble_amount(),
            'Дата публикации вакансии': lambda vac: vac.published_at,
            'Опыт работы': lambda vac: list(exp_naming.keys()).index(vac.experience_id),
            'Премиум-вакансия': lambda vac: int(vac.premium),
            'Идентификатор валюты оклада': lambda vac: vac.salary.salary_currency,
        }

        self.filter_key = None
        self.filter_value = None
        self.sorter = None
        self.reverse_sort = False
        self.number_string = None
        self.columns_string = None
        self.columns_naming = {}

    def set_filter_string(self, filter_string):
        if filter_string == '':
            return

        args = filter_string.split(': ')
        if len(args) != 2:
            raise FilterException('Формат ввода некорректен')
        if args[0] not in self._filters:
            raise FilterException('Параметр поиска некорректен')

        self.filter_key = args[0]
        self.filter_value = args[1]

    def set_sort_params(self, sort_string, reverse_str: str):
        if sort_string == '':
            pass
        elif sort_string not in self._sorters:
            raise SortException('Параметр сортировки некорректен')
        else:
            self.sorter = self._sorters[sort_string]

        if reverse_str == '':
            pass
        elif reverse_str not in bool_naming.values():
            raise SortException('Порядок сортировки задан некорректно')
        else:
            self.reverse_sort = reversed_bool_naming[reverse_str]

    def set_number_string(self, number_string):
        if number_string == "":
            return
        self.number_string = number_string

    def set_columns_string(self, columns_string):
        if columns_string == "":
            return
        self.columns_string = columns_string

    def set_columns_naming(self, columns_naming):
        self.columns_naming = columns_naming

    def print_as_table(self, vacancies):
        if self.filter_key is not None:
            vacancies = self._filter_vacancies_by_string(vacancies)

        if self.sorter is not None:
            vacancies = sorted(vacancies, key=self.sorter, reverse=self.reverse_sort)

        table = self._create_table(vacancies)
        if table is None:
            print('Нет данных')
            return

        table_formatter = self._get_table_formatter()
        if table_formatter is not None:
            print(table_formatter(table))
        else:
            print(table)

    def _create_table(self, vacancies_objects):
        table = PrettyTable()
        table.hrules = ALL
        table.field_names = ['№'] + list(self.columns_naming.values())
        table.align = 'l'
        table.max_width = 20

        n = 1
        for vacancy in vacancies_objects:
            formatted_vacancy = self._format_vacancy(vacancy)
            table.add_row([n] + list(map(self._cut_string, formatted_vacancy.values())))
            n += 1

        if n <= 1:
            return None
        else:
            return table

    @staticmethod
    def _cut_string(value):
        if len(value) > 100:
            return value[:100] + '...'
        else:
            return value

    @staticmethod
    def _format_vacancy(vacancy: Vacancy):
        new_row = dict()
        # Форматируем название и описание
        new_row['name'] = vacancy.name
        new_row['description'] = vacancy.description
        new_row['key_skills'] = '\n'.join(vacancy.key_skills)
        # Заменяем опыт работы
        new_row['experience_id'] = exp_naming[vacancy.experience_id]
        # Руссифицируем bool
        new_row['premium'] = bool_naming[vacancy.premium]
        # Получаем имя работодателя
        new_row['employer_name'] = vacancy.employer_name
        # Меняем оклад
        new_row['salary'] = InputConect._format_salary(vacancy.salary)
        # Получаем регион
        new_row['area_name'] = vacancy.area_name
        # Заменяем дату публикации
        new_row['published_at'] = format_date(vacancy.published_at)
        # Возвращаем словарь с форматированными значениями
        return new_row

    @staticmethod
    def _format_salary(salary: Salary):
        sal_from = format_sum(salary.salary_from)
        sal_to = format_sum(salary.salary_to)
        sal_gross_id = salary.salary_gross
        sal_gross = gross_naming[sal_gross_id]
        sal_currency_id = salary.salary_currency
        sal_currency = cur_naming[sal_currency_id]
        return f'{sal_from} - {sal_to} ({sal_currency}) ({sal_gross})'

    def _get_table_formatter(self):
        formatter_args = dict()
        if self.number_string is not None:
            values = self.number_string.split(' ')
            formatter_args['start'] = int(values[0]) - 1
            if len(values) == 2:
                formatter_args['end'] = int(values[1]) - 1
        if self.columns_string is not None:
            formatter_args['fields'] = ['№'] + self.columns_string.split(', ')
        return lambda t: t.get_string(**formatter_args)

    def _filter_vacancies_by_string(self, vacancies):
        def peek(iterable):
            try:
                first = next(iterable)
            except StopIteration:
                return None
            return first, itertools.chain([first], iterable)

        filtered = filter(lambda vac: self._filters[self.filter_key](vac, self.filter_value), vacancies)
        filtered_peek = peek(filtered)
        if filtered_peek is None:
            raise FilterException('Ничего не найдено')
        return filtered_peek[1]


def execute_program(file_name, filter_string, sort_column, sort_reversed_string, number_string, columns_string):
    conect = InputConect()
    try:
        conect.set_filter_string(filter_string)
        conect.set_sort_params(sort_column, sort_reversed_string)
    except (FilterException, SortException) as ex:
        print(ex)
        return
    conect.set_number_string(number_string)
    conect.set_columns_string(columns_string)
    conect.set_columns_naming({
        'name': 'Название',
        'description': 'Описание',
        'key_skills': 'Навыки',
        'experience_id': 'Опыт работы',
        'premium': 'Премиум-вакансия',
        'employer_name': 'Компания',
        'salary': 'Оклад',
        'area_name': 'Название региона',
        'published_at': 'Дата публикации вакансии',
    })

    try:
        data = DataSet(file_name)
    except EmptyFileException:
        print('Пустой файл')
        return

    try:
        conect.print_as_table(data.vacancy_objects)
    except FilterException as ex:
        print(ex)


if __name__ == "__main__":
    file_name = input('Введите название файла: ')
    filter_string = input('Введите параметр фильтрации: ')
    sort_column = input('Введите параметр сортировки: ')
    sort_reversed_string = input('Обратный порядок сортировки (Да / Нет): ')
    number_string = input('Введите диапазон вывода: ')
    columns_string = input('Введите требуемые столбцы: ')

    execute_program(file_name, filter_string, sort_column, sort_reversed_string, number_string, columns_string)
