# WoD VN Framework Core Engine — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the core Python engine for the WoD VN framework — schema loading, character objects, resource pools, stat gating, syntax compiler, and Mage splat data.

**Architecture:** Plugin architecture with a splat-agnostic core engine (`game/wod_core/`) and data-driven splat packs (`game/splats/`). Pure Python modules testable with pytest outside Ren'Py. The Ren'Py-specific integration (screens, themes, chargen UI, CDS registration) is deferred to a separate plan.

**Tech Stack:** Python 3.11+, PyYAML, pytest

**Spec:** `docs/superpowers/specs/2026-03-28-wod-vn-framework-design.md`

---

## File Map

| File | Responsibility |
|------|---------------|
| `game/wod_core/__init__.py` | Package init + module-level API (`wod.gate`, `wod.has`, `wod.load_splat`, etc.) |
| `game/wod_core/engine.py` | `Schema`, `CategoryDef`, `Constraint`, `MaxLinkedConstraint`, `Character` |
| `game/wod_core/resources.py` | `ResourcePool`, `ResourceLink`, `ResourceManager` |
| `game/wod_core/gating.py` | `gate()` and `has()` dispatch functions, operator map |
| `game/wod_core/syntax.py` | Bracket shorthand parser + source transformer |
| `game/wod_core/loader.py` | YAML file loading, splat discovery, character loading |
| `game/splats/mage/manifest.yaml` | Mage splat metadata |
| `game/splats/mage/schema.yaml` | M20 trait categories, ranges, constraints |
| `game/splats/mage/resources.yaml` | Quintessence, Paradox, Willpower, Health + Quintessence Wheel link |
| `game/splats/mage/templates/default_mage.yaml` | Standard Mage character blueprint |
| `game/splats/mage/templates/archmage.yaml` | Archmage variant (Spheres to 10) |
| `tests/conftest.py` | Shared fixtures: mage schema dict, resource config dict, sample character |
| `tests/test_engine.py` | Tests for Schema, Character, Constraints |
| `tests/test_resources.py` | Tests for ResourcePool, ResourceManager, ResourceLink |
| `tests/test_gating.py` | Tests for gate/has dispatch + module-level load API |
| `tests/test_syntax.py` | Tests for bracket parser + source transform |
| `tests/test_loader.py` | Tests for YAML loading + splat discovery |
| `tests/test_integration.py` | End-to-end: load Mage splat, create character, gate, spend resources |
| `pyproject.toml` | Project metadata + pytest config |

---

### Task 1: Project Setup

**Files:**
- Create: `pyproject.toml`
- Create: `game/wod_core/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p game/wod_core game/splats/mage/templates game/themes/gothic game/themes/neutral game/wod_screens tests
```

- [ ] **Step 2: Create pyproject.toml**

```toml
[project]
name = "wod-vn-framework"
version = "0.1.0"
description = "World of Darkness Visual Novel Framework for Ren'Py"
requires-python = ">=3.11"
dependencies = ["pyyaml>=6.0"]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["game"]
```

- [ ] **Step 3: Create wod_core package init**

```python
# game/wod_core/__init__.py
"""WoD VN Framework — Core Engine."""

__version__ = "0.1.0"
```

- [ ] **Step 4: Create test package and conftest with shared fixtures**

```python
# tests/__init__.py
```

```python
# tests/conftest.py
import pytest


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
```

- [ ] **Step 5: Verify pytest discovers the test directory**

Run: `cd /home/janothar/wod_vn_framework && pytest --collect-only`
Expected: "no tests ran" (0 items collected), no errors

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml game/wod_core/__init__.py tests/__init__.py tests/conftest.py
git commit -m "chore: project setup with pytest config and test fixtures"
```

---

### Task 2: Schema System

**Files:**
- Create: `game/wod_core/engine.py`
- Create: `tests/test_engine.py`

- [ ] **Step 1: Write failing tests for Schema and CategoryDef**

```python
# tests/test_engine.py
from wod_core.engine import Schema


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
        import pytest
        with pytest.raises(ValueError, match="Duplicate trait name"):
            Schema(data)

    def test_trait_lookup_maps_to_category(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        assert schema.trait_lookup["Strength"] == "attributes"
        assert schema.trait_lookup["Forces"] == "spheres"
        assert schema.trait_lookup["Arete"] == "arete"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/janothar/wod_vn_framework && pytest tests/test_engine.py -v`
Expected: FAIL — `ImportError: cannot import name 'Schema' from 'wod_core.engine'`

- [ ] **Step 3: Implement Schema and CategoryDef**

```python
# game/wod_core/engine.py
"""Core trait system — Schema, CategoryDef, Character."""

from __future__ import annotations


class CategoryDef:
    """A trait category parsed from schema YAML."""

    def __init__(self, name: str, data: dict):
        self.name = name
        self.display_name = data.get("display_name", name)
        self.range = tuple(data.get("range", [0, 5]))
        self.default = data.get("default", 0)
        self.trait_names: list[str] = []

        if "groups" in data:
            for traits in data["groups"].values():
                self.trait_names.extend(traits)
        elif "traits" in data:
            self.trait_names = list(data["traits"])


class Schema:
    """Splat schema — trait categories, ranges, defaults, constraints."""

    def __init__(self, data: dict):
        self.categories: dict[str, CategoryDef] = {}
        self.trait_lookup: dict[str, str] = {}
        self.constraints: list[Constraint] = []
        self._parse(data)

    def _parse(self, data: dict) -> None:
        for cat_name, cat_data in data.get("trait_categories", {}).items():
            category = CategoryDef(cat_name, cat_data)
            self.categories[cat_name] = category
            for trait_name in category.trait_names:
                if trait_name in self.trait_lookup:
                    raise ValueError(
                        f"Duplicate trait name: {trait_name!r} appears in both "
                        f"{self.trait_lookup[trait_name]!r} and {cat_name!r}"
                    )
                self.trait_lookup[trait_name] = cat_name

        for constraint_data in data.get("trait_constraints", []):
            self.constraints.append(Constraint.from_dict(constraint_data))

    def get_all_trait_names(self) -> list[str]:
        return list(self.trait_lookup.keys())

    def has_trait(self, name: str) -> bool:
        return name in self.trait_lookup

    def get_range(self, trait_name: str) -> tuple[int, int]:
        cat_name = self.trait_lookup[trait_name]
        return self.categories[cat_name].range

    def get_default(self, trait_name: str) -> int:
        cat_name = self.trait_lookup[trait_name]
        return self.categories[cat_name].default


class Constraint:
    """Base class for trait constraints."""

    @staticmethod
    def from_dict(data: dict) -> Constraint:
        ctype = data["type"]
        if ctype == "max_linked":
            return MaxLinkedConstraint(
                data["target_category"], data["limited_by"], data.get("rule", "")
            )
        raise ValueError(f"Unknown constraint type: {ctype!r}")

    def validate(
        self, trait_name: str, value: int, character: Character, schema: Schema
    ) -> tuple[bool, str]:
        raise NotImplementedError


class MaxLinkedConstraint(Constraint):
    """All traits in target_category are capped by limited_by trait's value."""

    def __init__(self, target_category: str, limited_by: str, rule: str = ""):
        self.target_category = target_category
        self.limited_by = limited_by
        self.rule = rule

    def validate(
        self, trait_name: str, value: int, character: Character, schema: Schema
    ) -> tuple[bool, str]:
        cat_name = schema.trait_lookup.get(trait_name)
        if cat_name != self.target_category:
            return True, ""
        limit = character.get(self.limited_by)
        if value > limit:
            return False, (
                f"{trait_name} cannot exceed {self.limited_by} "
                f"(current: {limit}). {self.rule}"
            )
        return True, ""
```

Note: `Character` is referenced but not yet defined — it will be added in Task 3. The `Constraint.validate` signature uses a forward reference.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/janothar/wod_vn_framework && pytest tests/test_engine.py -v`
Expected: All 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add game/wod_core/engine.py tests/test_engine.py
git commit -m "feat: Schema and CategoryDef with trait parsing and validation"
```

---

### Task 3: Character Object

**Files:**
- Modify: `game/wod_core/engine.py`
- Modify: `tests/test_engine.py`

- [ ] **Step 1: Write failing tests for Character**

Append to `tests/test_engine.py`:

```python
from wod_core.engine import Schema, Character


class TestCharacter:
    """Test Character creation, get/set/advance."""

    def test_defaults_populated_from_schema(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema)
        assert char.get("Strength") == 1  # attributes default
        assert char.get("Forces") == 0    # spheres default
        assert char.get("Arete") == 1     # arete default

    def test_init_with_traits(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Strength": 3, "Forces": 2})
        assert char.get("Strength") == 3
        assert char.get("Forces") == 2

    def test_set_valid(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema)
        char.set("Strength", 4)
        assert char.get("Strength") == 4

    def test_set_below_range_raises(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema)
        import pytest
        with pytest.raises(ValueError, match="must be between"):
            char.set("Strength", 0)  # min is 1 for attributes

    def test_set_above_range_raises(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema)
        import pytest
        with pytest.raises(ValueError, match="must be between"):
            char.set("Strength", 6)  # max is 5

    def test_set_unknown_trait_raises(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema)
        import pytest
        with pytest.raises(KeyError, match="Unknown trait"):
            char.set("Nonexistent", 3)

    def test_get_unknown_trait_raises(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema)
        import pytest
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
        import pytest
        with pytest.raises(ValueError, match="must be between"):
            char.advance("Strength")

    def test_has_merit(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        merits = [{"name": "Avatar Companion", "type": "merit", "value": 3}]
        char = Character(schema, merits_flaws=merits)
        assert char.has("Avatar Companion") is True
        assert char.has("Nonexistent") is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/janothar/wod_vn_framework && pytest tests/test_engine.py::TestCharacter -v`
Expected: FAIL — `ImportError: cannot import name 'Character'`

- [ ] **Step 3: Implement Character class**

Append to `game/wod_core/engine.py`:

```python
class Character:
    """A WoD character with traits, merits/flaws, and resource access."""

    def __init__(
        self,
        schema: Schema,
        traits: dict[str, int] | None = None,
        merits_flaws: list[dict] | None = None,
        identity: dict | None = None,
    ):
        self.schema = schema
        self.traits: dict[str, int] = {}
        self.merits_flaws = merits_flaws or []
        self.identity = identity or {}
        self.resources: ResourceManager | None = None  # set after creation

        # Initialize all traits to defaults
        for trait_name in schema.get_all_trait_names():
            self.traits[trait_name] = schema.get_default(trait_name)

        # Two-pass trait application: first set values (range-check only),
        # then validate constraints. This avoids ordering issues where e.g.
        # Forces=3 is rejected because Arete=3 hasn't been applied yet.
        if traits:
            for name, value in traits.items():
                if not self.schema.has_trait(name):
                    raise KeyError(f"Unknown trait: {name!r}")
                min_val, max_val = self.schema.get_range(name)
                if not (min_val <= value <= max_val):
                    raise ValueError(
                        f"{name} must be between {min_val} and {max_val}, got {value}"
                    )
                self.traits[name] = value
            # Validate all constraints after all traits are set
            for constraint in self.schema.constraints:
                for trait_name in self.schema.get_all_trait_names():
                    ok, msg = constraint.validate(
                        trait_name, self.traits[trait_name], self, self.schema
                    )
                    if not ok:
                        raise ValueError(msg)

    def get(self, name: str) -> int:
        if name not in self.traits:
            raise KeyError(f"Unknown trait: {name!r}")
        return self.traits[name]

    def set(self, name: str, value: int) -> None:
        if not self.schema.has_trait(name):
            raise KeyError(f"Unknown trait: {name!r}")
        min_val, max_val = self.schema.get_range(name)
        if not (min_val <= value <= max_val):
            raise ValueError(
                f"{name} must be between {min_val} and {max_val}, got {value}"
            )
        for constraint in self.schema.constraints:
            ok, msg = constraint.validate(name, value, self, self.schema)
            if not ok:
                raise ValueError(msg)
        self.traits[name] = value

    def advance(self, name: str) -> None:
        self.set(name, self.get(name) + 1)

    def has(self, name: str) -> bool:
        return any(mf["name"] == name for mf in self.merits_flaws)

    def spend(self, name: str, amount: int) -> bool:
        if self.resources is None:
            raise RuntimeError("No resources configured for this character")
        return self.resources.spend(name, amount)

    def gain(self, name: str, amount: int) -> int:
        if self.resources is None:
            raise RuntimeError("No resources configured for this character")
        return self.resources.gain(name, amount)
```

Note: `ResourceManager` is not yet defined. The type hint is used as a string annotation (or we use `from __future__ import annotations`). Since `from __future__ import annotations` is already at the top, this works.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/janothar/wod_vn_framework && pytest tests/test_engine.py -v`
Expected: All 18 tests PASS (8 schema + 10 character)

- [ ] **Step 5: Commit**

```bash
git add game/wod_core/engine.py tests/test_engine.py
git commit -m "feat: Character class with get/set/advance/has and range validation"
```

---

### Task 4: Trait Constraints

**Files:**
- Modify: `tests/test_engine.py`

No code changes to `engine.py` — constraints were already implemented in Task 2. This task adds test coverage.

- [ ] **Step 1: Write tests for constraint enforcement**

Append to `tests/test_engine.py`:

```python
class TestTraitConstraints:
    """Test max_linked constraint (Spheres capped by Arete)."""

    def test_sphere_within_arete_allowed(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Arete": 3, "Forces": 3})
        assert char.get("Forces") == 3

    def test_sphere_exceeding_arete_raises(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Arete": 2})
        import pytest
        with pytest.raises(ValueError, match="cannot exceed Arete"):
            char.set("Forces", 3)

    def test_advance_sphere_past_arete_raises(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Arete": 2, "Forces": 2})
        import pytest
        with pytest.raises(ValueError, match="cannot exceed Arete"):
            char.advance("Forces")

    def test_non_sphere_ignores_constraint(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema)
        # Attributes are not constrained by Arete
        char.set("Strength", 5)
        assert char.get("Strength") == 5

    def test_raising_arete_allows_higher_spheres(self, mage_schema_data):
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Arete": 3, "Forces": 3})
        char.set("Arete", 5)
        char.set("Forces", 5)
        assert char.get("Forces") == 5
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `cd /home/janothar/wod_vn_framework && pytest tests/test_engine.py::TestTraitConstraints -v`
Expected: All 5 tests PASS (constraints were already implemented)

- [ ] **Step 3: Commit**

```bash
git add tests/test_engine.py
git commit -m "test: add constraint enforcement tests for Arete-Sphere cap"
```

---

### Task 5: Resource Pools

**Files:**
- Create: `game/wod_core/resources.py`
- Create: `tests/test_resources.py`

- [ ] **Step 1: Write failing tests for ResourcePool**

```python
# tests/test_resources.py
import pytest
from wod_core.resources import ResourcePool


class TestResourcePool:
    """Test individual resource pool behavior."""

    def test_default_value(self):
        pool = ResourcePool("quintessence", {
            "range": [0, 20], "default": 0,
        })
        assert pool.current() == 0

    def test_default_current_max_uses_explicit_max(self):
        pool = ResourcePool("willpower", {
            "range": [0, 10], "default_max": 5, "default_current": "max",
        })
        assert pool.current() == 5
        assert pool.max == 5

    def test_default_current_max_uses_range_upper(self):
        pool = ResourcePool("health", {
            "range": [0, 7], "default_current": "max",
        })
        assert pool.current() == 7
        assert pool.max == 7

    def test_spend_success(self):
        pool = ResourcePool("quintessence", {
            "range": [0, 20], "default": 10,
        })
        assert pool.spend(3) is True
        assert pool.current() == 7

    def test_spend_insufficient_returns_false(self):
        pool = ResourcePool("quintessence", {
            "range": [0, 20], "default": 2,
        })
        assert pool.spend(5) is False
        assert pool.current() == 2  # unchanged

    def test_gain(self):
        pool = ResourcePool("quintessence", {
            "range": [0, 20], "default": 10,
        })
        gained = pool.gain(5)
        assert pool.current() == 15
        assert gained == 5

    def test_gain_capped_at_range_max(self):
        pool = ResourcePool("quintessence", {
            "range": [0, 20], "default": 18,
        })
        gained = pool.gain(5)
        assert pool.current() == 20
        assert gained == 2

    def test_at_max(self):
        pool = ResourcePool("willpower", {
            "range": [0, 10], "default_max": 5, "default_current": "max",
        })
        assert pool.at_max() is True
        pool.spend(1)
        assert pool.at_max() is False

    def test_at_min(self):
        pool = ResourcePool("quintessence", {
            "range": [0, 20], "default": 0,
        })
        assert pool.at_min() is True
        pool.gain(1)
        assert pool.at_min() is False

    def test_levels_stored(self):
        levels = [
            {"name": "Bruised", "penalty": 0},
            {"name": "Hurt", "penalty": -1},
        ]
        pool = ResourcePool("health", {
            "range": [0, 7], "default_current": "max",
            "track_type": "levels", "levels": levels,
        })
        assert pool.track_type == "levels"
        assert len(pool.levels) == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/janothar/wod_vn_framework && pytest tests/test_resources.py::TestResourcePool -v`
Expected: FAIL — `ImportError: cannot import name 'ResourcePool'`

- [ ] **Step 3: Implement ResourcePool**

```python
# game/wod_core/resources.py
"""Resource pool system — spend, gain, linked pools."""

from __future__ import annotations


class ResourcePool:
    """A single trackable resource (Quintessence, Health, etc.)."""

    def __init__(self, name: str, config: dict):
        self.name = name
        self.display_name = config.get("display_name", name)
        self.range: tuple[int, int] = tuple(config.get("range", [0, 10]))
        self.track_type = config.get("track_type", "pool")
        self.levels = config.get("levels", [])

        # Determine max: explicit default_max > range upper bound
        if "default_max" in config:
            self.max = config["default_max"]
        else:
            self.max = self.range[1]

        # Determine starting current value
        default_current = config.get("default_current", config.get("default", 0))
        if default_current == "max":
            self.current_value = self.max
        else:
            self.current_value = int(default_current)

    def spend(self, amount: int) -> bool:
        if self.current_value < amount:
            return False
        self.current_value -= amount
        return True

    def gain(self, amount: int) -> int:
        old = self.current_value
        self.current_value = min(self.current_value + amount, self.range[1])
        return self.current_value - old

    def current(self) -> int:
        return self.current_value

    def at_max(self) -> bool:
        return self.current_value >= self.max

    def at_min(self) -> bool:
        return self.current_value <= self.range[0]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/janothar/wod_vn_framework && pytest tests/test_resources.py::TestResourcePool -v`
Expected: All 10 tests PASS

- [ ] **Step 5: Commit**

```bash
git add game/wod_core/resources.py tests/test_resources.py
git commit -m "feat: ResourcePool with spend/gain/current and max defaults"
```

---

### Task 6: Resource Manager & Linked Resources

**Files:**
- Modify: `game/wod_core/resources.py`
- Modify: `tests/test_resources.py`

- [ ] **Step 1: Write failing tests for ResourceManager and ResourceLink**

Append to `tests/test_resources.py`:

```python
from wod_core.resources import ResourceManager


class TestResourceManager:
    """Test ResourceManager — multi-pool management."""

    def test_create_from_config(self, mage_resource_data):
        mgr = ResourceManager(mage_resource_data)
        assert mgr.current("quintessence") == 0
        assert mgr.current("willpower") == 5
        assert mgr.current("health") == 7

    def test_spend_and_gain(self, mage_resource_data):
        mgr = ResourceManager(mage_resource_data)
        mgr.gain("quintessence", 10)
        assert mgr.current("quintessence") == 10
        assert mgr.spend("quintessence", 3) is True
        assert mgr.current("quintessence") == 7

    def test_has_resource(self, mage_resource_data):
        mgr = ResourceManager(mage_resource_data)
        assert mgr.has_resource("quintessence") is True
        assert mgr.has_resource("nonexistent") is False


class TestLinkedResources:
    """Test Quintessence Wheel — quintessence + paradox <= 20."""

    def test_gain_paradox_reduces_quintessence(self, mage_resource_data):
        mgr = ResourceManager(mage_resource_data)
        mgr.gain("quintessence", 15)
        assert mgr.current("quintessence") == 15
        mgr.gain("paradox", 8)
        assert mgr.current("paradox") == 8
        # 15 + 8 = 23 > 20, so quintessence reduced to 12
        assert mgr.current("quintessence") == 12

    def test_gain_quintessence_reduces_paradox(self, mage_resource_data):
        mgr = ResourceManager(mage_resource_data)
        mgr.gain("paradox", 15)
        assert mgr.current("paradox") == 15
        mgr.gain("quintessence", 8)
        assert mgr.current("quintessence") == 8
        # 8 + 15 = 23 > 20, so paradox reduced to 12
        assert mgr.current("paradox") == 12

    def test_within_limit_no_reduction(self, mage_resource_data):
        mgr = ResourceManager(mage_resource_data)
        mgr.gain("quintessence", 10)
        mgr.gain("paradox", 5)
        # 10 + 5 = 15 <= 20, no reduction
        assert mgr.current("quintessence") == 10
        assert mgr.current("paradox") == 5

    def test_at_limit_exact(self, mage_resource_data):
        mgr = ResourceManager(mage_resource_data)
        mgr.gain("quintessence", 12)
        mgr.gain("paradox", 8)
        # 12 + 8 = 20, exactly at limit
        assert mgr.current("quintessence") == 12
        assert mgr.current("paradox") == 8

    def test_unlinked_resources_not_affected(self, mage_resource_data):
        mgr = ResourceManager(mage_resource_data)
        # Willpower is not linked to anything
        original_wp = mgr.current("willpower")
        mgr.gain("quintessence", 20)
        assert mgr.current("willpower") == original_wp
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/janothar/wod_vn_framework && pytest tests/test_resources.py::TestResourceManager tests/test_resources.py::TestLinkedResources -v`
Expected: FAIL — `ImportError: cannot import name 'ResourceManager'`

- [ ] **Step 3: Implement ResourceLink and ResourceManager**

Append to `game/wod_core/resources.py`:

```python
class ResourceLink:
    """Constraint linking multiple pools to a combined max."""

    def __init__(self, name: str, pool_names: list[str], combined_max: int):
        self.name = name
        self.pool_names = pool_names
        self.combined_max = combined_max

    def enforce(self, changed_pool: str, manager: ResourceManager) -> None:
        total = sum(manager.current(p) for p in self.pool_names)
        if total <= self.combined_max:
            return
        overflow = total - self.combined_max
        for pool_name in self.pool_names:
            if pool_name != changed_pool and overflow > 0:
                pool = manager.pools[pool_name]
                reduction = min(overflow, pool.current_value - pool.range[0])
                pool.current_value -= reduction
                overflow -= reduction


class ResourceManager:
    """Manages all resource pools for a character."""

    def __init__(self, config: dict):
        self.pools: dict[str, ResourcePool] = {}
        self.links: list[ResourceLink] = []

        for name, pool_config in config.get("resources", {}).items():
            self.pools[name] = ResourcePool(name, pool_config)

        for link_name, link_config in config.get("resource_links", {}).items():
            self.links.append(
                ResourceLink(link_name, link_config["pools"], link_config["combined_max"])
            )

    def spend(self, name: str, amount: int) -> bool:
        return self.pools[name].spend(amount)

    def gain(self, name: str, amount: int) -> int:
        result = self.pools[name].gain(amount)
        for link in self.links:
            if name in link.pool_names:
                link.enforce(name, self)
        return result

    def current(self, name: str) -> int:
        return self.pools[name].current()

    def at_max(self, name: str) -> bool:
        return self.pools[name].at_max()

    def at_min(self, name: str) -> bool:
        return self.pools[name].at_min()

    def has_resource(self, name: str) -> bool:
        return name in self.pools
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/janothar/wod_vn_framework && pytest tests/test_resources.py -v`
Expected: All 18 tests PASS (10 pool + 3 manager + 5 linked)

- [ ] **Step 5: Commit**

```bash
git add game/wod_core/resources.py tests/test_resources.py
git commit -m "feat: ResourceManager with linked pool constraints (Quintessence Wheel)"
```

---

### Task 7: Character gate() Method

**Files:**
- Modify: `game/wod_core/engine.py`
- Modify: `tests/test_engine.py`

- [ ] **Step 1: Write failing tests for gate()**

Append to `tests/test_engine.py`:

```python
from wod_core.resources import ResourceManager


class TestCharacterGate:
    """Test Character.gate() dispatching to traits and resources."""

    def _make_char_with_resources(self, mage_schema_data, mage_resource_data):
        schema = Schema(mage_schema_data)
        char = Character(schema, traits={"Strength": 3, "Forces": 2})
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
        import pytest
        with pytest.raises(KeyError, match="Unknown trait or resource"):
            char.gate("nonexistent", ">=", 1)

    def test_gate_bad_operator_raises(self, mage_schema_data, mage_resource_data):
        char = self._make_char_with_resources(mage_schema_data, mage_resource_data)
        import pytest
        with pytest.raises(ValueError, match="Unknown operator"):
            char.gate("Strength", "~", 3)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/janothar/wod_vn_framework && pytest tests/test_engine.py::TestCharacterGate -v`
Expected: FAIL — `AttributeError: 'Character' object has no attribute 'gate'`

- [ ] **Step 3: Add gate() to Character**

Add to `Character` class in `game/wod_core/engine.py`:

```python
    _OPERATORS = {
        ">=": lambda a, b: a >= b,
        "<=": lambda a, b: a <= b,
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
        ">": lambda a, b: a > b,
        "<": lambda a, b: a < b,
    }

    def gate(self, name: str, op: str, value: int) -> bool:
        if self.schema.has_trait(name):
            current = self.get(name)
        elif self.resources and self.resources.has_resource(name):
            current = self.resources.current(name)
        else:
            raise KeyError(f"Unknown trait or resource: {name!r}")
        if op not in self._OPERATORS:
            raise ValueError(f"Unknown operator: {op!r}")
        return self._OPERATORS[op](current, value)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/janothar/wod_vn_framework && pytest tests/test_engine.py -v`
Expected: All 33 tests PASS

- [ ] **Step 5: Commit**

```bash
git add game/wod_core/engine.py tests/test_engine.py
git commit -m "feat: Character.gate() with all comparison operators for traits and resources"
```

---

### Task 8: Module-Level API (gating.py + __init__.py)

**Files:**
- Create: `game/wod_core/gating.py`
- Modify: `game/wod_core/__init__.py`
- Create: `tests/test_gating.py`

- [ ] **Step 1: Write failing tests for module-level gate/has and active character**

```python
# tests/test_gating.py
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
            traits={"Strength": 3, "Forces": 2},
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/janothar/wod_vn_framework && pytest tests/test_gating.py -v`
Expected: FAIL — `AttributeError: module 'wod_core' has no attribute 'set_active'`

- [ ] **Step 3: Implement gating.py and update __init__.py**

```python
# game/wod_core/gating.py
"""Module-level gating API — delegates to active character."""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wod_core.engine import Character

_active_character: Character | None = None


def set_active(character: Character | None) -> None:
    global _active_character
    _active_character = character


def get_active() -> Character:
    if _active_character is None:
        raise RuntimeError("No active character set. Call wod_core.set_active(character) first.")
    return _active_character


def gate(name: str, op: str, value: int) -> bool:
    return get_active().gate(name, op, value)


def has(name: str) -> bool:
    return get_active().has(name)
```

Update `game/wod_core/__init__.py`:

```python
# game/wod_core/__init__.py
"""WoD VN Framework — Core Engine."""

__version__ = "0.1.0"

from wod_core.gating import gate, has, set_active, get_active
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/janothar/wod_vn_framework && pytest tests/test_gating.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add game/wod_core/gating.py game/wod_core/__init__.py tests/test_gating.py
git commit -m "feat: module-level gate()/has()/set_active() API"
```

---

### Task 9: YAML Loader — Splats & Characters

**Files:**
- Create: `game/wod_core/loader.py`
- Create: `tests/test_loader.py`

- [ ] **Step 1: Create Mage splat data files first (needed by loader tests)**

```yaml
# game/splats/mage/manifest.yaml
splat:
  id: mage
  display_name: "Mage: The Ascension"
  edition: "M20"
  version: "1.0"
  schema: schema.yaml
  resources: resources.yaml
  templates_dir: templates/
  screens:
    character_sheet: null
    chargen_steps:
      - identity
      - attributes
      - abilities
      - spheres
      - backgrounds
      - merits_flaws
      - review
```

```yaml
# game/splats/mage/schema.yaml
trait_categories:
  attributes:
    display_name: "Attributes"
    groups:
      physical: [Strength, Dexterity, Stamina]
      social: [Charisma, Manipulation, Appearance]
      mental: [Perception, Intelligence, Wits]
    default: 1
    range: [1, 5]

  abilities:
    display_name: "Abilities"
    groups:
      talents:
        - Alertness
        - Art
        - Athletics
        - Awareness
        - Brawl
        - Empathy
        - Expression
        - Intimidation
        - Leadership
        - Streetwise
        - Subterfuge
      skills:
        - Crafts
        - Drive
        - Etiquette
        - Firearms
        - Martial Arts
        - Meditation
        - Melee
        - Research
        - Stealth
        - Survival
        - Technology
      knowledges:
        - Academics
        - Computer
        - Cosmology
        - Enigmas
        - Esoterica
        - Investigation
        - Law
        - Medicine
        - Occult
        - Politics
        - Science
    default: 0
    range: [0, 5]

  spheres:
    display_name: "Spheres"
    traits:
      - Correspondence
      - Entropy
      - Forces
      - Life
      - Matter
      - Mind
      - Prime
      - Spirit
      - Time
    default: 0
    range: [0, 5]

  arete:
    display_name: "Arete"
    traits: [Arete]
    default: 1
    range: [1, 10]

  backgrounds:
    display_name: "Backgrounds"
    traits:
      - Allies
      - Avatar
      - Contacts
      - Destiny
      - Dream
      - Familiar
      - Influence
      - Mentor
      - Node
      - Resources
      - Sanctum
      - Wonder
    default: 0
    range: [0, 5]

trait_constraints:
  - type: max_linked
    target_category: spheres
    limited_by: Arete
    rule: "No Sphere can exceed Arete rating"
```

```yaml
# game/splats/mage/resources.yaml
resources:
  quintessence:
    display_name: "Quintessence"
    range: [0, 20]
    default: 0

  paradox:
    display_name: "Paradox"
    range: [0, 20]
    default: 0

  willpower:
    display_name: "Willpower"
    range: [0, 10]
    default_max: 5
    default_current: "max"

  health:
    display_name: "Health"
    range: [0, 7]
    default_current: "max"
    track_type: "levels"
    levels:
      - { name: "Bruised", penalty: 0 }
      - { name: "Hurt", penalty: -1 }
      - { name: "Injured", penalty: -1 }
      - { name: "Wounded", penalty: -2 }
      - { name: "Mauled", penalty: -2 }
      - { name: "Crippled", penalty: -5 }
      - { name: "Incapacitated", penalty: null }

resource_links:
  quintessence_wheel:
    pools: [quintessence, paradox]
    combined_max: 20
```

```yaml
# game/splats/mage/templates/default_mage.yaml
schema: mage
template: default_mage
character_type: pc

identity:
  name: ""
  tradition: ""
  essence: ""
  nature: ""
  demeanor: ""

traits:
  attributes:
    Strength: 1
    Dexterity: 1
    Stamina: 1
    Charisma: 1
    Manipulation: 1
    Appearance: 1
    Perception: 1
    Intelligence: 1
    Wits: 1
  abilities: {}
  spheres: {}
  arete:
    Arete: 1
  backgrounds: {}

resources:
  quintessence: 0
  paradox: 0
  willpower: 5

merits_flaws: []
```

```yaml
# game/splats/mage/templates/archmage.yaml
extends: default_mage
overrides:
  trait_categories:
    spheres:
      range: [0, 10]
    arete:
      range: [1, 10]
```

- [ ] **Step 2: Write failing tests for loader**

```python
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
        # Create a character file in a temp directory
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
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd /home/janothar/wod_vn_framework && pytest tests/test_loader.py -v`
Expected: FAIL — `ImportError: cannot import name 'SplatLoader'`

- [ ] **Step 4: Implement loader.py**

```python
# game/wod_core/loader.py
"""YAML file loading — splat discovery, schema loading, character loading."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

import yaml

from wod_core.engine import Schema, Character
from wod_core.resources import ResourceManager


@dataclass
class SplatData:
    """Loaded splat — schema, resource config, manifest."""

    splat_id: str
    schema: Schema
    resource_config: dict
    manifest: dict
    templates_dir: str


class SplatLoader:
    """Discovers and loads splat packs from the game directory."""

    def __init__(self, game_dir: str):
        self.game_dir = game_dir
        self.splats_dir = os.path.join(game_dir, "splats")
        self.loaded_splats: dict[str, SplatData] = {}

    def discover_splats(self) -> list[str]:
        splat_ids = []
        if not os.path.isdir(self.splats_dir):
            return splat_ids
        for name in os.listdir(self.splats_dir):
            manifest_path = os.path.join(self.splats_dir, name, "manifest.yaml")
            if os.path.isfile(manifest_path):
                splat_ids.append(name)
        return splat_ids

    def load_splat(self, splat_id: str) -> SplatData:
        splat_dir = os.path.join(self.splats_dir, splat_id)
        manifest_path = os.path.join(splat_dir, "manifest.yaml")

        with open(manifest_path) as f:
            manifest = yaml.safe_load(f)

        schema_file = manifest["splat"].get("schema", "schema.yaml")
        with open(os.path.join(splat_dir, schema_file)) as f:
            schema_data = yaml.safe_load(f)

        resources_file = manifest["splat"].get("resources", "resources.yaml")
        with open(os.path.join(splat_dir, resources_file)) as f:
            resource_config = yaml.safe_load(f)

        templates_dir = os.path.join(
            splat_dir, manifest["splat"].get("templates_dir", "templates")
        )

        schema = Schema(schema_data)

        splat = SplatData(
            splat_id=splat_id,
            schema=schema,
            resource_config=resource_config,
            manifest=manifest,
            templates_dir=templates_dir,
        )
        self.loaded_splats[splat_id] = splat
        return splat

    def load_character(self, char_path: str) -> Character:
        # Resolve relative paths against game_dir
        if not os.path.isabs(char_path):
            char_path = os.path.join(self.game_dir, char_path)
        with open(char_path) as f:
            char_data = yaml.safe_load(f)

        splat_id = char_data["schema"]
        if splat_id not in self.loaded_splats:
            raise ValueError(f"Splat {splat_id!r} not loaded. Call load_splat() first.")
        splat = self.loaded_splats[splat_id]

        # Flatten nested traits dict
        flat_traits: dict[str, int] = {}
        for category_traits in char_data.get("traits", {}).values():
            if isinstance(category_traits, dict):
                flat_traits.update(category_traits)

        char = Character(
            schema=splat.schema,
            traits=flat_traits,
            merits_flaws=char_data.get("merits_flaws", []),
            identity=char_data.get("identity", {}),
        )

        # Set up resources
        resource_config = dict(splat.resource_config)  # shallow copy
        char.resources = ResourceManager(resource_config)

        # Apply character-specific resource overrides
        for res_name, res_value in char_data.get("resources", {}).items():
            if char.resources.has_resource(res_name) and isinstance(res_value, int):
                pool = char.resources.pools[res_name]
                pool.current_value = res_value

        return char
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /home/janothar/wod_vn_framework && pytest tests/test_loader.py -v`
Expected: All 6 tests PASS

- [ ] **Step 6: Commit**

```bash
git add game/wod_core/loader.py tests/test_loader.py game/splats/
git commit -m "feat: SplatLoader with YAML loading, splat discovery, and character loading"
```

---

### Task 10: Module-Level Load API

**Files:**
- Modify: `game/wod_core/__init__.py`
- Modify: `tests/test_gating.py`

- [ ] **Step 1: Write failing tests for wod_core.load_splat and wod_core.load_character**

Append to `tests/test_gating.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/janothar/wod_vn_framework && pytest tests/test_gating.py::TestModuleLoadAPI -v`
Expected: FAIL — `AttributeError: module 'wod_core' has no attribute 'init'`

- [ ] **Step 3: Update __init__.py with load API**

```python
# game/wod_core/__init__.py
"""WoD VN Framework — Core Engine."""

__version__ = "0.1.0"

from wod_core.gating import gate, has, set_active, get_active
from wod_core.loader import SplatLoader

_loader: SplatLoader | None = None


def init(game_dir: str) -> None:
    global _loader
    _loader = SplatLoader(game_dir)


def get_loader() -> SplatLoader:
    if _loader is None:
        raise RuntimeError("wod_core not initialized. Call wod_core.init(game_dir) first.")
    return _loader


def load_splat(splat_id: str):
    return get_loader().load_splat(splat_id)


def load_all_splats():
    loader = get_loader()
    for splat_id in loader.discover_splats():
        loader.load_splat(splat_id)


def load_character(char_path: str):
    return get_loader().load_character(char_path)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/janothar/wod_vn_framework && pytest tests/test_gating.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add game/wod_core/__init__.py tests/test_gating.py
git commit -m "feat: module-level init/load_splat/load_character API"
```

---

### Task 11: Syntax Compiler

**Files:**
- Create: `game/wod_core/syntax.py`
- Create: `tests/test_syntax.py`

- [ ] **Step 1: Write failing tests for bracket syntax parser and identifier validation**

```python
# tests/test_syntax.py
from wod_core.syntax import transform_line, parse_condition, validate_identifiers


class TestParseCondition:
    """Test parsing individual bracket conditions into gate/has calls."""

    def test_simple_gte(self):
        assert parse_condition("Forces >= 3") == 'wod_core.gate("Forces", ">=", 3)'

    def test_simple_eq(self):
        assert parse_condition("Forces == 3") == 'wod_core.gate("Forces", "==", 3)'

    def test_simple_lt(self):
        assert parse_condition("Forces < 3") == 'wod_core.gate("Forces", "<", 3)'

    def test_simple_lte(self):
        assert parse_condition("Forces <= 3") == 'wod_core.gate("Forces", "<=", 3)'

    def test_simple_gt(self):
        assert parse_condition("Forces > 3") == 'wod_core.gate("Forces", ">", 3)'

    def test_simple_neq(self):
        assert parse_condition("Forces != 3") == 'wod_core.gate("Forces", "!=", 3)'

    def test_multi_word_trait(self):
        assert parse_condition("Martial Arts >= 2") == 'wod_core.gate("Martial Arts", ">=", 2)'

    def test_boolean_merit(self):
        assert parse_condition("Avatar Companion") == 'wod_core.has("Avatar Companion")'

    def test_negated_flaw(self):
        assert parse_condition("!Blind") == 'not wod_core.has("Blind")'

    def test_resource_name(self):
        assert parse_condition("quintessence >= 5") == 'wod_core.gate("quintessence", ">=", 5)'


class TestTransformLine:
    """Test full line transformation from shorthand to native Ren'Py."""

    def test_single_condition(self):
        line = '    "Rewrite the ward" [Forces >= 3]:'
        expected = '    "Rewrite the ward" if wod_core.gate("Forces", ">=", 3):'
        assert transform_line(line) == expected

    def test_multiple_conditions(self):
        line = '    "Rewrite the ward" [Prime >= 3, Forces >= 2]:'
        expected = '    "Rewrite the ward" if wod_core.gate("Prime", ">=", 3) and wod_core.gate("Forces", ">=", 2):'
        assert transform_line(line) == expected

    def test_boolean_condition(self):
        line = '    "Use your familiar" [Avatar Companion]:'
        expected = '    "Use your familiar" if wod_core.has("Avatar Companion"):'
        assert transform_line(line) == expected

    def test_negated_condition(self):
        line = '    "See clearly" [!Blind]:'
        expected = '    "See clearly" if not wod_core.has("Blind"):'
        assert transform_line(line) == expected

    def test_no_brackets_unchanged(self):
        line = '    "Just a normal choice":'
        assert transform_line(line) == line

    def test_existing_if_unchanged(self):
        line = '    "Choice" if pc.gate("Forces", ">=", 3):'
        assert transform_line(line) == line

    def test_locked_annotation_preserved(self):
        line = '    "Rewrite the ward" [Forces >= 3] (locked="You lack the knowledge..."):'
        result = transform_line(line)
        assert 'wod_core.gate("Forces", ">=", 3)' in result

    def test_mixed_conditions_and_boolean(self):
        line = '    "Astral travel" [Mind >= 4, Avatar Companion]:'
        expected = '    "Astral travel" if wod_core.gate("Mind", ">=", 4) and wod_core.has("Avatar Companion"):'
        assert transform_line(line) == expected


class TestValidateIdentifiers:
    """Test Phase 2 validation — checking identifiers against loaded schema."""

    def test_valid_identifiers_pass(self, mage_schema_data):
        from wod_core.engine import Schema
        from wod_core.resources import ResourceManager
        schema = Schema(mage_schema_data)

        source = '    "Cast spell" [Forces >= 3]:\n    "Check ward" [Prime >= 1]:'
        transform_line(source.split("\n")[0])
        transform_line(source.split("\n")[1])

        # validate_identifiers takes schema + resource manager, returns list of errors
        errors = validate_identifiers(schema, resource_names=["quintessence", "paradox", "willpower", "health"])
        assert errors == []

    def test_unknown_identifier_returns_error(self, mage_schema_data):
        from wod_core.engine import Schema
        schema = Schema(mage_schema_data)

        # Transform a line with a typo
        transform_line('    "Cast" [Forcs >= 3]:')

        errors = validate_identifiers(schema, resource_names=[])
        assert len(errors) >= 1
        assert "Forcs" in errors[0]

    def test_did_you_mean_suggestion(self, mage_schema_data):
        from wod_core.engine import Schema
        schema = Schema(mage_schema_data)

        transform_line('    "Cast" [Forcs >= 3]:')

        errors = validate_identifiers(schema, resource_names=[])
        assert "Forces" in errors[0]  # should suggest closest match
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/janothar/wod_vn_framework && pytest tests/test_syntax.py -v`
Expected: FAIL — `ImportError: cannot import name 'transform_line'`

- [ ] **Step 3: Implement syntax.py**

```python
# game/wod_core/syntax.py
"""Shorthand bracket syntax compiler.

Transforms lines like:
    "Choice text" [Forces >= 3, Prime >= 2]:
Into:
    "Choice text" if wod_core.gate("Forces", ">=", 3) and wod_core.gate("Prime", ">=", 2):
"""

from __future__ import annotations

import re

# Match bracket conditions on a menu choice line.
# Captures: (prefix with quoted text)(bracket contents)(optional locked annotation + colon)
_BRACKET_RE = re.compile(
    r'^(\s*"[^"]*")\s*'           # leading whitespace + quoted text
    r'\[([^\]]+)\]'               # [conditions]
    r'(\s*(?:\(.*\))?\s*:\s*)$'   # optional (locked=...) + colon
)

# Match a comparison condition: trait_name OP value
_COMPARISON_RE = re.compile(
    r'^(.+?)\s*(>=|<=|==|!=|>|<)\s*(\d+)$'
)

# Match a negated boolean: !Name
_NEGATION_RE = re.compile(r'^!(.+)$')


def parse_condition(cond: str) -> str:
    """Parse a single condition string into a Python expression."""
    cond = cond.strip()

    # Check for comparison: "Forces >= 3"
    m = _COMPARISON_RE.match(cond)
    if m:
        trait_name = m.group(1).strip()
        op = m.group(2)
        value = int(m.group(3))
        return f'wod_core.gate("{trait_name}", "{op}", {value})'

    # Check for negation: "!Blind"
    m = _NEGATION_RE.match(cond)
    if m:
        name = m.group(1).strip()
        return f'not wod_core.has("{name}")'

    # Boolean merit/flaw: "Avatar Companion"
    return f'wod_core.has("{cond}")'


def transform_line(line: str) -> str:
    """Transform a single line, replacing bracket shorthand with if expressions."""
    m = _BRACKET_RE.match(line)
    if not m:
        return line

    prefix = m.group(1)       # '    "Choice text"'
    conditions = m.group(2)   # 'Forces >= 3, Prime >= 2'
    suffix = m.group(3)       # ':'  or  '(locked="..."):''

    # Split conditions on comma, parse each
    parts = [parse_condition(c) for c in conditions.split(",")]
    condition_expr = " and ".join(parts)

    return f"{prefix} if {condition_expr}{suffix}"


def transform_source(source: str) -> str:
    """Transform all lines in a source string."""
    return "\n".join(transform_line(line) for line in source.split("\n"))


# --- Phase 2: Identifier validation ---

# Collects all identifiers encountered during transforms
_encountered_identifiers: set[str] = set()


def _register_identifier(name: str) -> None:
    """Record an identifier found during source transform."""
    _encountered_identifiers.add(name)


def clear_identifiers() -> None:
    """Reset the identifier registry (for testing)."""
    _encountered_identifiers.clear()


def _closest_match(name: str, valid_names: list[str]) -> str | None:
    """Find the closest valid name by edit distance (simple)."""
    from difflib import get_close_matches
    matches = get_close_matches(name, valid_names, n=1, cutoff=0.6)
    return matches[0] if matches else None


def validate_identifiers(
    schema, resource_names: list[str] | None = None
) -> list[str]:
    """Validate all encountered identifiers against the schema and resources.

    Returns a list of error messages for unknown identifiers.
    """
    valid_names = set(schema.get_all_trait_names())
    if resource_names:
        valid_names.update(resource_names)

    errors = []
    for name in _encountered_identifiers:
        if name not in valid_names:
            msg = f'Unknown identifier "{name}" in gate condition.'
            suggestion = _closest_match(name, list(valid_names))
            if suggestion:
                msg += f' Did you mean "{suggestion}"?'
            errors.append(msg)
    return errors
```

Update `parse_condition` to register identifiers by adding `_register_identifier(trait_name)` after extracting the trait name in comparisons and `_register_identifier(name)` / `_register_identifier(cond)` in the boolean paths. Specifically, add these calls:

```python
def parse_condition(cond: str) -> str:
    """Parse a single condition string into a Python expression."""
    cond = cond.strip()

    # Check for comparison: "Forces >= 3"
    m = _COMPARISON_RE.match(cond)
    if m:
        trait_name = m.group(1).strip()
        op = m.group(2)
        value = int(m.group(3))
        _register_identifier(trait_name)
        return f'wod_core.gate("{trait_name}", "{op}", {value})'

    # Check for negation: "!Blind"
    m = _NEGATION_RE.match(cond)
    if m:
        name = m.group(1).strip()
        # Don't register merits/flaws — they're not in the schema
        return f'not wod_core.has("{name}")'

    # Boolean merit/flaw: "Avatar Companion"
    # Don't register merits/flaws — they're not in the schema
    return f'wod_core.has("{cond}")'
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/janothar/wod_vn_framework && pytest tests/test_syntax.py -v`
Expected: All 18 tests PASS

- [ ] **Step 5: Commit**

```bash
git add game/wod_core/syntax.py tests/test_syntax.py
git commit -m "feat: bracket syntax compiler — transforms [trait >= N] to wod_core.gate() calls"
```

---

### Task 12: End-to-End Integration Test

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write integration test covering full workflow**

```python
# tests/test_integration.py
"""End-to-end integration test: load Mage splat, create character, gate, spend."""

import os
import wod_core
from wod_core.engine import Character
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
        # Spot-check key traits
        assert schema.has_trait("Strength")
        assert schema.has_trait("Forces")
        assert schema.has_trait("Arete")
        assert schema.has_trait("Science")
        assert schema.has_trait("Avatar")
        # Check counts
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

        # Trait gating
        assert wod_core.gate("Forces", ">=", 3) is True
        assert wod_core.gate("Forces", ">=", 4) is False
        assert wod_core.gate("Science", ">=", 4) is True
        assert wod_core.gate("Science", "==", 4) is True

        # Resource gating
        assert wod_core.gate("quintessence", ">=", 5) is True
        assert wod_core.gate("quintessence", ">=", 6) is False

        # Merit check
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

        # Spend quintessence
        assert char.resources.spend("quintessence", 5) is True
        assert char.resources.current("quintessence") == 10

        # Gain paradox — should not reduce quintessence yet (10 + 8 = 18 <= 20)
        char.resources.gain("paradox", 8)
        assert char.resources.current("paradox") == 8
        assert char.resources.current("quintessence") == 10

        # Gain more paradox — now 10 + 13 = 23 > 20, quintessence reduced
        char.resources.gain("paradox", 5)
        assert char.resources.current("paradox") == 13
        assert char.resources.current("quintessence") == 7  # 20 - 13

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

        # Can advance Forces to 2 (within Arete)
        char.advance("Forces")
        assert char.get("Forces") == 2

        # Cannot advance Forces to 3 (exceeds Arete of 2)
        import pytest
        with pytest.raises(ValueError, match="cannot exceed Arete"):
            char.advance("Forces")

        # Raise Arete first, then Forces
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
        assert '"Back away":' in result  # unchanged
        assert "jump retreat" in result  # unchanged
```

- [ ] **Step 2: Run integration tests**

Run: `cd /home/janothar/wod_vn_framework && pytest tests/test_integration.py -v`
Expected: All 5 tests PASS

- [ ] **Step 3: Run full test suite**

Run: `cd /home/janothar/wod_vn_framework && pytest -v`
Expected: All tests PASS (approximately 49 tests across all files)

- [ ] **Step 4: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: end-to-end integration tests for Mage splat workflow"
```

---

## Deferred to Plan 2: Ren'Py Integration

The following are out of scope for this plan and will be implemented in a follow-up:

- `game/wod_statements.rpy` — CDS registration for bracket syntax in Ren'Py
- `game/wod_screens/` — Character sheet, resource HUD, chargen screens
- `game/themes/` — Gothic and Neutral theme implementations
- `game/gui.rpy` — Root GUI delegation to active theme
- `game/wod_core/chargen.py` — Character creation UI flow
- `wod_core.set_theme()` / `wod_core.show_hud()` / `wod_core.hide_hud()`
- Demo `script.rpy` exercising the framework
- **Splat overrides** — `load_splat(overrides=...)` for author-level schema/resource tweaks (spec Section 5)
- **Template extension** — `extends`/`overrides` in template YAML files like `archmage.yaml` (spec Section 1). The archmage.yaml file is created as data but the extends/overrides parsing is deferred.
- **`load_all_splats()`** — implemented but untested; proper test coverage deferred
