# WoD VN Framework -- Author Guide

A complete reference for writing World of Darkness visual novels with the framework.

---

## Table of Contents

1. [Installation](#1-installation)
2. [Your First Scene](#2-your-first-scene)
3. [Characters](#3-characters)
4. [Stat Gating](#4-stat-gating)
5. [Bracket Shorthand](#5-bracket-shorthand)
6. [Resources](#6-resources)
7. [Character Creation](#7-character-creation)
8. [HUD & Character Sheet](#8-hud--character-sheet)
9. [Toast Notifications](#9-toast-notifications)
10. [Data Files](#10-data-files)
11. [Customization](#11-customization)
12. [Testing Your Game](#12-testing-your-game)

---

## 1. Installation

### Requirements

- [Ren'Py 8.x](https://www.renpy.org/latest.html) (Python 3 SDK)
- Python 3.10+ (for running the bracket shorthand CLI and tests outside of Ren'Py)

### Setup

```bash
# Clone the framework
git clone <repo-url> my_wod_game
cd my_wod_game

# Verify the project loads cleanly
renpy.sh . lint
```

If lint passes with no errors, the framework is installed correctly. The `wod_init.rpy` file bootstraps the engine automatically when Ren'Py starts -- you do not need to call any setup code yourself.

### What Happens at Startup

When Ren'Py loads your game, `wod_init.rpy` runs at `init -10`:

1. Imports `wod_core` and calls `wod_core.init(renpy.config.gamedir)`.
2. Discovers all splat packs in `game/splats/`.
3. Loads every discovered splat (schema, resources, chargen config).

If no splats are found, an error is raised immediately so you know something is wrong.

---

## 2. Your First Scene

Here is a minimal `script.rpy` that loads a character and presents a stat-gated choice:

```renpy
## Declare a Ren'Py Character for dialogue
define elena = Character("Elena", color="#c9a96e")

## Declare the pc variable for save/load compatibility
default pc = None

label start:
    ## Load a character from a YAML file
    $ pc = wod_core.load_character("demo/elena.yaml")

    ## Set her as the active character (required for module-level gate/has)
    $ wod_core.set_active(pc)

    ## Show the resource HUD
    $ wod_core.show_hud()

    elena "I can feel the ward's energy. Let me examine it."

    menu:
        "Unravel the ward with Forces" if pc.gate("Forces", ">=", 3):
            elena "The threads of energy come apart in my hands."

        "Hack the encryption" if pc.gate("Technology", ">=", 3):
            elena "Good old-fashioned hacking. No magick needed."

        "Leave quietly":
            elena "Not today."

    return
```

Key points:
- `wod_core.load_character()` takes a path relative to `game/`.
- `wod_core.set_active(pc)` makes `pc` the active character for module-level `wod_core.gate()` and `wod_core.has()` calls.
- `pc.gate(trait, operator, value)` returns `True` or `False` -- Ren'Py hides menu choices whose `if` condition is `False`.
- `wod_core.show_hud()` displays the resource HUD overlay.

---

## 3. Characters

### YAML Format

Characters are defined in YAML files. Here is the demo character `game/demo/elena.yaml`:

```yaml
# Demo character: Elena Vasquez, Virtual Adept
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

### Field Reference

| Field | Required | Description |
|-------|----------|-------------|
| `schema` | Yes | Which splat to use (e.g. `mage`). Must match a loaded splat ID. |
| `identity` | No | Freeform dict: name, tradition, essence, nature, demeanor, etc. |
| `traits` | No | Nested by category (attributes, abilities, spheres, arete, backgrounds). Omitted traits get the schema default. |
| `resources` | No | Override starting resource values. Omitted resources get their YAML defaults. |
| `merits_flaws` | No | List of `{name, type, value}` dicts. |

### Loading a Character

```renpy
$ pc = wod_core.load_character("demo/elena.yaml")
```

The path is relative to `game/`. The loader:

1. Reads the YAML file.
2. Looks up the splat by the `schema` field (it must already be loaded).
3. Initializes all traits to schema defaults, then applies your overrides.
4. Validates ranges and constraints (e.g., no Sphere can exceed Arete).
5. Attaches a `ResourceManager` with pools from the splat's `resources.yaml`.
6. Applies character-specific resource overrides.

### Accessing Character Data

```renpy
## Read a trait value
$ forces = pc.get("Forces")

## Set a trait (validated against range and constraints)
$ pc.set("Forces", 4)

## Advance a trait by 1
$ pc.advance("Awareness")

## Access identity fields
$ name = pc.identity["name"]
$ tradition = pc.identity.get("tradition", "Unknown")
```

---

## 4. Stat Gating

Stat gating is the core mechanic. Instead of dice rolls, a character's stats deterministically control which choices appear and which outcomes occur.

### Basic Gate Check

```renpy
if pc.gate("Forces", ">=", 3):
    "Your mastery of Forces lets you unravel the energy matrix."
```

`pc.gate(name, op, value)` returns `True` or `False`. It works with both traits and resources.

### Supported Operators

| Operator | Meaning |
|----------|---------|
| `>=` | Greater than or equal |
| `<=` | Less than or equal |
| `==` | Equal |
| `!=` | Not equal |
| `>` | Strictly greater than |
| `<` | Strictly less than |

### Gating Menu Choices

The most common use: show or hide menu choices based on stats.

```renpy
menu:
    "Unravel the ward" if pc.gate("Forces", ">=", 3) and pc.gate("Prime", ">=", 2):
        jump unravel

    "Brute-force the encryption" if pc.gate("Technology", ">=", 3):
        jump hack

    "Leave quietly":
        jump leave
```

Choices whose `if` condition evaluates to `False` are hidden from the player. The last choice has no condition and always appears as a fallback.

### Combining Conditions

Use Python's `and` / `or` for compound checks:

```renpy
if pc.gate("Forces", ">=", 3) and pc.gate("Prime", ">=", 2):
    "You have both the power and the insight."

if pc.gate("Technology", ">=", 3) or pc.gate("Science", ">=", 4):
    "Either skill would work here."
```

### Checking Merits and Flaws

Use `pc.has()` to check for merits or flaws by name:

```renpy
if pc.has("Avatar Companion"):
    "Your Avatar manifests beside you, offering guidance."
```

`pc.has(name)` returns `True` if any entry in the character's `merits_flaws` list has a matching `name` field.

### Module-Level Gating

If you have called `wod_core.set_active(pc)`, you can use module-level shortcuts:

```renpy
if wod_core.gate("Forces", ">=", 3):
    "This works too."

if wod_core.has("Avatar Companion"):
    "Module-level merit check."
```

These delegate to whichever character was last set as active.

### Outcome Branching

Gate checks are not limited to menu choices. Use them anywhere for branching:

```renpy
$ success = pc.spend("quintessence", 3)

if success:
    if pc.gate("Forces", ">=", 3):
        "Clean unraveling. Minimal Paradox."
        $ pc.gain("paradox", 2)
    else:
        "Rough unraveling. Heavy Paradox."
        $ pc.gain("paradox", 4)
else:
    "Not enough Quintessence."
```

---

## 5. Bracket Shorthand

For authors who prefer a more concise syntax, the framework includes a pre-processor that transforms bracket notation into native Ren'Py `if` expressions.

### Syntax

```renpy
## Before pre-processing:
"Unravel the ward" [Forces >= 3, Prime >= 2]:
    jump unravel

"Check for the merit" [Avatar Companion]:
    jump companion_scene

"Reject the dark path" [!Sphere Inept]:
    jump reject
```

```renpy
## After pre-processing:
"Unravel the ward" if wod_core.gate("Forces", ">=", 3) and wod_core.gate("Prime", ">=", 2):
    jump unravel

"Check for the merit" if wod_core.has("Avatar Companion"):
    jump companion_scene

"Reject the dark path" if not wod_core.has("Sphere Inept"):
    jump reject
```

### Rules

- `[Trait >= N]` becomes `wod_core.gate("Trait", ">=", N)` -- any comparison operator works.
- `[Merit Name]` (no operator) becomes `wod_core.has("Merit Name")`.
- `[!Flaw Name]` (leading `!`) becomes `not wod_core.has("Flaw Name")`.
- Multiple conditions separated by commas are joined with `and`.

### Running the Pre-Processor

```bash
# Transform files in-place
python -m wod_core game/script.rpy

# Preview without modifying files
python -m wod_core --dry-run game/script.rpy

# Process multiple files
python -m wod_core game/script.rpy game/chapter2.rpy
```

The pre-processor prints `Transformed: <file>` or `No changes: <file>` to stderr for each file.

### Important

The pre-processor modifies files **in place**. Run `--dry-run` first to review changes. Once transformed, the file contains standard Ren'Py syntax and the bracket shorthand is gone -- you can continue editing the transformed file normally.

---

## 6. Resources

Resources are numeric pools that characters spend and gain during gameplay: Quintessence, Paradox, Willpower, Health.

### Spending Resources

```renpy
## Returns True if the character had enough, False otherwise
$ success = pc.spend("quintessence", 3)

if success:
    "Three points of Quintessence flow into the ward."
else:
    "Not enough Quintessence."
```

`pc.spend(name, amount)` subtracts from the pool. It returns `False` (and does not modify the pool) if the character does not have enough.

### Gaining Resources

```renpy
## Returns the amount actually gained (may be less if pool is capped)
$ gained = pc.gain("paradox", 2)

"You accumulated [gained] points of Paradox."
```

`pc.gain(name, amount)` adds to the pool, capped at the pool's maximum range. It returns how much was actually gained.

### Reading Resource Values

```renpy
"Quintessence: [pc.resources.current('quintessence')]"
"Paradox: [pc.resources.current('paradox')]"
```

You can also gate on resources:

```renpy
if pc.gate("quintessence", ">=", 3):
    "You have enough Quintessence to attempt this."
```

### The Quintessence Wheel

In Mage, Quintessence and Paradox are linked on a shared 20-point Wheel. When one goes up, the other is pushed down if their combined total would exceed 20.

This is configured in `resources.yaml`:

```yaml
resource_links:
  quintessence_wheel:
    pools: [quintessence, paradox]
    combined_max: 20
```

Example: if a character has 15 Quintessence and gains 8 Paradox, the Paradox pool rises to 8 and Quintessence is automatically reduced to 12 (because 12 + 8 = 20). The framework enforces this constraint automatically whenever `gain()` is called on a linked pool.

### Resource Configuration

Resources are defined in the splat's `resources.yaml`. Each pool has:

```yaml
resources:
  quintessence:
    display_name: "Quintessence"
    range: [0, 20]        # Absolute min and max
    default: 0            # Starting value

  willpower:
    display_name: "Willpower"
    range: [0, 10]
    default_max: 5        # Max is 5 (not the range cap of 10)
    default_current: "max" # Start at max (i.e. 5)

  health:
    display_name: "Health"
    range: [0, 7]
    default_current: "max"
    track_type: "levels"   # Display as a damage track, not a numeric pool
    levels:
      - { name: "Bruised", penalty: 0 }
      - { name: "Hurt", penalty: -1 }
      - { name: "Injured", penalty: -1 }
      - { name: "Wounded", penalty: -2 }
      - { name: "Mauled", penalty: -2 }
      - { name: "Crippled", penalty: -5 }
      - { name: "Incapacitated", penalty: null }
```

---

## 7. Character Creation

The framework provides a full character creation flow with three modes.

### Running Chargen

```renpy
$ pc = wod_core.chargen("mage", mode="full")

if pc is None:
    ## Player cancelled
    "Character creation cancelled."
    return

$ wod_core.set_active(pc)
$ wod_core.show_hud()
elena "Welcome, [pc.identity['name']]."
```

`wod_core.chargen(splat_id, mode, preset)` runs the character creation screen loop. It returns a `Character` on success or `None` if the player cancels.

### Three Modes

#### Full M20 (`mode="full"`)

The traditional Mage: The Ascension creation process:

1. **Identity** -- Name, Tradition, Nature, Demeanor, Essence.
2. **Attribute Priority** -- Assign primary/secondary/tertiary to Physical/Social/Mental (pools of 7/5/3).
3. **Attribute Allocation** -- Distribute dots within each priority tier.
4. **Ability Priority** -- Same for Talents/Skills/Knowledges (pools of 13/9/5), max 3 per Ability at creation.
5. **Ability Allocation** -- Distribute dots.
6. **Spheres & Backgrounds** -- 6 Sphere dots, 7 Background dots. Tradition gives a free affinity Sphere dot.
7. **Freebies** -- 15 freebie points to spend on anything (costs: Attribute 5, Ability 2, Sphere 7, Background 1, Willpower 1). Merits and Flaws available here.
8. **Review** -- Final confirmation.

#### Simplified (`mode="simplified"`)

A streamlined version for quicker setup:

1. **Identity** -- Name, Tradition, Nature, Demeanor, Essence.
2. **Attributes** -- 15 allocatable dots on top of the free 1 per Attribute (total 24).
3. **Abilities** -- 27 allocatable dots.
4. **Spheres** -- 6 Sphere dots.
5. **Review** -- Final confirmation.

#### Template (`mode="template"`)

Pick a pre-built character archetype:

1. **Identity** -- Name and Tradition selection.
2. **Template Pick** -- Choose from pre-built character files defined in `chargen.yaml`.
3. **Review** -- Final confirmation.

Templates are full character YAML files stored in `game/splats/mage/templates/`.

### Presets

You can pre-fill identity fields:

```renpy
$ pc = wod_core.chargen("mage", mode="full", preset={"name": "Elena", "tradition": "virtual_adepts"})
```

The preset dict is merged into the identity step data before the first screen appears.

### Customizing chargen.yaml

The `chargen.yaml` file controls everything about character creation:

- **`modes`** -- Define which steps each mode uses, point pools, starting Arete, freebie costs.
- **`traditions`** -- List of Traditions with affinity Spheres, starting Arete overrides, and template file references.
- **`archetypes`** -- Nature/Demeanor options.
- **`essences`** -- Dynamic, Pattern, Primordial, Questing.
- **`merits`** / **`flaws`** -- Available during the freebie step, with name, cost, and description.

Example -- adding a new Tradition:

```yaml
traditions:
  # ... existing traditions ...
  - id: hollow_ones
    name: "Hollow Ones"
    affinity_sphere: Entropy
    free_sphere_dot: Entropy
    templates:
      - name: "Gothic Poet"
        description: "Entropy and Mind — find truth in decay and disillusion"
        file: templates/ho_gothic_poet.yaml
```

---

## 8. HUD & Character Sheet

### Resource HUD

The HUD displays resource pools as an overlay during gameplay.

```renpy
## Show the HUD with all resources
$ wod_core.show_hud()

## Show the HUD with only specific resources
$ wod_core.show_hud(resources=["quintessence", "paradox", "willpower"])

## Hide the HUD
$ wod_core.hide_hud()
```

The HUD displays:
- **Quintessence/Paradox** as a split bar (reflecting the Wheel).
- **Willpower** as dot pips.
- **Health** as a damage track.

### Save/Load Persistence

The HUD state is stored in `renpy.store.wod_hud_visible`. The framework's `after_load` label in `wod_init.rpy` automatically re-shows the HUD screen when a save is loaded:

```renpy
label after_load:
    if store.wod_hud_visible:
        show screen resource_hud
    return
```

You do not need to write any after_load code yourself. If you need custom after_load behavior, add it in your own `after_load` label -- Ren'Py chains them.

### Character Sheet

The character sheet is a full-screen overlay toggled with the **Tab** key. It displays:

- All trait categories with WoD-style dot ratings.
- Tabbed navigation (configured in `manifest.yaml`).
- Merits, flaws, and resource pools.

The tab configuration in `manifest.yaml`:

```yaml
character_sheet:
  tabs:
    - name: "Attributes & Abilities"
      categories: [attributes, abilities]
    - name: "Spheres & Backgrounds"
      categories: [arete, spheres, backgrounds]
    - name: "Merits & Resources"
      categories: []    # Empty = special merits/resources tab
```

---

## 9. Toast Notifications

Toast notifications are brief messages that appear on screen and automatically fade out.

### Basic Usage

```renpy
$ wod_core.show_toast("Awareness advanced to 3")
```

You can also set a custom duration (default is 2.0 seconds):

```renpy
$ wod_core.show_toast("Paradox surge!", duration=3.0)
```

### Automatic Gate Toasts

You can enable automatic toast notifications whenever a gate check is evaluated:

```renpy
$ wod_core.config.show_gate_toasts = True
```

The format is controlled by:

```renpy
$ wod_core.config.gate_toast_format = "{trait} {value} — {result}"
```

Set `show_gate_toasts` to `False` (the default) to disable them.

---

## 10. Data Files

The framework uses a data-driven architecture. All game-line-specific content lives in YAML files under `game/splats/<splat_id>/`.

### Splat Directory Structure

```
game/splats/mage/
  manifest.yaml      # Metadata and file references
  schema.yaml        # Trait categories, ranges, defaults, constraints
  resources.yaml     # Resource pools and linked pool config
  chargen.yaml       # Character creation modes, traditions, merits/flaws
  templates/         # Pre-built character files for template mode
```

### manifest.yaml

The manifest is the entry point for a splat. The loader reads this first.

```yaml
splat:
  id: mage
  display_name: "Mage: The Ascension"
  edition: "M20"
  version: "1.0"
  schema: schema.yaml
  resources: resources.yaml
  chargen: chargen.yaml
  templates_dir: templates/
  character_sheet:
    tabs:
      - name: "Attributes & Abilities"
        categories: [attributes, abilities]
      - name: "Spheres & Backgrounds"
        categories: [arete, spheres, backgrounds]
      - name: "Merits & Resources"
        categories: []
```

### schema.yaml

Defines all trait categories. Each category has a display name, range, default value, and a list of traits (optionally grouped).

```yaml
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
      talents: [Alertness, Art, Athletics, ...]
      skills: [Crafts, Drive, Etiquette, ...]
      knowledges: [Academics, Computer, Cosmology, ...]
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

trait_constraints:
  - type: max_linked
    target_category: spheres
    limited_by: Arete
    rule: "No Sphere can exceed Arete rating"
```

Key concepts:
- **`groups`** organizes traits into sub-groups (Physical/Social/Mental). Used for priority-based allocation in chargen and for display in the character sheet.
- **`traits`** is a flat list (used when grouping is not needed, e.g., Spheres).
- **`trait_constraints`** enforce rules like "no Sphere can exceed Arete." The `max_linked` type caps all traits in `target_category` by the value of `limited_by`.
- Trait names must be unique across all categories.

### resources.yaml

See [Section 6: Resources](#6-resources) for the full format. Key sections:

- **`resources`** -- Individual pool definitions.
- **`resource_links`** -- Linked pool constraints (e.g., the Quintessence Wheel).

### Creating a New Splat

To add a new game line (e.g., Vampire):

1. Create the directory: `game/splats/vampire/`
2. Write `manifest.yaml` with the splat metadata.
3. Write `schema.yaml` with Vampire trait categories (Disciplines, Virtues, etc.).
4. Write `resources.yaml` with Vampire resources (Blood Pool, Humanity, etc.).
5. Optionally write `chargen.yaml` for character creation.
6. Add template files in `templates/` if supporting template mode.

The framework auto-discovers any directory under `game/splats/` that contains a `manifest.yaml`.

---

## 11. Customization

### Splat Overrides

Authors can modify a splat's schema and resources without editing the base files. Create an overrides YAML file and pass it when loading the splat:

```renpy
$ wod_core.load_splat("mage", overrides="my_overrides.yaml")
```

The path is relative to `game/`. The overrides file uses this structure:

```yaml
overrides:
  trait_categories:
    abilities:
      # Append new traits to a group
      talents:
        append: [Lucid Dreaming, Parkour]

  resources:
    quintessence:
      range: [0, 30]    # Increase the Quintessence cap
```

Override capabilities:
- **Append traits** to existing groups or trait lists.
- **Change range, default, or display_name** for any category.
- **Modify resource pool settings** (range, defaults, etc.).

Note: If you call `wod_core.load_splat()` with overrides, it must be called **before** `wod_core.load_all_splats()` or in place of it for that specific splat. The `wod_init.rpy` bootstrap calls `load_all_splats()` automatically, so for overrides you would modify `wod_init.rpy`:

```renpy
init -10 python:
    import wod_core
    wod_core.init(renpy.config.gamedir)
    wod_core.load_splat("mage", overrides="my_overrides.yaml")
```

### Template Extends

Character templates can extend a base template to create variants without duplicating data:

```yaml
# templates/archmage_elena.yaml
extends: va_code_witch

overrides:
  trait_categories:
    arete:
      range: [1, 10]
```

This loads the base template `templates/va_code_witch.yaml` and applies the overrides on top of it. Use this to create "what if" variants -- e.g., an archmage version of a standard character with an expanded Arete range.

Load an extended template with:

```renpy
$ pc = wod_core.get_loader().load_character_from_template(
    "mage", "templates/archmage_elena.yaml"
)
```

### Adding Custom Traits

To add traits that do not exist in the base schema, use splat overrides to append them to an existing category:

```yaml
overrides:
  trait_categories:
    abilities:
      skills:
        append: [Hacking, Demolitions]
```

These new traits work with all framework features -- gating, character sheet display, chargen allocation, and save/load.

### Adding Custom Resources

To modify resource pools, use the resources section of splat overrides:

```yaml
overrides:
  resources:
    willpower:
      default_max: 8
      range: [0, 12]
```

---

## 12. Testing Your Game

### Ren'Py Lint

Run Ren'Py's built-in linter to catch syntax errors and undefined references:

```bash
renpy.sh . lint
```

This checks all `.rpy` files in your game directory for common issues.

### Engine Tests

The framework includes a pytest test suite covering all engine modules:

```bash
# Run all tests
pytest

# Run a specific test file
pytest tests/test_engine.py

# Run with verbose output
pytest -v
```

Test files:

| File | Coverage |
|------|----------|
| `tests/test_engine.py` | Character creation, trait get/set/advance, range validation, constraints |
| `tests/test_gating.py` | Gate operators, merit checks, module-level gating |
| `tests/test_resources.py` | Spend/gain, linked pools (Quintessence Wheel), pool caps |
| `tests/test_chargen.py` | ChargenState, PointPool allocation, build_character |
| `tests/test_syntax.py` | Bracket shorthand parsing and transformation |
| `tests/test_loader.py` | YAML loading, splat discovery, character loading, overrides |
| `tests/test_integration.py` | End-to-end flows combining multiple subsystems |

### Writing Your Own Tests

The test suite uses the real splat data files in `game/splats/mage/`. You can add your own tests in the `tests/` directory. See `tests/conftest.py` for shared fixtures.

```python
# tests/test_my_game.py
from wod_core.engine import Character, Schema

def test_custom_character(mage_schema):
    """Test that my custom character loads correctly."""
    char = Character(
        schema=mage_schema,
        traits={"Forces": 3, "Arete": 3},
        identity={"name": "Test Character"},
    )
    assert char.get("Forces") == 3
    assert char.gate("Forces", ">=", 3)
```
