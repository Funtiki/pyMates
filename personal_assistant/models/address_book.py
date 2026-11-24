"""Адресна книга — колекція контактів з пошуком і днями народження."""

from collections import UserDict
from dataclasses import dataclass
from datetime import date
from typing import Optional

from .record import Record

DEFAULT_BIRTHDAY_DAYS = 7


@dataclass(frozen=True)
class UpcomingBirthday:
    """Найближчий день народження контакту."""

    record: Record
    next_date: date  # найближча дата святкування (цього або наступного року)
    days_left: int
    turns: int  # скільки років виповнюється


def _birthday_in_year(birthday: date, year: int) -> date:
    """День народження в заданому році; 29.02 у невисокосний рік -> 28.02."""
    try:
        return birthday.replace(year=year)
    except ValueError:
        return birthday.replace(year=year, day=28)


class AddressBook(UserDict):
    """Контакти за ключем — ім'ям малими літерами (john = John)."""

    @staticmethod
    def _key(name: str) -> str:
        """Ключ словника з імені: без зайвих пробілів і регістру."""
        return " ".join(name.split()).lower()

    def add_record(self, record: Record) -> None:
        """Додати новий контакт; ім'я має бути унікальним."""
        key = self._key(record.name.value)
        if key in self.data:
            raise ValueError(f"Contact '{record.name.value}' already exists.")
        self.data[key] = record

    def find(self, name: str) -> Optional[Record]:
        """Знайти контакт за точним ім'ям (без урахування регістру)."""
        return self.data.get(self._key(name))

    def delete(self, name: str) -> Record:
        """Видалити контакт і повернути його."""
        record = self.data.pop(self._key(name), None)
        if record is None:
            raise KeyError(name)
        return record

    def rename(self, old_name: str, new_name: str) -> None:
        """Перейменувати контакт, оновивши ключ у книзі."""
        record = self.find(old_name)
        if record is None:
            raise KeyError(old_name)
        new_key = self._key(new_name)
        old_key = self._key(old_name)
        if new_key != old_key and new_key in self.data:
            raise ValueError(f"Contact '{new_name}' already exists.")
        record.set_name(new_name)
        del self.data[old_key]
        self.data[self._key(record.name.value)] = record

    def search(self, query: str) -> list[Record]:
        """Контакти, у яких будь-яке поле містить ``query``, за алфавітом."""
        found = [r for r in self.data.values() if r.matches(query)]
        return sorted(found, key=lambda r: r.name.value.lower())

    def get_upcoming_birthdays(
        self, days: int = DEFAULT_BIRTHDAY_DAYS, today: Optional[date] = None
    ) -> list[UpcomingBirthday]:
        """Дні народження від сьогодні до ``days`` днів уперед включно.

        Результат відсортовано від найближчого. ``today`` можна передати в
        тестах, щоб не залежати від поточної дати.
        """
        if days < 0:
            raise ValueError("Number of days cannot be negative.")
        today = today or date.today()
        upcoming = []

        for record in self.data.values():
            if record.birthday is None:
                continue
            born = record.birthday.value
            birthday = _birthday_in_year(born, today.year)
            if birthday < today:  # цього року вже минув
                birthday = _birthday_in_year(born, today.year + 1)

            days_left = (birthday - today).days
            if days_left <= days:
                upcoming.append(
                    UpcomingBirthday(
                        record, birthday, days_left, birthday.year - born.year
                    )
                )

        return sorted(upcoming, key=lambda u: (u.days_left, u.record.name.value))
