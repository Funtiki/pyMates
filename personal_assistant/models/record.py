"""Запис адресної книги: один контакт з усіма його полями."""

import re
from typing import Optional

from .fields import (
    COUNTRY_CODE,
    Address,
    Birthday,
    Email,
    Name,
    Phone,
    normalize_phone,
)


class Record:
    """Контакт: ім'я, телефони, email, адреса й день народження.

    Обов'язкове лише ім'я, решту полів можна додати пізніше.
    Телефонів може бути кілька, інших полів — по одному.
    """

    def __init__(self, name: str) -> None:
        """Створити контакт лише з іменем."""
        self.name = Name(name)
        self.phones: list[Phone] = []
        self.email: Optional[Email] = None
        self.address: Optional[Address] = None
        self.birthday: Optional[Birthday] = None

    def _ensure_new_phone(self, phone: str) -> None:
        """Кинути помилку, якщо такий номер уже є в контакті."""
        if self.find_phone(phone):
            raise ValueError(f"Phone {phone} already exists for {self.name.value}.")

    def add_phone(self, phone: str) -> None:
        """Додати ще один телефон (дублікати не допускаються)."""
        new_phone = Phone(phone)
        self._ensure_new_phone(new_phone.value)
        self.phones.append(new_phone)

    def remove_phone(self, phone: str) -> None:
        """Видалити телефон; номер можна передати в будь-якому форматі."""
        found = self.find_phone(phone)
        if found is None:
            raise ValueError(f"Phone {phone} not found.")
        self.phones.remove(found)

    def edit_phone(self, old_phone: str, new_phone: str) -> None:
        """Замінити старий номер новим, зберігши його позицію у списку."""
        found = self.find_phone(old_phone)
        if found is None:
            raise ValueError(f"Phone {old_phone} not found.")
        replacement = Phone(new_phone)
        if replacement.value == found.value:
            raise ValueError("New phone is the same as the old one, nothing changed.")
        self._ensure_new_phone(replacement.value)
        self.phones[self.phones.index(found)] = replacement

    def find_phone(self, phone: str) -> Optional[Phone]:
        """Знайти телефон; приймає будь-який формат: 066..., 38066..., +38066..."""
        phone = normalize_phone(phone)
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def set_name(self, name: str) -> None:
        """Змінити ім'я. Ключ у книзі оновлює ``AddressBook.rename``."""
        self.name = Name(name)

    def set_email(self, email: str) -> None:
        """Додати або замінити email."""
        self.email = Email(email)

    def set_address(self, address: str) -> None:
        """Додати або замінити адресу."""
        self.address = Address(address)

    def set_birthday(self, birthday: str) -> None:
        """Додати або замінити день народження."""
        self.birthday = Birthday(birthday)

    def clear_field(self, field: str) -> None:
        """Очистити необов'язкове поле: email, address, birthday або phones."""
        if field == "phones":
            self.phones = []
        elif field in ("email", "address", "birthday"):
            setattr(self, field, None)
        else:
            raise ValueError(f"Field '{field}' cannot be cleared.")

    def matches(self, query: str) -> bool:
        """Чи містить будь-яке поле контакту рядок ``query`` (без регістру).

        Телефон шукаємо і за цифрами, тож "067 123" знайде 0671234567.
        """
        query = query.strip().lower()
        if not query:
            return False
        texts = [self.name.value, *(p.value for p in self.phones)]
        texts += [str(f) for f in (self.email, self.address, self.birthday) if f]
        if any(query in text.lower() for text in texts):
            return True
        # Частина номера з кодом країни: "+38066" шукаємо як "066"
        digits = re.sub(r"[\s()+-]", "", query)
        if digits.startswith(COUNTRY_CODE + "0"):
            digits = digits[len(COUNTRY_CODE) :]
        return digits.isdigit() and any(digits in p.value for p in self.phones)

    def __str__(self) -> str:
        """Контакт одним рядком; порожні поля пропускаються."""
        parts = [f"Contact name: {self.name.value}"]
        if self.phones:
            parts.append("phones: " + "; ".join(p.value for p in self.phones))
        if self.email:
            parts.append(f"email: {self.email}")
        if self.address:
            parts.append(f"address: {self.address}")
        if self.birthday:
            parts.append(f"birthday: {self.birthday}")
        return ", ".join(parts)
