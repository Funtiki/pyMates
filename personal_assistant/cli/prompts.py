"""Діалоги з користувачем: повторний запит при помилці, скасування, y/n.

Уся взаємодія йде через ``ask``, тож у тестах достатньо підмінити
``prompts.input_func`` на функцію, що повертає заготовлені відповіді.
"""

from typing import Callable, Optional, TypeVar

from . import ui

T = TypeVar("T")

CANCEL_WORDS = {"cancel"}
YES_WORDS = {"y", "yes"}
NO_WORDS = {"n", "no"}

input_func: Callable[[str], str] = input


class OperationCancelled(Exception):
    """Користувач скасував дію (ввів cancel або натиснув Ctrl+C / Ctrl+D)."""


def ask(prompt: str) -> str:
    """Запитати рядок; ``cancel`` або Ctrl+C/Ctrl+D скасовують усю дію."""
    try:
        answer = input_func(ui.prompt(prompt)).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        raise OperationCancelled from None
    if answer.lower() in CANCEL_WORDS:
        raise OperationCancelled
    return answer


def ask_valid(
    prompt: str, parse: Callable[[str], T], optional: bool = False
) -> Optional[T]:
    """Питати, доки ``parse`` не прийме значення без ``ValueError``.

    Для необов'язкового поля порожня відповідь означає "пропустити"
    і повертає ``None``.
    """
    hint = " (Enter to skip)" if optional else ""
    while True:
        answer = ask(f"{prompt}{hint}: ")
        if not answer:
            if optional:
                return None
            print(ui.warning("This field is required. Type 'cancel' to abort."))
            continue
        try:
            return parse(answer)
        except ValueError as e:
            print(ui.error(f"{e} Try again or type 'cancel' to abort."))


def retry_until_valid(
    value: Optional[str], prompt: str, parse: Callable[[str], T]
) -> T:
    """Застосувати значення з команди, а якщо його нема чи воно хибне — питати.

    Так команду можна ввести одним рядком (``edit John email a@b.com``),
    а помилку виправити, не набираючи все заново.
    """
    if value:
        try:
            return parse(value)
        except ValueError as e:
            print(ui.error(f"{e} Try again or type 'cancel' to abort."))
    return ask_valid(prompt, parse)


def confirm(prompt: str) -> bool:
    """Запитати так/ні; повторює питання, доки не отримає y/yes або n/no."""
    while True:
        answer = ask(f"{prompt} (y/n): ").lower()
        if answer in YES_WORDS:
            return True
        if answer in NO_WORDS:
            return False
        print(ui.warning("Please answer 'y' or 'n'."))


def choose(prompt: str, options: list[str]) -> int:
    """Показати нумерований список і повернути індекс обраного варіанта."""
    for number, option in enumerate(options, start=1):
        print(f"  {ui.highlight(str(number) + '.')} {option}")

    def parse(answer: str) -> int:
        """Номер варіанта (з 1) -> індекс у списку (з 0)."""
        if not answer.isdigit() or not 1 <= int(answer) <= len(options):
            raise ValueError(f"Enter a number from 1 to {len(options)}.")
        return int(answer) - 1

    return ask_valid(prompt, parse)
