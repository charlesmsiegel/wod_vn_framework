# tests/test_chargen.py
import os
import pytest
import yaml
from wod_core.chargen import (
    ChargenState,
    PointPool,
    build_character,
    validate_priorities,
)
from wod_core.loader import SplatLoader

GAME_DIR = os.path.join(os.path.dirname(__file__), "..", "game")


def _all_tradition_templates():
    """Collect (tradition, template) pairs from chargen.yaml for parametrization."""
    splat = SplatLoader(GAME_DIR).load_splat("mage")
    return [
        (trad, tmpl)
        for trad in splat.chargen_config.get("traditions", [])
        for tmpl in trad.get("templates", [])
    ]


_TEMPLATE_PARAMS = _all_tradition_templates()
_TEMPLATE_IDS = [
    f"{trad['id']}-{os.path.basename(tmpl['file'])}"
    for trad, tmpl in _TEMPLATE_PARAMS
]


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


class TestPriorityValidation:
    """Priority steps must assign three distinct ranks (issue #14)."""

    def test_valid_distinct_attribute_priorities(self, mage_splat):
        state = ChargenState("mage", "full", mage_splat.schema, mage_splat.chargen_config, mage_splat)
        ok, msg = state.validate_priority_step(
            "attribute_priority", {"physical": 7, "social": 5, "mental": 3}
        )
        assert ok is True
        assert msg == ""

    def test_duplicate_primary_rejected(self, mage_splat):
        # The exact bug from issue #14: Primary (7) assigned to two groups.
        state = ChargenState("mage", "full", mage_splat.schema, mage_splat.chargen_config, mage_splat)
        ok, msg = state.validate_priority_step(
            "attribute_priority", {"physical": 7, "social": 7, "mental": 3}
        )
        assert ok is False
        assert "same rank" in msg

    def test_incomplete_priority_rejected(self, mage_splat):
        # One group left unassigned (0 dots).
        state = ChargenState("mage", "full", mage_splat.schema, mage_splat.chargen_config, mage_splat)
        ok, msg = state.validate_priority_step(
            "attribute_priority", {"physical": 7, "social": 5, "mental": 0}
        )
        assert ok is False
        assert msg

    def test_invalid_rank_values_rejected(self, mage_splat):
        # Distinct, but not the configured 7/5/3 pool.
        state = ChargenState("mage", "full", mage_splat.schema, mage_splat.chargen_config, mage_splat)
        ok, msg = state.validate_priority_step(
            "attribute_priority", {"physical": 7, "social": 5, "mental": 4}
        )
        assert ok is False
        assert msg

    def test_valid_distinct_ability_priorities(self, mage_splat):
        state = ChargenState("mage", "full", mage_splat.schema, mage_splat.chargen_config, mage_splat)
        ok, msg = state.validate_priority_step(
            "ability_priority", {"talents": 13, "skills": 9, "knowledges": 5}
        )
        assert ok is True

    def test_duplicate_ability_priority_rejected(self, mage_splat):
        state = ChargenState("mage", "full", mage_splat.schema, mage_splat.chargen_config, mage_splat)
        ok, msg = state.validate_priority_step(
            "ability_priority", {"talents": 13, "skills": 13, "knowledges": 5}
        )
        assert ok is False
        assert "same rank" in msg

    def test_non_priority_step_passes(self, mage_splat):
        # Steps without a configured rank pool validate trivially.
        state = ChargenState("mage", "full", mage_splat.schema, mage_splat.chargen_config, mage_splat)
        ok, msg = state.validate_priority_step("identity", {"name": "Test"})
        assert ok is True
        assert msg == ""

    def test_validate_priorities_helper_distinct(self):
        ok, msg = validate_priorities({"a": 7, "b": 5, "c": 3}, [7, 5, 3])
        assert ok is True
        assert msg == ""

    def test_validate_priorities_helper_duplicate(self):
        ok, msg = validate_priorities({"a": 7, "b": 7, "c": 3}, [7, 5, 3])
        assert ok is False
        assert "different group" in msg


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


class TestResonance:
    """Test the Resonance system (Dynamic/Entropic/Static)."""

    def test_resonance_types_from_schema(self, mage_splat):
        state = ChargenState("mage", "full", mage_splat.schema, mage_splat.chargen_config, mage_splat)
        assert state.get_resonance_types() == ["Dynamic", "Entropic", "Static"]

    def test_full_build_grants_starting_resonance(self, mage_splat):
        state = ChargenState("mage", "full", mage_splat.schema, mage_splat.chargen_config, mage_splat)
        state.save_step("identity", {
            "name": "Resonant Mage",
            "tradition": "Verbena",
            "resonance": "Dynamic",
        })
        state.save_step("attribute_allocate", {
            "Strength": 2, "Dexterity": 2, "Stamina": 2,
            "Charisma": 2, "Manipulation": 2, "Appearance": 2,
            "Perception": 2, "Intelligence": 2, "Wits": 2,
        })

        char = build_character(state)

        # Chosen type gets the starting dot; the others stay at 0.
        assert char.get("Dynamic") == 1
        assert char.get("Entropic") == 0
        assert char.get("Static") == 0

    def test_simplified_build_grants_starting_resonance(self, mage_splat):
        state = ChargenState("mage", "simplified", mage_splat.schema, mage_splat.chargen_config, mage_splat)
        state.save_step("identity", {
            "name": "Quick Mage",
            "tradition": "Euthanatos",
            "resonance": "Entropic",
        })

        char = build_character(state)

        assert char.get("Entropic") == 1
        assert char.get("Dynamic") == 0

    def test_build_without_resonance_pick_leaves_zero(self, mage_splat):
        state = ChargenState("mage", "full", mage_splat.schema, mage_splat.chargen_config, mage_splat)
        state.save_step("identity", {"name": "Plain Mage", "tradition": "Order of Hermes"})

        char = build_character(state)

        assert char.get("Dynamic") == 0
        assert char.get("Entropic") == 0
        assert char.get("Static") == 0

    def test_template_build_carries_resonance(self, mage_splat):
        state = ChargenState("mage", "template", mage_splat.schema, mage_splat.chargen_config, mage_splat)
        state.save_step("identity", {"name": "Net Runner"})
        state.save_step("template_pick", {
            "tradition": "virtual_adepts",
            "template_file": "templates/va_code_witch.yaml",
        })

        char = build_character(state)

        # va_code_witch.yaml defines Dynamic: 2.
        assert char.get("Dynamic") == 2


class TestTraditionTemplates:
    """Every Tradition ships at least one buildable template (issue #10)."""

    def test_all_nine_traditions_present(self, mage_splat):
        names = {t["name"] for t in mage_splat.chargen_config["traditions"]}
        assert names == {
            "Akashic Brotherhood", "Celestial Chorus", "Cult of Ecstasy",
            "Dreamspeakers", "Euthanatos", "Order of Hermes",
            "Sons of Ether", "Verbena", "Virtual Adepts",
        }

    def test_every_tradition_has_a_template(self, mage_splat):
        for trad in mage_splat.chargen_config["traditions"]:
            assert len(trad.get("templates", [])) >= 1, \
                f"{trad['name']} has no templates"

    @pytest.mark.parametrize("tradition,template", _TEMPLATE_PARAMS, ids=_TEMPLATE_IDS)
    def test_template_builds(self, mage_splat, tradition, template):
        """Each referenced template file loads and builds into a valid Character."""
        state = ChargenState(
            "mage", "template", mage_splat.schema,
            mage_splat.chargen_config, mage_splat,
        )
        state.save_step("identity", {"name": "Test Hero"})
        state.save_step("template_pick", {
            "tradition": tradition["id"],
            "template_file": template["file"],
        })

        char = build_character(state)

        # Player name override applied; tradition matches the config entry.
        assert char.identity["name"] == "Test Hero"
        assert char.identity["tradition"] == tradition["name"]
        # Resources are attached and usable.
        assert char.resources is not None
        assert char.resources.has_resource("willpower")
        # The template leads with its Tradition's affinity Sphere.
        assert char.get(tradition["affinity_sphere"]) >= 1
        # No Sphere exceeds Arete (engine enforces this on build; assert anyway).
        arete = char.get("Arete")
        for sphere in ("Correspondence", "Entropy", "Forces", "Life", "Matter",
                       "Mind", "Prime", "Spirit", "Time"):
            assert char.get(sphere) <= arete

    @pytest.mark.parametrize("tradition,template", _TEMPLATE_PARAMS, ids=_TEMPLATE_IDS)
    def test_template_identity_fields_valid(self, mage_splat, tradition, template):
        """Essence, archetypes, and merits/flaws reference valid chargen entries."""
        path = os.path.join(GAME_DIR, "splats", "mage", template["file"])
        with open(path) as f:
            data = yaml.safe_load(f)

        cfg = mage_splat.chargen_config
        ident = data["identity"]
        assert ident["tradition"] == tradition["name"]
        assert ident["essence"] in cfg["essences"]
        assert ident["nature"] in cfg["archetypes"]
        assert ident["demeanor"] in cfg["archetypes"]

        merit_names = {m["name"] for m in cfg["merits"]}
        flaw_names = {f["name"] for f in cfg["flaws"]}
        for mf in data.get("merits_flaws", []):
            if mf["type"] == "merit":
                assert mf["name"] in merit_names, f"unknown merit {mf['name']!r}"
            elif mf["type"] == "flaw":
                assert mf["name"] in flaw_names, f"unknown flaw {mf['name']!r}"
