"""Тести моделей: валідація полів, контакт, адресна книга."""

from datetime import date

import pytest

from personal_assistant.models import (
    Address,
    AddressBook,
    Birthday,
    Email,
    Name,
    Phone,
    Record,
)


@pytest.mark.parametrize(
    "value", ["John", "John Smith", "Anna-Maria", "O'Neil", "Іван"]
)
def test_name_valid(value):
    """Коректні імена приймаються без змін."""
    assert Name(value).value == value


@pytest.mark.parametrize("value", ["", "J", "John1", "   ", "x" * 51, "@nna"])
def test_name_invalid(value):
    """Порожні, короткі, задовгі імена та імена з цифрами відхиляються."""
    with pytest.raises(ValueError):
        Name(value)


@pytest.mark.parametrize(
    "value",
    ["0661234567", "+380661234567", "380661234567", "(066) 123-45-67"],
)
def test_phone_normalized(value):
    """Різні формати номера зводяться до 10 цифр."""
    assert Phone(value).value == "0661234567"


@pytest.mark.parametrize("value", ["066123456", "06612345678", "phone", ""])
def test_phone_invalid(value):
    """Номер не з 10 цифр відхиляється."""
    with pytest.raises(ValueError):
        Phone(value)


@pytest.mark.parametrize(
    "value", ["john@example.com", "J.Smith+work@mail.co.uk", "a_b@sub.domain.ua"]
)
def test_email_valid(value):
    """Коректний email приймається і зберігається малими літерами."""
    assert Email(value).value == value.lower()


@pytest.mark.parametrize(
    "value", ["john", "john@", "@mail.com", "john@mail", "john@mail.c", "a b@mail.com"]
)
def test_email_invalid(value):
    """Email без @, домену чи зони відхиляється."""
    with pytest.raises(ValueError):
        Email(value)


def test_address_trims_spaces_and_validates_length():
    """Зайві пробіли прибираються, порожня адреса відхиляється."""
    assert Address("  Kyiv,   Main St, 1 ").value == "Kyiv, Main St, 1"
    with pytest.raises(ValueError):
        Address("  ")


@pytest.mark.parametrize("value", ["31.02.1990", "1990-01-01", "01.01.3000"])
def test_birthday_invalid(value):
    """Неіснуюча дата, інший формат і майбутня дата відхиляються."""
    with pytest.raises(ValueError):
        Birthday(value)


def test_record_phones():
    """Додавання, заміна й видалення телефонів; дублікат відхиляється."""
    record = Record("John")
    record.add_phone("0661234567")
    with pytest.raises(ValueError):
        record.add_phone("+380661234567")  # той самий номер
    record.edit_phone("066 123 45 67", "0501112233")
    assert [p.value for p in record.phones] == ["0501112233"]
    record.remove_phone("0501112233")
    assert record.phones == []


def test_record_matches_any_field():
    """Пошук знаходить контакт за будь-яким полем."""
    record = Record("John Smith")
    record.add_phone("0661234567")
    record.set_email("john@example.com")
    record.set_address("Kyiv, Main St, 1")
    record.set_birthday("05.03.1990")
    for query in ("smith", "066 123", "+38066", "EXAMPLE", "main st", "05.03"):
        assert record.matches(query), query
    assert not record.matches("lviv")


@pytest.fixture
def book():
    """Книга з двома днями народження й контактом без дати."""
    book = AddressBook()
    for name, birthday in [("John", "25.11.1990"), ("Anna", "01.12.1985")]:
        record = Record(name)
        record.set_birthday(birthday)
        book.add_record(record)
    book.add_record(Record("Bob"))
    return book


def test_add_record_rejects_duplicates(book):
    """Контакт з наявним ім'ям (без урахування регістру) не додається."""
    with pytest.raises(ValueError):
        book.add_record(Record("john"))


def test_rename(book):
    """Перейменування оновлює ключ; зайняте ім'я відхиляється."""
    book.rename("john", "John Smith")
    assert book.find("john") is None
    assert book.find("JOHN SMITH").name.value == "John Smith"
    with pytest.raises(ValueError):
        book.rename("Anna", "Bob")


def test_delete(book):
    """Видалення прибирає контакт; повторне кидає KeyError."""
    book.delete("Bob")
    assert book.find("Bob") is None
    with pytest.raises(KeyError):
        book.delete("Bob")


def test_upcoming_birthdays(book):
    """Дні народження в межах N днів, від найближчого."""
    today = date(2026, 11, 24)
    names = [u.record.name.value for u in book.get_upcoming_birthdays(7, today)]
    assert names == ["John", "Anna"]
    assert [u.record.name.value for u in book.get_upcoming_birthdays(3, today)] == [
        "John"
    ]
    assert book.get_upcoming_birthdays(0, today) == []


def test_upcoming_birthdays_wraps_to_next_year():
    """Наприкінці року враховуються дні народження в січні."""
    book = AddressBook()
    record = Record("Ny")
    record.set_birthday("02.01.2000")
    book.add_record(record)
    (upcoming,) = book.get_upcoming_birthdays(7, date(2026, 12, 30))
    assert upcoming.next_date == date(2027, 1, 2)
    assert upcoming.days_left == 3
    assert upcoming.turns == 27
