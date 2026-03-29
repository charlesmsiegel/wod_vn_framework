"""Module-level gating API — delegates to active character."""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wod_core.engine import Character

_active_character: Character | None = None


def set_active(character: Character | None) -> None:
    global _active_character
    _active_character = character


def get_active() -> Character:
    if _active_character is None:
        raise RuntimeError("No active character set. Call wod_core.set_active(character) first.")
    return _active_character


def gate(name: str, op: str, value: int) -> bool:
    return get_active().gate(name, op, value)


def has(name: str) -> bool:
    return get_active().has(name)
