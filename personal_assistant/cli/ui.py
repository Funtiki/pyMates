"""Оформлення виводу: кольори (colorama) і таблиці (prettytable)."""

import sys
from typing import Iterable, Sequence

from colorama import Fore, Style, just_fix_windows_console
from prettytable import PrettyTable, TableStyle

# Вмикає ANSI-кольори в старих консолях Windows; на macOS/Linux нічого не робить
just_fix_windows_console()


def _colored(text: str, color: str) -> str:
    """Розфарбувати текст, лише якщо вивід іде в термінал (а не у файл чи тест)."""
    if not sys.stdout.isatty():
        return text
    return f"{color}{text}{Style.RESET_ALL}"


def success(text: str) -> str:
    """Повідомлення про успішну дію (зелене)."""
    return _colored(text, Fore.GREEN)


def error(text: str) -> str:
    """Повідомлення про помилку (червоне)."""
    return _colored(text, Fore.RED)


def warning(text: str) -> str:
    """Попередження або підказка (жовте)."""
    return _colored(text, Fore.YELLOW)


def info(text: str) -> str:
    """Нейтральний акцент, наприклад заголовок (блакитний)."""
    return _colored(text, Fore.CYAN)


def table(headers: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    """Таблиця з рамкою; довгий текст у клітинках переноситься."""
    pretty = PrettyTable(list(headers))
    pretty.set_style(TableStyle.SINGLE_BORDER)
    pretty.align = "l"
    pretty.max_width = 40
    for row in rows:
        pretty.add_row(["" if cell is None else str(cell) for cell in row])
    return pretty.get_string()
