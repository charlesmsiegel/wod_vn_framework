# HUD & Character Sheet (Phase 2b-1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a persistent resource HUD (top bar with Quintessence/Paradox split bar, Willpower, Health) and a tabbed character sheet overlay to the WoD VN framework.

**Architecture:** Two Ren'Py screens (`resource_hud.rpy`, `character_sheet.rpy`) that read from the existing `wod_core` engine. Small engine changes: `CategoryDef` stores group structure, loader fixes Willpower max, `__init__.py` adds `show_hud()`/`hide_hud()`. Manifest extended with tab mapping config.

**Tech Stack:** Ren'Py 8.3.7, Python 3, existing wod_core engine

**Spec:** `docs/superpowers/specs/2026-03-29-hud-character-sheet-design.md`

**Ren'Py SDK:** `/home/janothar/renpy-8.3.7-sdk/`

**Lint command:** `/home/janothar/renpy-8.3.7-sdk/renpy.sh /home/janothar/wod_vn_framework/game lint`

---

## File Map

| File | Responsibility |
|------|---------------|
| `game/wod_core/engine.py` | Add `self.groups` to `CategoryDef` |
| `game/wod_core/loader.py` | Fix: resource override updates max when current > max |
| `game/wod_core/__init__.py` | Add `show_hud()` / `hide_hud()` |
| `game/wod_screens/resource_hud.rpy` | HUD top bar screen |
| `game/wod_screens/character_sheet.rpy` | Tabbed character sheet overlay |
| `game/wod_init.rpy` | Add `after_load` label for HUD persistence |
| `game/script.rpy` | Add `show_hud()` call to demo |
| `game/splats/mage/manifest.yaml` | Add `character_sheet.tabs` config |
| `tests/test_engine.py` | Test CategoryDef groups |
| `tests/test_loader.py` | Test Willpower max fix |

---

### Task 1: CategoryDef Groups

**Files:**
- Modify: `game/wod_core/engine.py`
- Modify: `tests/test_engine.py`

- [ ] **Step 1: Write failing test for CategoryDef.groups**

Append to `tests/test_engine.py`:

```python
class TestCategoryDefGroups:
    """Test that CategoryDef preserves group structure."""

    def test_groups_stored_when_present(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        attrs = schema.categories["attributes"]
        assert attrs.groups is not None
        assert "physical" in attrs.groups
        assert attrs.groups["physical"] == ["Strength", "Dexterity", "Stamina"]
        assert attrs.groups["social"] == ["Charisma", "Manipulation", "Appearance"]
        assert attrs.groups["mental"] == ["Perception", "Intelligence", "Wits"]

    def test_groups_none_for_flat_traits(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        spheres = schema.categories["spheres"]
        assert spheres.groups is None

    def test_trait_names_still_flat(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        attrs = schema.categories["attributes"]
        assert len(attrs.trait_names) == 9
        assert "Strength" in attrs.trait_names
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/janothar/wod_vn_framework && pytest tests/test_engine.py::TestCategoryDefGroups -v`
Expected: FAIL — `AttributeError: 'CategoryDef' object has no attribute 'groups'`

- [ ] **Step 3: Implement CategoryDef.groups**

In `game/wod_core/engine.py`, replace the `CategoryDef.__init__` body:

```python
class CategoryDef:
    """A trait category parsed from schema YAML."""

    def __init__(self, name: str, data: dict):
        self.name = name
        self.display_name = data.get("display_name", name)
        self.range = tuple(data.get("range", [0, 5]))
        self.default = data.get("default", 0)
        self.trait_names: list[str] = []
        self.groups: dict[str, list[str]] | None = None

        if "groups" in data:
            self.groups = {}
            for group_name, traits in data["groups"].items():
                self.groups[group_name] = list(traits)
                self.trait_names.extend(traits)
        elif "traits" in data:
            self.trait_names = list(data["traits"])
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/janothar/wod_vn_framework && pytest -v`
Expected: All tests PASS (existing + 3 new)

- [ ] **Step 5: Commit**

```bash
git add game/wod_core/engine.py tests/test_engine.py
git commit -m "feat: CategoryDef preserves group structure for UI rendering"
```

---

### Task 2: Loader Willpower Max Fix

**Files:**
- Modify: `game/wod_core/loader.py`
- Modify: `tests/test_loader.py`

- [ ] **Step 1: Write failing test**

Append to `tests/test_loader.py`:

```python
class TestResourceMaxFix:
    """Test that resource overrides update max when current > max."""

    def test_willpower_override_updates_max(self, tmp_path):
        char_yaml = tmp_path / "wp_test.yaml"
        char_yaml.write_text("""
schema: mage
template: default_mage
character_type: pc
identity:
  name: "WP Test"
traits:
  arete:
    Arete: 1
resources:
  willpower: 8
merits_flaws: []
""")
        loader = SplatLoader(GAME_DIR)
        loader.load_splat("mage")
        char = loader.load_character(str(char_yaml))

        assert char.resources.current("willpower") == 8
        assert char.resources.pools["willpower"].max == 8
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/janothar/wod_vn_framework && pytest tests/test_loader.py::TestResourceMaxFix -v`
Expected: FAIL — `assert 5 == 8` (max stays at default 5)

- [ ] **Step 3: Fix loader**

In `game/wod_core/loader.py`, update the resource override loop:

```python
        # Apply character-specific resource overrides
        for res_name, res_value in char_data.get("resources", {}).items():
            if char.resources.has_resource(res_name) and isinstance(res_value, int):
                pool = char.resources.pools[res_name]
                pool.current_value = res_value
                if res_value > pool.max:
                    pool.max = res_value
```

- [ ] **Step 4: Run tests**

Run: `cd /home/janothar/wod_vn_framework && pytest -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add game/wod_core/loader.py tests/test_loader.py
git commit -m "fix: resource override updates max when current exceeds it"
```

---

### Task 3: show_hud() / hide_hud() API + Manifest Tab Config

**Files:**
- Modify: `game/wod_core/__init__.py`
- Modify: `game/splats/mage/manifest.yaml`

- [ ] **Step 1: Add show_hud/hide_hud to __init__.py**

Append to `game/wod_core/__init__.py`:

```python
def show_hud(resources=None):
    """Show the resource HUD. Call from within Ren'Py only."""
    import renpy
    renpy.store.wod_hud_visible = True
    renpy.store.wod_hud_resources = resources
    renpy.show_screen("resource_hud")


def hide_hud():
    """Hide the resource HUD. Call from within Ren'Py only."""
    import renpy
    renpy.store.wod_hud_visible = False
    renpy.store.wod_hud_resources = None
    renpy.hide_screen("resource_hud")
```

- [ ] **Step 2: Add character_sheet tabs config to manifest.yaml**

Add to `game/splats/mage/manifest.yaml`:

```yaml
splat:
  id: mage
  display_name: "Mage: The Ascension"
  edition: "M20"
  version: "1.0"
  schema: schema.yaml
  resources: resources.yaml
  templates_dir: templates/
  screens:
    character_sheet: null
    chargen_steps:
      - identity
      - attributes
      - abilities
      - spheres
      - backgrounds
      - merits_flaws
      - review
  character_sheet:
    tabs:
      - name: "Attributes & Abilities"
        categories: [attributes, abilities]
      - name: "Spheres & Backgrounds"
        categories: [arete, spheres, backgrounds]
      - name: "Merits & Resources"
        categories: []
```

- [ ] **Step 3: Run pytest + lint**

```bash
cd /home/janothar/wod_vn_framework && pytest -v
/home/janothar/renpy-8.3.7-sdk/renpy.sh /home/janothar/wod_vn_framework/game lint
```

Expected: All tests PASS, lint clean

- [ ] **Step 4: Commit**

```bash
git add game/wod_core/__init__.py game/splats/mage/manifest.yaml
git commit -m "feat: show_hud()/hide_hud() API and manifest character_sheet tab config"
```

---

### Task 4: Resource HUD Screen

**Files:**
- Create: `game/wod_screens/resource_hud.rpy`

- [ ] **Step 1: Create resource_hud.rpy**

```renpy
## game/wod_screens/resource_hud.rpy
## Persistent top bar showing resource pools during gameplay.

default wod_hud_visible = False
default wod_hud_resources = None

screen resource_hud():
    zorder 100
    layer "screens"

    $ pc = wod_core.get_active()
    $ res = pc.resources
    $ hud_resources = store.wod_hud_resources

    # Top bar frame
    frame:
        xfill True
        ysize 60
        xpos 0
        ypos 0
        background "#0d0d1aCC"
        padding (20, 8, 20, 8)

        hbox:
            spacing 30
            yalign 0.5

            # Quintessence/Paradox split bar
            if hud_resources is None or "quintessence" in hud_resources or "paradox" in hud_resources:
                $ quint = res.current("quintessence") if res.has_resource("quintessence") else 0
                $ paradox = res.current("paradox") if res.has_resource("paradox") else 0
                # Find combined max from resource links
                $ combined_max = 20
                for link in res.links:
                    if "quintessence" in link.pool_names and "paradox" in link.pool_names:
                        $ combined_max = link.combined_max

                vbox:
                    spacing 2
                    # Split bar
                    fixed:
                        xsize 300
                        ysize 16
                        # Background
                        bar:
                            value combined_max
                            range combined_max
                            xsize 300
                            ysize 16
                            left_bar "#333333"
                            right_bar "#333333"
                        # Quintessence (from left)
                        bar:
                            value quint
                            range combined_max
                            xsize 300
                            ysize 16
                            left_bar "#c9a96e"
                            right_bar "#00000000"
                        # Paradox (from right)
                        bar:
                            value paradox
                            range combined_max
                            xsize 300
                            ysize 16
                            right_bar "#8b4545"
                            left_bar "#00000000"
                            bar_invert True

                    hbox:
                        xsize 300
                        text "Qt: [quint]" size 12 color "#c9a96e"
                        xfill True
                        text "Pdx: [paradox]" size 12 color "#8b4545" xalign 1.0

            # Willpower bar
            if hud_resources is None or "willpower" in hud_resources:
                if res.has_resource("willpower"):
                    $ wp_cur = res.current("willpower")
                    $ wp_max = res.pools["willpower"].max
                    vbox:
                        spacing 2
                        bar:
                            value wp_cur
                            range wp_max
                            xsize 120
                            ysize 16
                            left_bar "#6a9ec9"
                            right_bar "#333333"
                        text "WP: [wp_cur]/[wp_max]" size 12 color "#6a9ec9"

            # Health track
            if hud_resources is None or "health" in hud_resources:
                if res.has_resource("health"):
                    $ hp_cur = res.current("health")
                    $ hp_max = res.pools["health"].max
                    $ hp_damaged = hp_max - hp_cur
                    vbox:
                        spacing 2
                        hbox:
                            spacing 3
                            for i in range(hp_max):
                                if i < hp_damaged:
                                    # Damaged box - filled red
                                    frame:
                                        xsize 14
                                        ysize 14
                                        background "#8b4545"
                                else:
                                    # Healthy box - empty outline
                                    frame:
                                        xsize 14
                                        ysize 14
                                        background "#333333"
                        text "Health" size 12 color "#5a8a5a"

            # Spacer pushes sheet button to the right
            null width 0 xfill True

            # Character sheet toggle button
            textbutton "[Sheet]":
                yalign 0.5
                text_size 14
                text_color "#c9a96e"
                text_hover_color "#e0c080"
                action ToggleScreen("character_sheet")

    # Keyboard shortcut for character sheet (active while HUD is shown)
    key "K_TAB" action ToggleScreen("character_sheet")
```

- [ ] **Step 2: Run Ren'Py lint**

```bash
/home/janothar/renpy-8.3.7-sdk/renpy.sh /home/janothar/wod_vn_framework/game lint
```

Expected: Clean lint (may have warnings about placeholder images, acceptable)

- [ ] **Step 3: Commit**

```bash
git add game/wod_screens/resource_hud.rpy
git commit -m "feat: resource HUD screen with Quintessence/Paradox split bar"
```

---

### Task 5: Character Sheet Screen

**Files:**
- Create: `game/wod_screens/character_sheet.rpy`

- [ ] **Step 1: Create character_sheet.rpy**

```renpy
## game/wod_screens/character_sheet.rpy
## Tabbed character sheet overlay — schema-driven, works for any splat.

screen character_sheet():
    modal True
    zorder 200
    default current_tab = 0

    $ pc = wod_core.get_active()
    $ schema = pc.schema
    $ splat_id = None
    $ splat_data = None

    # Find the splat data for tab config
    python:
        for sid, sd in wod_core.get_loader().loaded_splats.items():
            if sd.schema is schema:
                splat_id = sid
                splat_data = sd
                break

    # Get tab config from manifest, or auto-generate
    $ tab_config = []
    python:
        if splat_data and "character_sheet" in splat_data.manifest.get("splat", {}):
            tab_config = splat_data.manifest["splat"]["character_sheet"].get("tabs", [])
        if not tab_config:
            # Auto-generate: one tab per category
            for cat_name, cat_def in schema.categories.items():
                tab_config.append({"name": cat_def.display_name, "categories": [cat_name]})
            tab_config.append({"name": "Merits & Resources", "categories": []})

    # Dark overlay background
    frame:
        xfill True
        yfill True
        background "#000000AA"

        # Centered panel
        frame:
            xalign 0.5
            yalign 0.5
            xsize int(config.screen_width * 0.8)
            ysize int(config.screen_height * 0.85)
            background "#1a1a2eEE"
            padding (30, 20, 30, 20)

            vbox:
                spacing 10

                # Header: identity fields + close button
                hbox:
                    xfill True
                    # Identity
                    $ identity_parts = [str(v) for k, v in pc.identity.items() if v]
                    $ identity_text = " — ".join(identity_parts)
                    text "[identity_text]" size 24 color "#c9a96e"
                    # Close button
                    textbutton "✕":
                        xalign 1.0
                        text_size 24
                        text_color "#888888"
                        text_hover_color "#ffffff"
                        action Hide("character_sheet")

                # Tab buttons
                hbox:
                    spacing 10
                    for i, tab in enumerate(tab_config):
                        textbutton tab["name"]:
                            text_size 16
                            if i == current_tab:
                                text_color "#c9a96e"
                                text_underline True
                            else:
                                text_color "#888888"
                            action SetScreenVariable("current_tab", i)

                null height 10

                # Tab content - scrollable
                viewport:
                    scrollbars "vertical"
                    mousewheel True
                    xfill True
                    yfill True

                    vbox:
                        spacing 15
                        xfill True

                        if current_tab < len(tab_config):
                            $ tab = tab_config[current_tab]
                            $ cats = tab.get("categories", [])

                            if cats:
                                # Render trait categories with dot display
                                for cat_name in cats:
                                    if cat_name in schema.categories:
                                        $ cat = schema.categories[cat_name]
                                        text cat.display_name size 20 color "#c9a96e"
                                        null height 5

                                        if cat.groups is not None:
                                            # Grouped rendering
                                            for group_name, group_traits in cat.groups.items():
                                                text group_name.capitalize() size 14 color "#888888" italic True
                                                for trait_name in group_traits:
                                                    $ val = pc.get(trait_name)
                                                    $ max_val = cat.range[1]
                                                    if val > 0 or cat.default > 0:
                                                        hbox:
                                                            spacing 10
                                                            text trait_name size 14 color "#e0e0e0" min_width 200
                                                            # Dot display
                                                            hbox:
                                                                spacing 3
                                                                for d in range(max_val):
                                                                    if d < val:
                                                                        text "●" size 14 color "#c9a96e"
                                                                    else:
                                                                        text "○" size 14 color "#444444"
                                                null height 5
                                        else:
                                            # Flat trait list
                                            for trait_name in cat.trait_names:
                                                $ val = pc.get(trait_name)
                                                $ max_val = cat.range[1]
                                                if val > 0 or cat.default > 0:
                                                    hbox:
                                                        spacing 10
                                                        text trait_name size 14 color "#e0e0e0" min_width 200
                                                        hbox:
                                                            spacing 3
                                                            for d in range(max_val):
                                                                if d < val:
                                                                    text "●" size 14 color "#c9a96e"
                                                                else:
                                                                    text "○" size 14 color "#444444"
                                        null height 10
                            else:
                                # Merits & Resources tab (special)
                                # Merits/Flaws
                                if pc.merits_flaws:
                                    text "Merits & Flaws" size 20 color "#c9a96e"
                                    null height 5
                                    for mf in pc.merits_flaws:
                                        hbox:
                                            spacing 10
                                            text mf["name"] size 14 color "#e0e0e0"
                                            text "([mf.get('type', '')])" size 12 color "#888888"
                                            if "value" in mf:
                                                text str(mf["value"]) size 12 color "#888888"
                                    null height 10

                                # Resources
                                text "Resources" size 20 color "#c9a96e"
                                null height 5
                                $ res = pc.resources
                                if res is not None:
                                    for pool_name, pool in res.pools.items():
                                        hbox:
                                            spacing 10
                                            text pool.display_name size 14 color "#e0e0e0" min_width 200
                                            bar:
                                                value pool.current()
                                                range pool.max
                                                xsize 200
                                                ysize 14
                                                left_bar "#6a9ec9"
                                                right_bar "#333333"
                                            text "[pool.current()]/[pool.max]" size 12 color "#888888"

    # Close on Escape
    key "K_ESCAPE" action Hide("character_sheet")
    key "K_TAB" action Hide("character_sheet")
```

- [ ] **Step 2: Run Ren'Py lint**

```bash
/home/janothar/renpy-8.3.7-sdk/renpy.sh /home/janothar/wod_vn_framework/game lint
```

Expected: Clean lint

- [ ] **Step 3: Commit**

```bash
git add game/wod_screens/character_sheet.rpy
git commit -m "feat: tabbed character sheet overlay with WoD dot display"
```

---

### Task 6: Demo Integration + after_load

**Files:**
- Modify: `game/script.rpy`
- Modify: `game/wod_init.rpy`

- [ ] **Step 1: Add show_hud() to demo script**

In `game/script.rpy`, add after `$ wod_core.set_active(pc)`:

```renpy
    $ wod_core.show_hud()
```

- [ ] **Step 2: Add after_load label to wod_init.rpy**

Append to `game/wod_init.rpy`:

```renpy
label after_load:
    if store.wod_hud_visible:
        show screen resource_hud
    return
```

- [ ] **Step 3: Run lint + pytest**

```bash
/home/janothar/renpy-8.3.7-sdk/renpy.sh /home/janothar/wod_vn_framework/game lint
cd /home/janothar/wod_vn_framework && pytest -v
```

Expected: Clean lint, all tests PASS

- [ ] **Step 4: Commit**

```bash
git add game/script.rpy game/wod_init.rpy
git commit -m "feat: integrate HUD into demo script with after_load persistence"
```

---

### Task 7: Final Verification

- [ ] **Step 1: Full lint**

```bash
/home/janothar/renpy-8.3.7-sdk/renpy.sh /home/janothar/wod_vn_framework/game lint
```

- [ ] **Step 2: Full pytest**

```bash
cd /home/janothar/wod_vn_framework && pytest -v
```

- [ ] **Step 3: Verify screen list**

Lint should report resource_hud and character_sheet in the screen count (26 screens: 24 default + 2 new).
