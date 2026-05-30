import pytest


@pytest.fixture(autouse=True)
def _isolate_migrations():
    """Reset the global migration registry around every test.

    ``load_splat`` registers a splat's current schema in a module-level registry
    (used by save migration). Clearing it before and after each test keeps tests
    independent and prevents cross-test leakage of registered schemas or the
    ``strict`` flag.
    """
    from wod_core import migrations

    migrations.clear()
    migrations.strict = False
    yield
    migrations.clear()
    migrations.strict = False


@pytest.fixture
def mage_schema_data():
    """Minimal Mage schema dict for testing."""
    return {
        "trait_categories": {
            "attributes": {
                "display_name": "Attributes",
                "groups": {
                    "physical": ["Strength", "Dexterity", "Stamina"],
                    "social": ["Charisma", "Manipulation", "Appearance"],
                    "mental": ["Perception", "Intelligence", "Wits"],
                },
                "default": 1,
                "range": [1, 5],
            },
            "abilities": {
                "display_name": "Abilities",
                "groups": {
                    "talents": ["Alertness", "Awareness"],
                    "skills": ["Crafts", "Technology"],
                    "knowledges": ["Occult", "Science"],
                },
                "default": 0,
                "range": [0, 5],
            },
            "spheres": {
                "display_name": "Spheres",
                "traits": [
                    "Correspondence", "Entropy", "Forces",
                    "Life", "Matter", "Mind",
                    "Prime", "Spirit", "Time",
                ],
                "default": 0,
                "range": [0, 5],
            },
            "arete": {
                "display_name": "Arete",
                "traits": ["Arete"],
                "default": 1,
                "range": [1, 10],
            },
            "backgrounds": {
                "display_name": "Backgrounds",
                "traits": ["Allies", "Avatar", "Mentor", "Node", "Resources"],
                "default": 0,
                "range": [0, 5],
            },
        },
        "trait_constraints": [
            {
                "type": "max_linked",
                "target_category": "spheres",
                "limited_by": "Arete",
                "rule": "No Sphere can exceed Arete rating",
            }
        ],
    }


@pytest.fixture
def boolean_schema_data():
    """Schema with a dot-rated category plus a boolean (Gifts) category.

    The boolean category omits range/default on purpose so tests cover the
    [0, 1] default applied to boolean categories.
    """
    return {
        "trait_categories": {
            "attributes": {
                "display_name": "Attributes",
                "traits": ["Strength", "Dexterity"],
                "default": 1,
                "range": [1, 5],
            },
            "gifts": {
                "display_name": "Gifts",
                "type": "boolean",
                "traits": [
                    "Sense Wyrm",
                    "Mother's Touch",
                    "Razor Claws",
                    "Falling Touch",
                ],
            },
        }
    }


@pytest.fixture
def mage_resource_data():
    """Minimal Mage resource config for testing."""
    return {
        "resources": {
            "quintessence": {
                "display_name": "Quintessence",
                "range": [0, 20],
                "default": 0,
            },
            "paradox": {
                "display_name": "Paradox",
                "range": [0, 20],
                "default": 0,
            },
            "willpower": {
                "display_name": "Willpower",
                "range": [0, 10],
                "default_max": 5,
                "default_current": "max",
            },
            "health": {
                "display_name": "Health",
                "range": [0, 7],
                "default_current": "max",
                "track_type": "levels",
                "levels": [
                    {"name": "Bruised", "penalty": 0},
                    {"name": "Hurt", "penalty": -1},
                    {"name": "Injured", "penalty": -1},
                    {"name": "Wounded", "penalty": -2},
                    {"name": "Mauled", "penalty": -2},
                    {"name": "Crippled", "penalty": -5},
                    {"name": "Incapacitated", "penalty": None},
                ],
            },
        },
        "resource_links": {
            "quintessence_wheel": {
                "pools": ["quintessence", "paradox"],
                "combined_max": 20,
            }
        },
    }
