"""Головний цикл застосунку: читає команди і передає їх обробникам."""

import sys
from typing import Callable

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter

from .cli import handlers  # noqa: F401  (реєструє всі команди)
from .cli import ui
from .cli.handlers.general import EXIT_COMMANDS
from .cli.parser import parse_input
from .cli.registry import COMMANDS
from .context import AppContext

PROMPT = "Enter a command: "


def _make_reader() -> Callable[[str], str]:
    """Функція читання команди.

    У терміналі — prompt_toolkit з автодоповненням команд (Tab) та історією
    (стрілки вгору/вниз). Якщо ввід не з терміналу (наприклад, команди
    подано через pipe), prompt_toolkit не працює, тож беремо звичайний input.
    """
    if not sys.stdin.isatty():
        return input
    completer = WordCompleter(
        [*COMMANDS, *EXIT_COMMANDS], ignore_case=True, sentence=True
    )
    session: PromptSession[str] = PromptSession(completer=completer)
    return lambda prompt: session.prompt(prompt)


def run_command(user_input: str, ctx: AppContext) -> str:
    """Виконати один рядок вводу і повернути відповідь для виводу."""
    command, args = parse_input(user_input)
    entry = COMMANDS.get(command)
    if entry is None:
        return ui.error(
            f"Unknown command '{command}'. Type 'help' to see all commands."
        )
    return entry.handler(args, ctx)


def main() -> None:
    """Запустити застосунок; дані зберігаються після кожної команди і на виході."""
    ctx = AppContext.load()
    read = _make_reader()
    print(
        ui.info("Welcome to the personal assistant! Type 'help' to see all commands.")
    )
    try:
        while True:
            try:
                user_input = read(PROMPT)
            except (EOFError, KeyboardInterrupt):  # Ctrl+D / Ctrl+C
                print("\nGood bye!")
                break

            command, _ = parse_input(user_input)
            if not command:
                continue
            if command in EXIT_COMMANDS:
                print("Good bye!")
                break

            print(run_command(user_input, ctx))
            ctx.save()
    finally:
        ctx.save()


if __name__ == "__main__":
    main()
