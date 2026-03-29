"""End-to-end integration test: load Mage splat, create character, gate, spend."""

import os
import pytest
import wod_core
from wod_core.syntax import transform_source

GAME_DIR = os.path.join(os.path.dirname(__file__), "..", "game")


class TestMageIntegration:
    """Full workflow: load splat -> load character -> gate -> resources."""

    def setup_method(self):
        wod_core.init(GAME_DIR)
        wod_core.load_splat("mage")

    def test_load_mage_schema_has_all_traits(self):
        splat = wod_core.get_loader().loaded_splats["mage"]
        schema = splat.schema
        assert schema.has_trait("Strength")
        assert schema.has_trait("Forces")
        assert schema.has_trait("Arete")
        assert schema.has_trait("Science")
        assert schema.has_trait("Avatar")
        attrs = schema.categories["attributes"]
        assert len(attrs.trait_names) == 9
        abilities = schema.categories["abilities"]
        assert len(abilities.trait_names) == 33
        spheres = schema.categories["spheres"]
        assert len(spheres.trait_names) == 9

    def test_create_character_and_gate(self, tmp_path):
        char_yaml = tmp_path / "elena.yaml"
        char_yaml.write_text("""
schema: mage
template: default_mage
character_type: pc
identity:
  name: "Elena Vasquez"
  tradition: "Virtual Adepts"
traits:
  attributes:
    Strength: 2
    Dexterity: 3
    Perception: 4
    Intelligence: 3
    Wits: 3
  abilities:
    Science: 4
    Technology: 3
    Occult: 3
    Awareness: 2
    Research: 2
  spheres:
    Forces: 3
    Prime: 2
    Correspondence: 1
  arete:
    Arete: 3
  backgrounds:
    Avatar: 3
    Node: 2
resources:
  quintessence: 5
  paradox: 0
  willpower: 6
merits_flaws:
  - { name: "Avatar Companion", type: merit, value: 3 }
""")
        char = wod_core.load_character(str(char_yaml))
        wod_core.set_active(char)

        assert wod_core.gate("Forces", ">=", 3) is True
        assert wod_core.gate("Forces", ">=", 4) is False
        assert wod_core.gate("Science", ">=", 4) is True
        assert wod_core.gate("Science", "==", 4) is True

        assert wod_core.gate("quintessence", ">=", 5) is True
        assert wod_core.gate("quintessence", ">=", 6) is False

        assert wod_core.has("Avatar Companion") is True
        assert wod_core.has("Nonexistent") is False

    def test_resource_spending_and_linked_pools(self, tmp_path):
        char_yaml = tmp_path / "mage.yaml"
        char_yaml.write_text("""
schema: mage
template: default_mage
character_type: pc
identity:
  name: "Test Mage"
traits:
  arete:
    Arete: 3
resources:
  quintessence: 15
  paradox: 0
merits_flaws: []
""")
        char = wod_core.load_character(str(char_yaml))

        assert char.resources.spend("quintessence", 5) is True
        assert char.resources.current("quintessence") == 10

        char.resources.gain("paradox", 8)
        assert char.resources.current("paradox") == 8
        assert char.resources.current("quintessence") == 10

        char.resources.gain("paradox", 5)
        assert char.resources.current("paradox") == 13
        assert char.resources.current("quintessence") == 7

    def test_trait_advancement_with_constraints(self, tmp_path):
        char_yaml = tmp_path / "learner.yaml"
        char_yaml.write_text("""
schema: mage
template: default_mage
character_type: pc
identity:
  name: "Learning Mage"
traits:
  arete:
    Arete: 2
  spheres:
    Forces: 1
resources: {}
merits_flaws: []
""")
        char = wod_core.load_character(str(char_yaml))

        char.advance("Forces")
        assert char.get("Forces") == 2

        with pytest.raises(ValueError, match="cannot exceed Arete"):
            char.advance("Forces")

        char.set("Arete", 4)
        char.advance("Forces")
        assert char.get("Forces") == 3


class TestSyntaxIntegration:
    """Test syntax compiler with realistic Ren'Py-like script fragments."""

    def test_menu_block_transform(self):
        source = '''\
menu:
    "Rewrite the ward's resonance" [Prime >= 3, Forces >= 2]:
        jump rewrite_ward
    "Perceive the ward's structure" [Prime >= 1]:
        jump perceive_ward
    "Try to push through" [Stamina >= 3]:
        jump brute_force
    "Back away":
        jump retreat'''

        result = transform_source(source)
        assert 'if wod_core.gate("Prime", ">=", 3) and wod_core.gate("Forces", ">=", 2)' in result
        assert 'if wod_core.gate("Prime", ">=", 1)' in result
        assert 'if wod_core.gate("Stamina", ">=", 3)' in result
        assert '"Back away":' in result
        assert "jump retreat" in result
