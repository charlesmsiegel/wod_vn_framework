"""Shorthand bracket syntax compiler.

Transforms lines like:
    "Choice text" [Forces >= 3, Prime >= 2]:
Into:
    "Choice text" if wod_core.gate("Forces", ">=", 3) and wod_core.gate("Prime", ">=", 2):
"""

from __future__ import annotations

import re

# Match bracket conditions on a menu choice line.
_BRACKET_RE = re.compile(
    r'^(\s*"[^"]*")\s*'           # leading whitespace + quoted text
    r'\[([^\]]+)\]'               # [conditions]
    r'(\s*(?:\(.*\))?\s*:\s*)$'   # optional (locked=...) + colon
)

_COMPARISON_RE = re.compile(
    r'^(.+?)\s*(>=|<=|==|!=|>|<)\s*(\d+)$'
)

_NEGATION_RE = re.compile(r'^!(.+)$')

# Phase 2: identifier validation registry
_encountered_identifiers: set[str] = set()


def _register_identifier(name: str) -> None:
    _encountered_identifiers.add(name)


def clear_identifiers() -> None:
    _encountered_identifiers.clear()


def parse_condition(cond: str) -> str:
    """Parse a single condition string into a Python expression."""
    cond = cond.strip()

    m = _COMPARISON_RE.match(cond)
    if m:
        trait_name = m.group(1).strip()
        op = m.group(2)
        value = int(m.group(3))
        _register_identifier(trait_name)
        return f'wod_core.gate("{trait_name}", "{op}", {value})'

    m = _NEGATION_RE.match(cond)
    if m:
        name = m.group(1).strip()
        return f'not wod_core.has("{name}")'

    return f'wod_core.has("{cond}")'


def transform_line(line: str) -> str:
    """Transform a single line, replacing bracket shorthand with if expressions."""
    m = _BRACKET_RE.match(line)
    if not m:
        return line

    prefix = m.group(1)
    conditions = m.group(2)
    suffix = m.group(3)

    parts = [parse_condition(c) for c in conditions.split(",")]
    condition_expr = " and ".join(parts)

    return f"{prefix} if {condition_expr}{suffix}"


def transform_source(source: str) -> str:
    """Transform all lines in a source string."""
    return "\n".join(transform_line(line) for line in source.split("\n"))


def _closest_match(name: str, valid_names: list[str]) -> str | None:
    from difflib import get_close_matches
    matches = get_close_matches(name, valid_names, n=1, cutoff=0.6)
    return matches[0] if matches else None


def validate_identifiers(
    schema, resource_names: list[str] | None = None
) -> list[str]:
    """Validate all encountered identifiers against the schema and resources."""
    valid_names = set(schema.get_all_trait_names())
    if resource_names:
        valid_names.update(resource_names)

    errors = []
    for name in _encountered_identifiers:
        if name not in valid_names:
            msg = f'Unknown identifier "{name}" in gate condition.'
            suggestion = _closest_match(name, list(valid_names))
            if suggestion:
                msg += f' Did you mean "{suggestion}"?'
            errors.append(msg)
    return errors
