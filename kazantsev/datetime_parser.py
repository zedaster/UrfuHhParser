import ciso8601


# def _parse_datetime_ordinary(str_datetime):
#     return datetime.strptime(str_datetime, '%Y-%m-%dT%H:%M:%S%z')

def _parse_datetime_with_ciso8601(str_datetime):
    # Microsoft Visual C++ 14.0 or greater is required
    return ciso8601.parse_datetime(str_datetime)


# DATETIME_PATTERN = re.compile(r'^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})([+-]\d{2})(\d{2})$')
#
#
# def _parse_datetime_with_regex(str_datetime):
#     match = DATETIME_PATTERN.match(str_datetime)
#     tz = timezone(timedelta(hours=int(match.group(7)), minutes=int(match.group(8))))
#     return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4)),
#                     int(match.group(5)), int(match.group(6)), tzinfo=tz)
#
#
# def _parse_datetime_directly(str_datetime):
#     """
#     Парсит дату+время из строки посимвольно за O(n)
#     :param str_datetime: Строка формата '2022-07-05T20:45:58+0300'
#     :return: объект дата-времени
#     :rtype: datetime
#     """
#     # 2022-07-05T20:45:58+0300
#     # dt = datetime(2022, 7, 5, 20, 45, 58)
#     year = 0
#     month = 0
#     day = 0
#     hour = 0
#     minute = 0
#     second = 0
#     offset_hour = 0
#     offset_min = 0
#
#     if len(str_datetime) != 24 or str_datetime[4] != '-' or str_datetime[7] != '-' or str_datetime[10] != 'T' or \
#             str_datetime[13] != ':' or str_datetime[16] != ':' or str_datetime[19] not in ('-', '+'):
#         raise ValueError(f'Некоректный форматы даты "{str_datetime}". Коректный формат: 2022-07-05T20:45:58+0300')
#
#     for i in range(4):
#         year += int(str_datetime[i]) * 10 ** (3 - i)
#     for i in range(5, 7):
#         month += int(str_datetime[i]) * 10 ** (6 - i)
#     for i in range(8, 10):
#         day += int(str_datetime[i]) * 10 ** (9 - i)
#     for i in range(11, 13):
#         hour += int(str_datetime[i]) * 10 ** (12 - i)
#     for i in range(14, 16):
#         minute += int(str_datetime[i]) * 10 ** (15 - i)
#     for i in range(17, 19):
#         second += int(str_datetime[i]) * 10 ** (18 - i)
#     for i in range(20, 22):
#         offset_hour += int(str_datetime[i]) * 10 ** (21 - i)
#     for i in range(22, 24):
#         offset_min += int(str_datetime[i]) * 10 ** (23 - i)
#
#     offset = offset_hour * 60 * 60 + offset_min * 60
#     if str_datetime[19] == '-':
#         offset *= -1
#
#     return datetime(year, month, day, hour, minute, second, tzinfo=tzoffset(None, offset))

def parse_datetime(str_datetime):
    """
    Парсит datetime из строки самым быстрым способом
    :param str_datetime: Строка с датой и временем формата '2022-07-05T20:45:58+0300'
    :return: объект дата-времени
    :rtype datetime
    """
    _parse_datetime_with_ciso8601(str_datetime)
