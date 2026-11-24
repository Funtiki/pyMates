"""Тести оформлення виводу."""

import re

import pytest

from personal_assistant.cli import ui

ANSI_CODE = re.compile(r"\x1b\[[0-9;]*m")


@pytest.fixture
def colors(monkeypatch):
    """Увімкнути кольори примусово."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("FORCE_COLOR", "1")


def test_no_color_gives_plain_text():
    """З NO_COLOR текст лишається без службових кодів."""
    assert ui.success("ok") == "ok"


@pytest.mark.usefixtures("colors")
def test_force_color_adds_codes():
    """З FORCE_COLOR текст розфарбовується й закінчується скиданням стилю."""
    text = ui.error("bad")
    assert ANSI_CODE.search(text)
    assert ANSI_CODE.sub("", text) == "bad"


def test_pycharm_console_gets_colors(monkeypatch):
    """У консолі PyCharm (не термінал) кольори все одно вмикаються."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("PYCHARM_HOSTED", "1")
    assert ui.colors_enabled()


@pytest.mark.usefixtures("colors")
def test_colored_table_is_aligned():
    """Кольорові коди не ламають ширину стовпців таблиці."""
    rows = [(ui.highlight("John"), "x"), ("Anna-Maria", "y")]
    lines = [
        ANSI_CODE.sub("", line) for line in ui.table(("Name", "B"), rows).split("\n")
    ]
    assert len({len(line) for line in lines}) == 1
