## game/00_wod_preprocess.rpy
## WoD VN Framework — init-time bracket-shorthand preprocessor.
##
## Compiles bracket shorthand ([Forces >= 3]) into native Ren'Py `if`
## expressions automatically, so authors don't need to run the CLI
## (`python -m wod_core`) as a separate build step.
##
## HOW IT WORKS
## ------------
## Ren'Py loads .rpy files in sorted order, and a `python early` block runs
## before the files that sort *after* it are parsed (this is the same ordering
## guarantee that makes creator-defined statements work). This file is named
## `00_wod_preprocess.rpy` so it sorts first; its early block rewrites the
## remaining .rpy files on disk, and Ren'Py then parses the rewritten — now
## valid — source in the same run.
##
## The transform is idempotent: once a file holds `if` expressions there is no
## bracket shorthand left, so re-running rewrites nothing. That makes this safe
## to run on every launch.
##
## SCOPE & OPT-OUT
## ---------------
## * Runs in developer mode only. Distributed builds ship precompiled .rpyc and
##   have nothing to transform.
## * Author files that sort before this one (e.g. names beginning with "000")
##   are parsed before the early block runs — keep the framework's "00_" prefix
##   ahead of your own files, or compile those with the CLI.
## * To disable the pass, set the WOD_AUTO_PREPROCESS environment variable to 0
##   when launching (read before any script runs, so it always takes effect —
##   ideal for CI, `renpy lint`, or a CLI-only workflow):
##       WOD_AUTO_PREPROCESS=0 renpy.sh game/
##   The `wod_core.config.auto_preprocess` flag also disables it, but because
##   this runs in `python early` you must set the flag in a `python early` block
##   in a file that sorts before this one (e.g. 000_config.rpy) — setting it in
##   `init python` is too late.

python early:
    try:
        from wod_core import preprocess as wod_preprocess
    except ImportError as e:
        print(
            "WoD: bracket preprocessor unavailable (%s); "
            "run `python -m wod_core` to compile manually." % e
        )
    else:
        # run_init_preprocess() guards its own errors, so it never breaks load.
        wod_preprocess.run_init_preprocess()
