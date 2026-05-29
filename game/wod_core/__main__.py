# game/wod_core/__main__.py
"""CLI pre-processor for bracket shorthand syntax.

Usage:
    python -m wod_core <path> [<path> ...]
    python -m wod_core --dry-run <path> [<path> ...]

Each <path> may be a .rpy file or a directory (transformed recursively).
Transforms [Forces >= 3] shorthand into wod_core.gate() calls in place.
Use --dry-run to preview changes without modifying files.

The same transform also runs automatically at Ren'Py init time (see
game/00_wod_preprocess.rpy). This CLI is for explicit/batch use, CI checks, or
projects that disable the init-time pass.
"""

import os
import sys

from wod_core.syntax import transform_source
from wod_core.preprocess import preprocess_directory, process_file

USAGE = "Usage: python -m wod_core [--dry-run] <path> [<path> ...]"


def _process_dir(path: str, dry_run: bool) -> None:
    changed = preprocess_directory(path, dry_run=dry_run)
    verb = "Would transform" if dry_run else "Transformed"
    for fn in changed:
        print(f"{verb}: {fn}", file=sys.stderr)
    if not changed:
        print(f"No changes: {path}", file=sys.stderr)


def _process_file(path: str, dry_run: bool) -> None:
    if dry_run:
        # Print the transformed source so authors can review it.
        with open(path, encoding="utf-8") as f:
            print(transform_source(f.read()))
    elif process_file(path):
        print(f"Transformed: {path}", file=sys.stderr)
    else:
        print(f"No changes: {path}", file=sys.stderr)


def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    paths = [a for a in args if a != "--dry-run"]

    if not paths:
        print(USAGE, file=sys.stderr)
        sys.exit(1)

    for path in paths:
        if os.path.isdir(path):
            _process_dir(path, dry_run)
        else:
            _process_file(path, dry_run)


if __name__ == "__main__":
    main()
