"""Character creation logic — state management, point pools, validation."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

import yaml

from wod_core.engine import Schema, Character
from wod_core.resources import ResourceManager


# Invalidation rules: changing a step invalidates these dependent steps
_INVALIDATION_MAP = {
    "identity": ["spheres_backgrounds"],          # Tradition affects affinity Sphere
    "attribute_priority": ["attribute_allocate"],  # Priority pool sizes change
    "ability_priority": ["ability_allocate"],      # Priority pool sizes change
}


class ChargenState:
    """Tracks character creation progress across steps."""

    def __init__(self, splat_id: str, mode: str, schema, chargen_config: dict, splat_data):
        self.splat_id = splat_id
        self.mode = mode
        self.schema = schema
        self.config = chargen_config
        self.splat_data = splat_data
        self.current_step = 0
        self.data: dict[str, dict] = {}
        self.completed: set[int] = set()

        # Get step list from config
        mode_config = chargen_config["modes"].get(mode, {})
        self.steps: list[str] = list(mode_config.get("steps", []))

    def save_step(self, step_name: str, data: dict) -> None:
        self.data[step_name] = data

    def complete_step(self, step_index: int) -> None:
        self.completed.add(step_index)

    def invalidate_dependents(self, changed_step: str) -> None:
        dependents = _INVALIDATION_MAP.get(changed_step, [])
        for dep_step_name in dependents:
            if dep_step_name in self.steps:
                dep_index = self.steps.index(dep_step_name)
                self.completed.discard(dep_index)
                self.data.pop(dep_step_name, None)

    def get_mode_config(self) -> dict:
        return self.config["modes"].get(self.mode, {})

    def get_traditions(self) -> list[dict]:
        return self.config.get("traditions", [])

    def get_tradition_by_id(self, tradition_id: str) -> dict | None:
        for t in self.get_traditions():
            if t["id"] == tradition_id:
                return t
        return None

    def get_archetypes(self) -> list[str]:
        return self.config.get("archetypes", [])

    def get_essences(self) -> list[str]:
        return self.config.get("essences", [])


class PointPool:
    """Tracks dot allocation within a budget."""

    def __init__(self, total: int, per_trait_max: int = 5):
        self.total = total
        self.per_trait_max = per_trait_max
        self._allocations: dict[str, int] = {}

    @property
    def spent(self) -> int:
        return sum(self._allocations.values())

    @property
    def remaining(self) -> int:
        return self.total - self.spent

    def allocate(self, trait: str, dots: int) -> bool:
        current = self._allocations.get(trait, 0)
        if dots > self.per_trait_max:
            return False
        delta = dots - current
        if delta > self.remaining:
            return False
        self._allocations[trait] = dots
        return True

    def deallocate(self, trait: str, dots: int) -> None:
        current = self._allocations.get(trait, 0)
        new_val = max(0, current - dots)
        if new_val == 0:
            self._allocations.pop(trait, None)
        else:
            self._allocations[trait] = new_val

    def get(self, trait: str) -> int:
        return self._allocations.get(trait, 0)

    def get_all(self) -> dict[str, int]:
        return dict(self._allocations)

    def reset(self) -> None:
        self._allocations.clear()


def build_character(state: ChargenState) -> Character:
    """Convert a completed ChargenState into a Character object."""
    if state.mode == "template":
        return _build_from_template(state)
    return _build_from_allocation(state)


def _build_from_allocation(state: ChargenState) -> Character:
    """Build character from manual allocation data (full or simplified mode)."""
    identity = dict(state.data.get("identity", {}))
    mode_config = state.get_mode_config()

    # Start with all traits at defaults
    flat_traits: dict[str, int] = {}
    for trait_name in state.schema.get_all_trait_names():
        flat_traits[trait_name] = state.schema.get_default(trait_name)

    # Apply attribute allocations
    attr_data = state.data.get("attribute_allocate", {})
    for trait, value in attr_data.items():
        if state.schema.has_trait(trait):
            flat_traits[trait] = value

    # Apply ability allocations
    ability_data = state.data.get("ability_allocate", state.data.get("abilities", {}))
    for trait, value in ability_data.items():
        if state.schema.has_trait(trait):
            flat_traits[trait] = value

    # Set Arete BEFORE spheres (constraint: no Sphere can exceed Arete)
    starting_arete = mode_config.get("starting_arete", 1)
    tradition_id = identity.get("tradition", "")
    for t in state.get_traditions():
        if t["name"] == tradition_id or t["id"] == tradition_id:
            if "starting_arete" in t:
                starting_arete = t["starting_arete"]
            break
    flat_traits["Arete"] = starting_arete

    # Apply sphere and background allocations
    sb_data = state.data.get("spheres_backgrounds", state.data.get("spheres", {}))
    if isinstance(sb_data, dict):
        for sub_key in ("spheres", "backgrounds"):
            sub_data = sb_data.get(sub_key, {})
            for trait, value in sub_data.items():
                if state.schema.has_trait(trait):
                    flat_traits[trait] = value

    # Apply freebie additions
    freebie_data = state.data.get("freebies", {})
    for trait, value in freebie_data.get("trait_additions", {}).items():
        if state.schema.has_trait(trait):
            flat_traits[trait] = flat_traits.get(trait, 0) + value

    # Merits/flaws
    merits_flaws = freebie_data.get("merits", []) + freebie_data.get("flaws", [])

    # Create character
    char = Character(
        schema=state.schema,
        traits=flat_traits,
        merits_flaws=merits_flaws,
        identity=identity,
    )

    # Attach resources
    char.resources = ResourceManager(state.splat_data.resource_config)

    # Set willpower from freebie if raised
    wp_bonus = freebie_data.get("trait_additions", {}).get("willpower", 0)
    if wp_bonus > 0 and char.resources.has_resource("willpower"):
        pool = char.resources.pools["willpower"]
        pool.current_value = pool.max + wp_bonus
        pool.max = pool.current_value

    return char


def _build_from_template(state: ChargenState) -> Character:
    """Build character from a pre-built template file."""
    identity_data = state.data.get("identity", {})
    template_data = state.data.get("template_pick", {})
    template_file = template_data.get("template_file", "")

    # Resolve template path relative to the splat directory
    # templates_dir is e.g. /path/to/game/splats/mage/templates
    # template_file is e.g. "templates/va_code_witch.yaml"
    splat_dir = os.path.dirname(state.splat_data.templates_dir.rstrip("/"))
    full_path = os.path.join(splat_dir, template_file)

    with open(full_path) as f:
        char_data = yaml.safe_load(f)

    # Flatten traits
    flat_traits: dict[str, int] = {}
    for category_traits in char_data.get("traits", {}).values():
        if isinstance(category_traits, dict):
            flat_traits.update(category_traits)

    # Override identity with player's name
    file_identity = char_data.get("identity", {})
    if identity_data.get("name"):
        file_identity["name"] = identity_data["name"]

    char = Character(
        schema=state.schema,
        traits=flat_traits,
        merits_flaws=char_data.get("merits_flaws", []),
        identity=file_identity,
    )

    # Attach resources
    char.resources = ResourceManager(state.splat_data.resource_config)
    for res_name, res_value in char_data.get("resources", {}).items():
        if char.resources.has_resource(res_name) and isinstance(res_value, int):
            pool = char.resources.pools[res_name]
            pool.current_value = res_value
            if res_value > pool.max:
                pool.max = res_value

    return char
