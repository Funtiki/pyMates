"""Тести генератора тестових даних."""

from datetime import date

import pytest

from personal_assistant.demo_data import DEMO_CONTACTS, build_demo_book


@pytest.mark.parametrize("today", [date(2026, 11, 24), date(2028, 2, 29)])
def test_demo_book_is_valid_and_has_birthdays(today):
    """Усі контакти проходять валідацію, а за тиждень є 5 днів народження."""
    book = build_demo_book(today)
    assert len(book) == len(DEMO_CONTACTS)
    upcoming = book.get_upcoming_birthdays(7, today)
    assert [u.days_left for u in upcoming] == [0, 1, 3, 6, 7]
