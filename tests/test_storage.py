"""Тести збереження й завантаження даних."""

import pytest

from personal_assistant.models import AddressBook, Record
from personal_assistant.storage import load_data, save_data


def test_roundtrip(tmp_path):
    """Збережена книга завантажується з тими самими даними."""
    book = AddressBook()
    record = Record("John")
    record.set_email("john@example.com")
    book.add_record(record)
    path = tmp_path / "data" / "book.pkl"

    save_data(book, path)
    loaded = load_data(path, AddressBook)

    assert loaded.find("john").email.value == "john@example.com"


def test_missing_file_gives_empty(tmp_path):
    """Без файлу повертається порожня книга."""
    assert load_data(tmp_path / "none.pkl", AddressBook) == AddressBook()


@pytest.mark.parametrize("content", [b"not a pickle", b"garbage\n", b"", b"\x80"])
def test_broken_file_is_backed_up(tmp_path, content):
    """Пошкоджений файл відкладається як .broken, книга порожня."""
    path = tmp_path / "book.pkl"
    path.write_bytes(content)

    assert len(load_data(path, AddressBook)) == 0
    assert (tmp_path / "book.pkl.broken").exists()


def test_wrong_type_is_backed_up(tmp_path):
    """Файл з іншим типом даних не підсовується як адресна книга."""
    path = tmp_path / "book.pkl"
    save_data(["not", "a", "book"], path)

    assert isinstance(load_data(path, AddressBook), AddressBook)
    assert (tmp_path / "book.pkl.broken").exists()
