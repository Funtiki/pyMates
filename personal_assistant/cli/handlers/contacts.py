"""Команди для роботи з контактами адресної книги."""

from typing import Callable, Optional

from ...context import AppContext
from ...models import AddressBook, Record
from ...models.address_book import DEFAULT_BIRTHDAY_DAYS
from ...models.fields import DATE_FORMAT
from .. import prompts, ui
from ..decorators import NotFoundError
from ..registry import COMMANDS, command, require_args

GROUP = "Contacts"
CONTACT_HEADERS = ("Name", "Phones", "Email", "Address", "Birthday")
EDITABLE_FIELDS = ("name", "phone", "email", "address", "birthday")
CLEARABLE_FIELDS = ("phones", "email", "address", "birthday")


def _contact_not_found(name: str) -> NotFoundError:
    """Помилка "контакт не знайдено" з підказкою, як його шукати."""
    return NotFoundError(
        f"Contact '{name}' not found. Use 'search' or 'all' to see contacts."
    )


def resolve_contact(args: list[str], book: AddressBook) -> tuple[Record, list[str]]:
    """Знайти контакт на початку аргументів і повернути решту аргументів.

    Ім'я може складатися з кількох слів, тому беремо найдовший префікс,
    що збігається з наявним контактом: для ``John Smith email a@b.com``
    це ``John Smith``, а решта — ``["email", "a@b.com"]``.
    """
    for end in range(len(args), 0, -1):
        record = book.find(" ".join(args[:end]))
        if record is not None:
            return record, args[end:]
    raise _contact_not_found(_guess_name(args))


def _guess_name(args: list[str]) -> str:
    """Ймовірне ім'я для повідомлення про помилку: слова до назви поля чи значення.

    ``["Jon", "Smith", "email", "a@b.com"]`` -> ``"Jon Smith"``.
    """
    keywords = set(EDITABLE_FIELDS) | set(CLEARABLE_FIELDS)
    words = []
    for word in args:
        if word.lower() in keywords or any(ch in word for ch in "0123456789@+("):
            break
        words.append(word)
    return " ".join(words or args)


def _get_exact(args: list[str], book: AddressBook) -> Record:
    """Контакт, ім'я якого — усі аргументи разом."""
    name = " ".join(args)
    record = book.find(name)
    if record is None:
        raise _contact_not_found(name)
    return record


def _contact_row(record: Record) -> tuple[str, ...]:
    """Рядок таблиці контактів; кожен телефон з нового рядка."""
    return (
        record.name.value,
        "\n".join(p.value for p in record.phones),
        str(record.email or ""),
        str(record.address or ""),
        str(record.birthday or ""),
    )


def contacts_table(records: list[Record]) -> str:
    """Таблиця контактів."""
    return ui.table(CONTACT_HEADERS, (_contact_row(r) for r in records))


def _as_parser(setter: Callable[[str], None]) -> Callable[[str], bool]:
    """Пристосувати сеттер (``record.set_email`` тощо) до ``prompts.ask_valid``.

    ``ask_valid`` повторює запит, доки функція кидає ``ValueError``, і
    повертає її результат. Сеттери повертають ``None``, а ``None`` означає
    "пропущено", тож після успіху повертаємо ``True``.
    """

    def parse(value: str) -> bool:
        """Застосувати значення; ``ValueError`` з сеттера йде далі."""
        setter(value)
        return True

    return parse


def _ask_phones(record: Record) -> None:
    """Питати телефони по одному, доки користувач не натисне Enter."""
    prompt = "Phone"
    add = _as_parser(record.add_phone)
    while prompts.ask_valid(prompt, add, optional=True):
        prompt = "Another phone"


@command("add", "add [name]", "add a contact step by step", GROUP)
def add_contact(args: list[str], ctx: AppContext) -> str:
    """Додати контакт: ім'я, телефони, email, адреса, день народження.

    Кожне поле перевіряється одразу; при помилці питаємо ще раз.
    Контакт потрапляє в книгу лише наприкінці, тож ``cancel`` нічого не лишає.
    """

    def new_record(name: str) -> Record:
        """Створити контакт, якщо ім'я коректне й ще не зайняте."""
        record = Record(name)
        if ctx.book.find(record.name.value):
            raise ValueError(
                f"Contact '{record.name.value}' already exists. "
                "Use 'edit' to change it."
            )
        return record

    print(ui.info("New contact. Type 'cancel' at any step to abort."))
    record = prompts.retry_until_valid(" ".join(args), "Name", new_record)
    _ask_phones(record)
    prompts.ask_valid("Email", _as_parser(record.set_email), optional=True)
    prompts.ask_valid(
        "Address (e.g. Kyiv, Khreshchatyk St, 1, apt 5)",
        _as_parser(record.set_address),
        optional=True,
    )
    prompts.ask_valid(
        "Birthday (DD.MM.YYYY)", _as_parser(record.set_birthday), optional=True
    )

    ctx.book.add_record(record)
    return ui.success(f"Contact '{record.name.value}' added.")


@command("all", "all", "show all contacts", GROUP)
def show_all(args: list[str], ctx: AppContext) -> str:
    """Усі контакти за алфавітом."""
    if not ctx.book:
        return ui.warning("No contacts saved. Use 'add' to create one.")
    records = sorted(ctx.book.values(), key=lambda r: r.name.value.lower())
    return contacts_table(records)


@command("show", "show <name>", "show one contact", GROUP)
def show_contact(args: list[str], ctx: AppContext) -> str:
    """Один контакт за точним ім'ям."""
    require_args(args, 1, "show")
    return contacts_table([_get_exact(args, ctx.book)])


@command(
    "search",
    "search <text>",
    "find contacts by name, phone, email, address or birthday",
    GROUP,
)
def search_contacts(args: list[str], ctx: AppContext) -> str:
    """Пошук за входженням тексту в будь-яке поле, без урахування регістру."""
    require_args(args, 1, "search")
    query = " ".join(args)
    found = ctx.book.search(query)
    if not found:
        return ui.warning(f"No contacts match '{query}'.")
    return f"Found {len(found)} contact(s):\n" + contacts_table(found)


def _edit_phone(record: Record, value: Optional[str]) -> None:
    """Замінити телефон; якщо їх кілька — спершу спитати, який саме."""
    if not record.phones:
        prompts.retry_until_valid(value, "Phone", _as_parser(record.add_phone))
        return
    old = record.phones[0]
    if len(record.phones) > 1:
        index = prompts.choose(
            "Which phone to change", [p.value for p in record.phones]
        )
        old = record.phones[index]
    prompts.retry_until_valid(
        value,
        "New phone",
        _as_parser(lambda new: record.edit_phone(old.value, new)),
    )


@command(
    "edit",
    "edit <name> [field] [value]",
    "change name, phone, email, address or birthday",
    GROUP,
)
def edit_contact(args: list[str], ctx: AppContext) -> str:
    """Змінити одне поле контакту.

    Поле і значення можна передати одразу (``edit John email a@b.com``)
    або вибрати й ввести в діалозі. Некоректне значення питаємо повторно.
    """
    require_args(args, 1, "edit")
    record, rest = resolve_contact(args, ctx.book)

    if rest:
        field = rest[0].lower()
        if field not in EDITABLE_FIELDS:
            raise ValueError(
                f"Unknown field '{rest[0]}'. Choose one of: "
                + ", ".join(EDITABLE_FIELDS)
                + "."
            )
    else:
        print(ui.info(f"What do you want to change for {record.name.value}?"))
        field = EDITABLE_FIELDS[prompts.choose("Field", list(EDITABLE_FIELDS))]

    value = " ".join(rest[1:]) or None
    if field == "name":
        old_name = record.name.value
        prompts.retry_until_valid(
            value,
            "New name",
            _as_parser(lambda new: ctx.book.rename(old_name, new)),
        )
    elif field == "phone":
        _edit_phone(record, value)
    else:
        setters = {
            "email": record.set_email,
            "address": record.set_address,
            "birthday": record.set_birthday,
        }
        prompts.retry_until_valid(value, f"New {field}", _as_parser(setters[field]))

    return ui.success("Contact updated.") + "\n" + contacts_table([record])


@command("add-phone", "add-phone <name> [phone]", "add one more phone", GROUP)
def add_phone(args: list[str], ctx: AppContext) -> str:
    """Додати телефон до наявного контакту."""
    require_args(args, 1, "add-phone")
    record, rest = resolve_contact(args, ctx.book)
    prompts.retry_until_valid(
        "".join(rest) or None, "Phone", _as_parser(record.add_phone)
    )
    return ui.success(f"Phone added to {record.name.value}.")


@command("remove-phone", "remove-phone <name> [phone]", "remove a phone", GROUP)
def remove_phone(args: list[str], ctx: AppContext) -> str:
    """Видалити один телефон; без номера в аргументах — вибрати зі списку."""
    require_args(args, 1, "remove-phone")
    record, rest = resolve_contact(args, ctx.book)
    if not record.phones:
        return ui.warning(f"{record.name.value} has no phones.")
    if rest:
        record.remove_phone("".join(rest))
    else:
        phones = [p.value for p in record.phones]
        record.remove_phone(phones[prompts.choose("Phone to remove", phones)])
    return ui.success(f"Phone removed from {record.name.value}.")


@command(
    "clear",
    "clear <name> <field>",
    "clear phones, email, address or birthday",
    GROUP,
)
def clear_field(args: list[str], ctx: AppContext) -> str:
    """Очистити необов'язкове поле контакту після підтвердження."""
    require_args(args, 2, "clear")
    record, rest = resolve_contact(args, ctx.book)
    if len(rest) != 1 or rest[0].lower() not in CLEARABLE_FIELDS:
        raise ValueError(
            "Choose a field to clear: " + ", ".join(CLEARABLE_FIELDS) + "."
        )
    field = rest[0].lower()
    if not prompts.confirm(f"Clear {field} of {record.name.value}?"):
        return ui.warning("Nothing changed.")
    record.clear_field(field)
    return ui.success(f"Cleared {field} of {record.name.value}.")


@command("delete", "delete <name>", "delete a contact", GROUP)
def delete_contact(args: list[str], ctx: AppContext) -> str:
    """Видалити контакт після підтвердження."""
    require_args(args, 1, "delete")
    record = _get_exact(args, ctx.book)
    print(contacts_table([record]))
    if not prompts.confirm(f"Delete contact '{record.name.value}'?"):
        return ui.warning("Nothing deleted.")
    ctx.book.delete(record.name.value)
    return ui.success(f"Contact '{record.name.value}' deleted.")


def _parse_days(args: list[str]) -> int:
    """Кількість днів з аргументів; за замовчуванням 7."""
    if not args:
        return DEFAULT_BIRTHDAY_DAYS
    if len(args) > 1 or not args[0].isdigit():
        raise ValueError(
            "Days must be a whole number, e.g. 'birthdays 10'. "
            f"Usage: {COMMANDS['birthdays'].usage}"
        )
    return int(args[0])


def _days_label(days_left: int) -> str:
    """Людський опис відстані до дня народження."""
    if days_left == 0:
        return "today"
    if days_left == 1:
        return "tomorrow"
    return f"in {days_left} days"


@command(
    "birthdays",
    "birthdays [days]",
    f"birthdays in the next N days (default {DEFAULT_BIRTHDAY_DAYS})",
    GROUP,
)
def upcoming_birthdays(args: list[str], ctx: AppContext) -> str:
    """Контакти з днем народження від сьогодні до N днів уперед."""
    days = _parse_days(args)
    upcoming = ctx.book.get_upcoming_birthdays(days)
    if not upcoming:
        return ui.warning(f"No birthdays in the next {days} day(s).")
    rows = (
        (
            u.record.name.value,
            u.next_date.strftime(DATE_FORMAT),
            _days_label(u.days_left),
            u.turns,
        )
        for u in upcoming
    )
    title = ui.info(f"Birthdays in the next {days} day(s):")
    return title + "\n" + ui.table(("Name", "Date", "When", "Turns"), rows)
