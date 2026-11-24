"""Збереження даних на диск у форматі pickle.

Функції універсальні: ними можна зберігати будь-яку колекцію
(адресну книгу, нотатник тощо) в окремий файл.
"""

import os
import pickle
from pathlib import Path
from typing import Callable, TypeVar, Union

T = TypeVar("T")
PathLike = Union[Path, str]

# Дані лежать у домашній теці, щоб не залежати від того, звідки запущено
# застосунок. Для тестів чи демо теку можна змінити змінною середовища
DATA_DIR = Path(
    os.environ.get("PERSONAL_ASSISTANT_DATA_DIR", Path.home() / ".personal_assistant")
)


def data_file(name: str) -> Path:
    """Повний шлях до файлу даних у ``DATA_DIR``."""
    return DATA_DIR / name


def save_data(data: object, filename: PathLike) -> None:
    """Зберегти об'єкт у файл, створивши теку за потреби.

    Спершу пишемо у тимчасовий файл і лише потім підміняємо основний,
    щоб збій посеред запису не зіпсував уже збережені дані.
    """
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with open(tmp_path, "wb") as f:
        pickle.dump(data, f)
    tmp_path.replace(path)


def load_data(filename: PathLike, factory: Callable[[], T]) -> T:
    """Завантажити об'єкт з файлу або створити порожній через ``factory``.

    Якщо файл пошкоджено або в ньому інший тип даних, відкладаємо його поруч
    із суфіксом ``.broken``, щоб дані не перезаписались мовчки і їх можна
    було відновити.
    """
    path = Path(filename)
    try:
        with open(path, "rb") as f:
            data = pickle.load(f)
    except FileNotFoundError:
        return factory()
    # На пошкодженому файлі pickle може кинути майже будь-який виняток
    # (UnpicklingError, ValueError, KeyError, ImportError ...), тож ловимо всі
    except Exception:
        data = None

    # factory зазвичай сам клас (AddressBook), але може бути й функцією
    expected_type = factory if isinstance(factory, type) else type(factory())
    if isinstance(data, expected_type):
        return data

    backup = path.with_suffix(path.suffix + ".broken")
    path.replace(backup)
    print(f"Could not read {path.name}, saved it as {backup.name} and started fresh.")
    return factory()
