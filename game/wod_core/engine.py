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

    def spend(self, name: str, amount: int) -> bool:
        if self.resources is None:
            raise RuntimeError("No resources configured for this character")
        return self.resources.spend(name, amount)

    def gain(self, name: str, amount: int) -> int:
        if self.resources is None:
            raise RuntimeError("No resources configured for this character")
        return self.resources.gain(name, amount)
