# WoD VN Framework — HUD & Character Sheet (Phase 2b-1) Design Specification

**Date:** 2026-03-29
**Status:** Approved
**Depends on:** Core Engine (Plan 1), Ren'Py Bootstrap (Phase 2a)
**Target Engine:** Ren'Py 8.3.7 (Python 3)

## Overview

Add two UI screens to the framework: a persistent resource HUD (top bar) and a tabbed character sheet overlay. Both are read-only views of existing character data, schema-driven so they work for any splat.

**What's in scope:**

- `game/wod_screens/resource_hud.rpy` — Top bar HUD with Quintessence/Paradox split bar, Willpower, Health, character sheet button
- `game/wod_screens/character_sheet.rpy` — Tabbed full-screen overlay (Attrs/Abilities, Spheres/Backgrounds, Merits/Resources)
- `wod_core.show_hud()` / `wod_core.hide_hud()` — API for authors
- Keyboard shortcut `C` to toggle character sheet
- Integration with demo script to show the HUD during play

**What's deferred:**

- Gothic theme (custom fonts, textures)
- Toast notifications
- Chargen (separate spec: Phase 2b-2)

## Section 1: Resource HUD

A persistent top bar shown during gameplay via `show screen resource_hud`.

### Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│  ████████████░░░░░░░░░░████  │  WP ████████░░  │  ■■■■■■■  │ [📋] │
│  Quint: 5          Pdx: 2    │  6/6             │  Health    │      │
└──────────────────────────────────────────────────────────────────────┘
```

**Components left to right:**

1. **Quintessence/Paradox split bar** — Single horizontal bar (combined cap 20). Gold fills from left (Quintessence), red fills from right (Paradox), gap in the middle shows remaining capacity. Numeric values displayed at each end.
2. **Willpower bar** — Simple filled bar with current/max text.
3. **Health track** — 7 boxes in WoD style (filled = damaged, empty = healthy). Boxes colored by damage severity.
4. **Character sheet button** — Icon button, opens the character sheet overlay.

### Data Source

The HUD reads from `wod_core.get_active()`:
- `pc.resources.current("quintessence")` / `pc.resources.current("paradox")` for the split bar
- `pc.resources.current("willpower")` / `pc.resources.pools["willpower"].max` for Willpower
- `pc.resources.current("health")` / `pc.resources.pools["health"].max` for Health

Ren'Py re-evaluates screen expressions every interaction, so the HUD updates automatically when resources change.

### Author API

```renpy
# Show HUD (typically in label start, after loading character)
$ wod_core.show_hud()

# Hide HUD (during cutscenes, menus, etc.)
$ wod_core.hide_hud()
```

Implementation: `show_hud()` sets a Ren'Py variable that controls `show screen resource_hud`. `hide_hud()` hides it.

```python
# In wod_core/__init__.py
def show_hud():
    import renpy  # only available inside Ren'Py
    renpy.store.wod_hud_visible = True
    renpy.show_screen("resource_hud")

def hide_hud():
    import renpy
    renpy.store.wod_hud_visible = False
    renpy.hide_screen("resource_hud")
```

### HUD Configurability

Authors can configure which resources appear. Default shows all four (quintessence, paradox, willpower, health). For splats without certain resources, the HUD adapts:

```renpy
# Show only specific resources
$ wod_core.show_hud(resources=["willpower", "health"])
```

If quintessence or paradox is shown without the other, it renders as a simple bar rather than a split bar.

## Section 2: Character Sheet

A tabbed full-screen overlay opened via the HUD button or `C` keyboard shortcut.

### Layout

Semi-transparent dark background over the scene. Centered panel (~80% screen width, ~90% height).

**Header:** Character name, Tradition, Essence. Close button (X) in top-right corner.

**Three tabs:**

**Tab 1: Attributes & Abilities**
- Attributes in Physical/Social/Mental groups, each trait shown with WoD dot display (●●●○○)
- Abilities below, grouped by Talents/Skills/Knowledges
- Only abilities with rating > 0 are displayed to avoid clutter
- Dot display reads the schema range to determine max dots (typically 5)

**Tab 2: Spheres & Backgrounds**
- Arete displayed prominently at top (large dot display)
- 9 Spheres with dot display
- Backgrounds below with dot display
- Only non-zero Backgrounds shown

**Tab 3: Merits, Flaws & Resources**
- Merit/Flaw list with name and point value
- Resources displayed as bars with numeric current/max values
- Quintessence/Paradox shown as the split bar (same as HUD but larger)

### WoD Dot Display

Traits rendered as filled/empty circles:
- Rating 3 out of 5: `●●●○○`
- Uses the schema's range to determine total dots
- Gold accent color for filled dots, dark gray for empty

### Schema-Driven

The character sheet reads `schema.categories` to determine:
- Which trait categories exist and their display names
- Which traits belong to each category
- Groups within categories (Physical/Social/Mental for Attributes)
- Valid ranges for dot display

This means the sheet works for any splat — a Vampire character sheet would show Disciplines instead of Spheres, automatically.

### Access

- **HUD button:** Click the character sheet button on the HUD bar
- **Keyboard:** Press `C` to toggle the sheet open/closed
- **Close:** Click X button, press Escape, or press `C` again
- The sheet pauses gameplay (modal overlay)

### Implementation

```renpy
# game/wod_screens/character_sheet.rpy
screen character_sheet():
    modal True
    # ... tabbed layout reading from wod_core.get_active()

# Keyboard binding
key "c" action [
    If(renpy.get_screen("character_sheet"),
       true=Hide("character_sheet"),
       false=Show("character_sheet"))
]
```

Tab state is a screen-local variable (`default tab = "attributes"`).

## Section 3: Demo Integration

Update `game/script.rpy` to show the HUD after character loading:

```renpy
label start:
    $ pc = wod_core.load_character("demo/elena.yaml")
    $ wod_core.set_active(pc)
    $ wod_core.show_hud()
    # ... rest of demo
```

The HUD should be visible throughout the demo, updating as Quintessence is spent and Paradox is gained.

## Section 4: Testing Strategy

1. **Ren'Py lint** — verify no screen errors
2. **Manual verification:**
   - HUD displays correct values for Elena's starting stats
   - Split bar visually reflects Quintessence/Paradox ratio
   - After spending Quintessence in the demo, HUD updates
   - After gaining Paradox, split bar shifts
   - Character sheet opens/closes via button and C key
   - All three tabs show correct data
   - Dot display matches trait values
   - Only non-zero abilities shown
3. **pytest** — existing suite continues to pass

## Section 5: File Map

```
game/
├── wod_screens/
│   ├── resource_hud.rpy        # HUD top bar screen
│   └── character_sheet.rpy     # Tabbed character sheet overlay
├── wod_core/
│   └── __init__.py             # Add show_hud()/hide_hud()
└── script.rpy                  # Update: add show_hud() call
```
