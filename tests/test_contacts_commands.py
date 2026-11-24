"""Тести команд для контактів з підставленим вводом (фікстури — у conftest.py)."""

from personal_assistant.app import run_command


def test_add_reprompts_invalid_values(ctx, answers):
    """Майстер add перепитує некоректні телефон і email."""
    answers += [
        "123",  # телефон некоректний -> питаємо знову
        "0661234567",
        "",  # більше телефонів немає
        "john@",  # email некоректний
        "john@example.com",
        "Kyiv, Main St, 1",
        "",  # день народження пропускаємо
    ]
    result = run_command("add John Smith", ctx)
    assert "added" in result
    record = ctx.book.find("john smith")
    assert record.phones[0].value == "0661234567"
    assert record.email.value == "john@example.com"
    assert record.birthday is None
    assert answers == []


def test_add_cancel_leaves_book_unchanged(ctx, answers):
    """Після cancel контакт не додається."""
    answers += ["0661234567", "cancel"]
    assert "cancelled" in run_command("add John", ctx)
    assert len(ctx.book) == 0


def test_add_existing_name_asks_for_another(ctx, answers):
    """Зайняте ім'я відхиляється і запитується інше."""
    answers += ["", "", "", ""]
    run_command("add John", ctx)
    answers += ["Bob", "", "", "", ""]
    assert "Bob" in run_command("add john", ctx)
    assert answers == []


def test_edit_with_value_in_command(ctx, answers):
    """Поле можна змінити одним рядком."""
    answers += ["", "", "", ""]
    run_command("add John Smith", ctx)
    assert "updated" in run_command("edit John Smith email a@b.com", ctx)
    assert ctx.book.find("John Smith").email.value == "a@b.com"


def test_edit_invalid_value_then_fix(ctx, answers):
    """Некоректне значення з команди перепитується."""
    answers += ["", "", "", ""]
    run_command("add John", ctx)
    answers += ["01.01.1990"]
    run_command("edit John birthday 32.01.1990", ctx)
    assert str(ctx.book.find("John").birthday) == "01.01.1990"


def test_edit_name_by_menu(ctx, answers):
    """Ім'я змінюється через меню полів."""
    answers += ["", "", "", ""]
    run_command("add John", ctx)
    answers += ["1", "Johnny"]
    run_command("edit John", ctx)
    assert ctx.book.find("Johnny") is not None
    assert ctx.book.find("John") is None


def test_edit_unknown_field(ctx, answers):
    """Невідоме поле дає зрозумілу помилку."""
    answers += ["", "", "", ""]
    run_command("add John", ctx)
    assert "Unknown field" in run_command("edit John age 30", ctx)


def test_search(ctx, answers):
    """Пошук знаходить за адресою і повідомляє, коли нічого немає."""
    answers += ["0661234567", "", "", "Lviv, Main St", ""]
    run_command("add John", ctx)
    assert "John" in run_command("search lviv", ctx)
    assert "No contacts" in run_command("search kyiv", ctx)


def test_delete_needs_confirmation(ctx, answers):
    """Контакт видаляється лише після підтвердження."""
    answers += ["", "", "", ""]
    run_command("add John", ctx)
    answers += ["n"]
    run_command("delete John", ctx)
    assert ctx.book.find("John") is not None
    answers += ["y"]
    run_command("delete John", ctx)
    assert ctx.book.find("John") is None


def test_not_found_and_usage_errors(ctx):
    """Помилки показуються повідомленням, а не падінням."""
    assert "not found" in run_command("delete Nobody", ctx)
    assert "'Jon Smith' not found" in run_command("edit Jon Smith email a@b.com", ctx)
    assert "Usage" in run_command("edit", ctx)
    assert "whole number" in run_command("birthdays soon", ctx)
    assert "Unknown command" in run_command("fly", ctx)
