"""Оформлення виводу: кольори (colorama) і таблиці (prettytable).

Кольори вмикаються в терміналі та в консолі запуску PyCharm. Вимкнути їх
можна змінною середовища ``NO_COLOR=1``, увімкнути примусово — ``FORCE_COLOR=1``.
"""

import os
import sys
from typing import Iterable, Sequence

from colorama import Fore, Style, just_fix_windows_console
from prettytable import PrettyTable, TableStyle

# Вмикає ANSI-кольори в старих консолях Windows; на macOS/Linux нічого не робить
just_fix_windows_console()

# Консоль запуску PyCharm не є терміналом (isatty() == False), але кольори
# показує; PyCharm сам виставляє цю змінну
IDE_ENV_VARS = ("PYCHARM_HOSTED",)


def colors_enabled() -> bool:
    """Чи розфарбовувати вивід.

    Без кольорів, коли вивід іде у файл чи pipe (і в тестах), щоб там не
    з'являлись службові символи на кшталт ``\\x1b[32m``.
    """
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    if any(os.environ.get(name) for name in IDE_ENV_VARS):
        return True
    return sys.stdout.isatty()


def _colored(text: str, *styles: str) -> str:
    """Застосувати стилі colorama до тексту, якщо кольори ввімкнені."""
    if not colors_enabled():
        return text
    return "".join(styles) + text + Style.RESET_ALL


def success(text: str) -> str:
    """Успішна дія — зелений."""
    return _colored(text, Fore.GREEN)


def error(text: str) -> str:
    """Помилка — червоний."""
    return _colored(text, Fore.RED)


def warning(text: str) -> str:
    """Попередження, підказка, "нічого не знайдено" — жовтий."""
    return _colored(text, Fore.YELLOW)


def info(text: str) -> str:
    """Заголовок чи пояснення — блакитний."""
    return _colored(text, Fore.CYAN)


def title(text: str) -> str:
    """Помітний заголовок — жирний блакитний."""
    return _colored(text, Style.BRIGHT, Fore.CYAN)


def highlight(text: str) -> str:
    """Виділити важливе значення — жирний."""
    return _colored(text, Style.BRIGHT)


def accent(text: str) -> str:
    """Те, що треба помітити серед іншого (ДН сьогодні) — жирний пурпуровий."""
    return _colored(text, Style.BRIGHT, Fore.MAGENTA)


def command_name(text: str) -> str:
    """Назва команди в довідці — жовтий."""
    return _colored(text, Fore.YELLOW)


def prompt(text: str) -> str:
    """Запрошення до вводу — жирний зелений."""
    return _colored(text, Style.BRIGHT, Fore.GREEN)


def table(headers: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    """Таблиця з рамкою і кольоровими заголовками; довгий текст переноситься.

    prettytable правильно рахує ширину стовпців і для тексту з кольорами.
    """
    pretty = PrettyTable([title(h) for h in headers])
    pretty.set_style(TableStyle.SINGLE_BORDER)
    pretty.align = "l"
    pretty.max_width = 40
    for row in rows:
        pretty.add_row(["" if cell is None else str(cell) for cell in row])
    return pretty.get_string()
