## game/wod_screens/resource_hud.rpy
## WoD VN Framework — Resource HUD overlay (top bar).

default wod_hud_visible = False
default wod_hud_resources = None

screen resource_hud():
    zorder 100

    $ pc = wod_core.get_active()
    $ res = pc.resources
    $ hud_resources = store.wod_hud_resources

    frame:
        xfill True
        ysize 60
        xpos 0
        ypos 0
        background "#0a0814DD"
        padding (20, 8, 20, 8)

        hbox:
            spacing 30
            yalign 0.5

            # Quintessence / Paradox split bar
            if hud_resources is None or "quintessence" in (hud_resources or []) or "paradox" in (hud_resources or []):
                $ quint = res.current("quintessence") if res.has_resource("quintessence") else 0
                $ paradox_val = res.current("paradox") if res.has_resource("paradox") else 0
                $ combined_max = 20
                python:
                    for link in res.links:
                        if "quintessence" in link.pool_names and "paradox" in link.pool_names:
                            combined_max = link.combined_max

                vbox:
                    spacing 2
                    # Split bar: quintessence from left, paradox overlay from right
                    fixed:
                        xsize 300
                        ysize 16
                        bar:
                            value quint
                            range combined_max
                            xsize 300
                            ysize 16
                            left_bar "#b8860b"
                            right_bar "#333333"
                        bar:
                            value paradox_val
                            range combined_max
                            xsize 300
                            ysize 16
                            right_bar "#8b4545"
                            left_bar "#00000000"
                            bar_invert True

                    hbox:
                        xsize 300
                        $ qt_text = "Qt: {}".format(quint)
                        $ pdx_text = "Pdx: {}".format(paradox_val)
                        text "[qt_text]" size 12 color "#b8860b"
                        null width 0 xfill True
                        text "[pdx_text]" size 12 color "#8b4545"

            # Willpower bar
            if hud_resources is None or "willpower" in (hud_resources or []):
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
                        $ wp_text = "WP: {}/{}".format(wp_cur, wp_max)
                        text "[wp_text]" size 12 color "#6a9ec9"

            # Health track
            if hud_resources is None or "health" in (hud_resources or []):
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
                                    frame:
                                        xsize 14
                                        ysize 14
                                        background "#8b4545"
                                else:
                                    frame:
                                        xsize 14
                                        ysize 14
                                        background "#333333"
                        text "Health" size 12 color "#8a7e6c"

            # Spacer pushes sheet button to the right
            null width 0 xfill True

            # Character sheet toggle button
            textbutton "[Sheet]":
                yalign 0.5
                text_size 14
                text_color "#b8860b"
                text_hover_color "#e0c080"
                action ToggleScreen("character_sheet")

    key "K_TAB" action ToggleScreen("character_sheet")
