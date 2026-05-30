"""Choice-screen / menu integration helpers.

These are plain functions (no Ren'Py imports) so the gating and visibility logic
the choice screen and the menu wrapper rely on can be unit-tested.

Background: setting ``config.menu_include_disabled = True`` makes Ren'Py pass a
menu choice whose ``if`` condition is false through to the choice screen as an
*insensitive* item (a ``ChoiceReturn`` with ``sensitive == False``), rather than
dropping it. Menu captions arrive as items whose ``action`` is ``None``. These
helpers classify those items and decide whether a menu is worth displaying.
"""

from __future__ import annotations


def locked_hint(item) -> str | None:
    """Return the ``(locked="...")`` hint carried by a menu item, or ``None``.

    Works for both a choice-screen item (a ``MenuEntry``) and a ``ChoiceReturn``
    value, since both expose a ``kwargs`` mapping of the menu-choice arguments.
    """
    return (getattr(item, "kwargs", None) or {}).get("locked")


def classify_choice(action_is_none: bool, sensitive: bool, hint) -> str:
    """Classify a choice-screen item into how it should be rendered.

    Returns one of:

    * ``"caption"``  -- a menu caption (no action); render as Ren'Py does by
      default (an insensitive label).
    * ``"available"`` -- a selectable choice.
    * ``"locked"``   -- gated off but annotated with ``(locked="...")``; show it
      greyed-out with the hint.
    * ``"hidden"``   -- gated off with no hint; do not render it.
    """
    if action_is_none:
        return "caption"
    if sensitive:
        return "available"
    if hint is not None:
        return "locked"
    return "hidden"


def menu_has_available_choice(items) -> bool:
    """Return whether a menu has at least one item worth displaying.

    ``items`` are the ``(label, value)`` pairs Ren'Py passes to the ``menu``
    store function: ``value`` is a ``ChoiceReturn`` (carrying ``.sensitive`` and
    ``.kwargs``) for a real choice, or ``None`` for a caption.

    A menu is worth displaying if it has a selectable choice or a
    ``(locked="...")`` choice to show. Otherwise the caller should skip it,
    mirroring Ren'Py's built-in "no available choice" bail-out, which
    ``config.menu_include_disabled`` would otherwise suppress (leaving the player
    stranded on an empty choice screen).
    """
    for _label, value in items:
        if value is None:
            continue
        if getattr(value, "sensitive", True):
            return True
        if locked_hint(value):
            return True
    return False


def menu_has_selectable_choice(items) -> bool:
    """Return whether a menu has at least one *selectable* (clickable) choice.

    Like :func:`menu_has_available_choice`, except a ``(locked="...")`` choice
    does **not** count -- it is shown greyed-out and cannot be picked. The menu
    wrapper uses this to spot an *all-locked* menu (one displayed only because of
    its locked choices, with nothing the player can actually click) so it can add
    a "Continue" escape choice, rather than stranding the player on a screen
    whose every row is insensitive.
    """
    for _label, value in items:
        if value is None:
            continue
        if getattr(value, "sensitive", True):
            return True
    return False
