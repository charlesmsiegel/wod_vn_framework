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
