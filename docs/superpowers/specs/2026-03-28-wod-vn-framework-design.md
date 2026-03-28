# WoD Visual Novel Framework — Design Specification

**Date:** 2026-03-28
**Status:** Approved
**Target Engine:** Ren'Py 8.x (Python 3)
**Primary Splat:** Mage: The Ascension (M20)

## Overview

A Ren'Py framework for building World of Darkness visual novels. Distributed as a project template — authors install Ren'Py separately, clone this repo, and write their stories. The framework handles character management, stat-gated branching, resource tracking, and themed UI.

**Key design decisions:**

- **Deterministic, not dice-based.** Stats gate options and affect outcomes. No randomness.
- **Framework for authors, not a specific game.** Target audience is storytellers who know Ren'Py scripting but not Python.
- **Plugin architecture.** Splat-specific content (Mage, Vampire, etc.) lives in pluggable data packs. Core engine is splat-agnostic.
- **Dual syntax.** Authors can use a compact shorthand (`[Forces >= 3]`) or native Ren'Py (`if pc.check("Forces", 3)`).
- **Two bundled themes.** Gothic (WoD aesthetic) and Neutral (easy to reskin).
- **Single PC default, multi-PC opt-in.**
- **Pre-defined characters or player chargen — author's choice.**

## Project Structure

```
game/
├── wod_core/               # Core Python engine
│   ├── engine.py           # Trait system, resource pools, validation
│   ├── gating.py           # Stat-gating + choice filtering
│   ├── syntax.py           # Custom statement compiler ([Forces >= 3] -> Python)
│   ├── chargen.py          # Character creation framework
│   └── loader.py           # Data file loader (YAML)
├── wod_screens/            # Ren'Py screens
│   ├── character_sheet.rpy
│   ├── resource_bars.rpy
│   └── chargen.rpy
├── wod_statements.rpy      # Ren'Py custom statement registration
├── themes/
│   ├── gothic/
│   │   ├── theme.yaml
│   │   ├── gui.rpy
│   │   ├── screens.rpy
│   │   ├── fonts/
│   │   └── images/
│   └── neutral/
│       ├── theme.yaml
│       ├── gui.rpy
│       ├── screens.rpy
│       ├── fonts/
│       └── images/
└── splats/
    └── mage/
        ├── manifest.yaml
        ├── schema.yaml
        ├── resources.yaml
        └── templates/
            ├── default_mage.yaml
            └── archmage.yaml
```

## Section 1: Core Trait & Validation System

A generic system for defining, storing, and validating character traits. The engine knows nothing about specific traits — all definitions come from splat data files.

### Schema Definition (YAML)

```yaml
# splats/mage/schema.yaml
trait_categories:
  attributes:
    display_name: "Attributes"
    groups:
      physical: [Strength, Dexterity, Stamina]
      social: [Charisma, Manipulation, Appearance]
      mental: [Perception, Intelligence, Wits]
    default: 1
    range: [1, 5]

  abilities:
    display_name: "Abilities"
    groups:
      talents: [Alertness, Art, Athletics, Awareness, Brawl, Empathy, Expression, Intimidation, Leadership, Streetwise, Subterfuge]
      skills: [Crafts, Drive, Etiquette, Firearms, Martial Arts, Meditation, Melee, Research, Stealth, Survival, Technology]
      knowledges: [Academics, Computer, Cosmology, Enigmas, Esoterica, Investigation, Law, Medicine, Occult, Politics, Science]
    default: 0
    range: [0, 5]

  spheres:
    display_name: "Spheres"
    traits: [Correspondence, Entropy, Forces, Life, Matter, Mind, Prime, Spirit, Time]
    default: 0
    range: [0, 5]
```

### Runtime Behavior

- `engine.py` loads the schema at init time.
- Character objects hold current trait values as a flat dict (`{"Strength": 3, "Forces": 2, ...}`).
- Setting a trait validates against the schema's range — out-of-range raises an error during development, logs a warning in release.
- Traits not in the schema are rejected unless the author explicitly opts into freeform traits.

### Override/Extension

Templates can extend and override the base schema:

```yaml
# splats/mage/templates/archmage.yaml
extends: default_mage
overrides:
  trait_categories:
    spheres:
      range: [0, 10]
```

## Section 2: Resource Pool System

Generic trackable resources configured per splat. Handles anything with a current value, max, and rules about spending/gaining.

### Resource Definition (YAML)

```yaml
# splats/mage/resources.yaml
resources:
  quintessence:
    display_name: "Quintessence"
    range: [0, 20]
    default: 0

  paradox:
    display_name: "Paradox"
    range: [0, 20]
    default: 0

  willpower:
    display_name: "Willpower"
    range: [0, 10]
    default_max: "trait:Wits"
    default_current: "max"

  health:
    display_name: "Health"
    range: [0, 7]
    default_current: "max"
    track_type: "levels"
    levels:
      - { name: "Bruised", penalty: 0 }
      - { name: "Hurt", penalty: -1 }
      - { name: "Injured", penalty: -1 }
      - { name: "Wounded", penalty: -2 }
      - { name: "Mauled", penalty: -2 }
      - { name: "Crippled", penalty: -5 }
      - { name: "Incapacitated", penalty: null }

resource_links:
  quintessence_wheel:
    pools: [quintessence, paradox]
    combined_max: 20
```

### Runtime Behavior

- Resources are separate from traits — traits are static ratings, resources are pools that get spent and replenished.
- `resources.py` provides `spend(name, amount)`, `gain(name, amount)`, `current(name)`, `at_max(name)`, `at_min(name)`.
- Linked resources enforce combined constraints automatically (e.g., `quintessence + paradox <= 20`). When one pool increases, the other is capped down if necessary.
- Linked resources (like Willpower max derived from a trait) update automatically when the source trait changes.
- Spending more than available: the gated option doesn't appear; a manual `spend()` call returns False.

### Script Usage

```renpy
$ pc.spend("quintessence", 3)
$ pc.gain("paradox", 1)

# Gate on resource level
"Channel the node's energy" [quintessence >= 5]:
    $ pc.spend("quintessence", 5)
```

## Section 3: Stat Gating & Choice System

The core authoring mechanic. Two syntaxes, one system — the shorthand compiles to native Ren'Py calls.

### Shorthand Syntax

```renpy
menu:
    "Rewrite the ward's resonance" [Prime >= 3, Forces >= 2]:
        jump rewrite_ward
    "Perceive the ward's structure" [Prime >= 1]:
        jump perceive_ward
    "Try to push through" [Stamina >= 3]:
        jump brute_force
    "Back away":
        jump retreat
```

### Native Syntax

```renpy
menu:
    "Rewrite the ward's resonance" if pc.check("Prime", 3) and pc.check("Forces", 2):
        jump rewrite_ward
    "Perceive the ward's structure" if pc.check("Prime", 1):
        jump perceive_ward
    "Try to push through" if pc.check("Stamina", 3):
        jump brute_force
    "Back away":
        jump retreat
```

### Supported Conditions

| Syntax | Meaning |
|--------|---------|
| `[Forces >= 3]` | Trait check |
| `[quintessence >= 5]` | Resource check |
| `[Forces >= 3, Prime >= 2]` | Combined (AND) |
| `>=`, `<=`, `==`, `!=`, `>`, `<` | All comparisons |
| `[Avatar Companion]` | Boolean merit check |
| `[!Blind]` | Negated flaw check |

### Outcome Modification

The same stats that gate a choice can further branch the outcome:

```renpy
label rewrite_ward:
    if pc.check("Forces", 5):
        "Your mastery of Forces lets you not just rewrite the ward, but improve it."
        $ pc.gain("quintessence", 2)
    elif pc.check("Forces", 4):
        "You carefully rewrite the ward's structure."
    else:
        "You manage to alter the ward, but it's rough work."
        $ pc.gain("paradox", 1)
```

### Hidden vs. Visible Gating

By default, choices the PC doesn't qualify for are **hidden**. Authors can optionally show them greyed-out:

```renpy
"Rewrite the ward's resonance" [Prime >= 3, Forces >= 2, show_locked="You lack the knowledge..."]:
```

## Section 4: Character Definition & Creation

### Pre-defined Characters (Data Files)

```yaml
# splats/mage/templates/default_mage.yaml
schema: mage
character_type: pc

identity:
  name: ""
  tradition: ""
  essence: ""
  nature: ""
  demeanor: ""

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

resources:
  quintessence: 5
  paradox: 0
  willpower: 6

merits_flaws:
  - { name: "Avatar Companion", type: merit, value: 3 }
```

### Loading in Script

```renpy
$ pc = wod.load_character("my_story/elena.yaml")
$ mentor = wod.load_character("my_story/npcs/mentor.yaml")
```

### Character Creation (Opt-in)

```renpy
$ pc = wod.chargen("mage")
```

Launches a screen flow driven by the schema:
1. Identity (name, tradition, essence)
2. Attributes (priority pick + dot allocation)
3. Abilities (dot allocation)
4. Spheres (limited by Arete)
5. Backgrounds, Merits/Flaws
6. Resources (auto-calculated)
7. Review & confirm

Authors can customize:

```renpy
# Pre-set some values, player picks the rest
$ pc = wod.chargen("mage", preset={"tradition": "Virtual Adepts"})
```

### Mid-story Stat Changes

```renpy
$ pc.set("Science", 5)
$ pc.set("Spirit", 1)
$ pc.advance("Forces")  # increments by 1
```

## Section 5: Splat Plugin Structure

### Manifest File

```yaml
# splats/mage/manifest.yaml
splat:
  id: mage
  display_name: "Mage: The Ascension"
  edition: "M20"
  version: "1.0"
  schema: schema.yaml
  resources: resources.yaml
  templates_dir: templates/

  screens:
    character_sheet: null    # use default
    chargen_steps:
      - identity
      - attributes
      - abilities
      - spheres
      - backgrounds
      - merits_flaws
      - review
```

### Loading

```renpy
init python:
    wod.load_splat("mage")
    # Or auto-discover all splats:
    wod.load_all_splats()
```

### How It Works

- `loader.py` scans `splats/` for `manifest.yaml` files.
- Each manifest registers its schema and resources with the core engine.
- Multiple splats can be loaded simultaneously for crossover stories.
- Community splats go in `splats/custom/` following the same structure.

### Author-Level Overrides

Authors can tweak a splat without editing the pack itself:

```yaml
# game/my_story/mage_overrides.yaml
extends: mage
overrides:
  trait_categories:
    abilities:
      skills:
        append: [Hypertech]
  resources:
    quintessence:
      range: [0, 30]
```

```renpy
init python:
    wod.load_splat("mage", overrides="my_story/mage_overrides.yaml")
```

## Section 6: UI & Themes

### Theme Structure

```
themes/
├── gothic/
│   ├── theme.yaml
│   ├── gui.rpy
│   ├── screens.rpy
│   ├── fonts/
│   └── images/
│       ├── ui/
│       └── backgrounds/
└── neutral/
    ├── theme.yaml
    ├── gui.rpy
    ├── screens.rpy
    ├── fonts/
    └── images/
```

### Theme Selection

```renpy
init python:
    wod.set_theme("gothic")
```

### Provided Screens

| Screen | Purpose |
|--------|---------|
| `character_sheet` | Full stat display — traits, resources, merits/flaws |
| `resource_hud` | Persistent overlay showing key resource pools |
| `chargen_*` | Step-by-step character creation screens |
| `stat_check_toast` | Notification when a gated choice triggers |
| `stat_change_toast` | Notification when a stat changes mid-story |

### HUD Control

```renpy
$ wod.show_hud(["quintessence", "paradox", "health", "willpower"])
$ wod.hide_hud()
```

### Configuration

```renpy
init python:
    wod.config.show_gate_toasts = True
    wod.config.gate_toast_format = "{trait} {value} — {result}"
```

Custom themes follow the same directory structure. The framework falls back to `neutral` for any missing assets.

## Section 7: Custom Syntax Compiler

### How It Works

1. At `python early` init, `syntax.py` scans all `.rpy` files for the bracket pattern.
2. Compiles shorthand into native Ren'Py conditions:

| Shorthand | Compiles To |
|-----------|-------------|
| `[Forces >= 3]` | `if pc.check("Forces", 3)` |
| `[Forces >= 3, Prime >= 2]` | `if pc.check("Forces", 3) and pc.check("Prime", 2)` |
| `[quintessence >= 5]` | `if pc.resource("quintessence") >= 5` |
| `[Avatar Companion]` | `if pc.has_merit("Avatar Companion")` |
| `[!Blind]` | `if not pc.has_flaw("Blind")` |

3. The compiler distinguishes traits vs. resources vs. merits by checking the loaded schema.
4. Unknown identifiers raise a clear error at startup:

```
WoD Syntax Error (script.rpy:45): Unknown trait "Forcs" in gate condition.
Did you mean "Forces"?
```

### Limitation

The shorthand only works in `.rpy` files (static source transform). For dynamically generated menus from Python, authors use the native `pc.check()` API.

## Section 8: Data Flow & Lifecycle

### Init Sequence

```
1. Ren'Py starts
2. python early:
   └── syntax.py scans .rpy files, compiles bracket shorthand -> native Ren'Py
3. init python:
   ├── wod_core engine initializes
   ├── loader.py discovers and loads splat(s)
   │   ├── Parses manifest.yaml
   │   ├── Registers schema
   │   └── Registers resources
   ├── Theme loads
   └── Author's init code runs
       ├── wod.load_character() or wod.chargen() for PC
       └── wod.load_character() for NPCs
4. Game starts -> label start:
```

### Play Loop

```
Scene plays (dialogue, narration)
    |
Menu encountered
    |
Gating system evaluates each choice:
    ├── Check traits against schema
    ├── Check resources against pools
    ├── Check merits/flaws
    └── Filter: show, hide, or grey-out each option
    |
Player picks a visible/available choice
    |
Outcome label runs:
    ├── May branch further on stat values
    ├── May modify traits (pc.set, pc.advance)
    ├── May spend/gain resources (pc.spend, pc.gain)
    │   └── Resource links enforce constraints
    └── UI updates automatically (HUD, toasts)
    |
Next scene
```

### Save/Load

- All runtime state (trait values, resource pools, merits/flaws, identity) lives in Ren'Py-managed variables.
- Schema and resource definitions stay in YAML, reloaded on game start.
- Saving: Ren'Py snapshots the character objects automatically.
- Loading: Ren'Py restores them, framework re-validates against current schema.

### Multi-PC Flow (Opt-in)

```renpy
$ pc = wod.load_character("elena.yaml")
$ npc_mentor = wod.load_character("npcs/mentor.yaml")

# Switch active character for gating purposes
$ wod.set_active(pc)

# Or gate on a specific character
"Ask Marcus to ward the room" if npc_mentor.check("Prime", 3):
```
