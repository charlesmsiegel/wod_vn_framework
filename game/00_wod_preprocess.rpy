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
## * Disable entirely with:  init python: wod_core.config.auto_preprocess = False

python early:
    try:
        from wod_core import preprocess as wod_preprocess
        wod_preprocess.run_init_preprocess()
    except ImportError as e:
        print(
            "WoD: bracket preprocessor unavailable (%s); "
            "run `python -m wod_core` to compile manually." % e
        )
