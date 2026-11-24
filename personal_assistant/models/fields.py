"""Поля контакту. Кожне поле валідує значення ще в конструкторі.

Якщо значення некоректне, конструктор кидає ``ValueError`` з текстом,
який можна одразу показати користувачу.
"""

import re
from datetime import date, datetime
from typing import Any

DATE_FORMAT = "%d.%m.%Y"
PHONE_LENGTH = 10
COUNTRY_CODE = "38"

NAME_MIN_LENGTH = 2
NAME_MAX_LENGTH = 50
ADDRESS_MIN_LENGTH = 3
ADDRESS_MAX_LENGTH = 200

# Літери будь-якої абетки, пробіли, дефіс, апостроф і крапка: "Anna-Maria", "O'Neil"
NAME_PATTERN = re.compile(r"^[^\W\d_]+(?:[ .'’-]+[^\W\d_]+)*\.?$")

# Свідомо простий шаблон: локальна частина, @, домен із зоною від 2 літер.
# Повна перевірка за RFC 5322 тут зайва, а помилки на кшталт "user@mail" ловить
EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)*\.[A-Za-z]{2,}$"
)


def _strip_separators(value: str) -> str:
    """Прибрати пробіли, дефіси й дужки: "(066) 377-85-32" -> "0663778532"."""
    return re.sub(r"[\s()-]", "", value)


def normalize_phone(value: str) -> str:
    """Звести номер до 10 цифр: +380661234567 / 380661234567 -> 0661234567."""
    if not isinstance(value, str):
        return value
    value = _strip_separators(value)
    if value.startswith("+" + COUNTRY_CODE):
        value = value[1:]
    if (
        value.startswith(COUNTRY_CODE)
        and len(value) == len(COUNTRY_CODE) + PHONE_LENGTH
    ):
        value = value[len(COUNTRY_CODE) :]
    return value


def is_full_phone(value: str) -> bool:
    """Чи вже набрано повний номер: 10 цифр або 12 з кодом країни."""
    digits = _strip_separators(value).lstrip("+")
    if not digits.isdigit():
        return False
    if digits.startswith(COUNTRY_CODE):
        return len(digits) == len(COUNTRY_CODE) + PHONE_LENGTH
    return len(digits) == PHONE_LENGTH


class Field:
    """Базове поле: зберігає значення і вміє його показати."""

    def __init__(self, value: Any) -> None:
        """Зберегти значення без перевірок (їх роблять підкласи)."""
        self.value = value

    def __str__(self) -> str:
        """Значення як рядок для виводу."""
        return str(self.value)

    def __eq__(self, other: object) -> bool:
        """Поля рівні, якщо це той самий тип і те саме значення."""
        return type(self) is type(other) and self.value == other.value

    def __hash__(self) -> int:
        """Хеш за типом і значенням, щоб поле можна було класти в set."""
        return hash((type(self).__name__, self.value))


class Name(Field):
    """Ім'я контакту: 2–50 символів, лише літери та роздільники між словами."""

    def __init__(self, value: str) -> None:
        """Перевірити ім'я й прибрати зайві пробіли."""
        value = " ".join(str(value).split())
        if not NAME_MIN_LENGTH <= len(value) <= NAME_MAX_LENGTH:
            raise ValueError(
                f"Name must be {NAME_MIN_LENGTH}-{NAME_MAX_LENGTH} characters long."
            )
        if not NAME_PATTERN.match(value):
            raise ValueError(
                "Name may contain only letters, spaces, hyphens, "
                "apostrophes and dots (e.g. John Smith, Anna-Maria)."
            )
        super().__init__(value)


class Phone(Field):
    """Телефон: рівно 10 цифр, код країни +38 відкидається."""

    def __init__(self, value: str) -> None:
        """Нормалізувати номер і перевірити, що лишилось 10 цифр."""
        value = normalize_phone(value)
        if not (
            isinstance(value, str) and value.isdigit() and len(value) == PHONE_LENGTH
        ):
            raise ValueError(
                f"Phone number must contain exactly {PHONE_LENGTH} digits "
                "(e.g. 0661234567 or +380661234567)."
            )
        super().__init__(value)


class Email(Field):
    """Email у форматі name@domain.tld, зберігається малими літерами."""

    def __init__(self, value: str) -> None:
        """Перевірити email за шаблоном ``EMAIL_PATTERN``."""
        value = str(value).strip()
        if not EMAIL_PATTERN.match(value):
            raise ValueError("Invalid email. Use a format like name@example.com.")
        super().__init__(value.lower())


class Address(Field):
    """Адреса у довільному форматі, наприклад "Kyiv, Khreshchatyk St, 1, apt 5"."""

    def __init__(self, value: str) -> None:
        """Перевірити, що адреса не порожня і не надто довга."""
        value = " ".join(str(value).split())
        if not ADDRESS_MIN_LENGTH <= len(value) <= ADDRESS_MAX_LENGTH:
            raise ValueError(
                f"Address must be {ADDRESS_MIN_LENGTH}-{ADDRESS_MAX_LENGTH} "
                "characters long."
            )
        super().__init__(value)


class Birthday(Field):
    """День народження у форматі DD.MM.YYYY, не в майбутньому."""

    def __init__(self, value: str) -> None:
        """Розібрати дату; strptime відсіює й неіснуючі дати, як 31.02."""
        try:
            birthday = datetime.strptime(str(value).strip(), DATE_FORMAT).date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY.") from None
        if birthday > date.today():
            raise ValueError("Birthday cannot be in the future.")
        super().__init__(birthday)

    def __str__(self) -> str:
        """Дата у форматі DD.MM.YYYY."""
        return self.value.strftime(DATE_FORMAT)
