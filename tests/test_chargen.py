# tests/test_chargen.py
import os
import pytest
import yaml
from wod_core.chargen import (
    ChargenState,
    PointPool,
    FreebieCalculator,
    MAX_FLAW_POINTS,
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


@pytest.fixture
def full_mode_config(mage_splat):
    """The 'full' chargen mode config (carries freebie costs/points)."""
    return mage_splat.chargen_config["modes"]["full"]


@pytest.fixture
def freebie_calc(mage_splat, full_mode_config):
    """FreebieCalculator built from the real Mage chargen config."""
    return FreebieCalculator.from_config(mage_splat.schema, full_mode_config)


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
        # The nine core Traditions must always be offered. Quasi-Traditions
        # (Hollow Ones) and unaffiliated mages (Orphans) may also appear, so
        # this is a subset check rather than an exact-equality one.
        assert {
            "Akashic Brotherhood", "Celestial Chorus", "Cult of Ecstasy",
            "Dreamspeakers", "Euthanatos", "Order of Hermes",
            "Sons of Ether", "Verbena", "Virtual Adepts",
        } <= names

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
        spheres = ("Correspondence", "Entropy", "Forces", "Life", "Matter",
                   "Mind", "Prime", "Spirit", "Time")
        affinity = tradition["affinity_sphere"]
        if affinity in spheres:
            # The template leads with its Tradition's affinity Sphere.
            assert char.get(affinity) >= 1
        else:
            # Orphans/Disparates have no fixed affinity ("Any"); just require
            # that the template invests in at least one Sphere.
            assert any(char.get(s) >= 1 for s in spheres)
        # No Sphere exceeds Arete (engine enforces this on build; assert anyway).
        arete = char.get("Arete")
        for sphere in spheres:
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


class TestFreebieCostConfig:
    """The chargen config carries the documented M20 freebie costs."""

    def test_per_category_costs_match_m20(self, full_mode_config):
        costs = full_mode_config["freebie_costs"]
        assert costs["attribute"] == 5
        assert costs["ability"] == 2
        assert costs["sphere"] == 7
        assert costs["background"] == 1
        assert costs["willpower"] == 1

    def test_freebie_points_is_15(self, full_mode_config):
        assert full_mode_config["freebie_points"] == 15

    def test_max_flaw_points_is_7(self, full_mode_config):
        assert full_mode_config["max_flaw_points"] == 7

    def test_merits_have_positive_costs(self, mage_splat):
        merits = mage_splat.chargen_config["merits"]
        assert merits  # config defines at least one merit
        for merit in merits:
            assert merit["cost"] > 0, f"{merit['name']} should cost a positive value"

    def test_flaws_have_negative_costs(self, mage_splat):
        flaws = mage_splat.chargen_config["flaws"]
        assert flaws
        for flaw in flaws:
            assert flaw["cost"] < 0, f"{flaw['name']} should have a negative cost"


class TestFreebieCalculatorConstruction:
    """from_config and default construction wire up the expected values."""

    def test_from_config_reads_base_points(self, freebie_calc):
        assert freebie_calc.base_points == 15

    def test_from_config_reads_max_flaw_points(self, freebie_calc):
        assert freebie_calc.max_flaw_points == 7

    def test_default_max_flaw_points_constant(self):
        assert MAX_FLAW_POINTS == 7

    def test_defaults_when_no_config(self, mage_splat):
        # With no freebie_costs supplied, the M20 defaults apply.
        calc = FreebieCalculator(mage_splat.schema)
        assert calc.trait_cost("Strength", 1) == 5
        assert calc.trait_cost("Technology", 1) == 2
        assert calc.trait_cost("Forces", 1) == 7
        assert calc.trait_cost("Avatar", 1) == 1
        assert calc.trait_cost("willpower", 1) == 1
        assert calc.max_flaw_points == 7


class TestFreebieTraitCosts:
    """Per-category dot costs: Attribute=5, Ability=2, Sphere=7, etc."""

    @pytest.mark.parametrize("trait,expected_rate", [
        ("Strength", 5),       # attribute
        ("Intelligence", 5),   # attribute
        ("Technology", 2),     # ability (skill)
        ("Occult", 2),         # ability (knowledge)
        ("Forces", 7),         # sphere
        ("Correspondence", 7), # sphere
        ("Avatar", 1),         # background
        ("Node", 1),           # background
        ("willpower", 1),      # resource (matched by name)
    ])
    def test_cost_rate_per_category(self, freebie_calc, trait, expected_rate):
        assert freebie_calc.cost_rate(trait) == expected_rate

    def test_attribute_dot_costs_5(self, freebie_calc):
        assert freebie_calc.trait_cost("Strength", 1) == 5

    def test_attribute_multiple_dots(self, freebie_calc):
        assert freebie_calc.trait_cost("Strength", 3) == 15

    def test_ability_dot_costs_2(self, freebie_calc):
        assert freebie_calc.trait_cost("Technology", 1) == 2
        assert freebie_calc.trait_cost("Technology", 4) == 8

    def test_sphere_dot_costs_7(self, freebie_calc):
        assert freebie_calc.trait_cost("Forces", 1) == 7
        assert freebie_calc.trait_cost("Forces", 2) == 14

    def test_background_dot_costs_1(self, freebie_calc):
        assert freebie_calc.trait_cost("Avatar", 1) == 1
        assert freebie_calc.trait_cost("Avatar", 5) == 5

    def test_willpower_dot_costs_1(self, freebie_calc):
        # Willpower is a resource, not a schema trait — matched by name.
        assert freebie_calc.trait_cost("willpower", 1) == 1
        assert freebie_calc.trait_cost("willpower", 3) == 3

    def test_zero_dots_cost_nothing(self, freebie_calc):
        assert freebie_calc.trait_cost("Strength", 0) == 0

    def test_negative_dots_cost_nothing(self, freebie_calc):
        assert freebie_calc.trait_cost("Strength", -2) == 0

    def test_uncosted_category_is_free(self, freebie_calc):
        # Arete is a real trait but not a freebie-spendable category.
        assert freebie_calc.cost_rate("Arete") == 0
        assert freebie_calc.trait_cost("Arete", 3) == 0

    def test_unknown_trait_is_free(self, freebie_calc):
        assert freebie_calc.trait_cost("Nonexistent", 2) == 0

    def test_traits_cost_sums_mixed_categories(self, freebie_calc):
        additions = {"Strength": 1, "Technology": 2, "Forces": 1, "Avatar": 3}
        # 1*5 + 2*2 + 1*7 + 3*1 = 19
        assert freebie_calc.traits_cost(additions) == 19

    def test_traits_cost_empty(self, freebie_calc):
        assert freebie_calc.traits_cost({}) == 0


class TestFreebieMerits:
    """Merits cost their listed point value."""

    def test_merit_cost_matches_listed_value(self, freebie_calc):
        assert freebie_calc.merits_cost([{"name": "X", "cost": 3}]) == 3

    def test_multiple_merits_sum(self, freebie_calc):
        merits = [{"name": "A", "cost": 3}, {"name": "B", "cost": 5}]
        assert freebie_calc.merits_cost(merits) == 8

    def test_merit_uses_value_when_cost_absent(self, freebie_calc):
        assert freebie_calc.merits_cost([{"name": "X", "value": 4}]) == 4

    def test_no_merits_cost_nothing(self, freebie_calc):
        assert freebie_calc.merits_cost([]) == 0

    def test_config_merits_charged_listed_value(self, freebie_calc, mage_splat):
        # Each Merit defined in the config is charged exactly its listed cost.
        for merit in mage_splat.chargen_config["merits"]:
            assert freebie_calc.merits_cost([merit]) == merit["cost"]


class TestFreebieFlawCap:
    """Flaws grant freebie points, capped at 7 (M20 standard)."""

    def test_flaw_points_below_cap(self, freebie_calc):
        assert freebie_calc.flaw_points([{"name": "Blind", "cost": -6}]) == 6

    def test_flaw_points_exactly_at_cap(self, freebie_calc):
        flaws = [{"name": "Blind", "cost": -6}, {"name": "Nightmares", "cost": -1}]
        assert freebie_calc.flaw_points(flaws) == 7

    def test_flaw_points_capped_above_seven(self, freebie_calc):
        flaws = [{"name": "Blind", "cost": -6}, {"name": "Sphere Inept", "cost": -5}]
        assert freebie_calc.raw_flaw_points(flaws) == 11
        assert freebie_calc.flaw_points(flaws) == 7  # capped

    def test_raw_flaw_points_uncapped(self, freebie_calc):
        flaws = [{"cost": -6}, {"cost": -5}, {"cost": -1}]
        assert freebie_calc.raw_flaw_points(flaws) == 12

    def test_no_flaws_grant_nothing(self, freebie_calc):
        assert freebie_calc.flaw_points([]) == 0
        assert freebie_calc.raw_flaw_points([]) == 0

    def test_can_add_flaw_within_cap(self, freebie_calc):
        assert freebie_calc.can_add_flaw([{"cost": -6}], {"cost": -1}) is True

    def test_can_add_flaw_exactly_filling_cap(self, freebie_calc):
        assert freebie_calc.can_add_flaw([], {"cost": -7}) is True

    def test_cannot_add_flaw_exceeding_cap(self, freebie_calc):
        assert freebie_calc.can_add_flaw([{"cost": -6}], {"cost": -5}) is False

    def test_cannot_add_flaw_when_already_at_cap(self, freebie_calc):
        assert freebie_calc.can_add_flaw([{"cost": -7}], {"cost": -1}) is False

    def test_cap_is_configurable(self, mage_splat):
        calc = FreebieCalculator(mage_splat.schema, max_flaw_points=5)
        assert calc.flaw_points([{"cost": -6}]) == 5


class TestFreebieBudget:
    """Budget, spending, remaining, and validity."""

    def test_base_budget_no_flaws(self, freebie_calc):
        assert freebie_calc.total_budget([]) == 15

    def test_budget_includes_flaw_points(self, freebie_calc):
        flaws = [{"cost": -6}, {"cost": -1}]
        assert freebie_calc.total_budget(flaws) == 22  # 15 + 7

    def test_budget_caps_flaw_contribution(self, freebie_calc):
        # 11 raw flaw points only add the capped 7 to the budget.
        flaws = [{"cost": -6}, {"cost": -5}]
        assert freebie_calc.total_budget(flaws) == 22

    def test_total_spent_traits_and_merits(self, freebie_calc):
        spent = freebie_calc.total_spent({"Strength": 1}, [{"cost": 3}])
        assert spent == 8  # 5 + 3

    def test_remaining_within_budget(self, freebie_calc):
        remaining = freebie_calc.remaining({"Strength": 1}, [{"cost": 3}], [])
        assert remaining == 7  # 15 - 8

    def test_remaining_with_flaw_refund(self, freebie_calc):
        remaining = freebie_calc.remaining({}, [], [{"cost": -6}])
        assert remaining == 21  # (15 + 6) - 0

    def test_is_valid_within_budget(self, freebie_calc):
        assert freebie_calc.is_valid({"Strength": 1}, [{"cost": 3}], []) is True

    def test_is_valid_exactly_at_budget(self, freebie_calc):
        # 3 sphere dots = 21; budget 15 + 6 flaw = 21 → exactly spent.
        assert freebie_calc.remaining({"Forces": 3}, [], [{"cost": -6}]) == 0
        assert freebie_calc.is_valid({"Forces": 3}, [], [{"cost": -6}]) is True

    def test_overspend_is_invalid(self, freebie_calc):
        # 3 sphere dots = 21 > 15 budget.
        assert freebie_calc.remaining({"Forces": 3}, [], []) == -6
        assert freebie_calc.is_valid({"Forces": 3}, [], []) is False

    def test_flaws_beyond_cap_do_not_fund_overspend(self, freebie_calc):
        # Selecting 11 raw flaw points only funds 7, so a 22-point spend fails
        # if it relied on more than the cap.
        flaws = [{"cost": -6}, {"cost": -5}]  # raw 11, capped 7 → budget 22
        # Spend 4 attributes (20) + 1 background (1) = 21 ≤ 22 → valid
        assert freebie_calc.is_valid({"Strength": 4, "Avatar": 1}, [], flaws) is True
        # Spend 4 attributes (20) + 3 backgrounds (3) = 23 > 22 → invalid
        assert freebie_calc.is_valid({"Strength": 4, "Avatar": 3}, [], flaws) is False
