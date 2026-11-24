"""Декоратор, що перетворює помилки команд на зрозумілі повідомлення."""

from functools import wraps
from typing import Any, Callable

from . import ui
from .prompts import OperationCancelled


class UsageError(Exception):
    """Команду викликано з неправильними аргументами."""


class NotFoundError(KeyError):
    """Запис не знайдено; текст помилки показується користувачу як є."""

    def __str__(self) -> str:
        """Повідомлення без лапок, які KeyError додає за замовчуванням."""
        return str(self.args[0]) if self.args else "Not found."


def input_error(func: Callable[..., str]) -> Callable[..., str]:
    """Ловити очікувані помилки, щоб застосунок не падав.

    - ``UsageError`` — бракує аргументів, показуємо формат команди;
    - ``ValueError`` — не пройшла валідація поля;
    - ``KeyError`` — запис не знайдено; ключ — його ім'я чи ID, а саме
      повідомлення можна задати через ``NotFoundError``;
    - ``OperationCancelled`` — користувач скасував дію.
    """

    @wraps(func)
    def inner(*args: Any, **kwargs: Any) -> str:
        try:
            return func(*args, **kwargs)
        except UsageError as e:
            return ui.error(f"Not enough arguments. Usage: {e}")
        except ValueError as e:
            return ui.error(str(e))
        except NotFoundError as e:
            return ui.error(str(e))
        except KeyError as e:
            key = e.args[0] if e.args else ""
            return ui.error(f"'{key}' not found.")
        except OperationCancelled:
            return ui.warning("Operation cancelled.")

    return inner
