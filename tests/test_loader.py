# tests/test_loader.py
import os
import pytest
from wod_core.loader import SplatLoader


GAME_DIR = os.path.join(os.path.dirname(__file__), "..", "game")


class TestSplatLoader:
    """Test splat discovery and schema/resource loading."""

    def test_discover_splats(self):
        loader = SplatLoader(GAME_DIR)
        splats = loader.discover_splats()
        assert "mage" in splats

    def test_load_splat_schema(self):
        loader = SplatLoader(GAME_DIR)
        splat = loader.load_splat("mage")
        assert splat.schema.has_trait("Forces")
        assert splat.schema.has_trait("Arete")
        assert splat.schema.get_range("Strength") == (1, 5)

    def test_load_splat_resources(self):
        loader = SplatLoader(GAME_DIR)
        splat = loader.load_splat("mage")
        assert splat.resource_config is not None
        assert "quintessence" in splat.resource_config["resources"]

    def test_load_splat_manifest(self):
        loader = SplatLoader(GAME_DIR)
        splat = loader.load_splat("mage")
        assert splat.manifest["splat"]["id"] == "mage"
        assert splat.manifest["splat"]["edition"] == "M20"


class TestCharacterLoading:
    """Test loading characters from YAML files."""

    def test_load_character_from_file(self, tmp_path):
        char_yaml = tmp_path / "test_char.yaml"
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
  spheres:
    Forces: 3
    Prime: 2
    Correspondence: 1
  arete:
    Arete: 3
resources:
  quintessence: 5
  paradox: 0
  willpower: 6
merits_flaws:
  - { name: "Avatar Companion", type: merit, value: 3 }
""")
        loader = SplatLoader(GAME_DIR)
        loader.load_splat("mage")
        char = loader.load_character(str(char_yaml))

        assert char.identity["name"] == "Elena Vasquez"
        assert char.get("Strength") == 2
        assert char.get("Forces") == 3
        assert char.get("Arete") == 3
        assert char.resources.current("quintessence") == 5
        assert char.has("Avatar Companion") is True

    def test_load_character_validates_constraints(self, tmp_path):
        char_yaml = tmp_path / "bad_char.yaml"
        char_yaml.write_text("""
schema: mage
template: default_mage
character_type: pc
identity:
  name: "Bad Mage"
traits:
  arete:
    Arete: 2
  spheres:
    Forces: 5
resources: {}
merits_flaws: []
""")
        loader = SplatLoader(GAME_DIR)
        loader.load_splat("mage")

        with pytest.raises(ValueError, match="cannot exceed Arete"):
            loader.load_character(str(char_yaml))


class TestChargenConfigLoading:
    """Test that chargen.yaml is loaded from manifest."""

    def test_chargen_config_loaded(self):
        loader = SplatLoader(GAME_DIR)
        splat = loader.load_splat("mage")
        assert splat.chargen_config is not None
        assert "modes" in splat.chargen_config
        assert "traditions" in splat.chargen_config
        assert len(splat.chargen_config["traditions"]) == 9

    def test_chargen_config_has_all_modes(self):
        loader = SplatLoader(GAME_DIR)
        splat = loader.load_splat("mage")
        modes = splat.chargen_config["modes"]
        assert "full" in modes
        assert "simplified" in modes
        assert "template" in modes


class TestResourceMaxFix:
    """Test that resource overrides update max when current > max."""

    def test_willpower_override_updates_max(self, tmp_path):
        char_yaml = tmp_path / "wp_test.yaml"
        char_yaml.write_text("""
schema: mage
template: default_mage
character_type: pc
identity:
  name: "WP Test"
traits:
  arete:
    Arete: 1
resources:
  willpower: 8
merits_flaws: []
""")
        loader = SplatLoader(GAME_DIR)
        loader.load_splat("mage")
        char = loader.load_character(str(char_yaml))

        assert char.resources.current("willpower") == 8
        assert char.resources.pools["willpower"].max == 8


class TestSplatOverrides:
    """Test load_splat with author-level overrides."""

    def test_override_resource_range(self, tmp_path):
        override_yaml = tmp_path / "overrides.yaml"
        override_yaml.write_text("""
extends: mage
overrides:
  resources:
    quintessence:
      range: [0, 30]
""")
        loader = SplatLoader(GAME_DIR)
        splat = loader.load_splat("mage", overrides=str(override_yaml))
        assert splat.resource_config["resources"]["quintessence"]["range"] == [0, 30]
        # Other resources unchanged
        assert splat.resource_config["resources"]["paradox"]["range"] == [0, 20]

    def test_override_append_ability(self, tmp_path):
        override_yaml = tmp_path / "overrides.yaml"
        override_yaml.write_text("""
extends: mage
overrides:
  trait_categories:
    abilities:
      skills:
        append: [Hypertech]
""")
        loader = SplatLoader(GAME_DIR)
        splat = loader.load_splat("mage", overrides=str(override_yaml))
        assert splat.schema.has_trait("Hypertech")
        # Existing traits still present
        assert splat.schema.has_trait("Technology")


class TestTemplateExtension:
    """Test template extends/overrides mechanism."""

    def test_archmage_extends_default(self):
        loader = SplatLoader(GAME_DIR)
        splat = loader.load_splat("mage")

        # archmage.yaml extends default_mage with sphere range [0, 10]
        char = loader.load_character_from_template(
            "mage", "templates/archmage.yaml",
            identity_override={"name": "Archmaster"}
        )
        # Archmage should allow spheres up to 10
        assert char.schema.get_range("Forces") == (0, 10)
        assert char.identity["name"] == "Archmaster"
