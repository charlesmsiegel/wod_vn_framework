"""Tests for save migration across schema changes (issue #20).

These exercise version-aware migration end to end via pickle round-trips, which
is exactly how Ren'Py saves and loads characters: ``__getstate__`` stores a
schema snapshot plus version, and ``__setstate__`` migrates the character onto
the splat's currently-registered schema when the version has changed.
"""

import os
import pickle

import pytest

import wod_core
from wod_core import migrations
from wod_core.engine import Character, Schema
from wod_core.resources import ResourceManager

GAME_DIR = os.path.join(os.path.dirname(__file__), "..", "game")


# --- Helpers ---------------------------------------------------------------


def make_schema(version, traits, rng=(0, 5), default=0):
    """Build a single-category Schema with a flat trait list."""
    return Schema({
        "version": version,
        "trait_categories": {
            "stats": {
                "display_name": "Stats",
                "traits": list(traits),
                "default": default,
                "range": list(rng),
            }
        },
    })


def save_then_load(char, current_schema):
    """Pickle ``char``, register ``current_schema`` as current, then unpickle.

    Returns ``(restored_character, drained_reports)``.
    """
    blob = pickle.dumps(char)
    migrations.register_current_schema(char.splat_id, current_schema)
    restored = pickle.loads(blob)
    return restored, migrations.drain_reports()


# --- Schema versioning -----------------------------------------------------


class TestSchemaVersion:
    def test_version_parsed_from_data(self):
        assert make_schema("2.0", ["A"]).version == "2.0"

    def test_version_defaults_to_zero(self):
        schema = Schema({"trait_categories": {}})
        assert schema.version == "0"

    def test_version_coerced_to_string(self):
        # YAML may parse an unquoted 1.0 as a float.
        assert Schema({"version": 1.5, "trait_categories": {}}).version == "1.5"

    def test_to_dict_round_trips_version(self):
        schema = make_schema("3.1", ["A", "B"], rng=(0, 7), default=1)
        rebuilt = Schema(schema.to_dict())
        assert rebuilt.version == "3.1"
        assert rebuilt.get_range("A") == (0, 7)
        assert rebuilt.get_default("B") == 1
        assert schema.to_dict() == rebuilt.to_dict()


# --- Registry & splat_id wiring -------------------------------------------


class TestRegistryWiring:
    def test_load_splat_registers_current_schema(self):
        wod_core.init(GAME_DIR)
        splat = wod_core.load_splat("mage")
        registered = migrations.get_current_schema("mage")
        assert registered is splat.schema
        assert registered.version == "1.0"

    def test_load_character_records_splat_id(self, tmp_path):
        wod_core.init(GAME_DIR)
        wod_core.load_splat("mage")
        char_yaml = tmp_path / "c.yaml"
        char_yaml.write_text(
            "schema: mage\nidentity:\n  name: X\n"
            "traits:\n  arete:\n    Arete: 2\nresources: {}\nmerits_flaws: []\n"
        )
        char = wod_core.load_character(str(char_yaml))
        assert char.splat_id == "mage"

    def test_get_current_schema_unknown_returns_none(self):
        assert migrations.get_current_schema("nope") is None


# --- Paths that must NOT migrate ------------------------------------------


class TestNoMigration:
    def test_no_splat_id_uses_snapshot(self):
        # Pre-feature / detached characters have no splat_id and are untouched
        # even when some splat's current schema is registered.
        schema = make_schema("1", ["A", "B"])
        migrations.register_current_schema("stats", make_schema("2", ["A"]))
        char = Character(schema, traits={"A": 3, "B": 4})  # splat_id defaults None
        restored, reports = save_then_load(char, make_schema("2", ["A"]))
        assert restored.splat_id is None
        assert restored.get("B") == 4  # snapshot preserved B
        assert reports == []

    def test_same_version_identical_schema_rebinds_to_current(self):
        schema = make_schema("1", ["A", "B"])
        char = Character(schema, traits={"A": 3}, splat_id="stats")
        current = make_schema("1", ["A", "B"])
        restored, reports = save_then_load(char, current)
        # Structurally identical at the same version: bind to the shared object
        # so identity checks (splat.schema is char.schema) succeed.
        assert restored.schema is current
        assert reports == []

    def test_same_version_divergent_schema_keeps_snapshot(self):
        # A template-extended character: same version, wider range. Must keep
        # its own schema rather than being clamped to the canonical one.
        saved = make_schema("1", ["A"], rng=(0, 10))
        char = Character(saved, traits={"A": 9}, splat_id="stats")
        canonical = make_schema("1", ["A"], rng=(0, 5))
        restored, reports = save_then_load(char, canonical)
        assert restored.schema is not canonical
        assert restored.schema.get_range("A") == (0, 10)
        assert restored.get("A") == 9
        assert reports == []

    def test_no_registry_reconstructs_snapshot(self):
        schema = make_schema("1", ["A", "B"])
        char = Character(schema, traits={"A": 2}, splat_id="stats")
        # Nothing registered for "stats".
        blob = pickle.dumps(char)
        restored = pickle.loads(blob)
        assert restored.schema is not None
        assert restored.schema.has_trait("A")
        assert restored.get("A") == 2


# --- Automatic reconciliation ---------------------------------------------


class TestAutomaticReconciliation:
    def test_added_trait_gets_default(self):
        char = Character(make_schema("1", ["A", "B"]), traits={"A": 2}, splat_id="s")
        restored, reports = save_then_load(char, make_schema("2", ["A", "B", "C"], default=0))
        assert restored.get("C") == 0
        assert reports[0].added == ["C"]
        assert restored.schema.has_trait("C")

    def test_removed_trait_is_dropped(self):
        char = Character(make_schema("1", ["A", "B", "C"]), traits={"C": 4}, splat_id="s")
        restored, reports = save_then_load(char, make_schema("2", ["A", "B"]))
        assert "C" not in restored.traits
        assert reports[0].dropped == ["C"]
        with pytest.raises(KeyError):
            restored.get("C")

    def test_value_above_range_is_clamped(self):
        char = Character(make_schema("1", ["A"], rng=(0, 10)), traits={"A": 8}, splat_id="s")
        restored, reports = save_then_load(char, make_schema("2", ["A"], rng=(0, 5)))
        assert restored.get("A") == 5
        assert reports[0].clamped == [("A", 8, 5)]

    def test_value_below_range_is_clamped(self):
        char = Character(make_schema("1", ["A"], rng=(0, 5)), traits={"A": 0}, splat_id="s")
        restored, reports = save_then_load(char, make_schema("2", ["A"], rng=(2, 5)))
        assert restored.get("A") == 2
        assert reports[0].clamped == [("A", 0, 2)]

    def test_rebinds_to_current_schema_object(self):
        char = Character(make_schema("1", ["A"]), traits={"A": 1}, splat_id="s")
        current = make_schema("2", ["A", "B"])
        restored, _ = save_then_load(char, current)
        assert restored.schema is current

    def test_combined_changes_report(self):
        char = Character(
            make_schema("1", ["A", "B", "Old"], rng=(0, 10)),
            traits={"A": 9, "Old": 3},
            splat_id="s",
        )
        restored, reports = save_then_load(char, make_schema("2", ["A", "B", "New"], rng=(0, 5)))
        report = reports[0]
        assert report.clamped == [("A", 9, 5)]
        assert report.dropped == ["Old"]
        assert report.added == ["New"]
        assert report.from_version == "1"
        assert report.to_version == "2"


# --- Author-registered migration steps ------------------------------------


class TestAuthorMigrations:
    def test_rename_preserves_value(self):
        migrations.register_migration(
            "s", "1", "2",
            lambda st: st["traits"].update({"New": st["traits"].pop("Old")}),
        )
        char = Character(make_schema("1", ["Old", "B"]), traits={"Old": 4}, splat_id="s")
        restored, reports = save_then_load(char, make_schema("2", ["New", "B"]))
        assert restored.get("New") == 4
        assert "Old" not in restored.traits
        # The value was preserved, so "New" is not a default-added trait.
        assert reports[0].added == []
        assert reports[0].steps_applied == [("1", "2")]

    def test_decorator_registration(self):
        @migrations.migration("s", "1", "2")
        def _rename(state):  # noqa: ANN001
            state["traits"]["New"] = state["traits"].pop("Old", 0)

        char = Character(make_schema("1", ["Old"]), traits={"Old": 5}, splat_id="s")
        restored, _ = save_then_load(char, make_schema("2", ["New"]))
        assert restored.get("New") == 5

    def test_migration_chain_applies_in_order(self):
        order = []
        migrations.register_migration("s", "1", "2", lambda st: order.append("1->2"))
        migrations.register_migration("s", "2", "3", lambda st: order.append("2->3"))
        char = Character(make_schema("1", ["A"]), traits={"A": 1}, splat_id="s")
        _, reports = save_then_load(char, make_schema("3", ["A"]))
        assert order == ["1->2", "2->3"]
        assert reports[0].steps_applied == [("1", "2"), ("2", "3")]

    def test_chain_transforms_value_through_steps(self):
        migrations.register_migration("s", "1", "2", lambda st: st["traits"].__setitem__("A", st["traits"]["A"] + 1))
        migrations.register_migration("s", "2", "3", lambda st: st["traits"].__setitem__("A", st["traits"]["A"] * 2))
        char = Character(make_schema("1", ["A"], rng=(0, 20)), traits={"A": 2}, splat_id="s")
        restored, _ = save_then_load(char, make_schema("3", ["A"], rng=(0, 20)))
        assert restored.get("A") == (2 + 1) * 2

    def test_missing_link_falls_back_to_reconciliation(self):
        # A step exists for 1->2 but the target is 3; reconciliation covers 2->3.
        migrations.register_migration(
            "s", "1", "2",
            lambda st: st["traits"].update({"New": st["traits"].pop("Old")}),
        )
        char = Character(make_schema("1", ["Old"]), traits={"Old": 3}, splat_id="s")
        restored, reports = save_then_load(char, make_schema("3", ["New", "Extra"]))
        assert restored.get("New") == 3
        assert reports[0].added == ["Extra"]
        assert reports[0].steps_applied == [("1", "2")]

    def test_step_can_adjust_resources(self):
        migrations.register_migration(
            "s", "1", "2",
            lambda st: st["resources"].__setitem__("mana", st["resources"]["mana"] // 2),
        )
        char = Character(make_schema("1", ["A"]), traits={"A": 1}, splat_id="s")
        char.resources = ResourceManager({"resources": {"mana": {"range": [0, 20], "default": 10}}})
        assert char.resources.current("mana") == 10
        restored, _ = save_then_load(char, make_schema("2", ["A"]))
        assert restored.resources.current("mana") == 5

    def test_failing_step_warns_and_proceeds_when_not_strict(self):
        def _boom(state):
            raise RuntimeError("kaboom")

        migrations.register_migration("s", "1", "2", _boom)
        char = Character(make_schema("1", ["A"]), traits={"A": 2}, splat_id="s")
        # Should not raise; reconciliation still runs.
        restored, reports = save_then_load(char, make_schema("2", ["A"]))
        assert restored.get("A") == 2
        assert any("kaboom" in n for n in reports[0].notes)

    def test_cyclic_chain_warns_and_reconciles_when_not_strict(self):
        migrations.register_migration("s", "1", "2", lambda st: None)
        migrations.register_migration("s", "2", "1", lambda st: None)
        char = Character(make_schema("1", ["A"]), traits={"A": 1}, splat_id="s")
        # 1 -> 3 with a 1<->2 cycle: chain resolution detects the cycle, warns,
        # and reconciliation handles the rest.
        restored, reports = save_then_load(char, make_schema("3", ["A"]))
        assert restored.get("A") == 1
        assert any("Unresolved" in n for n in reports[0].notes)

    def test_failed_step_rolls_back_partial_mutation(self):
        # A step that pops the old key and then fails must not leave the data
        # half-migrated: the value should survive via rollback + reconciliation.
        def _bad_rename(state):
            state["traits"]["TEMP"] = state["traits"].pop("Old")
            raise RuntimeError("transform failed")

        migrations.register_migration("s", "1", "2", _bad_rename)
        char = Character(make_schema("1", ["Old", "B"]), traits={"Old": 4, "B": 2}, splat_id="s")
        restored, reports = save_then_load(char, make_schema("2", ["Old", "B"]))
        assert restored.get("Old") == 4          # not lost to the partial pop
        assert "TEMP" not in restored.traits      # partial mutation discarded
        assert any("transform failed" in n for n in reports[0].notes)


# --- Strict mode -----------------------------------------------------------


class TestStrictMode:
    def test_strict_raises_on_dropped_trait(self):
        migrations.strict = True
        char = Character(make_schema("1", ["A", "B", "C"]), traits={"C": 4}, splat_id="s")
        with pytest.raises(migrations.MigrationError) as exc:
            save_then_load(char, make_schema("2", ["A", "B"]))
        assert "C" in str(exc.value)
        assert "data loss" in str(exc.value)

    def test_strict_raises_on_clamp(self):
        migrations.strict = True
        char = Character(make_schema("1", ["A"], rng=(0, 10)), traits={"A": 9}, splat_id="s")
        with pytest.raises(migrations.MigrationError) as exc:
            save_then_load(char, make_schema("2", ["A"], rng=(0, 5)))
        assert "9→5" in str(exc.value) or "9" in str(exc.value)

    def test_strict_raises_on_step_failure(self):
        migrations.strict = True

        def _boom(state):
            raise ValueError("nope")

        migrations.register_migration("s", "1", "2", _boom)
        char = Character(make_schema("1", ["A"]), traits={"A": 1}, splat_id="s")
        with pytest.raises(migrations.MigrationError):
            save_then_load(char, make_schema("2", ["A"]))

    def test_strict_allows_clean_migration(self):
        # Adding traits is not data loss, so strict mode permits it.
        migrations.strict = True
        char = Character(make_schema("1", ["A"]), traits={"A": 1}, splat_id="s")
        restored, _ = save_then_load(char, make_schema("2", ["A", "B"]))
        assert restored.get("B") == 0


# --- Inter-trait constraint reconciliation ---------------------------------


class TestConstraintReconciliation:
    """A version bump that lowers a depended-on trait must not leave the
    character violating an inter-trait constraint (e.g. Sphere <= Arete)."""

    @staticmethod
    def _schema(version, arete_range, sphere_range):
        return Schema({
            "version": version,
            "trait_categories": {
                "arete": {"display_name": "Arete", "traits": ["Arete"],
                          "default": 1, "range": list(arete_range)},
                "spheres": {"display_name": "Spheres", "traits": ["Forces", "Prime"],
                            "default": 0, "range": list(sphere_range)},
            },
            "trait_constraints": [{
                "type": "max_linked", "target_category": "spheres",
                "limited_by": "Arete", "rule": "No Sphere may exceed Arete",
            }],
        })

    def test_sphere_clamped_when_arete_narrowed(self):
        v1 = self._schema("1", (1, 10), (0, 10))
        char = Character(v1, traits={"Arete": 5, "Forces": 5}, splat_id="m")
        v2 = self._schema("2", (1, 3), (0, 10))  # Arete capped at 3 now
        restored, reports = save_then_load(char, v2)
        assert restored.get("Arete") == 3                       # range-clamped
        assert restored.get("Forces") == 3                      # constraint-repaired
        assert ("Forces", 5, 3) in reports[0].constraint_adjusted
        # The loaded character is internally consistent: set() accepts it.
        restored.set("Forces", 3)

    def test_range_clamp_without_constraint_violation(self):
        # Forces is range-clamped, but Arete stays high enough that Sphere<=Arete
        # still holds, so no constraint repair occurs (only the range clamp).
        v1 = self._schema("1", (1, 10), (0, 10))
        char = Character(v1, traits={"Arete": 8, "Forces": 7}, splat_id="m")
        v2 = self._schema("2", (1, 10), (0, 5))
        restored, reports = save_then_load(char, v2)
        assert restored.get("Forces") == 5                 # range-clamped
        assert reports[0].clamped == [("Forces", 7, 5)]
        assert reports[0].constraint_adjusted == []         # constraint untouched

    def test_strict_raises_on_constraint_adjustment(self):
        migrations.strict = True
        v1 = self._schema("1", (1, 10), (0, 10))
        char = Character(v1, traits={"Arete": 5, "Forces": 5}, splat_id="m")
        v2 = self._schema("2", (1, 3), (0, 10))
        with pytest.raises(migrations.MigrationError) as exc:
            save_then_load(char, v2)
        assert "Forces" in str(exc.value)


# --- Resource pool reconciliation -----------------------------------------


class TestResourceReconciliation:
    """On a version bump the ResourceManager is rebuilt onto the splat's current
    resource config, so pools an author adds or renames exist and carry their
    values, and pools removed from the config are dropped."""

    def test_pool_rename_via_step_is_applied(self):
        # The bug Codex flagged: a step renames the Quintessence pool to Mana.
        # The pickled manager has no Mana pool, but rebuilding against the
        # current config (which defines Mana) lets the value land and gate work.
        migrations.register_migration(
            "s", "1", "2",
            lambda st: st["resources"].__setitem__(
                "Mana", st["resources"].pop("Quintessence")
            ),
        )
        migrations.register_current_resources(
            "s", {"resources": {"Mana": {"range": [0, 20], "default": 0}}}
        )
        char = Character(make_schema("1", ["A"]), traits={"A": 1}, splat_id="s")
        char.resources = ResourceManager(
            {"resources": {"Quintessence": {"range": [0, 20], "default": 10}}}
        )
        restored, _ = save_then_load(char, make_schema("2", ["A"]))
        assert restored.resources.has_resource("Mana")
        assert not restored.resources.has_resource("Quintessence")
        assert restored.resources.current("Mana") == 10
        # gate on the renamed pool now succeeds instead of raising KeyError.
        assert restored.gate("Mana", ">=", 10) is True

    def test_added_pool_gets_default_and_existing_value_carries(self):
        migrations.register_current_resources(
            "s", {"resources": {
                "Quintessence": {"range": [0, 20], "default": 0},
                "Paradox": {"range": [0, 20], "default": 3},
            }},
        )
        char = Character(make_schema("1", ["A"]), traits={"A": 1}, splat_id="s")
        char.resources = ResourceManager(
            {"resources": {"Quintessence": {"range": [0, 20], "default": 5}}}
        )
        char.resources.pools["Quintessence"].current_value = 7
        restored, reports = save_then_load(char, make_schema("2", ["A"]))
        assert restored.resources.current("Quintessence") == 7   # carried over
        assert restored.resources.current("Paradox") == 3        # new, at default
        assert "Paradox" in reports[0].resources_added

    def test_pool_removed_from_config_is_dropped(self):
        migrations.register_current_resources(
            "s", {"resources": {"Quintessence": {"range": [0, 20], "default": 0}}}
        )
        char = Character(make_schema("1", ["A"]), traits={"A": 1}, splat_id="s")
        char.resources = ResourceManager({"resources": {
            "Quintessence": {"range": [0, 20], "default": 5},
            "Obsolete": {"range": [0, 10], "default": 4},
        }})
        restored, reports = save_then_load(char, make_schema("2", ["A"]))
        assert restored.resources.has_resource("Quintessence")
        assert not restored.resources.has_resource("Obsolete")
        assert ("Obsolete", 4) in reports[0].resources_dropped

    def test_carried_value_above_pool_max_raises_max(self):
        # Mirrors the loader: a carried-over value beyond the configured max
        # lifts the max rather than silently clamping the player's total.
        migrations.register_current_resources(
            "s", {"resources": {"Willpower": {"range": [0, 10], "default": 5}}}
        )
        char = Character(make_schema("1", ["A"]), traits={"A": 1}, splat_id="s")
        char.resources = ResourceManager(
            {"resources": {"Willpower": {"range": [0, 10], "default": 5}}}
        )
        char.resources.pools["Willpower"].current_value = 8
        restored, _ = save_then_load(char, make_schema("2", ["A"]))
        assert restored.resources.current("Willpower") == 8
        assert restored.resources.pools["Willpower"].max >= 8

    def test_no_registered_config_falls_back_to_existing_pools(self):
        # Without a registered resource config, the pickled manager's pools are
        # reused and only their values updated (legacy behavior preserved).
        migrations.register_migration(
            "s", "1", "2",
            lambda st: st["resources"].__setitem__("mana", 3),
        )
        char = Character(make_schema("1", ["A"]), traits={"A": 1}, splat_id="s")
        char.resources = ResourceManager(
            {"resources": {"mana": {"range": [0, 20], "default": 10}}}
        )
        restored, _ = save_then_load(char, make_schema("2", ["A"]))
        assert restored.resources.current("mana") == 3

    def test_strict_raises_on_dropped_resource(self):
        migrations.strict = True
        migrations.register_current_resources(
            "s", {"resources": {"Quintessence": {"range": [0, 20], "default": 0}}}
        )
        char = Character(make_schema("1", ["A"]), traits={"A": 1}, splat_id="s")
        char.resources = ResourceManager({"resources": {
            "Quintessence": {"range": [0, 20], "default": 5},
            "Obsolete": {"range": [0, 10], "default": 4},
        }})
        with pytest.raises(migrations.MigrationError) as exc:
            save_then_load(char, make_schema("2", ["A"]))
        assert "Obsolete" in str(exc.value)

    def test_strict_allows_added_resource(self):
        # Adding a pool is not data loss, so strict mode permits it.
        migrations.strict = True
        migrations.register_current_resources(
            "s", {"resources": {
                "Quintessence": {"range": [0, 20], "default": 0},
                "Paradox": {"range": [0, 20], "default": 3},
            }},
        )
        char = Character(make_schema("1", ["A"]), traits={"A": 1}, splat_id="s")
        char.resources = ResourceManager(
            {"resources": {"Quintessence": {"range": [0, 20], "default": 5}}}
        )
        restored, _ = save_then_load(char, make_schema("2", ["A"]))
        assert restored.resources.current("Paradox") == 3


# --- Reports & surfacing ---------------------------------------------------


class TestReports:
    def test_summary_mentions_versions(self):
        char = Character(make_schema("1", ["A"]), traits={"A": 1}, splat_id="mage")
        _, reports = save_then_load(char, make_schema("2.0", ["A", "B"]))
        summary = reports[0].summary()
        assert "mage" in summary
        assert "1 → 2.0" in summary
        assert "trait(s) added" in summary

    def test_drain_clears_pending(self):
        char = Character(make_schema("1", ["A"]), traits={"A": 1}, splat_id="s")
        save_then_load(char, make_schema("2", ["A", "B"]))
        # save_then_load already drained once; a second drain is empty.
        assert migrations.drain_reports() == []

    def test_no_report_when_nothing_changed(self):
        # Same trait set, only the version bumped: no added/dropped/clamped.
        char = Character(make_schema("1", ["A", "B"]), traits={"A": 1}, splat_id="s")
        _, reports = save_then_load(char, make_schema("2", ["A", "B"]))
        assert reports == []

    def test_drain_via_public_api(self):
        char = Character(make_schema("1", ["A"]), traits={"A": 1}, splat_id="s")
        blob = pickle.dumps(char)
        migrations.register_current_schema("s", make_schema("2", ["A", "B"]))
        pickle.loads(blob)
        reports = wod_core.drain_migration_reports()
        assert len(reports) == 1


# --- Backward compatibility ------------------------------------------------


class TestBackwardCompat:
    def test_legacy_state_without_splat_id_or_version(self):
        # Emulate a save written before this feature: snapshot only, no
        # splat_id and no _schema_version. It must load and stay on its snapshot
        # even if some splat's schema happens to be registered.
        migrations.register_current_schema("stats", make_schema("9", ["A"]))
        old_schema = make_schema("0", ["A", "B"])
        state = {
            "traits": {"A": 2, "B": 3},
            "merits_flaws": [],
            "identity": {"name": "Legacy"},
            "resources": None,
            "_schema_data": old_schema.to_dict(),
        }
        char = Character.__new__(Character)
        char.__setstate__(state)
        assert char.splat_id is None
        assert char.get("A") == 2
        assert char.get("B") == 3  # not dropped despite registered schema

    def test_existing_pickle_round_trip_still_works(self, mage_schema_data):
        # Mirrors test_engine.TestCharacterSerialization with no registry.
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Strength": 3, "Arete": 3, "Forces": 2})
        restored = pickle.loads(pickle.dumps(char))
        assert restored.get("Strength") == 3
        assert restored.gate("Strength", ">=", 3) is True


# --- Idempotence -----------------------------------------------------------


class TestIdempotence:
    def test_migration_is_not_reapplied_after_first_load(self):
        char = Character(make_schema("1", ["A"]), traits={"A": 1}, splat_id="s")
        current = make_schema("2", ["A", "B"])
        restored, reports = save_then_load(char, current)
        assert len(reports) == 1
        # Re-save the migrated character and load again under the same schema:
        # versions now match, so no further migration occurs.
        restored2, reports2 = save_then_load(restored, current)
        assert reports2 == []
        assert restored2.schema is current
        assert restored2.get("B") == 0


# --- Regression: the bug from issue #20 -----------------------------------


class TestRenameRegression:
    """A renamed trait used to break saves: gating on the new name raised
    KeyError because the loaded character carried the old schema. With a
    migration step the value is preserved and gating works."""

    def test_gate_on_renamed_trait_after_migration(self):
        migrations.register_migration(
            "mage", "1.0", "1.1",
            lambda st: st["traits"].update({"Data": st["traits"].pop("Correspondence")}),
        )
        v1 = make_schema("1.0", ["Correspondence", "Forces"])
        char = Character(v1, traits={"Correspondence": 3}, splat_id="mage")
        restored, _ = save_then_load(char, make_schema("1.1", ["Data", "Forces"]))
        # The new name works and carries the old value.
        assert restored.gate("Data", ">=", 3) is True
        # The old name is gone from the current schema.
        assert restored.schema.has_trait("Correspondence") is False

    def test_without_step_value_is_lost_but_load_succeeds(self):
        # No migration step: the rename looks like drop+add, so the value resets
        # to default rather than crashing the load (graceful degradation).
        v1 = make_schema("1.0", ["Correspondence", "Forces"])
        char = Character(v1, traits={"Correspondence": 3}, splat_id="mage")
        restored, reports = save_then_load(char, make_schema("1.1", ["Data", "Forces"]))
        assert restored.get("Data") == 0
        assert "Correspondence" in reports[0].dropped
        assert "Data" in reports[0].added


# --- Real Mage schema integration -----------------------------------------


class TestRealSchemaIntegration:
    def test_mage_save_migrates_when_sphere_added(self, tmp_path):
        wod_core.init(GAME_DIR)
        splat = wod_core.load_splat("mage")
        char_yaml = tmp_path / "elena.yaml"
        char_yaml.write_text(
            "schema: mage\nidentity:\n  name: Elena\n"
            "traits:\n  arete:\n    Arete: 3\n  spheres:\n    Forces: 3\n"
            "resources:\n  quintessence: 5\nmerits_flaws: []\n"
        )
        char = wod_core.load_character(str(char_yaml))
        blob = pickle.dumps(char)

        # Author adds a new sphere and bumps the version.
        new_data = splat.schema.to_dict()
        new_data["version"] = "1.1"
        new_data["trait_categories"]["spheres"]["traits"].append("Data")
        migrations.register_current_schema("mage", Schema(new_data))

        restored = pickle.loads(blob)
        reports = migrations.drain_reports()
        assert restored.get("Data") == 0
        assert restored.get("Forces") == 3  # existing data preserved
        assert restored.resources.current("quintessence") == 5
        assert reports and "Data" in reports[0].added
