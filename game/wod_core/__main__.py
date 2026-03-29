# game/wod_core/__main__.py
"""CLI pre-processor for bracket shorthand syntax.

Usage:
    python -m wod_core <file.rpy> [<file2.rpy> ...]
    python -m wod_core --dry-run <file.rpy>

Transforms [Forces >= 3] shorthand into wod_core.gate() calls in-place.
Use --dry-run to preview changes without modifying files.
"""

import sys
from wod_core.syntax import transform_source


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m wod_core [--dry-run] <file.rpy> [<file2.rpy> ...]", file=sys.stderr)
        sys.exit(1)

    dry_run = "--dry-run" in sys.argv
    files = [f for f in sys.argv[1:] if f != "--dry-run"]

    if not files:
        print("Usage: python -m wod_core [--dry-run] <file.rpy> [<file2.rpy> ...]", file=sys.stderr)
        sys.exit(1)

    for filepath in files:
        with open(filepath) as f:
            original = f.read()

        transformed = transform_source(original)

        if dry_run:
            print(transformed)
        else:
            if transformed != original:
                with open(filepath, "w") as f:
                    f.write(transformed)
                print(f"Transformed: {filepath}", file=sys.stderr)
            else:
                print(f"No changes: {filepath}", file=sys.stderr)


if __name__ == "__main__":
    main()
