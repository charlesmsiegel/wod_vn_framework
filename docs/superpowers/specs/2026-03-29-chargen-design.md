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

**What's deferred:**

- Gothic theme
- Toast notifications
- Bracket shorthand pre-processor

## Section 1: Author API

```renpy
label start:
    $ pc = wod_core.chargen("mage", mode="full")
    $ wod_core.set_active(pc)
    $ wod_core.show_hud()
    "Your journey begins..."
```

Three modes:

| Mode | Target Audience | Steps | Complexity |
|------|----------------|-------|-----------|
| `"full"` | Tabletop players | 7 steps with priority picks, freebie points | High |
| `"simplified"` | VN players | 5 steps with flat point pools | Medium |
| `"template"` | Quick start | 3 steps — pick Tradition, pick preset | Low |

Authors can also provide presets to partially fill in steps:

```renpy
$ pc = wod_core.chargen("mage", mode="simplified", preset={"tradition": "Virtual Adepts"})
```

## Section 2: Full M20 Mode

Faithful to M20 tabletop character creation.

### Step 1: Identity

Player enters:
- Name (text input)
- Tradition (pick from list — data-driven from `chargen.yaml`)
- Essence (Dynamic, Pattern, Primordial, Questing)
- Nature (pick from Archetype list)
- Demeanor (pick from Archetype list)

### Step 2: Attributes (Priority)

1. Player assigns priority to the three Attribute groups:
   - Primary (7 dots), Secondary (5 dots), Tertiary (3 dots)
   - Visual: three columns (Physical, Social, Mental), player drags/clicks to assign priority rank
2. Then allocates dots within each group using WoD dot display (click to fill/unfill)
3. All Attributes start at 1 (the free dot), dots are added on top

### Step 3: Abilities (Priority)

Same structure as Attributes:
1. Assign priority: Talents/Skills/Knowledges → 13/9/5 dots
2. Allocate dots within each group
3. Abilities start at 0, max 3 during creation (no ability above 3 without freebie points)

### Step 4: Spheres

- Allocate Sphere dots (starting pool defined in `chargen.yaml`, typically 6)
- Limited by starting Arete (typically 1, set by Tradition config)
- Tradition's affinity Sphere highlighted
- Some Traditions grant a free dot in their affinity Sphere (configured in `chargen.yaml`)

### Step 5: Backgrounds

- Allocate 7 dots across Backgrounds
- Available Backgrounds listed from schema
- Max 5 per Background

### Step 6: Merits & Flaws

- Pick from available Merits and Flaws (defined in `chargen.yaml`)
- Each has a point cost (Merits positive, Flaws negative)
- Net budget configurable by author (default: 7 points of Flaws max, Merits paid from freebies)
- Freebie points: 15 (M20 standard), spent on extra dots in any category at varying costs

### Step 7: Review & Confirm

- Full character sheet display (reuses the character sheet screen from 2b-1)
- "Go back to step N" buttons for each section
- "Confirm" creates the Character object and returns it

## Section 3: Simplified Mode

Faster creation for VN-focused games.

### Step 1: Identity

Same as Full mode but only Name and Tradition.

### Step 2: Attributes

- Flat pool of 15 dots across all 9 Attributes (no priority pick)
- All start at 1, allocate 6 additional dots (since 9 Attributes × 1 free = 9, plus 6 = 15 total)
- Max 5 per Attribute

### Step 3: Abilities

- Flat pool of 27 dots across all Abilities
- Max 5 per Ability

### Step 4: Spheres

- Same as Full mode step 4
- Pool size and Arete from `chargen.yaml`

### Step 5: Review & Confirm

- No Backgrounds, no Merits/Flaws (author can enable these via config)
- Same review screen as Full mode

## Section 4: Template Mode

Quickest path to a playable character.

### Step 1: Identity

Name only (text input).

### Step 2: Pick Tradition & Template

- Player picks a Tradition
- Then picks from 2-3 pre-built stat spreads for that Tradition
- Each template has a name and short description (e.g., "Combat Adept — Forces-focused bruiser", "Code Witch — Correspondence and Mind specialist")
- Templates defined in `chargen.yaml`

### Step 3: Review & Confirm

- Shows the full character from the template
- Player can change name but not stats
- Confirm creates the Character

## Section 5: Navigation

All modes support full back/forward navigation:

- **Step indicator** at the top shows all steps, current step highlighted, completed steps checkmarked
- **Back button** returns to previous step with all allocations preserved
- **Forward button** (or clicking a completed step) jumps ahead
- **State preservation:** Each step's allocations are stored in a chargen state dict. Going back and changing a step does NOT reset subsequent steps unless the change invalidates them (e.g., changing Attribute priority resets Attribute allocations but not Abilities)

### State Management

```python
# In chargen.py
class ChargenState:
    def __init__(self, splat_id: str, mode: str, schema, chargen_config):
        self.splat_id = splat_id
        self.mode = mode
        self.schema = schema
        self.config = chargen_config
        self.current_step = 0
        self.steps = []  # list of step names for this mode
        self.data = {}   # step_name -> allocations dict
```

The `wod_core.chargen()` function creates a `ChargenState`, then loops through steps using `renpy.call_screen()`. Each screen receives the state and returns an action (next, back, confirm).

## Section 6: Chargen Data File

```yaml
# game/splats/mage/chargen.yaml
modes:
  full:
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
      merit: 1

  simplified:
    attribute_dots: 15  # total across all 9 (including the free 1 each)
    ability_dots: 27
    sphere_dots: 6
    starting_arete: 1

  template:
    # Templates defined per Tradition below

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

  # ... remaining Traditions

archetypes:
  - Architect
  - Autocrat
  - Bon Vivant
  - Bravo
  - Caregiver
  - Celebrant
  - Child
  - Competitor
  - Conformist
  - Conniver
  - Curmudgeon
  - Deviant
  - Director
  - Fanatic
  - Gallant
  - Judge
  - Loner
  - Martyr
  - Masochist
  - Monster
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
```

Only the first few Traditions are defined initially. Authors add more by extending this file. Template character YAML files follow the existing character file format.

## Section 7: Implementation Architecture

```
game/
├── wod_core/
│   ├── chargen.py              # ChargenState, point pool logic, validation
│   └── __init__.py             # Add chargen() function
├── wod_screens/
│   └── chargen.rpy             # All chargen screens
└── splats/
    └── mage/
        ├── chargen.yaml        # Modes, Traditions, Archetypes, templates
        └── templates/          # Pre-built template characters (for template mode)
            ├── default_mage.yaml   (existing)
            ├── archmage.yaml       (existing)
            ├── va_code_witch.yaml
            └── va_reality_hacker.yaml
```

### chargen.py responsibilities:
- `ChargenState` class — tracks mode, current step, accumulated allocations
- Point pool validation — enforces maximums, tracks remaining dots
- `build_character()` — converts final ChargenState into a Character object
- Template loading — reads pre-built character YAML files

### chargen.rpy responsibilities:
- Step screens: `chargen_identity`, `chargen_attributes_priority`, `chargen_attributes_allocate`, `chargen_abilities_priority`, `chargen_abilities_allocate`, `chargen_spheres`, `chargen_backgrounds`, `chargen_merits_flaws`, `chargen_review`
- Simplified mode reuses allocate screens but skips priority screens
- Template mode has its own `chargen_template_pick` screen
- Navigation bar component shared across all steps
- WoD dot allocation widget (click to add/remove dots)

### chargen() function:
```python
def chargen(splat_id: str, mode: str = "full", preset: dict | None = None):
    # Load chargen config
    # Create ChargenState
    # Loop: call_screen for current step, handle back/next/confirm
    # On confirm: build_character() and return Character
```

## Section 8: Testing Strategy

1. **pytest** for `chargen.py`:
   - ChargenState initialization per mode
   - Point pool tracking (allocate, deallocate, remaining)
   - Validation (max per trait, total pool limits, Arete-Sphere constraint)
   - `build_character()` produces valid Character
   - Template loading

2. **Ren'Py lint** — verify all chargen screens parse correctly

3. **Manual verification:**
   - Each mode's full flow (forward through all steps, confirm)
   - Back navigation preserves state
   - Forward after going back preserves subsequent state
   - Point pools enforce limits (can't over-allocate)
   - Template mode loads correct pre-built characters
   - Resulting Character works with gate(), spend(), etc.
