import csv
import shutil
from pathlib import Path

from kazantsev.datetime_parser import parse_datetime
from kazantsev.local_path import get_local_path

YEAR_SEPARATED_PATH = get_local_path('./year_separated/')


class YearSeparated(object):
    """
    Класс, делящий csv файл на несколько разных по годам

    Attributes:
        main_csv_path: Путь к переданному изначальному CSV
        chunk_csv_paths: Пути к полученным CSV, которые были получение путем разделения по годам основного CSV
    """
    def __init__(self, path: Path, datetime_column_name='published_at'):
        """
        Инициализирует объект и делить csv по указаному пути на csv файлы по годам
        Полученные файлы сохраняются по пути, указанному в `year_separated.YEAR_SEPARATED_PATH`
        :param path: Путь к CSV файлу
        :type path: Path
        :param datetime_column_name: Название колонки с датой, из которой будет браться год
        :type datetime_column_name: str
        """
        self.main_csv_path = path
        self.chunk_csv_paths = []

        shutil.rmtree(YEAR_SEPARATED_PATH, ignore_errors=True)
        YEAR_SEPARATED_PATH.mkdir()

        opened_files = []
        current_writers = {}
        with open(path.absolute(), 'r', encoding='utf_8_sig') as file:
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

                if len(row) != len(title_row):
                    continue

                year = parse_datetime(row[datetime_column_id]).year
                if year not in current_writers:
                    year_path = self._get_year_path(path, year)
                    self.chunk_csv_paths.append(year_path)
                    file = open(year_path, 'w', encoding='utf_8_sig', newline='')
                    opened_files.append(file)
                    current_writers[year] = csv.writer(file)
                    current_writers[year].writerow(title_row)
                current_writers[year].writerow(row)

        for file in opened_files:
            file.close()

    @staticmethod
    def _get_year_path(path: Path, year):
        split_filename = path.name.split('.')
        split_filename[0] += f'_{year}'
        year_filename = '.'.join(split_filename)
        return YEAR_SEPARATED_PATH.joinpath(year_filename)
