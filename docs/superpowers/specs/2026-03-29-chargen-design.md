# WoD VN Framework — Character Creation (Phase 2b-2) Design Specification

**Date:** 2026-03-29
**Status:** Approved
**Depends on:** Core Engine (Plan 1), Ren'Py Bootstrap (Phase 2a), HUD & Character Sheet (Phase 2b-1)
**Target Engine:** Ren'Py 8.3.7 (Python 3)

## Overview

Add interactive character creation to the framework with three modes: Full M20, Simplified, and Template-based. All modes are schema-driven, support full back/forward navigation, and return a Character object ready for gameplay.

**What's in scope:**

- `game/wod_core/chargen.py` — Creation logic, point pool tracking, validation, template loading
- `game/wod_screens/chargen.rpy` — Ren'Py screens for each creation step
- `game/splats/mage/chargen.yaml` — Mage-specific chargen config (dot pools, Traditions, template presets)
- `wod_core.chargen(splat_id, mode)` — Author-facing API
- Full back/forward navigation across steps
- Manifest and loader changes to support chargen.yaml

**What's deferred:**

- Gothic theme
- Toast notifications
- Bracket shorthand pre-processor
- Hollow Ones / Orphans / Disparates (only 9 core Traditions)

**Prerequisite engine change:** Phase 2b-1 adds `CategoryDef.groups` which chargen needs for priority group rendering.

## Section 1: Author API

```renpy
label start:
    $ pc = wod_core.chargen("mage", mode="full")
    if pc is None:
        # Player cancelled chargen
        jump main_menu
    $ wod_core.set_active(pc)
    $ wod_core.show_hud()
    "Your journey begins..."
```

Three modes:

| Mode | Target Audience | Steps | Complexity |
|------|----------------|-------|-----------|
| `"full"` | Tabletop players | 8 steps with priority picks, freebie points | High |
| `"simplified"` | VN players | 5 steps with flat point pools | Medium |
| `"template"` | Quick start | 3 steps — pick Tradition, pick preset | Low |

**Presets** partially fill in steps. Preset fields are pre-filled but NOT locked — the player can change them:

```renpy
$ pc = wod_core.chargen("mage", mode="simplified", preset={"tradition": "Virtual Adepts"})
```

**Cancellation:** Every step has a Cancel button. `chargen()` returns `None` if the player cancels. Authors must handle this.

## Section 2: Full M20 Mode

Faithful to M20 tabletop character creation. 8 steps (priority + allocation are separate logical steps in the step indicator).

### Step 1: Identity

Player enters:
- Name (text input)
- Tradition (pick from list — data-driven from `chargen.yaml`)
- Essence (Dynamic, Pattern, Primordial, Questing)
- Nature (pick from Archetype list)
- Demeanor (pick from Archetype list)

### Step 2: Attribute Priority

Player assigns priority to the three Attribute groups:
- Primary (7 dots), Secondary (5 dots), Tertiary (3 dots)
- Visual: three columns (Physical, Social, Mental) — group names and members read from `CategoryDef.groups`
- Player clicks to assign rank to each group

### Step 3: Attribute Allocation

Allocate dots within each group using WoD dot display (click to fill/unfill). All Attributes start at 1 (the free dot), allocated dots are added on top. Remaining dot count for each group shown prominently.

### Step 4: Ability Priority

Same as Attribute Priority but for Talents/Skills/Knowledges → 13/9/5 dots. Group names read from `CategoryDef.groups`.

### Step 5: Ability Allocation

Allocate dots within each group. Abilities start at 0, max 3 during creation (no ability above 3 without freebie points, per `ability_max_at_creation` in config).

### Step 6: Spheres & Backgrounds

- Allocate Sphere dots (pool from `chargen.yaml`, typically 6)
- Limited by starting Arete (set per-Tradition in `chargen.yaml`)
- Tradition's affinity Sphere highlighted, free dot if configured
- Allocate Background dots (default 7) below

### Step 7: Freebies & Merits/Flaws

A dedicated step for spending freebie points and picking Merits/Flaws.

**Freebie points: 15 (M20 standard).** Freebie budget is shown at the top. The screen shows all categories where freebies can be spent:

| Category | Cost per dot | Notes |
|----------|-------------|-------|
| Attribute | 5 | Can exceed allocation from Step 3 |
| Ability | 2 | Can raise above 3 (the creation max) |
| Sphere | 7 | Still limited by Arete |
| Background | 1 | |
| Willpower | 1 | Starting: 5 |
| Merit | variable | Costs listed per Merit in chargen.yaml |

**Flaws** grant additional freebie points (max 7 points of Flaws). Merits cost freebies at their listed point value.

The UI shows the current character with "+" buttons to spend freebies on each trait, and a Merit/Flaw picker. Remaining freebies update live.

### Step 8: Review & Confirm

- Full character sheet display (reuses the character sheet screen from 2b-1)
- "Go back to step N" buttons for each section
- "Confirm" creates the Character object and returns it

## Section 3: Simplified Mode

Faster creation for VN-focused games.

### Step 1: Identity

Same as Full mode but only Name and Tradition.

### Step 2: Attributes

- Flat pool of **15 allocatable dots** across all 9 Attributes (no priority pick)
- All start at 1 (the free dot), 15 additional dots to allocate (total: 24, matching Full mode's 7+5+3+9)
- Max 5 per Attribute

### Step 3: Abilities

- Flat pool of **27 allocatable dots** across all Abilities (matching Full mode's 13+9+5)
- Abilities start at 0, max 5 per Ability

### Step 4: Spheres

- Same as Full mode Step 6 but Spheres only (no Backgrounds)
- Pool size and Arete from `chargen.yaml`

### Step 5: Review & Confirm

- No Backgrounds, no Merits/Flaws, no Freebies (author can enable these via config)
- Same review screen as Full mode

## Section 4: Template Mode

Quickest path to a playable character.

### Step 1: Identity

Name only (text input).

### Step 2: Pick Tradition & Template

- Player picks a Tradition
- Then picks from 2-3 pre-built stat spreads for that Tradition
- Each template has a name and short description
- Templates are standard character YAML files (same format as `elena.yaml`), loaded via the existing `SplatLoader.load_character()`

### Step 3: Review & Confirm

- Shows the full character from the template
- Player can change name but not stats
- Confirm creates the Character

## Section 5: Navigation

All modes support full back/forward navigation:

- **Step indicator** at the top shows all steps, current step highlighted, completed steps checkmarked
- **Back button** returns to previous step with all allocations preserved
- **Forward button** (or clicking a completed step) jumps to a completed step
- **Cancel button** exits chargen, returns None

### Invalidation Rules

When the player goes back and changes a step, subsequent steps may be invalidated:

| Changed Step | Invalidates | Reason |
|---|---|---|
| Identity (Tradition change) | Spheres | Affinity Sphere and free dot change |
| Attribute Priority | Attribute Allocation | Dot pools changed |
| Ability Priority | Ability Allocation | Dot pools changed |
| Attribute Allocation | Nothing | Downstream steps don't depend on specific Attribute values |
| Ability Allocation | Nothing | Same |
| Spheres & Backgrounds | Nothing | |
| Freebies & Merits/Flaws | Nothing | |

When a step is invalidated, its data is cleared and the step indicator shows it as incomplete. The player must re-do that step before confirming.

### State Management

```python
class ChargenState:
    def __init__(self, splat_id: str, mode: str, schema, chargen_config, splat_data):
        self.splat_id = splat_id
        self.mode = mode
        self.schema = schema
        self.config = chargen_config
        self.splat_data = splat_data  # needed for build_character() to attach resources
        self.current_step = 0
        self.steps = []       # list of step names for this mode
        self.data = {}        # step_name -> allocations dict
        self.completed = set() # step indices that have been completed
```

The `wod_core.chargen()` function creates a `ChargenState`, then loops through steps using `renpy.call_screen()`. Each screen receives the state and returns an action (next, back, cancel, confirm, or jump-to-step-N).

**Save/load:** `ChargenState` must be picklable. It stores `splat_id` (string) rather than direct references to unpicklable objects. On unpickle, `schema` and `splat_data` are reloaded from the `splat_id`.

### Screen Contracts

Each screen receives `state` (ChargenState) and returns an action dict:

| Screen | Parameters | Returns |
|---|---|---|
| `chargen_identity(state)` | | `{"action": "next", "identity": {"name": "...", "tradition": "...", ...}}` |
| `chargen_priority(state, category)` | `category`: "attributes" or "abilities" | `{"action": "next", "priorities": {"physical": 7, "social": 5, "mental": 3}}` |
| `chargen_allocate(state, category, groups)` | `groups`: dict of group_name -> dot_pool | `{"action": "next", "allocations": {"Strength": 3, ...}}` |
| `chargen_spheres_backgrounds(state)` | | `{"action": "next", "spheres": {...}, "backgrounds": {...}}` |
| `chargen_freebies(state)` | | `{"action": "next", "freebie_allocations": {...}, "merits": [...], "flaws": [...]}` |
| `chargen_review(state)` | | `{"action": "confirm"}` or `{"action": "goto", "step": N}` |
| `chargen_template_pick(state)` | | `{"action": "next", "tradition": "...", "template_file": "..."}` |

All screens can also return `{"action": "back"}` or `{"action": "cancel"}`.

## Section 6: build_character()

`build_character()` converts the final `ChargenState` into a `Character` object:

1. Flatten all trait allocations into a single dict
2. Create `Character(schema=..., traits=..., merits_flaws=..., identity=...)`
3. Attach `ResourceManager` from `splat_data.resource_config`
4. Set starting resource values (Willpower from chargen, Quintessence from config)
5. Return the Character

This mirrors `SplatLoader.load_character()` but builds from chargen state instead of a YAML file.

## Section 7: Chargen Data File

```yaml
# game/splats/mage/chargen.yaml
modes:
  full:
    steps: [identity, attribute_priority, attribute_allocate, ability_priority, ability_allocate, spheres_backgrounds, freebies, review]
    attribute_priorities: [7, 5, 3]
    ability_priorities: [13, 9, 5]
    ability_max_at_creation: 3
    sphere_dots: 6
    background_dots: 7
    freebie_points: 15
    starting_arete: 1
    freebie_costs:
      attribute: 5
      ability: 2
      sphere: 7
      background: 1
      willpower: 1
      # Merits cost their listed point value, not a flat rate

  simplified:
    steps: [identity, attributes, abilities, spheres, review]
    attribute_dots: 15   # allocatable dots ON TOP of the free 1 per Attribute (total: 24)
    ability_dots: 27     # allocatable dots (Abilities start at 0)
    sphere_dots: 6
    starting_arete: 1

  template:
    steps: [identity, template_pick, review]

traditions:
  - id: akashic_brotherhood
    name: "Akashic Brotherhood"
    affinity_sphere: Mind
    free_sphere_dot: Mind
    templates:
      - name: "Martial Mystic"
        description: "Mind and Life focused — inner perfection through physical mastery"
        file: templates/akashic_martial.yaml
      - name: "Dream Walker"
        description: "Mind and Spirit focused — astral explorer and mediator"
        file: templates/akashic_dream.yaml

  - id: celestial_chorus
    name: "Celestial Chorus"
    affinity_sphere: Prime
    free_sphere_dot: Prime
    templates:
      - name: "Sacred Singer"
        description: "Prime and Forces — channel divine power through prayer and song"
        file: templates/cc_sacred_singer.yaml

  - id: cult_of_ecstasy
    name: "Cult of Ecstasy"
    affinity_sphere: Time
    free_sphere_dot: Time
    templates:
      - name: "Temporal Dancer"
        description: "Time and Life — ride the flow of experience to alter reality"
        file: templates/coe_temporal_dancer.yaml

  - id: dreamspeakers
    name: "Dreamspeakers"
    affinity_sphere: Spirit
    free_sphere_dot: Spirit
    templates:
      - name: "Spirit Walker"
        description: "Spirit and Life — bridge the Gauntlet and commune with the unseen"
        file: templates/ds_spirit_walker.yaml

  - id: euthanatos
    name: "Euthanatos"
    affinity_sphere: Entropy
    free_sphere_dot: Entropy
    templates:
      - name: "Fate Weaver"
        description: "Entropy and Life — shepherd the cycle of death and rebirth"
        file: templates/euth_fate_weaver.yaml

  - id: order_of_hermes
    name: "Order of Hermes"
    affinity_sphere: Forces
    free_sphere_dot: Forces
    templates:
      - name: "Hermetic Scholar"
        description: "Forces and Prime — classical magick through rigorous study"
        file: templates/ooh_hermetic_scholar.yaml

  - id: sons_of_ether
    name: "Sons of Ether"
    affinity_sphere: Matter
    free_sphere_dot: Matter
    templates:
      - name: "Mad Scientist"
        description: "Matter and Forces — reshape the world through SCIENCE!"
        file: templates/soe_mad_scientist.yaml

  - id: verbena
    name: "Verbena"
    affinity_sphere: Life
    free_sphere_dot: Life
    templates:
      - name: "Blood Witch"
        description: "Life and Prime — the old ways of blood and growing things"
        file: templates/verb_blood_witch.yaml

  - id: virtual_adepts
    name: "Virtual Adepts"
    affinity_sphere: Correspondence
    free_sphere_dot: Correspondence
    templates:
      - name: "Code Witch"
        description: "Correspondence and Mind — network infiltration and digital espionage"
        file: templates/va_code_witch.yaml
      - name: "Reality Hacker"
        description: "Correspondence and Forces — reshape the physical through the digital"
        file: templates/va_reality_hacker.yaml

# Curated subset of M20 Archetypes
archetypes:
  - Architect
  - Bon Vivant
  - Bravo
  - Caregiver
  - Celebrant
  - Competitor
  - Conformist
  - Conniver
  - Curmudgeon
  - Deviant
  - Director
  - Gallant
  - Idealist
  - Judge
  - Loner
  - Martyr
  - Pedagogue
  - Penitent
  - Perfectionist
  - Rebel
  - Rogue
  - Survivor
  - Thrill-Seeker
  - Traditionalist
  - Trickster
  - Visionary

essences:
  - Dynamic
  - Pattern
  - Primordial
  - Questing

# Merits and Flaws available during chargen
merits:
  - { name: "Avatar Companion", cost: 3, description: "Your Avatar manifests as a companion" }
  - { name: "Legendary Attribute", cost: 5, description: "One Attribute can be raised to 6" }
  - { name: "Natural Channel", cost: 3, description: "Quintessence flows easily to you" }

flaws:
  - { name: "Blind", cost: -6, description: "You cannot see" }
  - { name: "Nightmares", cost: -1, description: "Disturbing dreams plague your sleep" }
  - { name: "Sphere Inept", cost: -5, description: "One Sphere is extremely difficult for you" }
```

Template character files use the standard character YAML format (same as `elena.yaml`), loadable by the existing `SplatLoader.load_character()`. Only a few templates are created initially — authors add more.

## Section 8: Manifest & Loader Changes

Add `chargen` key to `manifest.yaml`:

```yaml
# splats/mage/manifest.yaml (addition)
splat:
  # ... existing fields ...
  chargen: chargen.yaml
```

Extend `SplatData` and `SplatLoader.load_splat()` to load chargen config:

```python
@dataclass
class SplatData:
    splat_id: str
    schema: Schema
    resource_config: dict
    manifest: dict
    templates_dir: str
    chargen_config: dict | None = None  # new field
```

The `chargen()` function accesses `splat_data.chargen_config` via the loaded splat.

## Section 9: Implementation Architecture

```
game/
├── wod_core/
│   ├── chargen.py              # ChargenState, point pool logic, build_character()
│   ├── loader.py               # Extend: load chargen.yaml from manifest
│   └── __init__.py             # Add chargen() function
├── wod_screens/
│   └── chargen.rpy             # All chargen screens
└── splats/
    └── mage/
        ├── manifest.yaml       # Add chargen key
        ├── chargen.yaml        # Modes, Traditions, Archetypes, Merits/Flaws
        └── templates/          # Pre-built template characters
            ├── default_mage.yaml   (existing)
            ├── archmage.yaml       (existing)
            ├── va_code_witch.yaml
            ├── va_reality_hacker.yaml
            └── ... (one per template defined in chargen.yaml)
tests/
└── test_chargen.py             # ChargenState, point pools, build_character()
```

## Section 10: Testing Strategy

1. **pytest** for `chargen.py`:
   - ChargenState initialization per mode (correct steps list)
   - Point pool tracking (allocate, deallocate, remaining, enforce max)
   - Priority assignment validation
   - Freebie spending at correct costs
   - Invalidation rules (change priority → allocation cleared)
   - `build_character()` produces valid Character with ResourceManager attached
   - Template loading via existing SplatLoader
   - Chargen config loading from manifest

2. **Ren'Py lint** — verify all chargen screens parse correctly

3. **Manual verification:**
   - Each mode's full flow (forward through all steps, confirm)
   - Back navigation preserves state
   - Invalidation clears correct steps
   - Cancel returns None
   - Point pools enforce limits (can't over-allocate)
   - Freebie costs are correct
   - Template mode loads correct pre-built characters
   - Resulting Character works with gate(), spend(), show_hud()
