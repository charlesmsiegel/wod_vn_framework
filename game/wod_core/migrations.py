"""Save migration — reconcile saved characters against the current schema.

When an author changes a splat's schema between releases (adds, removes, or
renames traits, or changes ranges), characters saved under the old schema can
fall out of sync with the new one: a renamed trait raises ``KeyError`` when the
script gates on its new name, a tightened range rejects an old value, and so on.

This module versions schemas and migrates saved characters onto the current
schema when a save is loaded:

* The loader registers each splat's current :class:`~wod_core.engine.Schema`
  here at init time (``register_current_schema``), along with its current
  resource config (``register_current_resources``).
* Authors bump the schema's ``version`` whenever they change traits or ranges.
  A version change is what *triggers* migration — same-version loads are left
  untouched, so author-level overrides and template-extended characters keep
  their custom schemas.
* :meth:`Character.__setstate__` calls :func:`migrate_character` when a save's
  recorded schema version differs from the registered current version.

Automatic reconciliation handles the common cases with no author code: traits
absent from the new schema are dropped, brand-new traits are added at their
default, and out-of-range values are clamped. Resource pools are reconciled the
same way: the character's :class:`~wod_core.resources.ResourceManager` is rebuilt
against the splat's current resource config, carrying current values across,
adding pools the new config introduces, and dropping pools it removes. Renames —
where a value should be *preserved* under a new key — need an explicit migration
step (:func:`register_migration` / :func:`migration`), since reconciliation
alone cannot know that ``Old`` became ``New``.

By default migration is graceful: reconcilable changes are applied with logged
warnings and surfaced through a :class:`MigrationReport` (the framework shows a
toast on load). Set :data:`strict` to ``True`` to instead raise
:class:`MigrationError` — with a clear, actionable message — whenever migration
would lose or clamp data, or an author step fails.
"""

from __future__ import annotations

import copy
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

# splat_id -> current resource config dict, populated by the loader at init time.
_current_resources: dict = {}

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


def register_current_resources(splat_id: str, resource_config: dict) -> None:
    """Register a splat's current resource config.

    On a version bump, a loaded character's :class:`ResourceManager` is rebuilt
    from this config so that pools the author added or renamed actually exist on
    the migrated character (see :func:`migrate_character`).
    """
    _current_resources[splat_id] = resource_config


def get_current_resources(splat_id: str):
    """Return the registered current resource config for a splat, or ``None``."""
    return _current_resources.get(splat_id)


def register_migration(
    splat_id: str, from_version, to_version, fn: Callable[[dict], None]
) -> None:
    """Register an author migration step from one schema version to another.

    ``fn`` receives a mutable ``state`` dict and should modify it in place. Keys:

    * ``traits`` -- ``{trait_name: value}`` (rename by moving the value to a
      new key, e.g. ``state["traits"]["New"] = state["traits"].pop("Old")``).
    * ``merits_flaws`` -- list of merit/flaw dicts.
    * ``identity`` -- the identity dict.
    * ``resources`` -- ``{pool_name: current_value}``. You may adjust values and
      rename a pool by moving its value to a new key (e.g.
      ``state["resources"]["Mana"] = state["resources"].pop("Quintessence")``).
      After your steps run, the character's ResourceManager is rebuilt against
      the splat's current resource config: keys naming a pool defined there are
      applied, pools the config adds are created at their default, and keys
      naming no current pool are dropped. So a renamed pool's value survives as
      long as the new pool exists in the current ``resources.yaml``.
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
    _current_resources.clear()
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
    # (trait, old_value, new_value) lowered to satisfy an inter-trait constraint
    constraint_adjusted: list = field(default_factory=list)
    resources_added: list = field(default_factory=list)    # pool names added at default
    resources_dropped: list = field(default_factory=list)  # (pool, lost_value)
    notes: list = field(default_factory=list)         # freeform / author messages

    @property
    def changed(self) -> bool:
        return bool(
            self.added or self.dropped or self.clamped
            or self.constraint_adjusted or self.steps_applied
            or self.resources_added or self.resources_dropped
        )

    def summary(self) -> str:
        """A one-line, player-friendly summary suitable for a toast."""
        parts = []
        if self.steps_applied:
            parts.append(f"{len(self.steps_applied)} migration step(s)")
        added = len(self.added) + len(self.resources_added)
        if added:
            parts.append(f"{added} trait(s) added")
        dropped = len(self.dropped) + len(self.resources_dropped)
        if dropped:
            parts.append(f"{dropped} trait(s) removed")
        adjusted = len(self.clamped) + len(self.constraint_adjusted)
        if adjusted:
            parts.append(f"{adjusted} value(s) adjusted")
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
    """Write snapshot values onto the character's existing pools, in place.

    Fallback used when no current resource config is registered for the splat
    (e.g. the engine used outside a loaded game): values are written only into
    pools that already exist, leaving the pickled ResourceManager's structure
    untouched.
    """
    res = getattr(char, "resources", None)
    if res is None:
        return
    for name, value in snapshot.items():
        pool = res.pools.get(name)
        if pool is not None and isinstance(value, int):
            pool.current_value = value


def _rebuild_resources(char, snapshot: dict, resource_config, report: MigrationReport) -> None:
    """Rebuild the character's ResourceManager onto the current resource config.

    The pickled ResourceManager carries the *old* set of pools, so a migration
    step that introduces or renames a pool (writing a new key into
    ``state["resources"]``) would otherwise be silently ignored. We rebuild the
    manager from the current config and then reconcile values:

    * a pool defined by the current config takes its value from ``snapshot``
      when present (so a renamed pool's value survives), else keeps the config
      default (recorded in ``resources_added``);
    * a ``snapshot`` key naming no current pool is dropped, its value lost
      (recorded in ``resources_dropped`` and treated as data loss in strict
      mode).

    A value carried over that exceeds the pool's configured max raises that max,
    matching how the loader applies character-specific resource values.
    """
    from wod_core.resources import ResourceManager

    new_res = ResourceManager(dict(resource_config))
    for name, value in snapshot.items():
        pool = new_res.pools.get(name)
        if pool is None:
            report.resources_dropped.append((name, value))
            continue
        if isinstance(value, int):
            pool.current_value = value
            if value > pool.max:
                pool.max = value
    for name in new_res.pools:
        if name not in snapshot:
            report.resources_added.append(name)
    char.resources = new_res


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


def _enforce_constraints(char, schema, report: MigrationReport) -> None:
    """Repair inter-trait constraint violations introduced by reconciliation.

    Per-trait range clamping can still leave a constraint unsatisfied — e.g.
    clamping ``Arete`` down below a Sphere that ``MaxLinkedConstraint`` caps by
    it, leaving the loaded character in a state that ``set()`` would reject. For
    each violated constraint, lower the offending trait one step at a time until
    it holds (bounded by the trait's own minimum). Each adjustment is recorded so
    it is reported and, in strict mode, treated as data loss.
    """
    for constraint in getattr(schema, "constraints", []):
        for trait_name in list(char.traits.keys()):
            if not schema.has_trait(trait_name):
                continue
            original = char.traits[trait_name]
            floor = schema.get_range(trait_name)[0]
            while char.traits[trait_name] > floor:
                try:
                    ok, _ = constraint.validate(
                        trait_name, char.traits[trait_name], char, schema
                    )
                except Exception:
                    # Cannot evaluate this constraint (e.g. it references a trait
                    # that no longer exists) — leave the value untouched.
                    break
                if ok:
                    break
                char.traits[trait_name] -= 1
            if char.traits[trait_name] != original:
                report.constraint_adjusted.append(
                    (trait_name, original, char.traits[trait_name])
                )


def _data_loss_message(report: MigrationReport) -> str:
    bits = []
    if report.dropped:
        bits.append("removed trait(s): " + ", ".join(report.dropped))
    if report.clamped:
        bits.append(
            "clamped value(s): "
            + ", ".join(f"{n} {o}→{v}" for n, o, v in report.clamped)
        )
    if report.constraint_adjusted:
        bits.append(
            "constraint-adjusted value(s): "
            + ", ".join(f"{n} {o}→{v}" for n, o, v in report.constraint_adjusted)
        )
    if report.resources_dropped:
        bits.append(
            "removed resource(s): "
            + ", ".join(f"{n} ({v})" for n, v in report.resources_dropped)
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
    current schema version, then reconciles trait data against the new schema and
    rebuilds resource pools against the splat's current resource config. Returns
    a :class:`MigrationReport`; appends it to the pending list (for ``after_load``
    to surface) when it represents real changes. The caller is responsible for
    binding ``char.schema = current_schema``.

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
        "notes": [],
    }

    try:
        chain = _resolve_chain(splat_id, from_version, to_version)
    except MigrationError:
        if strict:
            raise
        logger.warning("Migration chain unresolved for %r; reconciling instead.", splat_id)
        state["notes"].append(f"Unresolved migration chain for {splat_id!r}.")
        chain = []

    for step_from, step_to, fn in chain:
        # Snapshot before the step so that a step which mutates `state` and then
        # raises does not leave half-applied changes behind (e.g. a rename that
        # has popped the old key but not yet written the new one). On failure we
        # discard the step's partial mutations and fall back to reconciliation.
        before = copy.deepcopy(state)
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
            state = before  # roll back this step's partial mutations
            state["notes"].append(msg)
            break
        state["version"] = step_to
        report.steps_applied.append((step_from, step_to))

    report.notes.extend(state["notes"])

    # Write author-mutated collections back onto the character.
    char.traits = dict(state["traits"])
    char.merits_flaws = list(state["merits_flaws"])
    char.identity = dict(state["identity"])

    # Reconcile resource pools. When the splat's current resource config is known
    # (set by the loader), rebuild the ResourceManager onto it so pools an author
    # added or renamed exist and carry their migrated values; otherwise fall back
    # to writing values into the pickled manager's existing pools.
    current_resources = get_current_resources(splat_id)
    if current_resources is not None and getattr(char, "resources", None) is not None:
        _rebuild_resources(char, state["resources"], current_resources, report)
    else:
        _apply_resource_snapshot(char, state["resources"])

    # 2. Reconcile trait keys/values against the current schema, then repair any
    # inter-trait constraints left violated by per-trait clamping.
    _reconcile_traits(char, current_schema, report)
    _enforce_constraints(char, current_schema, report)

    if strict and (
        report.dropped or report.clamped or report.constraint_adjusted
        or report.resources_dropped
    ):
        raise MigrationError(_data_loss_message(report))

    # 3. Record the report.
    if report.changed or report.notes:
        logger.info(report.summary())
        _pending_reports.append(report)
    return report
