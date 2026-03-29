# Gothic Theme Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the default Ren'Py look with a dark World of Darkness gothic aesthetic — custom colors, typography, textbox styling, and menu UI.

**Architecture:** Override `gui.rpy` color variables, add a gothic-appropriate free font, restyle the textbox/choice screens via `screens.rpy` modifications, and add dark background images for main menu and game menus. No structural changes to the framework code — purely visual.

**Tech Stack:** Ren'Py 8.3.7, free gothic/serif fonts, image editing

**Ren'Py SDK:** `/home/janothar/renpy-8.3.7-sdk/`

---

## File Map

| File | Responsibility |
|------|---------------|
| `game/gui.rpy` | Color palette, font assignments, sizing overrides |
| `game/gui/fonts/` | Gothic/serif font files (OFL-licensed) |
| `game/gui/overlay/main_menu.png` | Dark atmospheric main menu background |
| `game/gui/overlay/game_menu.png` | Dark game menu overlay |
| `game/gui/textbox.png` | Semi-transparent dark textbox background |
| `game/screens.rpy` | Minor screen layout tweaks if needed |

---

### Task 1: Download and Install Gothic Font

**Files:**
- Create: `game/gui/fonts/` (font files)
- Modify: `game/gui.rpy`

- [ ] **Step 1: Download a free gothic/serif font**

Use **EB Garamond** (OFL license, available on Google Fonts) for body text and **Cinzel** for headings/character names. Both are freely licensed.

```bash
mkdir -p /home/janothar/wod_vn_framework/game/gui/fonts
cd /home/janothar/wod_vn_framework/game/gui/fonts

# Download EB Garamond (body text)
curl -sL "https://github.com/google/fonts/raw/main/ofl/ebgaramond/EBGaramond-Regular.ttf" -o EBGaramond-Regular.ttf
curl -sL "https://github.com/google/fonts/raw/main/ofl/ebgaramond/EBGaramond-Italic.ttf" -o EBGaramond-Italic.ttf
curl -sL "https://github.com/google/fonts/raw/main/ofl/ebgaramond/EBGaramond-Bold.ttf" -o EBGaramond-Bold.ttf

# Download Cinzel (headings)
curl -sL "https://github.com/google/fonts/raw/main/ofl/cinzel/Cinzel-Regular.ttf" -o Cinzel-Regular.ttf
curl -sL "https://github.com/google/fonts/raw/main/ofl/cinzel/Cinzel-Bold.ttf" -o Cinzel-Bold.ttf
```

- [ ] **Step 2: Update gui.rpy font assignments**

Edit `game/gui.rpy` — find the font definition lines and change:

```renpy
define gui.text_font = "gui/fonts/EBGaramond-Regular.ttf"
define gui.name_text_font = "gui/fonts/Cinzel-Regular.ttf"
define gui.interface_text_font = "gui/fonts/Cinzel-Regular.ttf"
```

Also increase the default text size slightly for readability with the serif font:

```renpy
define gui.text_size = 28
define gui.name_text_size = 32
define gui.interface_text_size = 28
define gui.label_text_size = 32
define gui.notify_text_size = 22
define gui.title_text_size = 56
```

- [ ] **Step 3: Run lint**

```bash
/home/janothar/renpy-8.3.7-sdk/renpy.sh /home/janothar/wod_vn_framework/game lint
```

- [ ] **Step 4: Commit**

```bash
git add game/gui/fonts/ game/gui.rpy
git commit -m "feat: gothic typography — EB Garamond body, Cinzel headings"
```

---

### Task 2: Deepen Color Palette

**Files:**
- Modify: `game/gui.rpy`

- [ ] **Step 1: Update color variables for deeper gothic feel**

The Phase 2a colors were a starting point. Deepen them:

| Variable | Current | New |
|----------|---------|-----|
| `gui.accent_color` | `"#c9a96e"` | `"#b8860b"` (darker gold) |
| `gui.text_color` | `"#e0e0e0"` | `"#d4c5a9"` (parchment) |
| `gui.interface_text_color` | `"#e0e0e0"` | `"#d4c5a9"` |
| `gui.muted_color` | `"#2a2a3e"` | `"#1a1a28"` |
| `gui.hover_muted_color` | `"#3a3a52"` | `"#2a2a3e"` |
| `gui.idle_color` | `"#888888"` | `"#8a7e6c"` (warm gray) |
| `gui.insensitive_color` | `"#55555580"` | `"#4a4a4a80"` |

- [ ] **Step 2: Run lint**

```bash
/home/janothar/renpy-8.3.7-sdk/renpy.sh /home/janothar/wod_vn_framework/game lint
```

- [ ] **Step 3: Commit**

```bash
git add game/gui.rpy
git commit -m "feat: deepen gothic color palette — darker golds, parchment text"
```

---

### Task 3: Dark Background Images

**Files:**
- Replace: `game/gui/overlay/main_menu.png`
- Replace: `game/gui/overlay/game_menu.png`
- Replace: `game/gui/textbox.png`

- [ ] **Step 1: Generate dark overlay images**

Use Python/Pillow to create solid dark semi-transparent overlays. These replace the default Ren'Py images.

```bash
cd /home/janothar/wod_vn_framework && python3 -c "
from PIL import Image

# Main menu overlay — near-black with slight purple tint
img = Image.new('RGBA', (1920, 1080), (15, 10, 25, 220))
img.save('game/gui/overlay/main_menu.png')

# Game menu overlay — same
img = Image.new('RGBA', (1920, 1080), (15, 10, 25, 200))
img.save('game/gui/overlay/game_menu.png')

# Confirm overlay
img = Image.new('RGBA', (1920, 1080), (10, 8, 18, 200))
img.save('game/gui/overlay/confirm.png')

# Textbox — wide semi-transparent dark bar
img = Image.new('RGBA', (1920, 360), (12, 10, 22, 200))
img.save('game/gui/textbox.png')

print('Images generated.')
"
```

- [ ] **Step 2: Run lint**

```bash
/home/janothar/renpy-8.3.7-sdk/renpy.sh /home/janothar/wod_vn_framework/game lint
```

- [ ] **Step 3: Commit**

```bash
git add game/gui/overlay/ game/gui/textbox.png
git commit -m "feat: dark gothic overlay and textbox images"
```

---

### Task 4: Update HUD and Sheet Colors

**Files:**
- Modify: `game/wod_screens/resource_hud.rpy`
- Modify: `game/wod_screens/character_sheet.rpy`

- [ ] **Step 1: Update HUD colors to match gothic palette**

In `resource_hud.rpy`, update:
- Background: `"#0d0d1aCC"` → `"#0a0814DD"` (deeper, more opaque)
- Quintessence gold: `"#c9a96e"` → `"#b8860b"`
- Health green label: `"#5a8a5a"` → `"#8a7e6c"` (warm gray, less gamey)

In `character_sheet.rpy`, update:
- Overlay: `"#000000AA"` → `"#0a0814CC"`
- Panel: `"#1a1a2eEE"` → `"#100d1cEE"`
- Accent: `"#c9a96e"` → `"#b8860b"`
- Filled dots: `"#c9a96e"` → `"#b8860b"`

- [ ] **Step 2: Run lint + pytest**

```bash
/home/janothar/renpy-8.3.7-sdk/renpy.sh /home/janothar/wod_vn_framework/game lint
cd /home/janothar/wod_vn_framework && pytest -q
```

- [ ] **Step 3: Commit**

```bash
git add game/wod_screens/resource_hud.rpy game/wod_screens/character_sheet.rpy
git commit -m "feat: apply gothic color palette to HUD and character sheet"
```

---

### Task 5: Final Verification

- [ ] **Step 1: Full lint**

```bash
/home/janothar/renpy-8.3.7-sdk/renpy.sh /home/janothar/wod_vn_framework/game lint
```

- [ ] **Step 2: Full pytest**

```bash
cd /home/janothar/wod_vn_framework && pytest -v
```

- [ ] **Step 3: Verify fonts load**

Check that the font files exist and are referenced correctly:
```bash
ls -la game/gui/fonts/
grep -n "text_font\|name_text_font\|interface_text_font" game/gui.rpy
```
