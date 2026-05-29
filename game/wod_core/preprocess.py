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


def run_init_preprocess(verbose: bool = True) -> list[str]:
    """Compile bracket shorthand at Ren'Py init time.

    Intended to be called from a ``python early`` block (see
    ``game/00_wod_preprocess.rpy``). It rewrites the game's ``.rpy`` source in
    place so the bracket shorthand is valid native Ren'Py by the time those
    files are parsed in the same run.

    The pass is a no-op unless **both** conditions hold:

    * Ren'Py is in developer mode. Distributed builds ship precompiled
      ``.rpyc`` and have no shorthand to transform, so there is nothing to do
      (and the source tree may be read-only).
    * ``wod_core.config.auto_preprocess`` is left enabled (the default).

    Returns the list of files that were changed (empty when skipped).
    """
    import renpy  # only importable from inside Ren'Py

    # Only rewrite source while developing; shipped builds are precompiled.
    if not renpy.config.developer:
        return []

    import wod_core

    if not getattr(wod_core.config, "auto_preprocess", True):
        return []

    gamedir = renpy.config.gamedir
    try:
        changed = preprocess_directory(gamedir)
    except OSError as e:
        if verbose:
            print(f"WoD: could not compile bracket shorthand ({e}).")
        return []

    if verbose:
        for path in changed:
            rel = os.path.relpath(path, gamedir)
            print(f"WoD: compiled bracket shorthand in {rel}")
    return changed
