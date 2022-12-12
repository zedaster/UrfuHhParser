from pathlib import Path


class LocalPath:
    """
    Класс для работы с локальными путями к файлам и директориям

    Attributes:
        value (str): Строковое значение данного локального путь
        path (Path): Данный путь в виде объекта pathlib.Path
    """

    def __init__(self, value):
        """
        Инициализирует класс
        :param value: Локальный путь к файлу или директории
        :type value: str
        """
        self.value = value
        self.path = Path(__file__).parent.joinpath(value)

    @property
    def absolute(self):
        """
        Возвращает абсолютный путь для данного локального
        :return: Абсолютный путь в виде строки
        :rtype: str
        """
        return self.path.absolute().as_posix()

    @property
    def name(self):
        """
        Возвращает имя текущего файла или директории
        :return: Строчное название
        :rtype: str
        """
        return self.path.name
