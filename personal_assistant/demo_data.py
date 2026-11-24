"""Заповнити адресну книгу тестовими контактами для перевірки й демо.

Запуск: ``python -m personal_assistant.demo_data``

Дні народження рахуються від сьогоднішньої дати, тож команда ``birthdays``
завжди має що показати. Наявну книгу перед перезаписом відкладаємо в ``.bak``.
"""

import calendar
import sys
from datetime import date, timedelta
from typing import Optional

from .context import ADDRESS_BOOK_FILE
from .models import AddressBook, Record
from .models.fields import DATE_FORMAT
from .storage import data_file, load_data, save_data

# (ім'я, телефони, email, адреса, (рік народження, через скільки днів ДН))
DemoContact = tuple[
    str, list[str], Optional[str], Optional[str], Optional[tuple[int, int]]
]

DEMO_CONTACTS: list[DemoContact] = [
    (
        "Іван Петренко",
        ["0501112233", "+380671234567"],
        "ivan.petrenko@ukr.net",
        "Київ, вул. Хрещатик, 22, кв. 5",
        (1990, 0),  # сьогодні
    ),
    (
        "Olena Kovalenko",
        ["0632223344"],
        "olena.k@gmail.com",
        "Lviv, Svobody Ave, 15",
        (1995, 1),  # завтра
    ),
    (
        "Андрій Шевченко",
        ["0939876543"],
        "andrii@meta.ua",
        "Одеса, вул. Дерибасівська, 7",
        (1988, 3),
    ),
    (
        "Maria Bondarenko",
        ["0661234567", "0441234567"],
        "maria.bond@outlook.com",
        None,
        (2000, 6),
    ),
    (
        "Taras Melnyk",
        ["0997654321"],
        None,
        "Kharkiv, Sumska St, 48, apt 12",
        (1979, 7),  # рівно на межі тижня
    ),
    (
        "Софія Ткаченко",
        ["0685554433"],
        "sofia.tkachenko@gmail.com",
        "Дніпро, просп. Яворницького, 101",
        (2002, 12),  # поза тижнем, видно з birthdays 14
    ),
    (
        "John Smith",
        ["+38 (073) 111-22-33"],
        "john.smith@example.com",
        "Kyiv, Velyka Vasylkivska St, 5",
        (1985, 30),
    ),
    (
        "Anna-Maria O'Neil",
        [],
        "anna.oneil@example.com",
        None,
        None,  # без дня народження і телефону
    ),
    (
        "Dmytro Lysenko",
        ["0954443322"],
        "d.lysenko@ukr.net",
        "Zaporizhzhia, Soborny Ave, 160",
        (1992, 200),
    ),
    (
        "Юлія Мороз",
        ["0671112200"],
        None,
        None,
        (1998, 364),  # щойно минув — найдальший
    ),
]


def _birthday(born_year: int, days_from_today: int, today: date) -> str:
    """Дата народження, щоб день народження був через ``days_from_today`` днів."""
    next_birthday = today + timedelta(days=days_from_today)
    if (next_birthday.month, next_birthday.day) == (2, 29):
        # Народитися 29.02 можна лише у високосний рік
        while not calendar.isleap(born_year):
            born_year -= 1
    return next_birthday.replace(year=born_year).strftime(DATE_FORMAT)


def build_demo_book(today: Optional[date] = None) -> AddressBook:
    """Створити адресну книгу з тестовими контактами."""
    today = today or date.today()
    book = AddressBook()
    for name, phones, email, address, birthday in DEMO_CONTACTS:
        record = Record(name)
        for phone in phones:
            record.add_phone(phone)
        if email:
            record.set_email(email)
        if address:
            record.set_address(address)
        if birthday:
            record.set_birthday(_birthday(*birthday, today))
        book.add_record(record)
    return book


def main() -> None:
    """Записати тестові контакти у файл даних, зберігши копію старого."""
    path = data_file(ADDRESS_BOOK_FILE)
    if path.exists():
        existing = load_data(path, AddressBook)
        if existing and "--force" not in sys.argv:
            try:
                answer = input(
                    f"{path} already has {len(existing)} contact(s). "
                    "Replace them with demo data? A backup will be kept (y/n): "
                )
            except (EOFError, KeyboardInterrupt):  # Ctrl+D / Ctrl+C = "ні"
                answer = ""
                print()
            if answer.strip().lower() not in ("y", "yes"):
                print("Nothing changed.")
                return
        if path.exists():
            backup = path.with_suffix(path.suffix + ".bak")
            path.replace(backup)
            print(f"Old data saved to {backup}")

    book = build_demo_book()
    save_data(book, path)
    print(f"Saved {len(book)} demo contacts to {path}")


if __name__ == "__main__":
    main()
