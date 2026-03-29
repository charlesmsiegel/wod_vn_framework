# WoD VN Framework

A Ren'Py framework for building World of Darkness visual novels.

## What is this?

WoD VN Framework is a **framework**, not a game. It provides the engine, screens, and data architecture that authors need to write interactive visual novels set in the World of Darkness. The current release targets **Mage: The Ascension (M20)**, with an extensible splat-pack system designed to support Vampire, Werewolf, and other WoD game lines.

You write your story in Ren'Py. The framework handles character stats, resource pools, gated choices, character creation, HUD display, and everything else that makes a WoD game feel like a WoD game.

## Features

- **Deterministic stat gating** -- no dice rolls. Stats unlock menu choices and affect story outcomes.
- **Data-driven splat packs** -- Mage: The Ascension ships built-in; extensible to Vampire, Werewolf, and custom splats.
- **Resource pools with linked constraints** -- Quintessence and Paradox share a 20-point Wheel; gaining one reduces the other.
- **Character creation** -- three modes: Full M20 (priority-based allocation), Simplified (flat dot pools), and Template (pick a pre-built archetype).
- **Persistent HUD** -- Quintessence/Paradox split bar, Willpower pips, Health track. Survives save/load.
- **Tabbed character sheet** -- toggle with Tab. WoD-style dot display, organized by trait category.
- **Gothic dark theme** -- serif typography (EB Garamond body, Cinzel headings), dark parchment palette.
- **Toast notifications** -- brief on-screen messages for gate results, stat changes, or custom alerts.
- **Bracket shorthand pre-processor** -- write `[Forces >= 3]` in your script; a CLI tool compiles it to native Ren'Py `if` expressions.
- **Save/load serialization optimization** -- Character objects pickle efficiently by excluding the Schema and reconstructing it on load.
- **Author-level splat overrides and template extension** -- add traits, tweak resources, or create archetype variants without modifying the base splat files.

## Quick Start

1. Install [Ren'Py 8.x](https://www.renpy.org/latest.html).
2. Clone this repository:
   ```bash
   git clone <repo-url> wod_vn_framework
   ```
3. Run the demo:
   ```bash
   renpy.sh wod_vn_framework/
   ```

The demo loads a pre-built Mage character (Elena Vasquez) and walks through stat-gated choices, resource spending, and outcome branching.

## Project Structure

```
wod_vn_framework/
  game/
    script.rpy              # Your game script (demo included)
    wod_init.rpy            # Framework bootstrap — loads engine and splats
    wod_core/               # Python engine
      __init__.py           #   Public API (load_character, chargen, show_hud, etc.)
      engine.py             #   Character class — get, set, advance, gate, spend, gain
      resources.py          #   Resource pools and linked constraints
      chargen.py            #   Character creation state machine
      gating.py             #   Module-level gate() and has() delegates
      loader.py             #   YAML splat/character loading
      syntax.py             #   Bracket shorthand compiler
      __main__.py           #   CLI entry point (python -m wod_core)
    wod_screens/            # Ren'Py screen definitions
      resource_hud.rpy      #   HUD overlay
      character_sheet.rpy   #   Tabbed character sheet
      chargen.rpy           #   Character creation screens
      toast.rpy             #   Toast notification screen
    splats/                 # Data-driven game-line packs
      mage/
        manifest.yaml       #   Splat metadata and file references
        schema.yaml         #   Trait categories, ranges, defaults, constraints
        resources.yaml      #   Resource pools and linked pool config
        chargen.yaml        #   Chargen modes, traditions, archetypes, merits/flaws
        templates/          #   Pre-built character templates
    demo/
      elena.yaml            # Demo character file
    themes/
      gothic/               # Default dark theme assets
      neutral/              # Fallback neutral theme
  tests/                    # pytest test suite
  docs/
    author-guide.md         # Complete reference for writing games with the framework
```

## For Authors

See the **[Author Guide](docs/author-guide.md)** for a complete reference covering character files, stat gating, resource management, character creation, HUD configuration, bracket shorthand, data files, and customization.

## For Developers

Run the test suite:

```bash
pytest
```

The test suite covers the core engine (`test_engine.py`), stat gating (`test_gating.py`), resource pools (`test_resources.py`), character creation (`test_chargen.py`), bracket syntax compilation (`test_syntax.py`), YAML loading (`test_loader.py`), and end-to-end integration (`test_integration.py`).

### Engine Architecture

- **`engine.py`** -- `Character` class with trait storage, range/constraint validation, gating operators, and resource delegation. Implements `__getstate__`/`__setstate__` for optimized pickling.
- **`resources.py`** -- `ResourcePool` (individual pools with spend/gain/range) and `ResourceManager` (manages all pools, enforces linked constraints like the Quintessence Wheel).
- **`loader.py`** -- `SplatLoader` discovers splat directories, loads YAML schemas/resources/chargen configs, and applies author-level overrides. Also loads character files from YAML.
- **`chargen.py`** -- `ChargenState` tracks multi-step character creation with point pools, step invalidation, and final character building.
- **`syntax.py`** -- Regex-based compiler that transforms bracket shorthand (`[Forces >= 3]`) into `wod_core.gate()` calls with identifier validation against the schema.

## License

TBD
