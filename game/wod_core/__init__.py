"""WoD VN Framework — Core Engine."""

from __future__ import annotations

__version__ = "0.1.0"

from wod_core import migrations
from wod_core.gating import gate, has, can_use, set_active, get_active
from wod_core.menus import locked_hint, classify_choice, menu_has_available_choice
from wod_core.loader import SplatLoader
from wod_core.migrations import (
    MigrationError,
    migration,
    register_migration,
)


def drain_migration_reports() -> list:
    """Return and clear migration reports produced since the last call.

    Surfaced by the framework's ``after_load`` label to notify the player when
    a save was migrated onto a newer schema version.
    """
    return migrations.drain_reports()

_loader: SplatLoader | None = None


def init(game_dir: str) -> None:
    global _loader
    _loader = SplatLoader(game_dir)


def get_loader() -> SplatLoader:
    if _loader is None:
        raise RuntimeError("wod_core not initialized. Call wod_core.init(game_dir) first.")
    return _loader


def load_splat(splat_id: str, overrides: str | None = None):
    return get_loader().load_splat(splat_id, overrides=overrides)


def load_all_splats():
    loader = get_loader()
    for splat_id in loader.discover_splats():
        loader.load_splat(splat_id)


def load_character(char_path: str):
    return get_loader().load_character(char_path)


def show_hud(resources=None):
    """Show the resource HUD. Call from within Ren'Py only."""
    import renpy.exports as renpy_api
    import renpy
    renpy.store.wod_hud_visible = True
    renpy.store.wod_hud_resources = resources
    renpy_api.show_screen("resource_hud")


def hide_hud():
    """Hide the resource HUD. Call from within Ren'Py only."""
    import renpy.exports as renpy_api
    import renpy
    renpy.store.wod_hud_visible = False
    renpy.store.wod_hud_resources = None
    renpy_api.hide_screen("resource_hud")


class _Config:
    """Framework configuration."""
    show_gate_toasts = False
    gate_toast_format = "{trait} {value} — {result}"
    # When True, bracket shorthand ([Forces >= 3]) is compiled to native
    # Ren'Py automatically at init time, in developer mode. The pass runs in
    # `python early`, so this flag only disables it when set that early (a
    # `python early` block in a file sorting before 00_wod_preprocess.rpy);
    # for an ordering-independent opt-out set WOD_AUTO_PREPROCESS=0 instead.
    # See game/00_wod_preprocess.rpy.
    auto_preprocess = True

config = _Config()


def show_toast(message: str, duration: float = 2.0):
    """Show a brief toast notification. Call from within Ren'Py only."""
    import renpy.exports as renpy_api
    renpy_api.show_screen("wod_toast", message=message, duration=duration)


def chargen(splat_id: str, mode: str = "full", preset: dict | None = None):
    """Run character creation. Call from within Ren'Py only.

    Returns a Character on success, or None if the player cancels.
    """
    import renpy.exports as renpy_api
    from wod_core.chargen import ChargenState, build_character

    loader = get_loader()
    if splat_id not in loader.loaded_splats:
        raise ValueError(f"Splat {splat_id!r} not loaded.")
    splat = loader.loaded_splats[splat_id]

    if splat.chargen_config is None:
        raise ValueError(f"Splat {splat_id!r} has no chargen config.")

    state = ChargenState(splat_id, mode, splat.schema, splat.chargen_config, splat)

    # Apply presets
    if preset:
        if "identity" not in state.data:
            state.data["identity"] = {}
        state.data["identity"].update(preset)

    # Screen loop
    while True:
        step_name = state.steps[state.current_step]
        screen_name = f"chargen_{step_name}"

        result = renpy_api.call_screen(screen_name, state=state)

        if result is None or result.get("action") == "cancel":
            return None
        elif result["action"] == "next":
            # Save step data (strip "action" key, keep the rest)
            step_data = {k: v for k, v in result.items() if k != "action"}
            # Reject invalid priority picks (e.g. the same rank on two groups)
            # rather than corrupting the downstream allocation pools.
            ok, msg = state.validate_priority_step(step_name, step_data)
            if not ok:
                show_toast(msg)
                continue
            state.save_step(step_name, step_data)
            state.complete_step(state.current_step)
            state.invalidate_dependents(step_name)
            if state.current_step < len(state.steps) - 1:
                state.current_step += 1
        elif result["action"] == "back":
            if state.current_step > 0:
                state.current_step -= 1
        elif result["action"] == "confirm":
            return build_character(state)
        elif result["action"] == "goto":
            target = result.get("step", 0)
            if 0 <= target < len(state.steps):
                state.current_step = target

    return None
