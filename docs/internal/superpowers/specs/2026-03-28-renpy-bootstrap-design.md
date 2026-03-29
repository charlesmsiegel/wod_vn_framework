# WoD VN Framework — Ren'Py Bootstrap (Phase 2a) Design Specification

**Date:** 2026-03-28
**Status:** Approved
**Depends on:** Core Engine (Plan 1 — merged)
**Target Engine:** Ren'Py 8.3.7 (Python 3)

## Overview

Get the WoD VN framework running inside Ren'Py with a playable demo that proves the core engine works end-to-end. This is the minimal integration layer — no custom UI screens, no themes, no chargen.

**What's in scope:**

- `wod_init.rpy` — Framework init at Ren'Py startup (splat auto-loading). Named `wod_init` rather than `wod_statements` since CDS registration is deferred.
- `game/options.rpy` — Game config (title, resolution)
- `game/gui.rpy` — Ren'Py GUI variables with dark neutral styling
- `game/screens.rpy` — Ren'Py required screens (defaults with color tweaks)
- `game/gui/` — Default GUI image assets from Ren'Py template
- `game/script.rpy` — Playable demo scene exercising stat gating, resources, branching
- `game/demo/elena.yaml` — Pre-built demo character
- Native syntax only (`if pc.gate(...)`) — bracket shorthand pre-processor deferred

**What's deferred to Phase 2b:**

- Character sheet screen
- Resource HUD overlay
- Chargen screens + `chargen.py`
- Gothic theme
- Toast notifications
- `show_hud()` / `hide_hud()`
- Bracket shorthand as Ren'Py source pre-processor
- CDS registration (`wod_init.rpy` will be extended for this)

**Note on module naming:** The Python module is `wod_core` (matching the package directory). The Phase 1 spec occasionally uses `wod` as shorthand — the canonical module name is `wod_core`.

## Section 1: Framework Init

`wod_init.rpy` bootstraps the framework at Ren'Py init time:

```renpy
init -10 python:
    import wod_core

    # renpy.config.gamedir is the absolute path to game/
    wod_core.init(renpy.config.gamedir)
    splats = wod_core.get_loader().discover_splats()
    if not splats:
        raise Exception("WoD Framework: No splats found in game/splats/. Check your installation.")
    wod_core.load_all_splats()
```

**Why `init -10`:** Ren'Py's own GUI init runs at -2 to -1. Author code defaults to 0. Using -10 ensures the framework is available for everything, including GUI customization. Authors should not use init levels below -10 for their own code.

**Why `renpy.config.gamedir`:** Ren'Py `.rpy` files don't have `__file__` — they're compiled to `.rpyc` and executed in a special namespace. `renpy.config.gamedir` provides the absolute path to the `game/` directory.

Authors load characters in their script:

```renpy
default pc = None

label start:
    $ pc = wod_core.load_character("demo/elena.yaml")
    $ wod_core.set_active(pc)
```

The `default pc = None` declaration ensures the variable participates correctly in Ren'Py's save/load and rollback systems.

## Section 2: Serialization Note

`Character` objects stored in Ren'Py `$` variables are serialized into save files via Python's `pickle`. The current implementation is picklable (no lambdas or file handles in instance state; `_OPERATORS` is a class attribute, not instance state).

The `Schema` object on each `Character` will be redundantly serialized into every save. This is acceptable for Phase 2a (schemas are small). Phase 2b should add `__getstate__`/`__setstate__` to exclude the schema from serialization and reattach it on load, reducing save bloat and avoiding schema drift.

## Section 3: Required Ren'Py Files

Ren'Py requires `gui.rpy`, `screens.rpy`, and `options.rpy` to function.

### Generation Approach

Copy `gui.rpy`, `screens.rpy`, and the `gui/` images directory from the Ren'Py SDK template directory:

```
<renpy-sdk>/gui/game/gui.rpy        → game/gui.rpy
<renpy-sdk>/gui/game/screens.rpy    → game/screens.rpy
<renpy-sdk>/gui/game/gui/           → game/gui/
```

If the SDK template directory layout differs, create a throwaway project via the Ren'Py Launcher GUI and copy from there.

### options.rpy

Game metadata and config:

```renpy
define config.name = "WoD VN Framework Demo"
define config.version = "0.1.0"
define config.screen_width = 1920
define config.screen_height = 1080
define gui.show_name = True
define config.has_sound = False
define config.has_music = False
define config.has_voice = False
define config.main_menu_music = None
```

### gui.rpy

Ren'Py's default `gui.rpy` with color tweaks for a dark, moody baseline:

- Background: dark grays (#1a1a2e, #16213e)
- Text: light (#e0e0e0)
- Accent: muted gold (#c9a96e)
- Choice buttons: dark with lighter hover

No custom fonts — just color overrides on the generated defaults.

### screens.rpy

Ren'Py's default `screens.rpy` taken as-is. Color scheme is applied through `gui.rpy` variables.

### gui/ images

The `gui/` directory contains default Ren'Py UI images (button backgrounds, slider bars, overlay images, etc.). These are copied from the template and used as-is for 2a. Custom images are a 2b concern.

## Section 4: Demo Scene

A short playable scene where the player character (Elena, a Virtual Adept) investigates a Technocratic ward on a server room. Choices are gated by Spheres, Abilities, and Quintessence.

### Demo character: `game/demo/elena.yaml`

```yaml
schema: mage
template: default_mage
character_type: pc

identity:
  name: "Elena Vasquez"
  tradition: "Virtual Adepts"
  essence: "Dynamic"
  nature: "Visionary"
  demeanor: "Architect"

traits:
  attributes:
    Strength: 2
    Dexterity: 3
    Stamina: 2
    Charisma: 3
    Manipulation: 2
    Appearance: 2
    Perception: 4
    Intelligence: 3
    Wits: 3
  abilities:
    Awareness: 2
    Occult: 3
    Research: 2
    Science: 4
    Technology: 3
  spheres:
    Forces: 3
    Prime: 2
    Correspondence: 1
  arete:
    Arete: 3
  backgrounds:
    Avatar: 3
    Node: 2
    Resources: 2

resources:
  quintessence: 5
  paradox: 0
  willpower: 6

merits_flaws:
  - { name: "Avatar Companion", type: merit, value: 3 }
```

### Demo script: `game/script.rpy`

The script demonstrates:

1. **Character loading** — Load Elena from YAML, set as active
2. **Trait gating** — Menu choices filtered by Sphere/Ability ratings
3. **Resource spending** — Spending Quintessence to power Effects
4. **Linked pool constraint** — Gaining Paradox reduces Quintessence capacity
5. **Outcome branching** — Higher stats produce different dialogue
6. **Mid-story stat changes** — Advancing a trait during play

Scene flow:

```
start -> Elena at terminal, Technocratic ward detected
  |-- [Forces >= 3, Prime >= 2] Analyze the ward -> spend Quintessence, unravel it
  |     |-- [Forces >= 3] Successful unraveling (reachable)
  |     |-- But imperfect — gain Paradox, linked pool reduces Quintessence
  |-- [Technology >= 3] Brute-force the encryption -> mundane approach, partial success
  |-- [Awareness >= 2] Observe the pattern -> gain insight, advance Awareness
  |     |-- Demonstrates mid-story stat change (pc.advance)
  |-- Leave -> safe ending
-> epilogue (summarizes what happened based on path taken)
-> return (back to main menu)
```

All branches with Elena's stats (Forces 3, Prime 2, Technology 3, Awareness 2) are **reachable** — the demo shows the player making real choices, not being locked out. Each path ends with `return` to cleanly return to the main menu.

## Section 5: Testing Strategy

Since Ren'Py files can't be pytest-tested:

1. **Ren'Py lint** — `renpy.sh game lint` catches syntax errors, undefined labels, missing images
2. **Manual playthrough** — Each path in the demo is played to verify gating works
3. **Core engine tests remain** — `pytest` validates the Python engine (existing test suite)

Lint runs as the primary automated check after each change.

## Section 6: File Map

```
game/
├── wod_init.rpy            # Framework init (init -10)
├── options.rpy             # Game config (title, resolution)
├── gui.rpy                 # GUI variables (dark neutral colors)
├── screens.rpy             # Default Ren'Py screens
├── gui/                    # Default GUI image assets
├── script.rpy              # Demo scene
└── demo/
    └── elena.yaml          # Demo character
```
