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
