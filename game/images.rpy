## game/images.rpy
## Demo chronicle art registry  --  "The Hollow Vigil"
##
## Every image the chronicle uses is registered here ONCE, in WOD_CHRONICLE_ART.
## For each entry:
##   * If the real art file exists (its `target` path is loadable), that file is
##     used as the image.
##   * Otherwise a labelled on-screen PLACEHOLDER is generated automatically, so
##     the chronicle runs end-to-end with zero art assets.
##
## To ship real art: drop a file at the listed `target` path (e.g.
## game/images/bg/sanctum_library.png) and it overrides the placeholder on the
## next launch -- NO code change required. The script references images by the
## short `name` (e.g. `scene sanctum_library`), which is decoupled from the file
## path, so you can organise the images/ folder however you like.
##
## The canonical, human- and machine-readable list of what art is needed lives
## in game/images/manifest.yaml  (see also docs/demo-chronicle.md).

init python:

    import textwrap

    # Per-kind (base fill, accent) colours for the placeholder cards.
    _WOD_PH_PALETTE = {
        "bg":     ("#0e1118", "#c9a96e"),   # backgrounds  -- warm gold accent
        "cg":     ("#160e16", "#d98fb0"),   # event CGs     -- rose accent
        "sprite": ("#0b0f0d", "#7fc9ad"),   # characters    -- jade accent
        "ui":     ("#13130d", "#c9c07e"),   # title / UI    -- pale gold accent
    }

    def _wod_placeholder(kind, name, desc, w, h, target):
        """Build a self-describing placeholder displayable (no art needed).

        Uses only Fixed/Solid/Text so it is valid on any Ren'Py 8.x install.
        """
        base, accent = _WOD_PH_PALETTE.get(kind, ("#101010", "#dddddd"))

        wide = w >= 900
        big   = 54 if wide else 32     # asset name
        body  = 26 if wide else 18     # art-direction note
        small = 20 if wide else 14     # dimensions / path
        wrap  = max(18, min(58, w // 22))

        # (text, size, colour) rows, top to bottom. Empty text == vertical gap.
        rows = [(kind.upper() + " PLACEHOLDER", small, "#7d7d7d"), ("", body // 2, base)]
        rows.append((name, big, accent))
        rows.append(("", body // 2, base))
        for line in textwrap.wrap(desc, width=wrap):
            rows.append((line, body, "#d2d2d2"))
        rows.append(("", body // 2, base))
        rows.append(("%d x %d" % (w, h), small, "#6b6b6b"))
        rows.append((target, small, "#6b6b6b"))

        total = sum(sz + 8 for _, sz, _ in rows)
        y = max(8, (h - total) // 2)

        children = [
            Solid(accent, xysize=(w, h)),                              # border
            Solid(base, xysize=(w - 6, h - 6), xpos=3, ypos=3),        # inner fill
        ]
        for text, sz, col in rows:
            if text:
                children.append(Text(
                    text, size=sz, color=col,
                    xpos=w // 2, xanchor=0.5, ypos=y, yanchor=0.0,
                    outlines=[(2, "#000000", 0, 0)],
                ))
            y += sz + 8

        return Fixed(*children, xysize=(w, h))

    def _wod_register_art(name, kind, target, w, h, desc):
        """Define `name` as the real file if present, else a placeholder."""
        if renpy.loadable(target):
            renpy.image(name, target)
        else:
            renpy.image(name, _wod_placeholder(kind, name, desc, w, h, target))

    # ------------------------------------------------------------------ #
    #  ART REGISTRY  --  keep in sync with game/images/manifest.yaml      #
    #  (image name, kind, target file, width, height, art direction)      #
    # ------------------------------------------------------------------ #
    WOD_CHRONICLE_ART = [

        # ---- Backgrounds (1920x1080) -------------------------------------
        ("apartment_night", "bg", "images/bg/apartment_night.png", 1920, 1080,
         "Soraya's cramped Hermetic study at night: candle-lit desk, brass astrolabe, "
         "stacked grimoires and ley-line charts, rain streaking a dark window."),
        ("rain_street", "bg", "images/bg/rain_street.png", 1920, 1080,
         "Rain-slick city street after midnight, sodium streetlights smearing on wet "
         "asphalt, a row of old townhouses, the chantry's silhouette at the end."),
        ("chantry_exterior", "bg", "images/bg/chantry_exterior.png", 1920, 1080,
         "Imposing gothic townhouse -- the Order's chantry -- iron gate ajar, a single "
         "amber-lit upper window, fog pooling on the stone steps."),
        ("sanctum_library", "bg", "images/bg/sanctum_library.png", 1920, 1080,
         "Two-storey sanctum library: floor-to-ceiling shelves, a great brass orrery, "
         "green-shaded lamps, a heavy worktable strewn with star-charts."),
        ("sanctum_residue", "bg", "images/bg/sanctum_residue.png", 1920, 1080,
         "The same library through Awakened sight: glowing Prime residue, drifting "
         "motes, half-burnt sigils smouldering violet in the air."),
        ("node_chamber", "bg", "images/bg/node_chamber.png", 1920, 1080,
         "Stone undercroft housing the Node: a luminous quintessential spring at centre, "
         "a runic floor, warm gold light welling up the walls."),
        ("node_breach", "bg", "images/bg/node_breach.png", 1920, 1080,
         "The Node chamber gone wrong: a jagged tear of static and bruised light, the "
         "geometry of the room bending, Paradox bleeding across the runes."),
        ("vigil_threshold", "bg", "images/bg/vigil_threshold.png", 1920, 1080,
         "A liminal dream-threshold: an endless candle-lit corridor dissolving into "
         "starless dark, reality worn thin -- where the wraith holds vigil."),
        ("dawn_rooftop", "bg", "images/bg/dawn_rooftop.png", 1920, 1080,
         "A city rooftop at first light: pale gold sky, mist over the streets below, "
         "the storm spent. Quiet, exhausted dawn."),

        # ---- Character sprites (560x1040, transparent) -------------------
        ("soraya neutral", "sprite", "images/sprites/soraya/neutral.png", 560, 1040,
         "Soraya Mir, late 20s, Order of Hermes: dark coat over a waistcoat, ink-stained "
         "fingers, a brass focus-ring. Composed, watchful. Neutral expression."),
        ("soraya focused", "sprite", "images/sprites/soraya/focused.png", 560, 1040,
         "Soraya mid-working: eyes lit with Awakened focus, one hand tracing a sigil, a "
         "faint gold Quintessence glow at her fingertips. Casting expression."),
        ("soraya strained", "sprite", "images/sprites/soraya/strained.png", 560, 1040,
         "Soraya strained: jaw set, sweat at the brow, faint Paradox static crackling at "
         "her silhouette. Wounded resolve."),
        ("vance calm", "sprite", "images/sprites/vance/calm.png", 560, 1040,
         "Magister Aurelio Vance, 60s, silver-bearded, tweed jacket with a star-chart "
         "sash; kindly, tired eyes. The mentor as he was -- for flashbacks."),
        ("vance wraith", "sprite", "images/sprites/vance/wraith.png", 560, 1040,
         "Vance consumed by Paradox: half-dissolved into flickering static and "
         "mirror-shards, eyes like blown-out screens. Sorrowful and monstrous."),
        ("corvin", "sprite", "images/sprites/corvin/corvin.png", 560, 1040,
         "Corvin, Vance's raven-familiar: a large black bird limned in faint silver "
         "spirit-light, too-knowing eyes, head cocked. Visible only to Spirit sight."),

        # ---- Event CGs (1920x1080) ---------------------------------------
        ("cg_breach", "cg", "images/cg/breach.png", 1920, 1080,
         "Splash CG: the Node ruptures. Soraya silhouetted against a blossoming tear of "
         "Paradox light, charts and candle-flames whipping up around her."),
        ("cg_severance", "cg", "images/cg/severance.png", 1920, 1080,
         "Splash CG: Soraya severs the wraith's tether -- a blade of Prime light parting "
         "Vance's static form, his face for one instant human again."),

        # ---- Title / UI --------------------------------------------------
        ("chronicle_title", "ui", "images/ui/title.png", 1200, 460,
         "Title treatment: 'THE HOLLOW VIGIL' in engraved Cinzel-style serif, a faint "
         "hermetic sigil and ley-line motif behind it. Transparent background."),
    ]

    for _entry in WOD_CHRONICLE_ART:
        _wod_register_art(*_entry)
