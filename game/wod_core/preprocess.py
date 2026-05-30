# game/wod_core/preprocess.py
"""Bracket-shorthand preprocessor — file and directory transforms.

Compiles author-written bracket shorthand (``[Forces >= 3]``) into native
Ren'Py ``if`` expressions by rewriting ``.rpy`` files in place. This is the
engine behind two entry points:

* the CLI (``python -m wod_core``), and
* the automatic Ren'Py init-time pass (``game/00_wod_preprocess.rpy``), which
  runs during the ``python early`` phase so authors don't need a separate
  build step.

The transform is **idempotent**: once a file has been compiled to ``if``
expressions it no longer contains bracket shorthand, so re-running is a no-op
that rewrites nothing. That property is what makes the init-time pass safe to
run on every launch.
"""

from __future__ import annotations

import os
from typing import Iterable, Iterator

from wod_core.syntax import transform_source

# The preprocessor's own Ren'Py shim — never rewrite it.
PREPROCESSOR_FILENAME = "00_wod_preprocess.rpy"

# Directories that never hold authored source and should not be walked.
DEFAULT_EXCLUDES: tuple[str, ...] = ("cache", "saves", "tmp", "__pycache__")


def process_file(path: str, dry_run: bool = False) -> bool:
    """Transform a single ``.rpy`` file in place.

    Returns ``True`` if the file's contents changed (or *would* change, under
    ``dry_run``), ``False`` if there was nothing to transform.
    """
    with open(path, encoding="utf-8") as f:
        original = f.read()

    transformed = transform_source(original)
    if transformed == original:
        return False

    if not dry_run:
        with open(path, "w", encoding="utf-8") as f:
            f.write(transformed)
    return True


def iter_rpy_files(
    root: str, excludes: Iterable[str] = DEFAULT_EXCLUDES,
) -> Iterator[str]:
    """Yield absolute paths to every ``.rpy`` file under ``root``.

    Directory and file names listed in ``excludes`` are skipped, as is the
    preprocessor's own shim file. Files are yielded in sorted order within each
    directory for deterministic, reproducible runs.
    """
    exclude_set = set(excludes)
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune excluded directories in place so os.walk doesn't descend.
        dirnames[:] = sorted(d for d in dirnames if d not in exclude_set)
        for name in sorted(filenames):
            if not name.endswith(".rpy"):
                continue
            if name == PREPROCESSOR_FILENAME or name in exclude_set:
                continue
            yield os.path.join(dirpath, name)


def preprocess_directory(
    root: str,
    excludes: Iterable[str] = DEFAULT_EXCLUDES,
    dry_run: bool = False,
) -> list[str]:
    """Transform every ``.rpy`` file under ``root``; return the changed paths."""
    changed = []
    for path in iter_rpy_files(root, excludes):
        if process_file(path, dry_run=dry_run):
            changed.append(path)
    return changed


# Environment variable that disables the init-time pass. It is read before any
# script runs, so — unlike ``config.auto_preprocess`` — it always takes effect
# regardless of file load order. Set it to a falsey value (e.g. ``0``) to skip.
ENV_OPT_OUT = "WOD_AUTO_PREPROCESS"
_FALSEY = frozenset({"0", "false", "no", "off"})


def _disabled_by_env() -> bool:
    """True if ``WOD_AUTO_PREPROCESS`` is set to a falsey value."""
    val = os.environ.get(ENV_OPT_OUT)
    return val is not None and val.strip().lower() in _FALSEY


def run_init_preprocess(verbose: bool = True) -> list[str]:
    """Compile bracket shorthand at Ren'Py init time.

    Intended to be called from a ``python early`` block (see
    ``game/00_wod_preprocess.rpy``). It rewrites the game's ``.rpy`` source in
    place so the bracket shorthand is valid native Ren'Py by the time those
    files are parsed in the same run.

    The pass is a no-op when any of these hold:

    * Ren'Py has *already resolved* developer mode to off. This is a best-effort
      one-directional safety only: the function runs in ``python early``, where
      ``config.developer`` may still be the unresolved default ``"auto"`` and an
      init-time ``config.developer = False`` (in ``options.rpy``) is evaluated
      too late to be seen here. It is **not** the authoritative switch — use the
      env var below. (Packaged builds are safe regardless: they ship precompiled
      ``.rpyc`` with no shorthand to transform, and a read-only tree degrades
      gracefully.)
    * The ``WOD_AUTO_PREPROCESS`` environment variable is set to a falsey value.
      This is the authoritative, ordering-independent opt-out (read before any
      script runs), and the right one for CI / ``renpy lint`` / CLI-only
      workflows or for an author who has turned developer mode off.
    * ``wod_core.config.auto_preprocess`` is disabled. Because this function
      runs in ``python early``, that flag only takes effect when set early
      enough — i.e. from a ``python early`` block in a file that sorts before
      ``00_wod_preprocess.rpy``; setting it in ``init python`` is too late.

    Returns the list of files that were changed (empty when skipped).
    """
    import renpy  # only importable from inside Ren'Py

    # Best-effort safety for packaged games: skip when Ren'Py has already
    # resolved developer mode to off. NOTE: in `python early` config.developer
    # may still be the default "auto" (truthy), and an init-time
    # `config.developer = False` runs later — so this is not the authoritative
    # switch. The env var below is; it's read before any script runs.
    if not renpy.config.developer:
        return []

    if _disabled_by_env():
        return []

    import wod_core

    if not getattr(wod_core.config, "auto_preprocess", True):
        return []

    gamedir = renpy.config.gamedir
    try:
        changed = preprocess_directory(gamedir)
    except Exception as e:
        # This runs in `python early` on every launch and during `renpy lint`,
        # so it must never crash the game. Degrade to a warning; the author can
        # still compile manually with the CLI. (OSError = unreadable/unwritable
        # file; UnicodeDecodeError = a non-UTF-8 .rpy; etc.)
        if verbose:
            print(f"WoD: could not compile bracket shorthand ({e!r}).")
        return []

    if verbose:
        for path in changed:
            rel = os.path.relpath(path, gamedir)
            print(f"WoD: compiled bracket shorthand in {rel}")
    return changed
