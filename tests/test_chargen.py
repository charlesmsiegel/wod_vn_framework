# tests/test_chargen.py
import os
import pytest
from wod_core.chargen import ChargenState, PointPool, build_character
from wod_core.loader import SplatLoader

GAME_DIR = os.path.join(os.path.dirname(__file__), "..", "game")


@pytest.fixture
def mage_splat():
    loader = SplatLoader(GAME_DIR)
    return loader.load_splat("mage")


class TestChargenState:
    """Test ChargenState initialization and step management."""

    def test_full_mode_steps(self, mage_splat):
        state = ChargenState("mage", "full", mage_splat.schema, mage_splat.chargen_config, mage_splat)
        assert state.mode == "full"
        assert len(state.steps) == 8
        assert state.steps[0] == "identity"
        assert state.steps[-1] == "review"

    def test_simplified_mode_steps(self, mage_splat):
        state = ChargenState("mage", "simplified", mage_splat.schema, mage_splat.chargen_config, mage_splat)
        assert len(state.steps) == 5

    def test_template_mode_steps(self, mage_splat):
        state = ChargenState("mage", "template", mage_splat.schema, mage_splat.chargen_config, mage_splat)
        assert len(state.steps) == 3

    def test_initial_state(self, mage_splat):
        state = ChargenState("mage", "full", mage_splat.schema, mage_splat.chargen_config, mage_splat)
        assert state.current_step == 0
        assert state.data == {}
        assert len(state.completed) == 0

    def test_save_step_data(self, mage_splat):
        state = ChargenState("mage", "full", mage_splat.schema, mage_splat.chargen_config, mage_splat)
        state.save_step("identity", {"name": "Test", "tradition": "Virtual Adepts"})
        assert "identity" in state.data
        assert state.data["identity"]["name"] == "Test"

    def test_complete_step(self, mage_splat):
        state = ChargenState("mage", "full", mage_splat.schema, mage_splat.chargen_config, mage_splat)
        state.save_step("identity", {"name": "Test"})
        state.complete_step(0)
        assert 0 in state.completed

    def test_invalidate_step(self, mage_splat):
        state = ChargenState("mage", "full", mage_splat.schema, mage_splat.chargen_config, mage_splat)
        state.save_step("attribute_priority", {"physical": 7, "social": 5, "mental": 3})
        state.complete_step(1)
        state.save_step("attribute_allocate", {"Strength": 4})
        state.complete_step(2)
        # Changing priority should invalidate allocation
        state.invalidate_dependents("attribute_priority")
        assert 2 not in state.completed
        assert "attribute_allocate" not in state.data

    def test_tradition_change_invalidates_spheres(self, mage_splat):
        state = ChargenState("mage", "full", mage_splat.schema, mage_splat.chargen_config, mage_splat)
        state.save_step("identity", {"tradition": "Virtual Adepts"})
        state.complete_step(0)
        state.save_step("spheres_backgrounds", {"Forces": 2})
        state.complete_step(5)
        # Change identity (tradition change)
        state.save_step("identity", {"tradition": "Verbena"})
        state.invalidate_dependents("identity")
        assert 5 not in state.completed


class TestPointPool:
    """Test point pool allocation and validation."""

    def test_allocate_within_budget(self):
        pool = PointPool(total=7, per_trait_max=5)
        assert pool.allocate("Strength", 3) is True
        assert pool.allocate("Dexterity", 2) is True
        assert pool.remaining == 2

    def test_allocate_exceeds_budget(self):
        pool = PointPool(total=7, per_trait_max=5)
        pool.allocate("Strength", 5)
        assert pool.allocate("Dexterity", 3) is False
        assert pool.remaining == 2

    def test_allocate_exceeds_per_trait_max(self):
        pool = PointPool(total=15, per_trait_max=5)
        assert pool.allocate("Strength", 6) is False

    def test_deallocate(self):
        pool = PointPool(total=7, per_trait_max=5)
        pool.allocate("Strength", 3)
        pool.deallocate("Strength", 1)
        assert pool.get("Strength") == 2
        assert pool.remaining == 5

    def test_get_allocations(self):
        pool = PointPool(total=7, per_trait_max=5)
        pool.allocate("Strength", 3)
        pool.allocate("Dexterity", 2)
        allocs = pool.get_all()
        assert allocs == {"Strength": 3, "Dexterity": 2}

    def test_reset(self):
        pool = PointPool(total=7, per_trait_max=5)
        pool.allocate("Strength", 3)
        pool.reset()
        assert pool.remaining == 7
        assert pool.get_all() == {}


class TestBuildCharacter:
    """Test converting ChargenState into a Character."""

    def test_build_from_full_state(self, mage_splat):
        state = ChargenState("mage", "full", mage_splat.schema, mage_splat.chargen_config, mage_splat)
        state.save_step("identity", {
            "name": "Test Mage",
            "tradition": "Virtual Adepts",
            "essence": "Dynamic",
            "nature": "Visionary",
            "demeanor": "Architect",
        })
        state.save_step("attribute_allocate", {
            "Strength": 2, "Dexterity": 3, "Stamina": 2,
            "Charisma": 2, "Manipulation": 3, "Appearance": 1,
            "Perception": 3, "Intelligence": 4, "Wits": 2,
        })
        state.save_step("ability_allocate", {
            "Technology": 3, "Science": 2, "Computer": 2,
        })
        state.save_step("spheres_backgrounds", {
            "spheres": {"Correspondence": 1, "Forces": 1, "Mind": 1},
            "backgrounds": {"Avatar": 2, "Node": 1},
        })
        state.save_step("freebies", {
            "trait_additions": {},
            "merits": [{"name": "Natural Channel", "type": "merit", "value": 3}],
            "flaws": [],
        })

        char = build_character(state)

        assert char.identity["name"] == "Test Mage"
        assert char.get("Strength") == 2
        assert char.get("Intelligence") == 4
        assert char.get("Technology") == 3
        assert char.get("Correspondence") == 1
        assert char.get("Arete") == 1  # starting arete (default)
        assert char.has("Natural Channel")
        assert char.resources is not None
        assert char.resources.has_resource("quintessence")
        assert char.resources.has_resource("willpower")

    def test_build_from_template(self, mage_splat):
        state = ChargenState("mage", "template", mage_splat.schema, mage_splat.chargen_config, mage_splat)
        state.save_step("identity", {"name": "Elena"})
        state.save_step("template_pick", {
            "tradition": "virtual_adepts",
            "template_file": "templates/va_code_witch.yaml",
        })

        char = build_character(state)

        assert char.identity["name"] == "Elena"
        assert char.get("Correspondence") == 3  # from template
        assert char.resources is not None
