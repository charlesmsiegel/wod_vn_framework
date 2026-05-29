"""Shorthand bracket syntax compiler.

Transforms lines like:
    "Choice text" [Forces >= 3, Prime >= 2]:
    "Pray over it" [via prayer]:
Into:
    "Choice text" if wod_core.gate("Forces", ">=", 3) and wod_core.gate("Prime", ">=", 2):
    "Pray over it" if wod_core.can_use("prayer"):
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

# Paradigm/focus method gate: "via prayer" -> can_use("prayer").
_VIA_RE = re.compile(r'^via\s+(.+)$', re.IGNORECASE)

# Phase 2: identifier validation registry
_encountered_identifiers: set[str] = set()
_encountered_methods: set[str] = set()


def _register_identifier(name: str) -> None:
    _encountered_identifiers.add(name)


def _register_method(name: str) -> None:
    _encountered_methods.add(name)


def clear_identifiers() -> None:
    _encountered_identifiers.clear()
    _encountered_methods.clear()


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

    # Paradigm/focus method gate, optionally negated: "via X" / "!via X".
    neg = _NEGATION_RE.match(cond)
    body = neg.group(1).strip() if neg else cond
    via = _VIA_RE.match(body)
    if via:
        method = via.group(1).strip()
        _register_method(method)
        expr = f'wod_core.can_use("{method}")'
        return f"not {expr}" if neg else expr

    if neg:
        return f'not wod_core.has("{body}")'

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
    """Validate all encountered identifiers against the schema and resources.

    Trait/resource names (from comparison gates) are checked against the schema
    and resource pools. Casting methods (from ``via`` gates) are checked against
    the schema's paradigm registry, when one is defined.
    """
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

    paradigm = getattr(schema, "paradigm", None)
    if paradigm is not None:
        valid_methods = paradigm.all_methods()
        if valid_methods:
            for method in _encountered_methods:
                if method not in valid_methods:
                    msg = f'Unknown casting method "{method}" in via condition.'
                    suggestion = _closest_match(method, list(valid_methods))
                    if suggestion:
                        msg += f' Did you mean "{suggestion}"?'
                    errors.append(msg)

    return errors
