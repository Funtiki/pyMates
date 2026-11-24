"""Загальні команди: привітання й довідка."""

from itertools import groupby

from ...context import AppContext
from .. import ui
from ..registry import COMMANDS, command

EXIT_COMMANDS = ("exit", "close")


@command("hello", "hello", "greeting")
def hello(args: list[str], ctx: AppContext) -> str:
    """Привітатися."""
    return "How can I help you?"


@command("help", "help", "show this list")
def show_help(args: list[str], ctx: AppContext) -> str:
    """Список усіх команд, згрупований за розділами."""
    commands = list(COMMANDS.values())
    width = max(len(c.usage) for c in commands) + 2
    lines = [ui.info("Available commands:")]
    # groupby без сортування: розділи йдуть у порядку реєстрації
    for group, items in groupby(commands, key=lambda c: c.group):
        lines.append(ui.info(f"\n{group}:"))
        lines += [f"  {c.usage:<{width}}- {c.description}" for c in items]
    lines.append(f"\n  {' / '.join(EXIT_COMMANDS):<{width}}- save and exit")
    lines.append(ui.warning("\nIn any dialog type 'cancel' to abort the action."))
    return "\n".join(lines)
