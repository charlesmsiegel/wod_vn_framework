"""Save migration — reconcile saved characters against the current schema.

When an author changes a splat's schema between releases (adds, removes, or
renames traits, or changes ranges), characters saved under the old schema can
fall out of sync with the new one: a renamed trait raises ``KeyError`` when the
script gates on its new name, a tightened range rejects an old value, and so on.

This module versions schemas and migrates saved characters onto the current
schema when a save is loaded:

* The loader registers each splat's current :class:`~wod_core.engine.Schema`
  here at init time (``register_current_schema``).
* Authors bump the schema's ``version`` whenever they change traits or ranges.
  A version change is what *triggers* migration — same-version loads are left
  untouched, so author-level overrides and template-extended characters keep
  their custom schemas.
* :meth:`Character.__setstate__` calls :func:`migrate_character` when a save's
  recorded schema version differs from the registered current version.

Automatic reconciliation handles the common cases with no author code: traits
absent from the new schema are dropped, brand-new traits are added at their
default, and out-of-range values are clamped. Renames — where a value should be
*preserved* under a new key — need an explicit migration step
(:func:`register_migration` / :func:`migration`), since reconciliation alone
cannot know that ``Old`` became ``New``.

By default migration is graceful: reconcilable changes are applied with logged
warnings and surfaced through a :class:`MigrationReport` (the framework shows a
toast on load). Set :data:`strict` to ``True`` to instead raise
:class:`MigrationError` — with a clear, actionable message — whenever migration
would lose or clamp data, or an author step fails.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable

logger = logging.getLogger("wod_core.migrations")


class MigrationError(Exception):
    """Raised when a saved character cannot be migrated to the current schema."""


# --- Configuration ---------------------------------------------------------

#: When True, reconciliation that would drop or clamp trait data (or an author
#: migration step that raises) aborts the load with a :class:`MigrationError`
#: carrying a clear message, rather than warning and proceeding.
strict: bool = False


# --- Registry --------------------------------------------------------------

# splat_id -> current Schema, populated by the loader at init time.
_current_schemas: dict = {}

# splat_id -> list of (from_version, to_version, fn) author migration steps.
_migration_steps: dict = {}

# MigrationReports produced since the last drain, surfaced after a save loads.
_pending_reports: list = []


def register_current_schema(splat_id: str, schema) -> None:
    """Register a splat's current schema so loaded saves can be migrated onto it."""
    _current_schemas[splat_id] = schema


def get_current_schema(splat_id: str):
    """Return the registered current schema for a splat, or ``None``."""
    return _current_schemas.get(splat_id)


def register_migration(
    splat_id: str, from_version, to_version, fn: Callable[[dict], None]
) -> None:
    """Register an author migration step from one schema version to another.

    ``fn`` receives a mutable ``state`` dict and should modify it in place. Keys:

    * ``traits`` -- ``{trait_name: value}`` (rename by moving the value to a
      new key, e.g. ``state["traits"]["New"] = state["traits"].pop("Old")``).
    * ``merits_flaws`` -- list of merit/flaw dicts.
    * ``identity`` -- the identity dict.
    * ``resources`` -- ``{pool_name: current_value}`` for existing pools (you
      may adjust values; renaming a *pool* is not handled automatically).
    * ``version`` / ``splat_id`` -- read-only context.
    * ``notes`` -- a list you may append human-readable messages to; they are
      included in the migration report.

    Steps are chained by exact version string (``from_version`` -> ``to_version``);
    gaps are tolerated (automatic reconciliation covers them).
    """
    _migration_steps.setdefault(splat_id, []).append(
        (str(from_version), str(to_version), fn)
    )


def migration(splat_id: str, from_version, to_version):
    """Decorator form of :func:`register_migration`.

    ::

        @wod_core.migration("mage", "1.0", "1.1")
        def _rename_correspondence(state):
            if "Correspondence" in state["traits"]:
                state["traits"]["Data"] = state["traits"].pop("Correspondence")
    """

    def decorator(fn: Callable[[dict], None]) -> Callable[[dict], None]:
        register_migration(splat_id, from_version, to_version, fn)
        return fn

    return decorator


def clear() -> None:
    """Reset all registry state. Primarily for tests."""
    _current_schemas.clear()
    _migration_steps.clear()
    _pending_reports.clear()


def drain_reports() -> list:
    """Return and clear the migration reports accumulated since the last drain.

    Called from the framework's ``after_load`` hook to surface a notification.
    """
    reports = list(_pending_reports)
    _pending_reports.clear()
    return reports


# --- Report ----------------------------------------------------------------


@dataclass
class MigrationReport:
    """A record of what changed when a save was migrated onto a new schema."""

    splat_id: str
    from_version: str
    to_version: str
    added: list = field(default_factory=list)       # trait names added at default
    dropped: list = field(default_factory=list)      # trait names removed
    clamped: list = field(default_factory=list)      # (trait, old_value, new_value)
    steps_applied: list = field(default_factory=list)  # (from_version, to_version)
    notes: list = field(default_factory=list)         # freeform / author messages

    @property
    def changed(self) -> bool:
        return bool(self.added or self.dropped or self.clamped or self.steps_applied)

    def summary(self) -> str:
        """A one-line, player-friendly summary suitable for a toast."""
        parts = []
        if self.steps_applied:
            parts.append(f"{len(self.steps_applied)} migration step(s)")
        if self.added:
            parts.append(f"{len(self.added)} trait(s) added")
        if self.dropped:
            parts.append(f"{len(self.dropped)} trait(s) removed")
        if self.clamped:
            parts.append(f"{len(self.clamped)} value(s) adjusted")
        detail = ", ".join(parts) if parts else "no changes"
        return (
            f"Save updated: {self.splat_id} schema "
            f"{self.from_version} → {self.to_version} ({detail})."
        )


# --- Migration -------------------------------------------------------------


def _resolve_chain(splat_id: str, from_version: str, to_version: str) -> list:
    """Return author migration steps chaining ``from_version`` to ``to_version``.

    Matches steps by exact ``from_version``. Missing links are allowed (automatic
    reconciliation covers them); a cycle raises :class:`MigrationError`.
    """
    by_from: dict = {}
    for step in _migration_steps.get(splat_id, []):
        by_from.setdefault(step[0], step)  # first registered step per from-version
    chain = []
    version = from_version
    seen = set()
    while version != to_version:
        if version in seen:
            raise MigrationError(
                f"Cyclic migration steps for splat {splat_id!r} at version {version!r}."
            )
        seen.add(version)
        step = by_from.get(version)
        if step is None:
            break  # no further author step — reconciliation handles the rest
        chain.append(step)
        version = step[1]
    return chain


def _resource_snapshot(char) -> dict:
    res = getattr(char, "resources", None)
    if res is None:
        return {}
    return {name: pool.current_value for name, pool in res.pools.items()}


def _apply_resource_snapshot(char, snapshot: dict) -> None:
    res = getattr(char, "resources", None)
    if res is None:
        return
    for name, value in snapshot.items():
        pool = res.pools.get(name)
        if pool is not None and isinstance(value, int):
            pool.current_value = value


def _reconcile_traits(char, schema, report: MigrationReport) -> None:
    """Bring ``char.traits`` into line with ``schema``: drop, clamp, add defaults."""
    reconciled: dict = {}
    for name, value in char.traits.items():
        if not schema.has_trait(name):
            report.dropped.append(name)
            continue
        if not isinstance(value, int):
            new_value = schema.get_default(name)
            report.clamped.append((name, value, new_value))
            reconciled[name] = new_value
            continue
        lo, hi = schema.get_range(name)
        if value < lo:
            report.clamped.append((name, value, lo))
            value = lo
        elif value > hi:
            report.clamped.append((name, value, hi))
            value = hi
        reconciled[name] = value

    for name in schema.get_all_trait_names():
        if name not in reconciled:
            reconciled[name] = schema.get_default(name)
            report.added.append(name)

    char.traits = reconciled


def _data_loss_message(report: MigrationReport) -> str:
    bits = []
    if report.dropped:
        bits.append("removed trait(s): " + ", ".join(report.dropped))
    if report.clamped:
        bits.append(
            "clamped value(s): "
            + ", ".join(f"{n} {o}→{v}" for n, o, v in report.clamped)
        )
    return (
        f"Cannot migrate {report.splat_id} save from schema "
        f"{report.from_version} to {report.to_version} without data loss "
        f"({'; '.join(bits)}). Register a migration step to preserve this data, "
        f"or set wod_core.migrations.strict = False to reconcile automatically."
    )


def migrate_character(char, saved_version, current_schema) -> MigrationReport:
    """Migrate a freshly-unpickled ``char`` onto ``current_schema``, in place.

    Runs any registered author migration steps from ``saved_version`` to the
    current schema version, then reconciles trait data against the new schema.
    Returns a :class:`MigrationReport`; appends it to the pending list (for
    ``after_load`` to surface) when it represents real changes. The caller is
    responsible for binding ``char.schema = current_schema``.

    Raises :class:`MigrationError` when :data:`strict` is set and migration
    would lose data or an author step fails.
    """
    splat_id = getattr(char, "splat_id", None)
    from_version = "0" if saved_version is None else str(saved_version)
    to_version = current_schema.version
    report = MigrationReport(splat_id, from_version, to_version)

    # 1. Run author migration steps over a mutable state dict.
    state = {
        "version": from_version,
        "splat_id": splat_id,
        "traits": dict(getattr(char, "traits", {}) or {}),
        "merits_flaws": list(getattr(char, "merits_flaws", []) or []),
        "identity": dict(getattr(char, "identity", {}) or {}),
        "resources": _resource_snapshot(char),
        "notes": report.notes,
    }

    try:
        chain = _resolve_chain(splat_id, from_version, to_version)
    except MigrationError:
        if strict:
            raise
        logger.warning("Migration chain unresolved for %r; reconciling instead.", splat_id)
        report.notes.append(f"Unresolved migration chain for {splat_id!r}.")
        chain = []

    for step_from, step_to, fn in chain:
        try:
            fn(state)
        except Exception as exc:  # noqa: BLE001 — surface author step failures
            msg = (
                f"Migration step {step_from} → {step_to} for splat "
                f"{splat_id!r} failed: {exc}"
            )
            if strict:
                raise MigrationError(msg) from exc
            logger.warning(msg)
            report.notes.append(msg)
            break
        state["version"] = step_to
        report.steps_applied.append((step_from, step_to))

    # Write author-mutated collections back onto the character.
    char.traits = dict(state["traits"])
    char.merits_flaws = list(state["merits_flaws"])
    char.identity = dict(state["identity"])
    _apply_resource_snapshot(char, state["resources"])

    # 2. Reconcile trait keys/values against the current schema.
    _reconcile_traits(char, current_schema, report)

    if strict and (report.dropped or report.clamped):
        raise MigrationError(_data_loss_message(report))

    # 3. Record the report.
    if report.changed or report.notes:
        logger.info(report.summary())
        _pending_reports.append(report)
    return report
