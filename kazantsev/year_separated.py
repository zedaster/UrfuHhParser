import csv

from kazantsev.datetime_parser import parse_datetime
from kazantsev.local_path import LocalPath

YEAR_SEPARATED_PATH = LocalPath('./year_separated/')


class YearSeparated(object):
    """
    Класс, делящий csv файл на несколько разных по годам
    """
    def __init__(self, local_path: LocalPath, datetime_column_name: str):
        """
        Инициализирует объект и делить csv по указаному пути на csv файлы по годам
        Полученные файлы сохраняются по пути, указанному в `year_separated.YEAR_SEPARATED_PATH`
        :param local_path: Локальный путь к CSV файлу
        :type local_path: LocalPath
        :param datetime_column_name: Название колонки с датой, из которой будет браться год
        :type datetime_column_name: str
        """
        opened_files = []
        current_writers = {}
        with open(local_path.absolute, 'r', encoding='utf_8_sig') as file:
            reader = csv.reader(file)
            datetime_column_id = None
            title_row = None
            for row in reader:
                if datetime_column_id is None:
                    try:
                        datetime_column_id = row.index(datetime_column_name)
                    except ValueError:
                        raise ValueError(
                            f'Datetime column name "{datetime_column_name}" is not defined in the first row')
                    title_row = row
                    continue

                year = parse_datetime(row[datetime_column_id]).year

                if year not in current_writers:
                    year_path = self._get_year_path(local_path, year)
                    if year_path.exists():
                        year_path.unlink()
                    file = open(year_path, 'w', encoding='utf_8_sig', newline='')
                    opened_files.append(file)
                    current_writers[year] = csv.writer(file)
                    current_writers[year].writerow(title_row)

                current_writers[year].writerow(row)

        for file in opened_files:
            file.close()

    @staticmethod
    def _get_year_path(local_path, year):
        split_filename = local_path.name.split('.')
        split_filename[0] += f'_{year}'
        year_filename = '.'.join(split_filename)
        return YEAR_SEPARATED_PATH.path.joinpath(year_filename)
