# tests/test_engine.py
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
