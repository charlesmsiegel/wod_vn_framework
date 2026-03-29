# Ren'Py Bootstrap (Phase 2a) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Get the WoD VN framework running inside Ren'Py with a playable demo scene that proves the core engine works end-to-end.

**Architecture:** Copy Ren'Py's default GUI template files, apply dark color tweaks, add framework init (wod_init.rpy), and write a demo script that exercises stat gating, resource spending, linked pool constraints, and mid-story stat changes.

**Tech Stack:** Ren'Py 8.3.7, Python 3, PyYAML (bundled with Ren'Py)

**Spec:** `docs/superpowers/specs/2026-03-28-renpy-bootstrap-design.md`

**Ren'Py SDK:** `/home/janothar/renpy-8.3.7-sdk/`

**Lint command:** `/home/janothar/renpy-8.3.7-sdk/renpy.sh /home/janothar/wod_vn_framework/game lint`

**NOTE:** Ren'Py `.rpy` files cannot be tested with pytest. The testing strategy is Ren'Py lint (automated) + manual playthrough. The existing pytest suite (91 tests) validates the Python engine and should continue to pass throughout.

---

## File Map

| File | Responsibility |
|------|---------------|
| `game/wod_init.rpy` | Framework bootstrap at init -10 (imports wod_core, loads splats) |
| `game/options.rpy` | Game title, version, resolution, sound config |
| `game/gui.rpy` | GUI variables — copied from SDK template, colors tweaked to dark neutral |
| `game/screens.rpy` | All required Ren'Py screens — copied from SDK template as-is |
| `game/guisupport.rpy` | GUI image auto-generation — copied from SDK template |
| `game/gui/` | GUI image assets — copied from SDK template |
| `game/script.rpy` | Demo scene: Elena vs. Technocratic ward |
| `game/demo/elena.yaml` | Pre-built demo character YAML |

---

### Task 1: Copy Ren'Py Template Files

**Files:**
- Create: `game/gui.rpy` (copied from SDK template)
- Create: `game/screens.rpy` (copied from SDK template)
- Create: `game/guisupport.rpy` (copied from SDK template — auto-generates GUI images)
- Create: `game/gui/` (copied from SDK template)

- [ ] **Step 1: Copy gui.rpy, screens.rpy, guisupport.rpy, and gui/ from SDK template**

```bash
cp /home/janothar/renpy-8.3.7-sdk/gui/game/gui.rpy /home/janothar/wod_vn_framework/game/gui.rpy
cp /home/janothar/renpy-8.3.7-sdk/gui/game/screens.rpy /home/janothar/wod_vn_framework/game/screens.rpy
cp /home/janothar/renpy-8.3.7-sdk/gui/game/guisupport.rpy /home/janothar/wod_vn_framework/game/guisupport.rpy
cp -r /home/janothar/renpy-8.3.7-sdk/gui/game/gui/* /home/janothar/wod_vn_framework/game/gui/
```

- [ ] **Step 2: Apply resolution and dark color scheme to gui.rpy**

Edit `game/gui.rpy`. First, change the resolution:

| Variable | Old Value | New Value |
|----------|-----------|-----------|
| `gui.init(1280, 720)` | `gui.init(1280, 720)` | `gui.init(1920, 1080)` |

Then edit these color variables:

| Variable | Old Value | New Value |
|----------|-----------|-----------|
| `gui.accent_color` | `"#00b8c3"` | `"#c9a96e"` |
| `gui.idle_color` | `"#888888"` | `"#888888"` (keep) |
| `gui.selected_color` | `"#ffffff"` | `"#ffffff"` (keep) |
| `gui.insensitive_color` | `"#55555580"` | `"#55555580"` (keep) |
| `gui.muted_color` | `"#004e49"` | `"#2a2a3e"` |
| `gui.hover_muted_color` | `"#006e75"` | `"#3a3a52"` |
| `gui.text_color` | `"#ffffff"` | `"#e0e0e0"` |
| `gui.interface_text_color` | `"#ffffff"` | `"#e0e0e0"` |

The `gui.hover_color` is derived from `gui.accent_color` via `Color(gui.accent_color).tint(.6)`, so it updates automatically.

- [ ] **Step 3: Run Ren'Py lint**

```bash
/home/janothar/renpy-8.3.7-sdk/renpy.sh /home/janothar/wod_vn_framework/game lint
```

Expected: Clean lint (warnings about missing `label start` are OK at this stage)

- [ ] **Step 4: Run pytest to ensure core engine still passes**

```bash
cd /home/janothar/wod_vn_framework && pytest -v
```

Expected: All existing tests PASS

- [ ] **Step 5: Commit**

```bash
git add game/gui.rpy game/screens.rpy game/guisupport.rpy game/gui/
git commit -m "chore: add Ren'Py default GUI template with dark color scheme"
```

---

### Task 2: Create options.rpy

**Files:**
- Create: `game/options.rpy`

- [ ] **Step 1: Create options.rpy**

```renpy
## game/options.rpy
## Game configuration for the WoD VN Framework Demo.

## Game identity
define config.name = _("WoD VN Framework Demo")
define config.version = "0.1.0"
define build.name = "wod_vn_demo"

## Show title on main menu
define gui.show_name = True

## About text
define gui.about = _p("""
World of Darkness Visual Novel Framework Demo

A Ren'Py framework for building World of Darkness visual novels.
Targeting Mage: The Ascension (M20).
""")

## Sound — disabled for demo
define config.has_sound = False
define config.has_music = False
define config.has_voice = False

## No main menu music
define config.main_menu_music = None

## Save directory — unique per game
define config.save_directory = "wod_vn_demo-1714000000"

## Build configuration
init python:
    build.classify("game/**.rpy", None)
    build.classify("game/**.rpyc", "archive")
    build.classify("game/demo/**", "archive")
    build.classify("game/splats/**", "archive")
```

- [ ] **Step 2: Run Ren'Py lint**

```bash
/home/janothar/renpy-8.3.7-sdk/renpy.sh /home/janothar/wod_vn_framework/game lint
```

Expected: Clean lint

- [ ] **Step 3: Commit**

```bash
git add game/options.rpy
git commit -m "feat: add options.rpy with game config and display settings"
```

---

### Task 3: Create wod_init.rpy

**Files:**
- Create: `game/wod_init.rpy`

- [ ] **Step 1: Create wod_init.rpy**

```renpy
## game/wod_init.rpy
## WoD VN Framework — Ren'Py integration bootstrap.
## Loads the core engine and all splat packs at init time.

init -10 python:
    import wod_core

    # renpy.config.gamedir is the absolute path to game/
    wod_core.init(renpy.config.gamedir)

    # Discover and load all splat packs
    splats = wod_core.get_loader().discover_splats()
    if not splats:
        raise Exception(
            "WoD Framework: No splats found in game/splats/. "
            "Check your installation."
        )
    wod_core.load_all_splats()
```

- [ ] **Step 2: Run Ren'Py lint**

```bash
/home/janothar/renpy-8.3.7-sdk/renpy.sh /home/janothar/wod_vn_framework/game lint
```

Expected: Clean lint. The framework init should succeed — it will find and load the `mage` splat from `game/splats/mage/`.

- [ ] **Step 3: Run pytest to verify core engine still passes**

```bash
cd /home/janothar/wod_vn_framework && pytest -v
```

Expected: All existing tests PASS

- [ ] **Step 4: Commit**

```bash
git add game/wod_init.rpy
git commit -m "feat: wod_init.rpy — framework bootstrap at Ren'Py init time"
```

---

### Task 4: Create Demo Character

**Files:**
- Create: `game/demo/elena.yaml`

- [ ] **Step 1: Create demo directory and character file**

```bash
mkdir -p /home/janothar/wod_vn_framework/game/demo
```

```yaml
# game/demo/elena.yaml
# Demo character: Elena Vasquez, Virtual Adept
# Forces 3, Prime 2, Technology 3, Awareness 2 — all demo branches are reachable.
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

- [ ] **Step 2: Verify the character loads correctly with a quick pytest**

```python
# Run inline — not a permanent test file, just verification
cd /home/janothar/wod_vn_framework && python -c "
import sys; sys.path.insert(0, 'game')
import wod_core
wod_core.init('game')
wod_core.load_splat('mage')
pc = wod_core.load_character('demo/elena.yaml')
assert pc.get('Forces') == 3
assert pc.get('Prime') == 2
assert pc.get('Technology') == 3
assert pc.get('Awareness') == 2
assert pc.resources.current('quintessence') == 5
assert pc.has('Avatar Companion')
print('Elena loaded successfully — all stats verified.')
"
```

Expected: `Elena loaded successfully — all stats verified.`

- [ ] **Step 3: Commit**

```bash
git add game/demo/elena.yaml
git commit -m "feat: demo character Elena Vasquez (Virtual Adept)"
```

---

### Task 5: Create Demo Script

**Files:**
- Create: `game/script.rpy`

- [ ] **Step 1: Create script.rpy**

```renpy
## game/script.rpy
## WoD VN Framework Demo — Elena vs. the Technocratic Ward

## Declare Elena's character for dialogue
define elena = Character("Elena", color="#c9a96e")

## Declare pc variable for save/load compatibility
default pc = None


label start:

    ## Load the demo character
    $ pc = wod_core.load_character("demo/elena.yaml")
    $ wod_core.set_active(pc)

    scene black with fade

    "The server room hums with cold fluorescence. Rows of black monoliths blink in the dark."

    elena "There it is. The ward."

    "You can feel it — a Technocratic Pattern woven into the network's firmware. It pulses with rigid, static Resonance."

    "Your Avatar stirs. There are several ways to approach this."

    menu ward_choice:
        "Analyze the ward's Pattern" if pc.gate("Forces", ">=", 3) and pc.gate("Prime", ">=", 2):
            jump analyze_ward

        "Brute-force the encryption" if pc.gate("Technology", ">=", 3):
            jump brute_force

        "Observe the pattern carefully" if pc.gate("Awareness", ">=", 2):
            jump observe

        "This is beyond me. Leave.":
            jump leave


label analyze_ward:

    elena "I can see the threads. Forces and Prime, woven together. I can unravel this."

    "You reach out with your Avatar, channeling Quintessence into the Pattern."

    $ success = pc.spend("quintessence", 3)

    if success:
        "Three points of Quintessence flow from you into the ward. The rigid Pattern begins to dissolve."

        if pc.gate("Forces", ">=", 3):
            "Your understanding of Forces lets you unravel the energy matrix cleanly."
            "But the Consensus pushes back. The ward was {i}expected{/i} to be there."
            $ pc.gain("paradox", 2)
            "You feel Paradox settle into your Pattern like static on a screen."
            elena "Done. But the Consensus noticed. [pc.resources.current('paradox')] points of Paradox."
            elena "And my Quintessence is down to [pc.resources.current('quintessence')]."
        else:
            "You manage to disrupt the ward, but the unraveling is rough."
            $ pc.gain("paradox", 4)
            elena "Sloppy. Too much Paradox."
    else:
        elena "Not enough Quintessence. I need to find another way."
        jump ward_choice

    jump epilogue


label brute_force:

    elena "I don't need magick for this. Good old-fashioned hacking."

    "Your fingers fly across the keyboard. Technology [pc.get('Technology')], don't fail me now."

    "The encryption is military-grade, but you know Technocratic patterns."

    if pc.gate("Science", ">=", 4):
        "Your deep understanding of the underlying Science lets you find a flaw in the algorithm."
        elena "There. Buffer overflow in the authentication layer. Classic."
        "You slip past the ward without triggering it. No Paradox. No trace."
    else:
        "You crack the outer layer, but the ward's core remains intact."
        elena "Partial access. Better than nothing, but they'll know someone was here."

    jump epilogue


label observe:

    elena "Let me watch it for a moment. There's always a pattern within the Pattern."

    "You quiet your mind and let your Awareness expand."

    "The ward pulses. Every seven seconds, there's a gap — a brief moment where the Pattern thins."

    "Your understanding deepens. You feel your Awareness sharpen."

    $ pc.advance("Awareness")

    elena "Awareness advanced to [pc.get('Awareness')]. I can see more clearly now."

    "With this new insight, you could try a more direct approach."

    menu:
        "Analyze the ward now" if pc.gate("Forces", ">=", 3) and pc.gate("Prime", ">=", 2):
            jump analyze_ward

        "Try the brute-force approach" if pc.gate("Technology", ">=", 3):
            jump brute_force

        "I've learned what I can. Time to go.":
            jump leave


label leave:

    elena "Not today. I'll be back when I'm ready."

    "You shut down your terminal and walk away. The ward continues to pulse, undisturbed."

    "Sometimes discretion is the better part of valor."

    jump epilogue


label epilogue:

    scene black with fade

    "— End of Demo —"

    "This demo exercised the WoD VN Framework's core features:"
    "  - Character loading from YAML"
    "  - Stat-gated menu choices (Forces, Prime, Technology, Awareness)"
    "  - Resource spending (Quintessence)"
    "  - Linked pool constraints (Paradox gain)"
    "  - Outcome branching based on stat levels"
    "  - Mid-story stat advancement (Awareness)"

    if pc is not None:
        "Final character state:"
        "  Quintessence: [pc.resources.current('quintessence')]"
        "  Paradox: [pc.resources.current('paradox')]"
        "  Awareness: [pc.get('Awareness')]"

    return
```

- [ ] **Step 2: Run Ren'Py lint**

```bash
/home/janothar/renpy-8.3.7-sdk/renpy.sh /home/janothar/wod_vn_framework/game lint
```

Expected: Clean lint with no errors. There may be warnings about missing image files (`bg room`, etc.) — these are acceptable for a demo without art assets.

- [ ] **Step 3: Run pytest to verify core engine still passes**

```bash
cd /home/janothar/wod_vn_framework && pytest -v
```

Expected: All existing tests PASS

- [ ] **Step 4: Commit**

```bash
git add game/script.rpy
git commit -m "feat: demo script — Elena vs. the Technocratic Ward"
```

---

### Task 6: Lint Verification & Final Check

**Files:**
- No new files — verification only

- [ ] **Step 1: Run full Ren'Py lint**

```bash
/home/janothar/renpy-8.3.7-sdk/renpy.sh /home/janothar/wod_vn_framework/game lint
```

Expected: Clean lint. Framework initializes, splats load, all labels reachable, no undefined references.

- [ ] **Step 2: Run full pytest suite**

```bash
cd /home/janothar/wod_vn_framework && pytest -v
```

Expected: All tests PASS (existing 91 + no regressions)

- [ ] **Step 3: Verify all demo paths are reachable**

Check Elena's stats against the gating conditions:
- `[Forces >= 3, Prime >= 2]` — Elena has Forces 3, Prime 2 → REACHABLE
- `[Technology >= 3]` — Elena has Technology 3 → REACHABLE
- `[Awareness >= 2]` — Elena has Awareness 2 → REACHABLE
- `"This is beyond me"` — always available
- After observe: `[Forces >= 3, Prime >= 2]` still reachable, `[Technology >= 3]` still reachable

- [ ] **Step 4: Commit any lint fixes if needed**

```bash
git add -A
git commit -m "fix: address any lint warnings" # only if changes were needed
```

---

## Deferred to Phase 2b

- Character sheet screen
- Resource HUD overlay
- Chargen screens + `chargen.py`
- Gothic theme (custom images, fonts)
- Toast notifications
- `show_hud()` / `hide_hud()`
- Bracket shorthand pre-processor / CDS registration
- `__getstate__`/`__setstate__` for Character serialization optimization
