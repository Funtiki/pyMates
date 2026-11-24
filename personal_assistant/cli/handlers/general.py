"""Загальні команди: привітання й довідка."""

from itertools import groupby

from ...context import AppContext
from .. import ui
from ..registry import COMMANDS, command

EXIT_COMMANDS = ("exit", "close")


def _help_line(usage: str, description: str, width: int) -> str:
    """Рядок довідки: команда кольором, вирівняна по ширині, і опис."""
    # Вирівнюємо до розфарбовування: кольорові коди не мають ширини на екрані
    return f"  {ui.command_name(usage.ljust(width))}- {description}"


@command("hello", "hello", "greeting")
def hello(args: list[str], ctx: AppContext) -> str:
    """Привітатися."""
    return "How can I help you?"


@command("help", "help", "show this list")
def show_help(args: list[str], ctx: AppContext) -> str:
    """Список усіх команд, згрупований за розділами."""
    commands = list(COMMANDS.values())
    width = max(len(c.usage) for c in commands) + 2
    lines = [ui.title("Available commands:")]
    # groupby без сортування: розділи йдуть у порядку реєстрації
    for group, items in groupby(commands, key=lambda c: c.group):
        lines.append(ui.title(f"\n{group}:"))
        lines += [_help_line(c.usage, c.description, width) for c in items]
    lines.append("")
    lines.append(_help_line(" / ".join(EXIT_COMMANDS), "save and exit", width))
    lines.append(ui.warning("\nIn any dialog type 'cancel' to abort the action."))
    return "\n".join(lines)
