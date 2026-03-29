# WoD VN Framework — HUD & Character Sheet (Phase 2b-1) Design Specification

**Date:** 2026-03-29
**Status:** Approved
**Depends on:** Core Engine (Plan 1), Ren'Py Bootstrap (Phase 2a)
**Target Engine:** Ren'Py 8.3.7 (Python 3)

## Overview

Add two UI screens to the framework: a persistent resource HUD (top bar) and a tabbed character sheet overlay. Both are read-only views of existing character data, schema-driven so they work for any splat.

**What's in scope:**

- `game/wod_screens/resource_hud.rpy` — Top bar HUD with Quintessence/Paradox split bar, Willpower, Health, character sheet button
- `game/wod_screens/character_sheet.rpy` — Tabbed full-screen overlay, schema-driven
- `wod_core.show_hud()` / `wod_core.hide_hud()` — API for authors
- Keyboard shortcut `Tab` to toggle character sheet
- Engine change: `CategoryDef` retains group structure for grouped rendering
- Integration with demo script to show the HUD during play

**What's deferred:**

- Gothic theme (custom fonts, textures)
- Toast notifications
- Chargen (separate spec: Phase 2b-2)

## Section 1: Engine Change — CategoryDef Groups

`CategoryDef` in `engine.py` currently flattens group structure into a single `trait_names` list. The character sheet needs group info to render Attributes as Physical/Social/Mental and Abilities as Talents/Skills/Knowledges.

**Change:** Add `self.groups: dict[str, list[str]] | None` to `CategoryDef.__init__`:

```python
if "groups" in data:
    self.groups = {}
    for group_name, traits in data["groups"].items():
        self.groups[group_name] = list(traits)
        self.trait_names.extend(traits)
else:
    self.groups = None
```

Categories with `groups` have `self.groups` set (e.g., `{"physical": ["Strength", ...], "social": [...], "mental": [...]}`). Categories with flat `traits` have `self.groups = None`. This change is backwards-compatible — `trait_names` still contains the flat list.

Add a pytest test for this.

## Section 2: Resource HUD

A persistent top bar shown during gameplay via `show screen resource_hud`.

### Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│  ████████████░░░░░░░░░░████  │  WP ████████░░  │  □□□□□□□  │ [📋] │
│  Quint: 5          Pdx: 2    │  6/6             │  Health    │      │
└──────────────────────────────────────────────────────────────────────┘
```

**Components left to right:**

1. **Quintessence/Paradox split bar** — Single horizontal bar. Combined cap read from `ResourceManager.links` (data-driven, not hard-coded). Gold fills from left (Quintessence), red fills from right (Paradox), gap in the middle shows remaining capacity. Numeric values displayed at each end. If only one of the two is configured, renders as a simple bar.
2. **Willpower bar** — Simple filled bar with current/max text.
3. **Health track** — 7 boxes in WoD style. See rendering rules below.
4. **Character sheet button** — Text button "[Sheet]", opens the character sheet overlay.

### Health Track Rendering

Health boxes represent damage levels. The `ResourcePool` stores `current_value` as remaining health (starts at max, decreases as damage is taken).

- **Number of damaged boxes** = `max - current_value` (filled from top: Bruised first)
- **Undamaged boxes** = empty, dark gray outline
- **Damaged boxes** = filled, uniform red color (severity-based coloring deferred to Gothic theme)
- The boxes are labeled by level name only on hover or in the character sheet detail view

### Data Source

The HUD reads from `wod_core.get_active()`:
- `pc.resources.current("quintessence")` / `pc.resources.current("paradox")` for the split bar
- Combined cap from the `ResourceLink` in `pc.resources.links`
- `pc.resources.current("willpower")` / `pc.resources.pools["willpower"].max` for Willpower
- `pc.resources.current("health")` / `pc.resources.pools["health"].max` for Health

Ren'Py re-evaluates screen expressions every interaction, so the HUD updates automatically when resources change.

### Author API

```renpy
# Show HUD with all resources (default)
$ wod_core.show_hud()

# Show only specific resources
$ wod_core.show_hud(resources=["willpower", "health"])

# Hide HUD (during cutscenes, menus, etc.)
$ wod_core.hide_hud()
```

Implementation:

```python
# In wod_core/__init__.py
def show_hud(resources=None):
    import renpy
    renpy.store.wod_hud_visible = True
    renpy.store.wod_hud_resources = resources  # None = show all
    renpy.show_screen("resource_hud")

def hide_hud():
    import renpy
    renpy.store.wod_hud_visible = False
    renpy.store.wod_hud_resources = None
    renpy.hide_screen("resource_hud")
```

The `resource_hud` screen reads `store.wod_hud_resources` to decide which components to render. When `None`, all resources for the active character's splat are shown.

### Save/Load Handling

`renpy.store.wod_hud_visible` persists across save/load. But `show screen` calls are not replayed on load. Add an `after_load` label:

```renpy
# In wod_init.rpy
label after_load:
    if store.wod_hud_visible:
        show screen resource_hud
    return
```

## Section 3: Character Sheet

A tabbed full-screen overlay opened via the HUD button or `Tab` keyboard shortcut.

### Layout

Semi-transparent dark background over the scene. Centered panel (~80% screen width, ~90% height).

**Header:** Displays all identity fields from `pc.identity` as key-value pairs (e.g., "Elena Vasquez — Virtual Adepts — Dynamic"). Schema-driven — different splats show different identity fields automatically. Close button (X) in top-right corner.

**Tab mapping** — which categories go on which tab is configured in the splat manifest:

```yaml
# In splats/mage/manifest.yaml (addition)
splat:
  # ... existing fields ...
  character_sheet:
    tabs:
      - name: "Attributes & Abilities"
        categories: [attributes, abilities]
      - name: "Spheres & Backgrounds"
        categories: [arete, spheres, backgrounds]
      - name: "Merits & Resources"
        categories: []  # special tab: merits_flaws + resources
```

The third tab is always "Merits & Resources" — it shows the merit/flaw list and resource bars. Categories listed in `tabs` are rendered with WoD dot display. If a splat doesn't define `character_sheet.tabs`, the sheet auto-generates tabs from the schema categories (one tab per category).

### Tab Rendering

For each category in a tab:
- **Display name** from schema (e.g., "Attributes")
- If the category has `groups`, render each group with its label (e.g., "Physical: Strength ●●○○○, Dexterity ●●●○○, ...")
- If the category has flat `traits`, render as a single list
- Only traits with rating > 0 are shown for categories with `default: 0` (Abilities, Backgrounds)
- All traits are shown for categories with `default: 1` (Attributes — player always has at least 1 dot)

### WoD Dot Display

Traits rendered as filled/empty circles:
- Rating 3 out of 5: `●●●○○`
- Uses the schema's range to determine total dots
- Gold accent color (`#c9a96e`) for filled dots, dark gray for empty

### Merits & Resources Tab

- Merit/Flaw list with name and point value
- Resources displayed as bars with numeric current/max values
- Quintessence/Paradox shown as the split bar (same style as HUD but larger)

### Access

- **HUD button:** Click "[Sheet]" on the HUD bar
- **Keyboard:** Press `Tab` to toggle the sheet open/closed (placed inside the `resource_hud` screen so it's active whenever the HUD is visible)
- **Close:** Click X button, press Escape, or press `Tab` again
- The sheet pauses gameplay (modal overlay)

### Implementation

```renpy
# In resource_hud screen:
key "K_TAB" action ToggleScreen("character_sheet")

# Character sheet screen:
screen character_sheet():
    modal True
    # ... tabbed layout reading from wod_core.get_active()
```

Tab state is a screen-local variable (`default tab = 0`).

## Section 4: Willpower Current/Max Fix

Elena's character file sets `willpower: 6` as a resource override, which only sets `current_value` — leaving `max` at 5 (from `default_max` in the resources config). This means current > max, which would display incorrectly.

**Fix in `loader.py`:** When applying character resource overrides, also update `max` if the override value exceeds the current max:

```python
for res_name, res_value in char_data.get("resources", {}).items():
    if char.resources.has_resource(res_name) and isinstance(res_value, int):
        pool = char.resources.pools[res_name]
        pool.current_value = res_value
        if res_value > pool.max:
            pool.max = res_value
```

## Section 5: Demo Integration

Update `game/script.rpy` to show the HUD after character loading:

```renpy
label start:
    $ pc = wod_core.load_character("demo/elena.yaml")
    $ wod_core.set_active(pc)
    $ wod_core.show_hud()
    # ... rest of demo
```

The HUD should be visible throughout the demo, updating as Quintessence is spent and Paradox is gained.

## Section 6: Testing Strategy

1. **pytest** for engine change:
   - `CategoryDef` with groups stores `self.groups` dict
   - `CategoryDef` with flat traits has `self.groups = None`
   - `trait_names` still contains the flat list (backwards-compat)
   - Willpower max fix in loader
2. **Ren'Py lint** — verify no screen errors
3. **Manual verification:**
   - HUD displays correct values for Elena's starting stats
   - Split bar visually reflects Quintessence/Paradox ratio
   - After spending Quintessence in the demo, HUD updates
   - After gaining Paradox, split bar shifts
   - Character sheet opens/closes via button and Tab key
   - All tabs show correct data with grouped rendering
   - Dot display matches trait values
   - Only non-zero abilities/backgrounds shown
   - Save/load preserves HUD visibility

## Section 7: File Map

```
game/
├── wod_screens/
│   ├── resource_hud.rpy        # HUD top bar screen
│   └── character_sheet.rpy     # Tabbed character sheet overlay
├── wod_core/
│   ├── engine.py               # CategoryDef: add self.groups
│   ├── loader.py               # Fix Willpower max on resource override
│   └── __init__.py             # Add show_hud()/hide_hud()
├── wod_init.rpy                # Add after_load label
├── script.rpy                  # Update: add show_hud() call
├── splats/mage/
│   └── manifest.yaml           # Add character_sheet.tabs config
tests/
└── test_engine.py              # Add CategoryDef groups test
```
