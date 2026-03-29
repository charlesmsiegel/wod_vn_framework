# tests/test_chargen.py
import os
import pytest
from wod_core.chargen import ChargenState
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
