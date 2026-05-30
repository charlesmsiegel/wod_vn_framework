# tests/test_menus.py
"""Tests for choice-screen / menu integration helpers."""

from wod_core.menus import locked_hint, classify_choice, menu_has_available_choice


class FakeChoice:
    """Stand-in for a Ren'Py MenuEntry / ChoiceReturn (exposes kwargs/sensitive)."""

    def __init__(self, kwargs=None, sensitive=None, no_kwargs=False):
        if not no_kwargs:
            self.kwargs = kwargs if kwargs is not None else {}
        if sensitive is not None:
            self.sensitive = sensitive


class TestLockedHint:
    def test_none_when_kwargs_missing(self):
        assert locked_hint(FakeChoice(no_kwargs=True)) is None

    def test_none_when_kwargs_empty(self):
        assert locked_hint(FakeChoice(kwargs={})) is None

    def test_none_when_kwargs_is_none(self):
        item = FakeChoice(no_kwargs=True)
        item.kwargs = None
        assert locked_hint(item) is None

    def test_returns_hint(self):
        assert locked_hint(FakeChoice(kwargs={"locked": "You lack the knowledge..."})) == (
            "You lack the knowledge..."
        )


class TestClassifyChoice:
    def test_caption(self):
        # action is None -> menu caption, rendered as default (not dropped).
        assert classify_choice(action_is_none=True, sensitive=False, hint=None) == "caption"

    def test_caption_takes_precedence(self):
        assert classify_choice(action_is_none=True, sensitive=False, hint="x") == "caption"

    def test_available(self):
        assert classify_choice(action_is_none=False, sensitive=True, hint=None) == "available"

    def test_available_even_with_hint(self):
        # A locked choice whose gate is met is simply available.
        assert classify_choice(action_is_none=False, sensitive=True, hint="x") == "available"

    def test_locked(self):
        assert classify_choice(action_is_none=False, sensitive=False, hint="nope") == "locked"

    def test_hidden(self):
        # Gated off with no hint -> hidden (spec: hidden by default).
        assert classify_choice(action_is_none=False, sensitive=False, hint=None) == "hidden"


class TestMenuHasAvailableChoice:
    def test_empty(self):
        assert menu_has_available_choice([]) is False

    def test_only_caption(self):
        # A caption alone is not a reason to display the menu.
        assert menu_has_available_choice([("Which way?", None)]) is False

    def test_enabled_choice(self):
        items = [("Go", FakeChoice(sensitive=True))]
        assert menu_has_available_choice(items) is True

    def test_all_disabled_no_locked_skips(self):
        # Every choice gated off and none annotated -> skip (no stall).
        items = [
            ("A", FakeChoice(sensitive=False)),
            ("B", FakeChoice(sensitive=False)),
        ]
        assert menu_has_available_choice(items) is False

    def test_disabled_but_locked_displays(self):
        items = [("A", FakeChoice(kwargs={"locked": "nope"}, sensitive=False))]
        assert menu_has_available_choice(items) is True

    def test_mixed(self):
        items = [
            ("Caption", None),
            ("Gated", FakeChoice(sensitive=False)),
            ("Open", FakeChoice(sensitive=True)),
        ]
        assert menu_has_available_choice(items) is True
