# Demo Chronicle — *The Hollow Vigil*

A complete, branching **Mage: The Ascension** short story built on the WoD VN
Framework. It is meant as a worked example for authors: a chronicle long enough
to show real structure (5 scenes, multiple endings) while exercising every core
framework feature. It ships **playable with zero art** — every background,
sprite, and CG renders a labelled placeholder until you supply the real file.

- **Script:** [`game/chronicle.rpy`](../game/chronicle.rpy)
- **Protagonist:** [`game/demo/soraya.yaml`](../game/demo/soraya.yaml) — Soraya Mir, Order of Hermes
- **Art registry / placeholders:** [`game/images.rpy`](../game/images.rpy)
- **Image manifest (canonical):** [`game/images/manifest.yaml`](../game/images/manifest.yaml)

---

## Running it

```bash
renpy.sh game/
```

From the title screen, choose **"The Hollow Vigil — a Mage demo chronicle (5
scenes)."** (The short single-scene feature demo, *Elena vs. the Technocratic
Ward*, is still available from the same launcher.)

You can play start-to-finish immediately — placeholders stand in for any missing
art. See [Supplying art](#supplying-art) to drop in real assets.

---

## Synopsis

Soraya Mir's mentor, Magister Aurelio Vance, has missed the new-moon vigil for
the first time in thirty years and his wards have gone dark. Soraya follows the
trail to his chantry and the failing Node beneath it, where she finds that Vance
attempted the *Hollow Vigil* — holding a dying Node open by sheer will — and that
Paradox has claimed him for it. She must stabilise the breach and then decide her
mentor's fate: sever the working, anchor him with her own Pattern, reach him
through their bond, or flee.

The ending is determined by the player's choices and resource state.

---

## Scene breakdown & features demonstrated

| Scene | Title | What happens | Framework features exercised |
|-------|-------|--------------|------------------------------|
| 1 | **The Summons** | Soraya learns Vance is missing and decides how to begin. | `load_character`, `set_active`, `show_hud`, `show_toast`, identity interpolation, **Flaw** check (`has("Nightmares")`), gates on **Background** (`Mentor`) and **Ability** (`Investigation`), a hidden premium gate (`Correspondence >= 3`). |
| 2 | **The Sanctum** | Searching Vance's library for what he did and why. | **Spirit** gate reveals the familiar Corvin; investigation menu gated on `Prime`/`Occult`/`Investigation`/`Awareness`; **Quintessence spend** + small **Paradox gain** (the Wheel); one-time **`advance("Cosmology")`** with a toast. |
| 3 | **The Breach** | The Node tears open; Soraya must stabilise it. | **Resonance** gate (`Static >= 2`); **Merit** check (`has("Natural Channel")`) to **gain Quintessence** from the Node; stabilise menu gated on `Forces`/`Spirit` (+ hidden `Correspondence`); **spend** Quintessence/Willpower/Health; **Paradox backlash** branch; spend-failure fallback. |
| 4 | **The Vigil** *(climax)* | Confront the Paradox-touched Vance and choose his fate. | Compound gates (`Spirit >= 2 and Prime >= 2`), `Prime`, `Mentor` bond, hidden `Forces >= 4`; Willpower/Quintessence spends with insufficient-resource fallbacks; sets the ending flag `hv_mentor_fate`. |
| 5 | **Aftermath** | Resolution keyed to choices, plus a final-state readout. | Four-way ending branch (`reconciled`/`released`/`anchored`/`fled`), reads back final resources & advanced traits, `hide_hud`. |

Every menu includes an unconditional fallback choice, so the chronicle is always
completable regardless of the protagonist's sheet.

### Why these stats?

Soraya's sheet (`demo/soraya.yaml`) is tuned so the **main path** of every scene
is reachable, while two **premium gates** stay deliberately out of reach to show
how gating *hides* choices rather than failing them:

- Reachable: `Forces 3`, `Prime 2`, `Spirit 2`, `Static 2` (Resonance), `Awareness 3`, `Occult 3`, `Investigation 3`, `Mentor 3`, `Avatar 3`, `Node 2`.
- Hidden for Soraya: `Correspondence >= 3` (she has 1) and `Forces >= 4` (she has 3).

Swap in a character with higher `Correspondence` or `Forces` and new options
appear — a good way to feel the gating system at work.

---

## Supplying art

The chronicle references images by short logical names (e.g. `sanctum_library`,
`soraya focused`). Each name is registered in `game/images.rpy`, which checks
whether the real file exists and, if not, draws a self-describing placeholder:

```
   if renpy.loadable(target):  use the file
   else:                       draw a labelled placeholder
```

So to ship real art, **just drop a file at the path in the manifest** — no code
change is needed. The logical name is decoupled from the file path, so you can
organise `game/images/` however you like; only the paths in `game/images.rpy`
(and the manifest) need to match where you put the files.

- Backgrounds & CGs: full-frame at the project resolution **1920×1080**.
- Sprites: PNG with transparency, roughly **560×1040**, full-figure (the script
  shows them with the built-in `left` / `center` / `right` positions, so they are
  bottom-aligned).

If you add or remove assets, keep `WOD_CHRONICLE_ART` in `game/images.rpy` and
`game/images/manifest.yaml` in sync (the two are cross-checked in spirit; the
manifest is the canonical spec).

---

## Image manifest

18 assets. Until supplied, each renders as an on-screen placeholder.

| # | Image name | Type | File | Size | Scenes | Art direction |
|---|------------|------|------|------|--------|---------------|
| 1 | `apartment_night` | Background | `images/bg/apartment_night.png` | 1920x1080 | 1 | Soraya's cramped Hermetic study at night: candle-lit desk, brass astrolabe, stacked grimoires and ley-line charts, rain on a dark window. |
| 2 | `rain_street` | Background | `images/bg/rain_street.png` | 1920x1080 | 1 | Rain-slick city street after midnight, sodium streetlights smearing on wet asphalt, old townhouses, the chantry's silhouette at the far end. |
| 3 | `chantry_exterior` | Background | `images/bg/chantry_exterior.png` | 1920x1080 | 1 | Imposing gothic townhouse (the Order's chantry), iron gate ajar, one amber-lit upper window, fog pooling on the stone steps. |
| 4 | `sanctum_library` | Background | `images/bg/sanctum_library.png` | 1920x1080 | 2 | Two-storey sanctum library: floor-to-ceiling shelves, a great brass orrery, green-shaded lamps, a worktable strewn with star-charts. |
| 5 | `sanctum_residue` | Background | `images/bg/sanctum_residue.png` | 1920x1080 | 2 | The same library through Awakened sight: glowing Prime residue, drifting motes, half-burnt sigils smouldering violet in the air. |
| 6 | `node_chamber` | Background | `images/bg/node_chamber.png` | 1920x1080 | 3 | Stone undercroft housing the Node: a luminous quintessential spring at centre, a runic floor, warm gold light welling up the walls. |
| 7 | `node_breach` | Background | `images/bg/node_breach.png` | 1920x1080 | 3 | The Node chamber gone wrong: a jagged tear of static and bruised light, the room's geometry bending, Paradox bleeding across the runes. |
| 8 | `vigil_threshold` | Background | `images/bg/vigil_threshold.png` | 1920x1080 | 4 | A liminal dream-threshold: an endless candle-lit corridor dissolving into starless dark, reality worn thin -- where the wraith holds vigil. |
| 9 | `dawn_rooftop` | Background | `images/bg/dawn_rooftop.png` | 1920x1080 | 5 | A city rooftop at first light: pale gold sky, mist over the streets, the storm spent. Quiet, exhausted dawn. |
| 10 | `soraya neutral` | Sprite | `images/sprites/soraya/neutral.png` | 560x1040 | 1, 2, 3, 4, 5 | Soraya Mir, late 20s, Order of Hermes: dark coat over a waistcoat, ink-stained fingers, a brass focus-ring. Composed, watchful. |
| 11 | `soraya focused` | Sprite | `images/sprites/soraya/focused.png` | 560x1040 | 2, 3, 4 | Soraya mid-working: eyes lit with Awakened focus, a hand tracing a sigil, a faint gold Quintessence glow at her fingertips. |
| 12 | `soraya strained` | Sprite | `images/sprites/soraya/strained.png` | 560x1040 | 3, 4 | Soraya strained: jaw set, sweat at the brow, faint Paradox static crackling at her silhouette. Wounded resolve. |
| 13 | `vance calm` | Sprite | `images/sprites/vance/calm.png` | 560x1040 | 1, 4 | Magister Aurelio Vance, 60s, silver-bearded, tweed jacket with a star-chart sash; kindly, tired eyes. The mentor as he was. |
| 14 | `vance wraith` | Sprite | `images/sprites/vance/wraith.png` | 560x1040 | 4 | Vance consumed by Paradox: half-dissolved into flickering static and mirror-shards, eyes like blown-out screens. Sorrowful and monstrous. |
| 15 | `corvin` | Sprite | `images/sprites/corvin/corvin.png` | 560x1040 | 2, 4 | Corvin, Vance's raven-familiar: a large black bird limned in faint silver spirit-light, too-knowing eyes. Visible only to Spirit sight. |
| 16 | `cg_breach` | Event CG | `images/cg/breach.png` | 1920x1080 | 3 | The Node ruptures: Soraya silhouetted against a blossoming tear of Paradox light, charts and candle-flames whipping up around her. |
| 17 | `cg_severance` | Event CG | `images/cg/severance.png` | 1920x1080 | 4 | Soraya severs the wraith's tether: a blade of Prime light parting Vance's static form, his face for one instant human again. |
| 18 | `chronicle_title` | Title / UI | `images/ui/title.png` | 1200x460 | 1 | Title treatment: 'THE HOLLOW VIGIL' in engraved Cinzel-style serif with a faint hermetic sigil and ley-line motif. Transparent background. |

> The canonical machine-readable version of this table is
> [`game/images/manifest.yaml`](../game/images/manifest.yaml).
