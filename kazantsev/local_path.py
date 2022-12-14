from pathlib import Path


def get_local_path(value: str) -> Path:
    """
    Преобразует строковый локальный путь в объект Path
    :param value: строковый локальный путь относительно папки kazantsev
    :return: объект Path
    """
    return Path(__file__).parent.joinpath(value)
