"""Розбір введеного рядка на команду й аргументи."""


def parse_input(user_input: str) -> tuple[str, list[str]]:
    """Розбити рядок: "add John Smith" -> ("add", ["John", "Smith"])."""
    parts = user_input.split()
    if not parts:
        return "", []
    cmd, *args = parts
    return cmd.lower(), args
