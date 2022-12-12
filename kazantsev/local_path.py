from pathlib import Path


class LocalPath:
    """
    Класс для работы с локальными путями к файлам и директориям
    """
    def __init__(self, value):
        """
        Инициализирует класс
        :param value: Локальный путь к файлу или директории
        :type value: str
        """
        self.value = value

    @property
    def absolute(self):
        """
        Возвращает абсолютный путь для данного локального
        :return: Абсолютный путь в виде строки
        :rtype: str
        """
        return Path(__file__).parent.joinpath(self.value).absolute().as_posix()