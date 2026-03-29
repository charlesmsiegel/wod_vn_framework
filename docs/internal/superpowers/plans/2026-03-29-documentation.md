# Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Write a README and author guide so someone else can use the WoD VN Framework to build their own visual novel.

**Architecture:** Two documents: a `README.md` at the repo root (quick start, overview, feature list) and an `docs/author-guide.md` (detailed how-to for writing games with the framework).

**Tech Stack:** Markdown

---

## File Map

| File | Responsibility |
|------|---------------|
| `README.md` | Repo landing page — what it is, quick start, feature summary |
| `docs/author-guide.md` | Complete guide: installation, project setup, writing scenes, stat gating, resources, chargen, HUD, character sheet, data files |

---

### Task 1: README.md

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README.md**

The README should cover:

1. **Title and one-line description**
2. **What is this?** — A Ren'Py framework for WoD visual novels, targeting Mage: The Ascension (M20)
3. **Features** — bullet list: deterministic stat gating, data-driven splat packs, resource pools (Quintessence Wheel), character creation (3 modes), HUD, character sheet, gothic theme
4. **Quick Start** — install Ren'Py 8.x, clone repo, run the demo
5. **Project Structure** — tree diagram of key files
6. **For Authors** — link to author guide
7. **For Developers** — how to run tests, how the engine works (brief)
8. **License** — state it (user should choose)
9. **Credits** — framework, fonts used

Keep it concise — the author guide has the details.

- [ ] **Step 2: Verify links and paths**

Check that all referenced files/paths in the README actually exist.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add README with quick start and feature overview"
```

---

### Task 2: Author Guide

**Files:**
- Create: `docs/author-guide.md`

- [ ] **Step 1: Write the author guide**

Sections:

1. **Installation** — Install Ren'Py 8.x, clone the repo, verify with `renpy.sh game lint`
2. **Your First Scene** — Create script.rpy, load a character, write dialogue
3. **Characters** — YAML format, loading, pre-defined vs chargen
4. **Stat Gating** — Native syntax (`if pc.gate(...)`), all operators, boolean merits, outcome branching
5. **Bracket Shorthand** — The `[Forces >= 3]` syntax, running the pre-processor CLI
6. **Resources** — spend/gain, linked pools (Quintessence Wheel), how the HUD shows them
7. **Character Creation** — Three modes (full/simplified/template), author API, preset support, customizing chargen.yaml
8. **HUD & Character Sheet** — show_hud(), hide_hud(), Tab key, configuring which resources appear
9. **Splat Data Files** — Schema structure, resources, manifest, creating custom splats
10. **Customization** — Override files, template extends, adding traits/resources
11. **Toasts** — show_toast() API, config options
12. **Testing** — Ren'Py lint, running pytest for engine tests

Each section should have a complete, copy-pasteable example.

- [ ] **Step 2: Verify all code examples**

Spot-check that the API calls in the guide match the actual implementation:
```bash
cd /home/janothar/wod_vn_framework && grep -n "def show_hud\|def hide_hud\|def show_toast\|def chargen\|def load_character\|def load_splat\|def gate\|def has\|def set_active" game/wod_core/__init__.py
```

- [ ] **Step 3: Commit**

```bash
git add docs/author-guide.md
git commit -m "docs: add author guide — complete reference for writing WoD visual novels"
```

---

### Task 3: Final Check

- [ ] **Step 1: Verify documentation completeness**

Check that all public API functions in `__init__.py` are documented in the author guide:
```bash
grep "^def " game/wod_core/__init__.py
```

Compare with sections in the guide.

- [ ] **Step 2: Commit any fixes**

```bash
git add -A && git commit -m "docs: fix any issues found during review" # only if needed
```
