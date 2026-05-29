# tests/test_paradigm.py
"""Paradigm/Focus gating — Tradition-appropriate casting methods (issue #22)."""

import copy
import os
import pickle

import pytest

import wod_core
from wod_core.engine import Schema, Character, Paradigm, _normalize_tradition
from wod_core.resources import ResourceManager
from wod_core import syntax


GAME_DIR = os.path.join(os.path.dirname(__file__), "..", "game")

# A compact paradigm used across the unit tests.
PARADIGM_DATA = {
    "methods": {
        "code": "Cybernetics & Code",
        "science": "Hypertech & Mad Science",
        "prayer": "Prayer & Faith",
        "ritual": "High Ritual Magick",
        "blood": "Blood Magic",
    },
    "traditions": {
        "virtual_adepts": ["code", "science"],
        "celestial_chorus": ["prayer"],
        "order_of_hermes": ["ritual"],
        "verbena": ["blood", "ritual"],
    },
}


@pytest.fixture
def paradigm_schema_data(mage_schema_data):
    """The minimal Mage schema with a paradigm block attached."""
    data = copy.deepcopy(mage_schema_data)
    data["paradigm"] = copy.deepcopy(PARADIGM_DATA)
    return data


class TestNormalizeTradition:
    """Tradition keys may be written as ids or display names."""

    def test_name_normalizes_to_id(self):
        assert _normalize_tradition("Virtual Adepts") == "virtual_adepts"
        assert _normalize_tradition("Order of Hermes") == "order_of_hermes"
        assert _normalize_tradition("Sons of Ether") == "sons_of_ether"

    def test_id_unchanged(self):
        assert _normalize_tradition("virtual_adepts") == "virtual_adepts"

    def test_handles_hyphens_and_whitespace(self):
        assert _normalize_tradition("  Cult-of-Ecstasy  ") == "cult_of_ecstasy"


class TestParadigmParsing:
    """Parse the various accepted shapes of the paradigm block."""

    def test_methods_dict_keeps_display_names(self):
        p = Paradigm(PARADIGM_DATA)
        assert p.display_name("code") == "Cybernetics & Code"
        assert p.display_name("prayer") == "Prayer & Faith"

    def test_methods_list_of_ids(self):
        p = Paradigm({"methods": ["code", "prayer"], "traditions": {}})
        assert set(p.declared_methods) == {"code", "prayer"}
        # No display name supplied -> falls back to the id.
        assert p.display_name("code") == "code"

    def test_methods_list_of_single_key_dicts(self):
        p = Paradigm({"methods": [{"code": "Code"}, {"prayer": "Prayer"}]})
        assert p.display_name("code") == "Code"
        assert p.display_name("prayer") == "Prayer"

    def test_methods_list_of_id_name_dicts(self):
        p = Paradigm({"methods": [{"id": "code", "name": "Code"}]})
        assert p.display_name("code") == "Code"

    def test_tradition_keys_normalized(self):
        p = Paradigm({"traditions": {"Virtual Adepts": ["code"]}})
        assert p.methods_for("virtual_adepts") == {"code"}
        assert p.methods_for("Virtual Adepts") == {"code"}

    def test_all_methods_unions_registry_and_traditions(self):
        p = Paradigm({"methods": ["code"], "traditions": {"verbena": ["blood", "ritual"]}})
        assert p.all_methods() == {"code", "blood", "ritual"}

    def test_registry_inferred_when_methods_omitted(self):
        p = Paradigm({"traditions": {"verbena": ["blood", "ritual"]}})
        assert p.declared_methods == []
        assert p.all_methods() == {"blood", "ritual"}


class TestMethodsFor:
    """Resolving which methods a Tradition may use."""

    def test_lookup_by_id(self):
        p = Paradigm(PARADIGM_DATA)
        assert p.methods_for("virtual_adepts") == {"code", "science"}

    def test_lookup_by_display_name(self):
        p = Paradigm(PARADIGM_DATA)
        assert p.methods_for("Virtual Adepts") == {"code", "science"}

    def test_unknown_tradition_without_default_is_empty(self):
        p = Paradigm(PARADIGM_DATA)
        assert p.methods_for("Hollow Ones") == set()

    def test_none_tradition_is_empty(self):
        p = Paradigm(PARADIGM_DATA)
        assert p.methods_for(None) == set()

    def test_default_fallback(self):
        data = copy.deepcopy(PARADIGM_DATA)
        data["traditions"]["default"] = ["ritual"]
        p = Paradigm(data)
        assert p.methods_for("Hollow Ones") == {"ritual"}
        assert p.methods_for(None) == {"ritual"}
        # Explicit Traditions still take precedence over default.
        assert p.methods_for("virtual_adepts") == {"code", "science"}


class TestParadigmCanUse:
    def test_can_use_true_and_false(self):
        p = Paradigm(PARADIGM_DATA)
        assert p.can_use("code", "virtual_adepts") is True
        assert p.can_use("prayer", "virtual_adepts") is False
        assert p.can_use("prayer", "Celestial Chorus") is True


class TestSchemaCanUse:
    def test_schema_with_paradigm(self, paradigm_schema_data):
        schema = Schema(paradigm_schema_data)
        assert schema.paradigm is not None
        assert schema.can_use("code", "Virtual Adepts") is True
        assert schema.can_use("prayer", "Virtual Adepts") is False

    def test_schema_without_paradigm_is_permissive(self, mage_schema_data):
        """The system is optional: with no paradigm, nothing is restricted."""
        schema = Schema(mage_schema_data)
        assert schema.paradigm is None
        assert schema.can_use("anything", "Virtual Adepts") is True
        assert schema.can_use("prayer", None) is True


class TestCharacterCanUse:
    def test_uses_identity_tradition(self, paradigm_schema_data):
        schema = Schema(paradigm_schema_data)
        char = Character(schema, identity={"tradition": "Virtual Adepts"})
        assert char.can_use("code") is True
        assert char.can_use("science") is True
        assert char.can_use("prayer") is False

    def test_chorister_can_pray(self, paradigm_schema_data):
        schema = Schema(paradigm_schema_data)
        char = Character(schema, identity={"tradition": "Celestial Chorus"})
        assert char.can_use("prayer") is True
        assert char.can_use("code") is False

    def test_character_without_tradition(self, paradigm_schema_data):
        schema = Schema(paradigm_schema_data)
        char = Character(schema)
        assert char.can_use("code") is False

    def test_permissive_without_paradigm(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema, identity={"tradition": "Virtual Adepts"})
        assert char.can_use("prayer") is True


class TestModuleLevelCanUse:
    def test_set_active_and_can_use(self, paradigm_schema_data):
        schema = Schema(paradigm_schema_data)
        char = Character(schema, identity={"tradition": "Virtual Adepts"})
        wod_core.set_active(char)
        assert wod_core.can_use("code") is True
        assert wod_core.can_use("prayer") is False

    def test_can_use_without_active_raises(self):
        wod_core.set_active(None)
        with pytest.raises(RuntimeError, match="No active character"):
            wod_core.can_use("code")


class TestViaSyntax:
    """Bracket shorthand: [via method] -> wod_core.can_use("method")."""

    def setup_method(self):
        syntax.clear_identifiers()

    def test_parse_via(self):
        assert syntax.parse_condition("via prayer") == 'wod_core.can_use("prayer")'

    def test_parse_via_negated(self):
        assert syntax.parse_condition("!via prayer") == 'not wod_core.can_use("prayer")'

    def test_parse_via_case_insensitive(self):
        assert syntax.parse_condition("VIA code") == 'wod_core.can_use("code")'

    def test_parse_multi_word_method(self):
        assert syntax.parse_condition("via spirit speech") == 'wod_core.can_use("spirit speech")'

    def test_via_does_not_misfire_on_word_starting_with_via(self):
        # "Vianna" has no space after "via" -> treated as a merit check, not a method.
        assert syntax.parse_condition("Vianna") == 'wod_core.has("Vianna")'

    def test_transform_line_via(self):
        line = '    "Pray over the ward" [via prayer]:'
        expected = '    "Pray over the ward" if wod_core.can_use("prayer"):'
        assert syntax.transform_line(line) == expected

    def test_transform_line_mixed_gate_and_via(self):
        line = '    "Rewrite the ward" [Forces >= 3, via code]:'
        expected = '    "Rewrite the ward" if wod_core.gate("Forces", ">=", 3) and wod_core.can_use("code"):'
        assert syntax.transform_line(line) == expected

    def test_clear_identifiers_clears_methods(self):
        syntax.parse_condition("via prayer")
        syntax.clear_identifiers()
        assert syntax._encountered_methods == set()


class TestValidateMethods:
    def setup_method(self):
        syntax.clear_identifiers()

    def test_valid_method_passes(self, paradigm_schema_data):
        schema = Schema(paradigm_schema_data)
        syntax.parse_condition("via code")
        assert syntax.validate_identifiers(schema) == []

    def test_unknown_method_errors_with_suggestion(self, paradigm_schema_data):
        schema = Schema(paradigm_schema_data)
        syntax.parse_condition("via cod")  # typo
        errors = syntax.validate_identifiers(schema)
        assert len(errors) == 1
        assert "cod" in errors[0]
        assert "code" in errors[0]  # did-you-mean

    def test_methods_not_validated_without_paradigm(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        syntax.parse_condition("via whatever")
        # No paradigm registry -> method validation is skipped entirely.
        assert syntax.validate_identifiers(schema) == []


class TestParadigmSerialization:
    """Paradigm must survive Schema.to_dict() and the pickle round-trip (saves)."""

    def test_paradigm_to_dict_round_trip(self):
        p = Paradigm(PARADIGM_DATA)
        reparsed = Paradigm(p.to_dict())
        assert reparsed.methods_for("virtual_adepts") == {"code", "science"}
        assert reparsed.display_name("code") == "Cybernetics & Code"
        assert reparsed.all_methods() == p.all_methods()

    def test_schema_to_dict_includes_paradigm(self, paradigm_schema_data):
        schema = Schema(paradigm_schema_data)
        rebuilt = Schema(schema.to_dict())
        assert rebuilt.can_use("code", "Virtual Adepts") is True
        assert rebuilt.can_use("prayer", "Virtual Adepts") is False

    def test_schema_to_dict_omits_paradigm_when_absent(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        assert "paradigm" not in schema.to_dict()

    def test_pickle_preserves_can_use(self, paradigm_schema_data):
        schema = Schema(paradigm_schema_data)
        char = Character(schema, traits={"Arete": 3, "Forces": 2},
                         identity={"tradition": "Virtual Adepts"})
        char.resources = ResourceManager({"resources": {}, "resource_links": {}})

        restored = pickle.loads(pickle.dumps(char))

        assert restored.can_use("code") is True
        assert restored.can_use("prayer") is False


class TestRealMageParadigm:
    """The shipped Mage schema defines a paradigm for all nine Traditions."""

    def setup_method(self):
        wod_core.init(GAME_DIR)
        wod_core.load_splat("mage")

    def test_schema_has_paradigm(self):
        schema = wod_core.get_loader().loaded_splats["mage"].schema
        assert schema.paradigm is not None
        # Every Tradition in chargen.yaml has a paradigm entry.
        chargen = wod_core.get_loader().loaded_splats["mage"].chargen_config
        for trad in chargen["traditions"]:
            assert schema.paradigm.methods_for(trad["id"]), trad["id"]

    def test_demo_virtual_adept(self):
        char = wod_core.load_character("demo/elena.yaml")
        assert char.can_use("code") is True
        assert char.can_use("science") is True
        # The headline example from the issue: a Virtual Adept can't pray.
        assert char.can_use("prayer") is False

    def test_verbena_and_hermetic_methods(self):
        schema = wod_core.get_loader().loaded_splats["mage"].schema
        verbena = Character(schema, identity={"tradition": "Verbena"})
        assert verbena.can_use("blood") is True
        assert verbena.can_use("code") is False

        hermetic = Character(schema, identity={"tradition": "Order of Hermes"})
        assert hermetic.can_use("ritual") is True
        assert hermetic.can_use("blood") is False
