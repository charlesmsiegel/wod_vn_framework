import pytest
from wod_core.engine import Schema, Character
from wod_core.resources import ResourceManager
import wod_core


class TestModuleLevelAPI:
    """Test wod_core.gate(), wod_core.has(), wod_core.set_active()."""

    def _setup(self, mage_schema_data, mage_resource_data):
        schema = Schema(mage_schema_data)
        char = Character(
            schema,
            traits={"Arete": 3, "Strength": 3, "Forces": 2},
            merits_flaws=[{"name": "Avatar Companion", "type": "merit", "value": 3}],
        )
        char.resources = ResourceManager(mage_resource_data)
        char.resources.gain("quintessence", 10)
        wod_core.set_active(char)
        return char

    def test_set_active_and_gate(self, mage_schema_data, mage_resource_data):
        self._setup(mage_schema_data, mage_resource_data)
        assert wod_core.gate("Strength", ">=", 3) is True
        assert wod_core.gate("Forces", ">=", 5) is False

    def test_gate_resource(self, mage_schema_data, mage_resource_data):
        self._setup(mage_schema_data, mage_resource_data)
        assert wod_core.gate("quintessence", ">=", 5) is True

    def test_has(self, mage_schema_data, mage_resource_data):
        self._setup(mage_schema_data, mage_resource_data)
        assert wod_core.has("Avatar Companion") is True
        assert wod_core.has("Nonexistent") is False

    def test_gate_without_active_raises(self):
        wod_core.set_active(None)
        with pytest.raises(RuntimeError, match="No active character"):
            wod_core.gate("Strength", ">=", 1)

    def test_has_without_active_raises(self):
        wod_core.set_active(None)
        with pytest.raises(RuntimeError, match="No active character"):
            wod_core.has("Something")


import os

GAME_DIR = os.path.join(os.path.dirname(__file__), "..", "game")


class TestModuleLoadAPI:
    """Test wod_core.load_splat() and wod_core.load_character()."""

    def test_load_splat(self):
        wod_core.init(GAME_DIR)
        wod_core.load_splat("mage")
        assert "mage" in wod_core.get_loader().loaded_splats

    def test_load_character(self, tmp_path):
        wod_core.init(GAME_DIR)
        wod_core.load_splat("mage")

        char_yaml = tmp_path / "pc.yaml"
        char_yaml.write_text("""
schema: mage
template: default_mage
character_type: pc
identity:
  name: "Test"
traits:
  arete:
    Arete: 3
  spheres:
    Forces: 2
resources:
  quintessence: 5
merits_flaws: []
""")
        char = wod_core.load_character(str(char_yaml))
        assert char.get("Forces") == 2
        assert char.resources.current("quintessence") == 5
