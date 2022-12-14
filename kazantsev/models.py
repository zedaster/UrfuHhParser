from datetime import datetime

from kazantsev.datetime_parser import parse_datetime


def to_bool(str_val):
    """
    Преобразует строку 'True' или 'False' в соответсующий bool
    :param str_val: string-значение
    :type str_val: str
    :return: bool-значение или ValueError, если значение не подходит
    :rtype: bool
    :raises ValueError: если значение не равно 'True' или 'False'

    >>> to_bool('True')
    True
    >>> to_bool('False')
    False
    """
    if str_val is None:
        return None
    if str_val == 'True':
        return True
    if str_val == 'False':
        return False

    raise ValueError(f'Failed to parse bool value "{str_val}"')


class Salary:
    """
    Класс для представления зарплаты

    Attributes:
        from_amount (int): Нижняя граница вилки оклада
        to_amount (int): Верхняя граница вилки оклада
        currency (str): Валюта оклада
        gross (bool or None): Брутто оклад или нет?
    """

    _exchange_rates = {
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

    def __init__(self, from_amount: int, to_amount: int, currency: str, gross=None):
        """
        Инициализирует объект Salary, конвертация здесь не выполняется
        :param from_amount: Нижняя граница вилки оклада
        :type from_amount: int
        :param to_amount: Верхняя граница вилки оклада
        :type to_amount: int
        :param currency: Валюта оклада
        :type currency: str
        :param gross: Брутто оклад или нет?
        :type gross: Union[bool, None]
        """
        self.from_amount = from_amount
        self.to_amount = to_amount
        self.gross = gross
        self.currency = currency

    @property
    def avg_ruble_amount(self):
        """
        Вычисляет среднюю зарплату из вилки и переводит ее в рубли
        :return: Средняя зарплата в рублях
        :rtype: float
        """
        avg = (self.from_amount + self.to_amount) / 2
        return avg * Salary._exchange_rates[self.currency]

    @staticmethod
    def parse_from_dict(row_dict):
        """
        Переводит словарь строка -> строка в объект Salary
        :param row_dict: словарь
        :type row_dict: typing.Dict[str,str]
        :return: объект Salary
        :rtype: Salary
        :raises ValueError: Если одно из переданных значений не соотвествует нужному формату
        """
        currency = row_dict['salary_currency']
        if type(currency) is not str:
            raise ValueError(f'salary_currency must be a string')
        if currency not in Salary._exchange_rates:
            raise ValueError(f'Currency "{currency}" is not defined.')

        return Salary(
            from_amount=int(float(row_dict['salary_from'])),
            to_amount=int(float(row_dict['salary_to'])),
            gross=to_bool(row_dict.get('salary_gross', None)),
            currency=currency
        )


class Vacancy:
    """
    Класс для представления вакансии

    Attributes:
        name (str): Название
        description (str): Описание
        salary (Salary): Зарпалата
        area_name (str): Название региона или города
        published_at (datetime): Время публикации вакансии
        key_skills (List[str] or None): Список ключевых навыков
        experience_id (str or None): Идендитификатор опыта работы (см. словарь exp_naming)
        premium (bool or None): Премиум-вакансия
        employer_name (str or None): Название работодателя
    """

    def __init__(self, name: str, salary: Salary, area_name: str, published_at: datetime,
                 description=None, key_skills=None, experience_id=None, premium=None, employer_name=None):
        """
        Инициализирует объект Vacancy
        :param name: Название вакансии
        :type name: str
        :param salary: Зарплата
        :type salary: Salary
        :param area_name: Название региона или города
        :type area_name: str
        :param published_at: Время публикации вакансии
        :type published_at: datetime
        :param description: Описание вакансии
        :type description: str
        :param key_skills: Список ключевых навыков
        :type key_skills: List[str] or None
        :param experience_id: Идендитификатор опыта работы (см. словарь exp_naming)
        :type experience_id: str or None
        :param premium: Премиум-вакансия
        :type premium: bool or None
        :param employer_name: Название работодателя
        :type employer_name: str
        """
        self.name = name
        self.description = description
        self.key_skills = key_skills
        self.experience_id = experience_id
        self.premium = premium
        self.employer_name = employer_name
        self.salary = salary
        self.area_name = area_name
        self.published_at = published_at

    @staticmethod
    def parse_from_dict(row_dict: dict):
        """
        Переводит словарь строка -> строка в объект Vacancy
        :param row_dict: словарь
        :type row_dict: typing.Dict[str,str]
        :return: объект Vacancy
        :rtype: Vacancy
        """
        return Vacancy(
            name=row_dict['name'],
            salary=Salary.parse_from_dict(row_dict),
            area_name=row_dict['area_name'],
            published_at=parse_datetime(row_dict['published_at']),
            description=row_dict.get('description', None),
            key_skills=Vacancy._list_skills(row_dict.get('key_skills', None)),
            experience_id=row_dict.get('experience_id', None),
            premium=to_bool(row_dict.get('premium', None)),
            employer_name=row_dict.get('employer_name', None)
        )

    @staticmethod
    def _list_skills(skills):
        """
        Преобразует строку с навыком в список навыков. Список навыков или None возращает обратно
        :param skills: Строка с навыком, или список навыков, или None
        :type skills: List[str] or str or None
        :return: Список навыков или None, если он передан в skills
        :rtype: List[str] or None
        :raises TypeError: Если тип skills не является подходящим
        """
        if skills is None:
            return None
        if type(skills) is list:
            return skills
        if type(skills) is str:
            return [skills]

        raise TypeError(f"Type ${type(skills)} is wrong for raw skills")

    @property
    def year(self):
        """
        Возвращает год публикации вакансии
        :return: Год
        :rtype: int
        """
        return self.published_at.year

    @property
    def str_publish_date(self):
        """
        Возвращает отформатированную строку даты публикации
        :return: Дата публикации в формате ДД.ММ.ГГГГ
        :rtype: str
        """
        return self.published_at.strftime('%d.%m.%Y')
