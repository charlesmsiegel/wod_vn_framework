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

label after_load:
    ## If the save was written under an older schema version, the framework
    ## migrates each character onto the current schema as it is unpickled.
    ## Surface a brief notice so the player (and author) know it happened.
    python:
        for _wod_report in wod_core.drain_migration_reports():
            wod_core.show_toast(_wod_report.summary(), duration=4.0)
    if store.wod_hud_visible:
        show screen resource_hud
    return
