## game/wod_screens/character_sheet.rpy
## WoD VN Framework — Tabbed character sheet overlay.

screen character_sheet():
    modal True
    zorder 200
    default current_tab = 0

    $ pc = wod_core.get_active()
    $ schema = pc.schema

    # Find splat data for tab config
    $ splat_data = None
    python:
        for sid, sd in wod_core.get_loader().loaded_splats.items():
            if sd.schema is schema:
                splat_data = sd
                break

    # Get tab config from manifest, or auto-generate
    $ tab_config = []
    python:
        if splat_data and "character_sheet" in splat_data.manifest.get("splat", {}):
            tab_config = splat_data.manifest["splat"]["character_sheet"].get("tabs", [])
        if not tab_config:
            for cat_name, cat_def in schema.categories.items():
                tab_config.append({"name": cat_def.display_name, "categories": [cat_name]})
            tab_config.append({"name": "Merits & Resources", "categories": []})

    # Dark overlay
    frame:
        xfill True
        yfill True
        background "#000000AA"

        frame:
            xalign 0.5
            yalign 0.5
            xsize int(config.screen_width * 0.8)
            ysize int(config.screen_height * 0.85)
            background "#1a1a2eEE"
            padding (30, 20, 30, 20)

            vbox:
                spacing 10

                # Header with identity and close button
                hbox:
                    xfill True
                    $ identity_parts = [str(v) for k, v in pc.identity.items() if v]
                    $ identity_text = " — ".join(identity_parts)
                    text "[identity_text]" size 24 color "#c9a96e"
                    null width 0 xfill True
                    textbutton "\u2715" action Hide("character_sheet") text_size 24 text_color "#888888" text_hover_color "#ffffff"

                # Tab buttons
                hbox:
                    spacing 10
                    for i, tab in enumerate(tab_config):
                        if i == current_tab:
                            textbutton tab["name"] text_size 16 text_color "#c9a96e" text_underline True action SetScreenVariable("current_tab", i)
                        else:
                            textbutton tab["name"] text_size 16 text_color "#888888" action SetScreenVariable("current_tab", i)

                null height 10

                # Tab content
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
                                for cat_name in cats:
                                    if cat_name in schema.categories:
                                        $ cat = schema.categories[cat_name]
                                        text cat.display_name size 20 color "#c9a96e"
                                        null height 5

                                        if cat.groups is not None:
                                            for group_name, group_traits in cat.groups.items():
                                                $ group_label = group_name.capitalize()
                                                text "[group_label]" size 14 color "#888888" italic True
                                                for trait_name in group_traits:
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
                                                                        text "\u25cf" size 14 color "#c9a96e"
                                                                    else:
                                                                        text "\u25cb" size 14 color "#444444"
                                                null height 5
                                        else:
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
                                                                    text "\u25cf" size 14 color "#c9a96e"
                                                                else:
                                                                    text "\u25cb" size 14 color "#444444"
                                        null height 10
                            else:
                                # Merits & Resources tab
                                if pc.merits_flaws:
                                    text "Merits & Flaws" size 20 color "#c9a96e"
                                    null height 5
                                    for mf in pc.merits_flaws:
                                        hbox:
                                            spacing 10
                                            text mf["name"] size 14 color "#e0e0e0"
                                            $ mf_type = mf.get("type", "")
                                            text "([mf_type])" size 12 color "#888888"
                                            if "value" in mf:
                                                $ mf_val = str(mf["value"])
                                                text "[mf_val]" size 12 color "#888888"
                                    null height 10

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
                                            $ pool_text = "{}/{}".format(pool.current(), pool.max)
                                            text "[pool_text]" size 12 color "#888888"

    key "K_ESCAPE" action Hide("character_sheet")
    key "K_TAB" action Hide("character_sheet")
