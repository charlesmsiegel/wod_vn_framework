# tests/test_engine.py
import pickle

from wod_core.engine import Schema, Character
from wod_core.resources import ResourceManager
import pytest


class TestCategoryDef:
    """Test trait category parsing — groups vs. flat traits."""

    def test_groups_format_extracts_trait_names(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        attrs = schema.categories["attributes"]
        assert "Strength" in attrs.trait_names
        assert "Wits" in attrs.trait_names
        assert len(attrs.trait_names) == 9

    def test_flat_traits_format_extracts_trait_names(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        spheres = schema.categories["spheres"]
        assert "Forces" in spheres.trait_names
        assert len(spheres.trait_names) == 9

    def test_category_range_and_default(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        attrs = schema.categories["attributes"]
        assert attrs.range == (1, 5)
        assert attrs.default == 1
        abilities = schema.categories["abilities"]
        assert abilities.range == (0, 5)
        assert abilities.default == 0


class TestSchema:
    """Test schema-level operations."""

    def test_get_all_trait_names(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        names = schema.get_all_trait_names()
        assert "Strength" in names
        assert "Forces" in names
        assert "Arete" in names
        assert "Avatar" in names

    def test_has_trait(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        assert schema.has_trait("Forces") is True
        assert schema.has_trait("Nonexistent") is False

    def test_get_range(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        assert schema.get_range("Strength") == (1, 5)
        assert schema.get_range("Forces") == (0, 5)
        assert schema.get_range("Arete") == (1, 10)

    def test_get_default(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        assert schema.get_default("Strength") == 1
        assert schema.get_default("Forces") == 0
        assert schema.get_default("Arete") == 1

    def test_duplicate_trait_name_raises(self):
        data = {
            "trait_categories": {
                "cat_a": {"traits": ["Duplicate"], "default": 0, "range": [0, 5]},
                "cat_b": {"traits": ["Duplicate"], "default": 0, "range": [0, 5]},
            }
        }
        with pytest.raises(ValueError, match="Duplicate trait name"):
            Schema(data)

    def test_trait_lookup_maps_to_category(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        assert schema.trait_lookup["Strength"] == "attributes"
        assert schema.trait_lookup["Forces"] == "spheres"
        assert schema.trait_lookup["Arete"] == "arete"


class TestCharacter:
    """Test Character creation, get/set/advance."""

    def test_defaults_populated_from_schema(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema)
        assert char.get("Strength") == 1
        assert char.get("Forces") == 0
        assert char.get("Arete") == 1

    def test_init_with_traits(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Strength": 3, "Crafts": 2})
        assert char.get("Strength") == 3
        assert char.get("Crafts") == 2

    def test_set_valid(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema)
        char.set("Strength", 4)
        assert char.get("Strength") == 4

    def test_set_below_range_raises(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema)
        with pytest.raises(ValueError, match="must be between"):
            char.set("Strength", 0)

    def test_set_above_range_raises(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema)
        with pytest.raises(ValueError, match="must be between"):
            char.set("Strength", 6)

    def test_set_unknown_trait_raises(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema)
        with pytest.raises(KeyError, match="Unknown trait"):
            char.set("Nonexistent", 3)

    def test_get_unknown_trait_raises(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema)
        with pytest.raises(KeyError, match="Unknown trait"):
            char.get("Nonexistent")

    def test_advance_increments_by_one(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Strength": 3})
        char.advance("Strength")
        assert char.get("Strength") == 4

    def test_advance_at_max_raises(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Strength": 5})
        with pytest.raises(ValueError, match="must be between"):
            char.advance("Strength")

    def test_has_merit(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        merits = [{"name": "Avatar Companion", "type": "merit", "value": 3}]
        char = Character(schema, merits_flaws=merits)
        assert char.has("Avatar Companion") is True
        assert char.has("Nonexistent") is False


class TestTraitConstraints:
    """Test max_linked constraint (Spheres capped by Arete).

    Design note: constraints are enforced by set() and advance() only.
    Character.__init__ is intentionally lenient so saves can be loaded without
    regard to trait-application order.
    """

    def test_sphere_within_arete_allowed(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Arete": 3, "Forces": 3})
        assert char.get("Forces") == 3

    def test_sphere_exceeding_arete_raises(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Arete": 2})
        with pytest.raises(ValueError, match="cannot exceed Arete"):
            char.set("Forces", 3)

    def test_advance_sphere_past_arete_raises(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Arete": 2, "Forces": 2})
        with pytest.raises(ValueError, match="cannot exceed Arete"):
            char.advance("Forces")

    def test_non_sphere_ignores_constraint(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema)
        char.set("Strength", 5)
        assert char.get("Strength") == 5

    def test_raising_arete_allows_higher_spheres(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Arete": 3, "Forces": 3})
        char.set("Arete", 5)
        char.set("Forces", 5)
        assert char.get("Forces") == 5


class TestBooleanTraits:
    """Boolean (on/off) trait type — Gifts, Edges, binary Discipline powers."""

    def test_default_category_type_is_dots(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        assert schema.categories["attributes"].type == "dots"
        assert schema.categories["spheres"].type == "dots"

    def test_boolean_category_type_parsed(self, boolean_schema_data):
        schema = Schema(boolean_schema_data)
        assert schema.categories["gifts"].type == "boolean"

    def test_boolean_category_default_range_is_0_1(self, boolean_schema_data):
        schema = Schema(boolean_schema_data)
        gifts = schema.categories["gifts"]
        assert gifts.range == (0, 1)
        assert gifts.default == 0

    def test_is_boolean_trait(self, boolean_schema_data):
        schema = Schema(boolean_schema_data)
        assert schema.is_boolean_trait("Sense Wyrm") is True
        assert schema.is_boolean_trait("Strength") is False
        assert schema.is_boolean_trait("Nonexistent") is False

    def test_get_category_type(self, boolean_schema_data):
        schema = Schema(boolean_schema_data)
        assert schema.get_category_type("Sense Wyrm") == "boolean"
        assert schema.get_category_type("Strength") == "dots"

    def test_get_boolean_trait_names(self, boolean_schema_data):
        schema = Schema(boolean_schema_data)
        assert set(schema.get_boolean_trait_names()) == {
            "Sense Wyrm", "Mother's Touch", "Razor Claws", "Falling Touch",
        }

    def test_boolean_trait_rejects_value_above_one(self, boolean_schema_data):
        schema = Schema(boolean_schema_data)
        char = Character(schema)
        with pytest.raises(ValueError, match="must be between"):
            char.set("Sense Wyrm", 2)

    def test_has_true_for_owned_boolean(self, boolean_schema_data):
        schema = Schema(boolean_schema_data)
        char = Character(schema, traits={"Sense Wyrm": 1})
        assert char.has("Sense Wyrm") is True

    def test_has_false_for_unowned_boolean(self, boolean_schema_data):
        schema = Schema(boolean_schema_data)
        char = Character(schema)
        assert char.has("Sense Wyrm") is False

    def test_has_false_for_dot_trait(self, boolean_schema_data):
        # Dot-rated traits never satisfy has(); use gate() for those.
        schema = Schema(boolean_schema_data)
        char = Character(schema, traits={"Strength": 5})
        assert char.has("Strength") is False

    def test_has_still_checks_merits(self, boolean_schema_data):
        schema = Schema(boolean_schema_data)
        char = Character(
            schema, merits_flaws=[{"name": "Brave", "type": "merit", "value": 1}]
        )
        assert char.has("Brave") is True
        assert char.has("Sense Wyrm") is False

    def test_gate_boolean_trait(self, boolean_schema_data):
        schema = Schema(boolean_schema_data)
        char = Character(schema, traits={"Sense Wyrm": 1})
        assert char.gate("Sense Wyrm", ">=", 1) is True
        assert char.gate("Sense Wyrm", "==", 1) is True
        assert char.gate("Razor Claws", ">=", 1) is False
        assert char.gate("Razor Claws", "==", 0) is True

    def test_boolean_type_survives_pickle(self, boolean_schema_data):
        schema = Schema(boolean_schema_data)
        char = Character(schema, traits={"Sense Wyrm": 1})
        restored = pickle.loads(pickle.dumps(char))
        assert restored.schema.is_boolean_trait("Sense Wyrm") is True
        assert restored.schema.categories["gifts"].range == (0, 1)
        assert restored.has("Sense Wyrm") is True
        assert restored.gate("Sense Wyrm", ">=", 1) is True

    def test_has_tracks_temporary_modifier_like_gate(self, boolean_schema_data):
        # has() reads the effective value, so a temporary grant/suppression
        # keeps has() and gate() in agreement.
        schema = Schema(boolean_schema_data)
        char = Character(schema)
        assert char.has("Sense Wyrm") is False

        char.apply_modifier("Sense Wyrm", 1, source="rite")
        assert char.has("Sense Wyrm") is True
        assert char.gate("Sense Wyrm", ">=", 1) is True

        char.remove_modifier("rite")
        assert char.has("Sense Wyrm") is False

        # Suppression: a debuff on an owned Gift hides it from has().
        char.set("Razor Claws", 1)
        char.apply_modifier("Razor Claws", -1, source="curse")
        assert char.has("Razor Claws") is False
        assert char.gate("Razor Claws", ">=", 1) is False


class TestCharacterGate:
    """Test Character.gate() dispatching to traits and resources."""

    def _make_char_with_resources(self, mage_schema_data, mage_resource_data):
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Arete": 3, "Strength": 3, "Forces": 2})
        char.resources = ResourceManager(mage_resource_data)
        char.resources.gain("quintessence", 10)
        return char

    def test_gate_trait_gte_pass(self, mage_schema_data, mage_resource_data):
        char = self._make_char_with_resources(mage_schema_data, mage_resource_data)
        assert char.gate("Strength", ">=", 3) is True

    def test_gate_trait_gte_fail(self, mage_schema_data, mage_resource_data):
        char = self._make_char_with_resources(mage_schema_data, mage_resource_data)
        assert char.gate("Strength", ">=", 4) is False

    def test_gate_trait_eq(self, mage_schema_data, mage_resource_data):
        char = self._make_char_with_resources(mage_schema_data, mage_resource_data)
        assert char.gate("Strength", "==", 3) is True
        assert char.gate("Strength", "==", 4) is False

    def test_gate_trait_neq(self, mage_schema_data, mage_resource_data):
        char = self._make_char_with_resources(mage_schema_data, mage_resource_data)
        assert char.gate("Strength", "!=", 4) is True
        assert char.gate("Strength", "!=", 3) is False

    def test_gate_trait_lt(self, mage_schema_data, mage_resource_data):
        char = self._make_char_with_resources(mage_schema_data, mage_resource_data)
        assert char.gate("Strength", "<", 4) is True
        assert char.gate("Strength", "<", 3) is False

    def test_gate_trait_gt(self, mage_schema_data, mage_resource_data):
        char = self._make_char_with_resources(mage_schema_data, mage_resource_data)
        assert char.gate("Strength", ">", 2) is True
        assert char.gate("Strength", ">", 3) is False

    def test_gate_trait_lte(self, mage_schema_data, mage_resource_data):
        char = self._make_char_with_resources(mage_schema_data, mage_resource_data)
        assert char.gate("Strength", "<=", 3) is True
        assert char.gate("Strength", "<=", 2) is False

    def test_gate_resource(self, mage_schema_data, mage_resource_data):
        char = self._make_char_with_resources(mage_schema_data, mage_resource_data)
        assert char.gate("quintessence", ">=", 5) is True
        assert char.gate("quintessence", ">=", 15) is False

    def test_gate_unknown_raises(self, mage_schema_data, mage_resource_data):
        char = self._make_char_with_resources(mage_schema_data, mage_resource_data)
        with pytest.raises(KeyError, match="Unknown trait or resource"):
            char.gate("nonexistent", ">=", 1)

    def test_gate_bad_operator_raises(self, mage_schema_data, mage_resource_data):
        char = self._make_char_with_resources(mage_schema_data, mage_resource_data)
        with pytest.raises(ValueError, match="Unknown operator"):
            char.gate("Strength", "~", 3)


class TestTraitModifiers:
    """Test temporary stat modifiers (form-shifting, buffs) — issue #33."""

    def test_apply_modifier_changes_get(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Strength": 3})
        char.apply_modifier("Strength", 4, "Crinos")
        assert char.get("Strength") == 7

    def test_base_ignores_modifiers(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Strength": 3})
        char.apply_modifier("Strength", 4, "Crinos")
        assert char.base("Strength") == 3
        assert char.get("Strength") == 7

    def test_modifiers_from_different_sources_stack(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Strength": 2})
        char.apply_modifier("Strength", 4, "Crinos")
        char.apply_modifier("Strength", 1, "Rage Buff")
        assert char.get("Strength") == 7
        assert char.modifier_total("Strength") == 5

    def test_repeated_modifier_from_same_source_accumulates(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Strength": 2})
        char.apply_modifier("Strength", 1, "Buff")
        char.apply_modifier("Strength", 2, "Buff")
        assert char.get("Strength") == 5

    def test_one_source_modifies_multiple_traits(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Strength": 3, "Stamina": 2})
        char.apply_modifier("Strength", 4, "Crinos")
        char.apply_modifier("Stamina", 1, "Crinos")
        assert char.get("Strength") == 7
        assert char.get("Stamina") == 3

    def test_remove_modifier_by_source(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Strength": 3, "Stamina": 2})
        char.apply_modifier("Strength", 4, "Crinos")
        char.apply_modifier("Stamina", 1, "Crinos")
        char.remove_modifier("Crinos")
        assert char.get("Strength") == 3
        assert char.get("Stamina") == 2

    def test_remove_one_source_leaves_others(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Strength": 2})
        char.apply_modifier("Strength", 4, "Crinos")
        char.apply_modifier("Strength", 1, "Rage Buff")
        char.remove_modifier("Crinos")
        assert char.get("Strength") == 3

    def test_remove_unknown_source_is_noop(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Strength": 3})
        char.remove_modifier("Nonexistent")  # should not raise
        assert char.get("Strength") == 3

    def test_clear_modifiers(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Strength": 2})
        char.apply_modifier("Strength", 4, "Crinos")
        char.apply_modifier("Strength", 1, "Rage Buff")
        char.clear_modifiers()
        assert char.get("Strength") == 2
        assert char.modifiers == {}

    def test_modifier_can_exceed_normal_range(self, mage_schema_data):
        # Supernatural forms intentionally push traits past the human maximum.
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Strength": 5})
        char.apply_modifier("Strength", 4, "Crinos")
        assert char.get("Strength") == 9

    def test_negative_modifier_penalty(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Strength": 4})
        char.apply_modifier("Strength", -2, "Wounded")
        assert char.get("Strength") == 2

    def test_modifier_total_zero_when_unmodified(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Strength": 3})
        assert char.modifier_total("Strength") == 0

    def test_apply_modifier_unknown_trait_raises(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema)
        with pytest.raises(KeyError, match="Unknown trait"):
            char.apply_modifier("Nonexistent", 2, "Buff")

    def test_gate_uses_modified_value(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Strength": 3})
        assert char.gate("Strength", ">=", 5) is False
        char.apply_modifier("Strength", 4, "Crinos")
        assert char.gate("Strength", ">=", 5) is True
        assert char.gate("Strength", ">=", 7) is True

    def test_advance_uses_base_not_modified(self, mage_schema_data):
        # Advancing a buffed trait must increment the base, not base+modifier.
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Strength": 3})
        char.apply_modifier("Strength", 1, "Buff")
        char.advance("Strength")
        assert char.base("Strength") == 4
        assert char.get("Strength") == 5

    def test_constraint_uses_base_not_modified(self, mage_schema_data):
        # A temporary Arete buff must not permit permanently raising a Sphere.
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Arete": 2, "Forces": 2})
        char.apply_modifier("Arete", 3, "Time Magic")
        assert char.get("Arete") == 5
        with pytest.raises(ValueError, match="cannot exceed Arete"):
            char.set("Forces", 3)


class TestCategoryDefGroups:
    """Test that CategoryDef preserves group structure."""

    def test_groups_stored_when_present(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        attrs = schema.categories["attributes"]
        assert attrs.groups is not None
        assert "physical" in attrs.groups
        assert attrs.groups["physical"] == ["Strength", "Dexterity", "Stamina"]
        assert attrs.groups["social"] == ["Charisma", "Manipulation", "Appearance"]
        assert attrs.groups["mental"] == ["Perception", "Intelligence", "Wits"]

    def test_groups_none_for_flat_traits(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        spheres = schema.categories["spheres"]
        assert spheres.groups is None

    def test_trait_names_still_flat(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        attrs = schema.categories["attributes"]
        assert len(attrs.trait_names) == 9
        assert "Strength" in attrs.trait_names


class TestCharacterSerialization:
    """Test Character pickle round-trip (for Ren'Py save/load)."""

    def test_pickle_round_trip(self, mage_schema_data):
        from wod_core.resources import ResourceManager
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Strength": 3, "Arete": 3, "Forces": 2},
                        merits_flaws=[{"name": "Test", "type": "merit", "value": 1}],
                        identity={"name": "Pickle Test"})
        char.resources = ResourceManager({
            "resources": {"willpower": {"range": [0, 10], "default_max": 5, "default_current": "max"}},
            "resource_links": {},
        })

        data = pickle.dumps(char)
        restored = pickle.loads(data)

        assert restored.get("Strength") == 3
        assert restored.get("Forces") == 2
        assert restored.identity["name"] == "Pickle Test"
        assert restored.has("Test")
        assert restored.resources.current("willpower") == 5

    def test_pickle_excludes_schema(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Strength": 3})

        state = char.__getstate__()
        assert "schema" not in state
        assert "_schema_data" in state

    def test_pickle_restores_schema(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Strength": 3})

        data = pickle.dumps(char)
        restored = pickle.loads(data)

        # Schema should be reconstructed
        assert restored.schema is not None
        assert restored.schema.has_trait("Strength")
        assert restored.gate("Strength", ">=", 3) is True

    def test_modifiers_excluded_from_state(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Strength": 3})
        char.apply_modifier("Strength", 4, "Crinos")

        state = char.__getstate__()
        assert "modifiers" not in state

    def test_modifiers_do_not_persist_in_saves(self, mage_schema_data):
        # Modifiers are runtime-only; a loaded character has its base values.
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Strength": 3})
        char.apply_modifier("Strength", 4, "Crinos")
        assert char.get("Strength") == 7

        restored = pickle.loads(pickle.dumps(char))
        assert restored.modifiers == {}
        assert restored.get("Strength") == 3
        # Game logic can reapply the modifier after load.
        restored.apply_modifier("Strength", 4, "Crinos")
        assert restored.get("Strength") == 7
