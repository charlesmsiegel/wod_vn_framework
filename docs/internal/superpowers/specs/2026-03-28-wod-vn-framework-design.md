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
- **Dual syntax.** Authors can use a compact shorthand (`[Forces >= 3]`) or native Ren'Py (`if pc.gate("Forces", ">=", 3)`).
- **Two bundled themes.** Gothic (WoD aesthetic) and Neutral (easy to reskin).
- **Single PC default, multi-PC opt-in.**
- **Pre-defined characters or player chargen — author's choice.**

## Project Structure

```
game/
├── wod_core/               # Core Python engine
│   ├── engine.py           # Trait system, validation, character objects
│   ├── resources.py        # Resource pool system (spend, gain, links)
│   ├── gating.py           # Stat-gating + choice filtering
│   ├── syntax.py           # Shorthand compiler ([Forces >= 3] -> wod.gate())
│   ├── chargen.py          # Character creation framework
│   └── loader.py           # Data file loader (YAML)
├── wod_screens/            # Ren'Py screens
│   ├── character_sheet.rpy
│   ├── resource_bars.rpy
│   └── chargen.rpy
├── wod_statements.rpy      # Registers shorthand syntax via Ren'Py CDS API
├── themes/
│   ├── gothic/
│   │   ├── theme.yaml      # Color palette, font config
│   │   ├── screens.rpy     # Themed screen implementations
│   │   ├── fonts/
│   │   └── images/
│   └── neutral/
│       ├── theme.yaml
│       ├── screens.rpy
│       ├── fonts/
│       └── images/
├── gui.rpy                 # Root GUI config — delegates to active theme
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

Trait categories use either `groups` (traits organized under sub-groups) or `traits` (flat list). These are mutually exclusive — use `groups` when the category has meaningful sub-groupings (e.g., Attributes split into Physical/Social/Mental), use `traits` for flat lists.

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

  arete:
    display_name: "Arete"
    traits: [Arete]
    default: 1
    range: [1, 10]

  backgrounds:
    display_name: "Backgrounds"
    traits: [Allies, Avatar, Contacts, Destiny, Dream, Familiar, Influence, Mentor, Node, Resources, Sanctum, Wonder]
    default: 0
    range: [0, 5]

# Constraints between traits — validated on set() and during chargen
trait_constraints:
  - type: "max_linked"
    target_category: "spheres"
    limited_by: "Arete"
    rule: "No Sphere can exceed Arete rating"
```

### Trait Constraints

The `trait_constraints` section defines inter-trait dependencies. Supported constraint types:

| Type | Meaning | Example |
|------|---------|---------|
| `max_linked` | All traits in target category capped by another trait's value | Spheres capped by Arete |
| `min_required` | A trait requires a minimum in another trait to be raised | (Future: Disciplines requiring Generation) |

Constraints are enforced by `engine.py` during `set()`, `advance()`, and chargen. Violations raise errors in development, log warnings in release.

### Runtime Behavior

- `engine.py` loads the schema at init time.
- Character objects hold current trait values as a flat dict (`{"Strength": 3, "Forces": 2, ...}`). The loader flattens the nested YAML structure (traits grouped by category) into this flat dict at load time. **Trait names must be unique across all categories within a splat** — the schema loader validates this at init.
- Setting a trait validates against both the schema's range and any applicable trait constraints.
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
    arete:
      range: [1, 10]
```

## Section 2: Resource Pool System

Generic trackable resources configured per splat. Handles anything with a current value, max, and rules about spending/gaining. Implemented in `resources.py`.

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
    default_max: 5
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

### Resource Max Defaults

When a resource specifies `default_current: "max"`, the max value is determined by (in priority order):

1. Explicit `default_max` value (e.g., `default_max: 5`)
2. Upper bound of `range` (e.g., `range: [0, 7]` → max is 7)

### Linked Resource Behavior

When a linked pool constraint would be violated (e.g., `quintessence` is 15, `paradox` is 5, and `gain("paradox", 3)` is called):

- The gain succeeds: paradox becomes 8.
- The linked pool is reduced to maintain the constraint: quintessence is reduced to 12.
- If the author wants the gain to be capped instead (paradox stays at 5), they should check the constraint before calling gain.

### Runtime Behavior

- Resources are separate from traits — traits are static ratings, resources are pools that get spent and replenished.
- `resources.py` provides `spend(name, amount)`, `gain(name, amount)`, `current(name)`, `at_max(name)`, `at_min(name)`.
- Linked resources enforce combined constraints automatically.
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

The core authoring mechanic. Two syntaxes, one system — the shorthand compiles to generic `wod.gate()` calls that dispatch at runtime.

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
    "Rewrite the ward's resonance" if pc.gate("Prime", ">=", 3) and pc.gate("Forces", ">=", 2):
        jump rewrite_ward
    "Perceive the ward's structure" if pc.gate("Prime", ">=", 1):
        jump perceive_ward
    "Try to push through" if pc.gate("Stamina", ">=", 3):
        jump brute_force
    "Back away":
        jump retreat
```

### The `gate()` and `has()` Methods

Two levels of API exist:

- **`pc.gate(name, op, value)`** / **`pc.has(name)`** — instance methods on a character object. Used in native syntax and outcome branching where the author specifies which character to check.
- **`wod.gate(name, op, value)`** / **`wod.has(name)`** — module-level convenience functions that delegate to `wod.active_character.gate(...)`. Used by the shorthand compiler output, since the compiler doesn't know which character variable the author is using.

In single-PC games, `wod.active_character` is the PC and authors never think about this distinction. In multi-PC games, `wod.set_active(pc)` determines which character the shorthand syntax checks against, while native syntax can target any character directly.

All six comparison operators are supported: `>=`, `<=`, `==`, `!=`, `>`, `<`.

For boolean merits/flaws, `has()` is used — `pc.has("Avatar Companion")` returns True/False.

### Supported Conditions

| Shorthand | Compiles To |
|-----------|-------------|
| `[Forces >= 3]` | `if pc.gate("Forces", ">=", 3)` |
| `[Forces >= 3, Prime >= 2]` | `if pc.gate("Forces", ">=", 3) and pc.gate("Prime", ">=", 2)` |
| `[quintessence >= 5]` | `if pc.gate("quintessence", ">=", 5)` |
| `[Forces == 3]` | `if pc.gate("Forces", "==", 3)` |
| `[Avatar Companion]` | `if pc.has("Avatar Companion")` |
| `[!Blind]` | `if not pc.has("Blind")` |

### Outcome Modification

The same stats that gate a choice can further branch the outcome:

```renpy
label rewrite_ward:
    if pc.gate("Forces", ">=", 5):
        "Your mastery of Forces lets you not just rewrite the ward, but improve it."
        $ pc.gain("quintessence", 2)
    elif pc.gate("Forces", ">=", 4):
        "You carefully rewrite the ward's structure."
    else:
        "You manage to alter the ward, but it's rough work."
        $ pc.gain("paradox", 1)
```

### Hidden vs. Visible Gating

By default, choices the PC doesn't qualify for are **hidden**. Authors can optionally show them greyed-out using a separate annotation:

```renpy
"Rewrite the ward's resonance" [Prime >= 3, Forces >= 2] (locked="You lack the knowledge..."):
```

The `(locked=...)` annotation is separate from the condition brackets, keeping condition syntax pure.

## Section 4: Character Definition & Creation

### Templates vs. Character Files

- **Templates** live in `splats/<splat>/templates/` and define character blueprints — starting stat distributions, valid ranges, and defaults. Used by chargen and as a base for pre-defined characters.
- **Character files** live in the author's story directory (e.g., `game/my_story/characters/`) and define specific characters with concrete stat values. They reference a template via `schema` and `template` fields.

### Pre-defined Characters (Data Files)

```yaml
# game/my_story/characters/elena.yaml
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

### Loading in Script

```renpy
label start:
    $ pc = wod.load_character("my_story/characters/elena.yaml")
    $ mentor = wod.load_character("my_story/characters/npcs/mentor.yaml")
```

### Character Creation (Opt-in)

Character creation is a UI flow that runs during gameplay (after `label start`), not during init. Internally, `wod.chargen()` uses `renpy.call_screen()` in a loop to walk through each chargen step, collecting input and returning the completed character object:

```renpy
label start:
    "Welcome to the Chronicle."
    $ pc = wod.chargen("mage")
    # Internally calls renpy.call_screen() for each step, returns character object
    "Your journey begins..."
```

The chargen screen flow is driven by the splat manifest's `chargen_steps`:
1. Identity (name, tradition, essence)
2. Attributes (priority pick + dot allocation)
3. Abilities (dot allocation)
4. Spheres (limited by Arete — enforced by trait constraints)
5. Backgrounds
6. Merits/Flaws
7. Resources (auto-calculated)
8. Review & confirm

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

All changes are validated against schema ranges and trait constraints.

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
- Multiple splats can be loaded simultaneously for crossover stories. Each character is assigned to a specific splat via its `schema` field. Trait name collisions across splats are scoped to the character's splat — a Mage character validates against the Mage schema, a Vampire character against the Vampire schema. Characters cannot have traits from multiple schemas.
- Community splats go in `splats/custom/` following the same structure.
- Multi-splat crossover mechanics (e.g., cross-splat interactions) are out of scope for v1.

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
│   ├── theme.yaml          # Color palette, font config, style vars
│   ├── screens.rpy         # Themed screen implementations
│   ├── fonts/
│   └── images/
│       ├── ui/
│       └── backgrounds/
└── neutral/
    ├── theme.yaml
    ├── screens.rpy
    ├── fonts/
    └── images/
```

### Theme and GUI Integration

The root `gui.rpy` delegates to the active theme. It reads the selected theme's `theme.yaml` and sets Ren'Py GUI variables (colors, fonts, sizes) accordingly. Theme-specific `screens.rpy` files provide styled implementations of the framework screens.

Theme selection happens at init time and is not hot-swappable during gameplay:

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

### Architecture

The shorthand syntax is implemented as a **two-phase system** to resolve the timing constraint that Ren'Py's `python early` phase runs before splat schemas are loaded:

**Phase 1 — Source Transform (python early):** `syntax.py` scans `.rpy` files and performs a schema-agnostic textual transform. It does not need to know whether "Forces" is a trait, resource, or merit — it just converts bracket syntax into generic `wod.gate()` calls.

**Phase 2 — Validation (init python):** After splat schemas are loaded, the framework runs a validation pass over all registered gate calls. This is where unknown identifiers are caught and "did you mean?" errors are raised.

### Registration via CDS

`wod_statements.rpy` uses Ren'Py's Creator-Defined Statements (CDS) API to register the framework's custom syntax handling. This is the idiomatic Ren'Py mechanism for extending the scripting language.

### Compilation Table

| Shorthand | Phase 1 Output |
|-----------|----------------|
| `[Forces >= 3]` | `if wod.gate("Forces", ">=", 3)` |
| `[Forces >= 3, Prime >= 2]` | `if wod.gate("Forces", ">=", 3) and wod.gate("Prime", ">=", 2)` |
| `[quintessence >= 5]` | `if wod.gate("quintessence", ">=", 5)` |
| `[Forces == 3]` | `if wod.gate("Forces", "==", 3)` |
| `[Avatar Companion]` | `if wod.has("Avatar Companion")` |
| `[!Blind]` | `if not wod.has("Blind")` |

At runtime, `wod.gate()` dispatches to the appropriate system (trait check, resource check) based on the loaded schema. `wod.has()` checks merits/flaws.

### Validation Errors

After schemas load, the framework validates all gate/has calls encountered during source transform:

```
WoD Validation Error (script.rpy:45): Unknown identifier "Forcs" in gate condition.
Did you mean "Forces"?
```

These errors appear at game startup before any scene plays.

### Limitation

The shorthand only works in `.rpy` files (static source transform). For dynamically generated menus from Python, authors use the native `pc.gate()` / `pc.has()` API.

## Section 8: Data Flow & Lifecycle

### Init Sequence

```
1. Ren'Py starts
2. python early:
   └── syntax.py scans .rpy files
       └── Compiles bracket shorthand -> generic wod.gate()/wod.has() calls
       └── (No schema knowledge needed — pure textual transform)
3. init python:
   ├── wod_core engine initializes
   ├── loader.py discovers and loads splat(s)
   │   ├── Parses manifest.yaml
   │   ├── Registers schema (traits, constraints)
   │   └── Registers resources (pools, links)
   ├── Validation pass: checks all gate()/has() identifiers against loaded schemas
   ├── Theme loads (gui.rpy reads theme.yaml, sets Ren'Py GUI vars)
   └── Author's init code runs
       └── wod.load_character() for NPCs if desired
4. Game starts -> label start:
   ├── Author loads/creates PC (wod.load_character or wod.chargen)
   └── Story begins
```

### Play Loop

```
Scene plays (dialogue, narration)
    |
Menu encountered
    |
Gating system evaluates each choice:
    ├── wod.gate() dispatches to trait or resource check
    ├── wod.has() checks merits/flaws
    └── Filter: show, hide, or grey-out each option
    |
Player picks a visible/available choice
    |
Outcome label runs:
    ├── May branch further on stat values
    ├── May modify traits (pc.set, pc.advance)
    │   └── Trait constraints enforced
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
- Save migration across schema changes (renamed traits, changed ranges) is out of scope for v1. Authors should treat released schema as stable.

### Multi-PC Flow (Opt-in)

```renpy
label start:
    $ pc = wod.load_character("elena.yaml")
    $ npc_mentor = wod.load_character("npcs/mentor.yaml")

    # Switch active character for gating purposes
    $ wod.set_active(pc)

    # Or gate on a specific character
    "Ask Marcus to ward the room" if npc_mentor.gate("Prime", ">=", 3):
```
