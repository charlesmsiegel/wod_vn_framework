"""Character creation logic — state management, point pools, validation."""

from __future__ import annotations

from dataclasses import dataclass, field


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
