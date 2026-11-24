"""Реєстр команд.

Кожна команда реєструється декоратором ``@command`` у своєму модулі
(``cli/handlers/contacts.py``, ``cli/handlers/notes.py`` ...). Звідси
беруться і диспетчеризація, і ``help``, і автодоповнення, тож нову
команду не треба дописувати в кілька місць.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from .decorators import UsageError, input_error

if TYPE_CHECKING:
    from ..context import AppContext

Handler = Callable[[list[str], "AppContext"], str]


@dataclass(frozen=True)
class Command:
    """Опис команди для диспетчера й довідки."""

    name: str
    handler: Handler
    usage: str
    description: str
    group: str


COMMANDS: dict[str, Command] = {}


def command(
    name: str, usage: str, description: str, group: str = "General"
) -> Callable[[Handler], Handler]:
    """Зареєструвати функцію як команду ``name``.

    Функція отримує список аргументів і ``AppContext`` та повертає рядок
    для виводу. Помилки обробляє ``input_error``.
    """

    def decorator(func: Handler) -> Handler:
        if name in COMMANDS:
            raise ValueError(f"Command '{name}' is already registered.")
        COMMANDS[name] = Command(name, input_error(func), usage, description, group)
        return func

    return decorator


def require_args(args: list[str], count: int, name: str) -> None:
    """Кинути ``UsageError`` з форматом команди, якщо аргументів замало."""
    if len(args) < count:
        # .get: помилка в назві команди не має маскуватись під "not found"
        entry = COMMANDS.get(name)
        raise UsageError(entry.usage if entry else name)
