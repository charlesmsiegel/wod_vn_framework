# WoD VN Framework — Ren'Py Bootstrap (Phase 2a) Design Specification

**Date:** 2026-03-28
**Status:** Approved
**Depends on:** Core Engine (Plan 1 — merged)
**Target Engine:** Ren'Py 8.3.7 (Python 3)

## Overview

Get the WoD VN framework running inside Ren'Py with a playable demo that proves the core engine works end-to-end. This is the minimal integration layer — no custom UI screens, no themes, no chargen.

**What's in scope:**

- `wod_statements.rpy` — Framework init at Ren'Py startup (splat auto-loading)
- `game/options.rpy` — Game config (title, resolution)
- `game/gui.rpy` — Ren'Py GUI variables with dark neutral styling
- `game/screens.rpy` — Ren'Py required screens (defaults with color tweaks)
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

## Section 1: Framework Init

`wod_statements.rpy` bootstraps the framework at Ren'Py init time:

```renpy
init -10 python:
    import wod_core
    import os

    wod_core.init(os.path.dirname(__file__))
    wod_core.load_all_splats()
```

`init -10` ensures the framework loads before author code at the default `init` level. By the time `label start` runs, all splat schemas and resources are registered.

Authors load characters in their script:

```renpy
label start:
    $ pc = wod_core.load_character("demo/elena.yaml")
    $ wod_core.set_active(pc)
```

## Section 2: Required Ren'Py Files

Ren'Py requires `gui.rpy`, `screens.rpy`, and `options.rpy` to function. These are generated from Ren'Py's default project template, then customized minimally.

### options.rpy

Game metadata and config:

```renpy
define config.name = "WoD VN Framework Demo"
define config.version = "0.1.0"
define gui.show_name = True
define config.has_sound = False
define config.has_music = False
define config.has_voice = False
define config.main_menu_music = None
```

### gui.rpy

Ren'Py's default `gui.rpy` (~400 lines of GUI variable definitions). We take the generated default and tweak colors for a dark, moody baseline:

- Background: dark grays (#1a1a2e, #16213e)
- Text: light (#e0e0e0)
- Accent: muted gold (#c9a96e)
- Choice buttons: dark with lighter hover

No custom images or fonts — just color overrides. This is the "neutral" theme baseline.

### screens.rpy

Ren'Py's default `screens.rpy` (~1100 lines). Provides all required screens: `say`, `choice`, `main_menu`, `game_menu`, `navigation`, `preferences`, `save`, `load`, `about`, `help`, `confirm`, `notify`, etc.

We take the generated default as-is with the color scheme applied through `gui.rpy` variables. No custom screen logic in 2a.

### Generation approach

Use Ren'Py's CLI to generate a new project into a temp directory, then copy `gui.rpy` and `screens.rpy` into our game directory:

```bash
# Generate default project
/path/to/renpy.sh /tmp/wod_gen generate /tmp/wod_gen --template default

# Copy the GUI files
cp /tmp/wod_gen/game/gui.rpy game/gui.rpy
cp /tmp/wod_gen/game/screens.rpy game/screens.rpy
```

Then apply color tweaks to `gui.rpy`.

## Section 3: Demo Scene

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
5. **Outcome branching** — Higher stats produce better results
6. **Mid-story stat changes** — Advancing a trait during play

Scene flow:

```
start → Elena at terminal, Technocratic ward detected
  ├── [Forces >= 3, Prime >= 2] Analyze the ward → spend Quintessence, unravel it
  │     ├── [Forces >= 5] Perfect unraveling
  │     └── [Forces < 5] Rough but effective, gain Paradox
  ├── [Technology >= 3] Brute-force the encryption → mundane approach, partial success
  ├── [Awareness >= 2] Observe the pattern → gain insight, advance a skill
  └── Leave → safe ending
→ epilogue (summarizes what happened based on path taken)
```

Each path ends with a brief epilogue. The demo is self-contained — 3-5 minutes of play showing the framework's capabilities.

## Section 4: Testing Strategy

Since Ren'Py files can't be pytest-tested:

1. **Ren'Py lint** — `renpy.sh game lint` catches syntax errors, undefined labels, missing images
2. **Manual playthrough** — Each path in the demo is played through to verify gating works
3. **Core engine tests remain** — `pytest` still validates the Python engine (91 tests)

Lint runs as the primary automated check after each change.

## Section 5: File Map

```
game/
├── wod_statements.rpy      # Framework init (init -10)
├── options.rpy              # Game config
├── gui.rpy                  # GUI variables (dark neutral colors)
├── screens.rpy              # Default Ren'Py screens
├── script.rpy               # Demo scene
└── demo/
    └── elena.yaml           # Demo character
```
