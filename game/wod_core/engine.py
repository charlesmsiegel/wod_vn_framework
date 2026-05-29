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
        self.groups: dict[str, list[str]] | None = None

        if "groups" in data:
            self.groups = {}
            for group_name, traits in data["groups"].items():
                self.groups[group_name] = list(traits)
                self.trait_names.extend(traits)
        elif "traits" in data:
            self.trait_names = list(data["traits"])


def _normalize_tradition(key: str) -> str:
    """Normalize a Tradition id/name so authors can key by either.

    "Virtual Adepts" and "virtual_adepts" both normalize to "virtual_adepts".
    """
    return key.strip().lower().replace(" ", "_").replace("-", "_")


class Paradigm:
    """Optional paradigm/focus system — which casting *methods* each Tradition allows.

    A Virtual Adept can cast through "code" but not "prayer"; a Celestial Chorister
    is the reverse. Authors declare a registry of methods plus a per-Tradition
    allow-list, then gate choices with ``can_use("method")``.

    Parsed from a schema's optional ``paradigm`` block::

        paradigm:
          methods:                  # registry (id -> display name); optional
            code: "Cybernetics & Code"
            prayer: "Prayer & Faith"
          traditions:               # per-Tradition allow-lists
            virtual_adepts: [code, science]
            celestial_chorus: [prayer, art]
            default: [code]         # optional fallback for unlisted Traditions

    ``methods`` may also be a plain list of ids; display names then default to
    the id. If ``methods`` is omitted entirely, the registry is inferred from
    the union of the per-Tradition lists.
    """

    def __init__(self, data: dict):
        self.method_names: dict[str, str] = {}
        methods = data.get("methods")
        if isinstance(methods, dict):
            for mid, disp in methods.items():
                self.method_names[mid] = disp if isinstance(disp, str) else mid
        elif isinstance(methods, list):
            for item in methods:
                if isinstance(item, dict):
                    mid = item.get("id")
                    if mid is None and len(item) == 1:
                        mid, disp = next(iter(item.items()))
                        self.method_names[mid] = disp
                    elif mid is not None:
                        self.method_names[mid] = item.get("name", mid)
                else:
                    self.method_names[item] = item

        self.tradition_methods: dict[str, set[str]] = {}
        for trad, mlist in (data.get("traditions") or {}).items():
            self.tradition_methods[_normalize_tradition(trad)] = set(mlist or [])

    @property
    def declared_methods(self) -> list[str]:
        """Method ids in the explicit registry (insertion order)."""
        return list(self.method_names.keys())

    def all_methods(self) -> set[str]:
        """Every method id known to the paradigm (registry + all Tradition lists)."""
        methods = set(self.method_names)
        for allowed in self.tradition_methods.values():
            methods |= allowed
        return methods

    def methods_for(self, tradition: str | None) -> set[str]:
        """Methods permitted to a Tradition, falling back to ``default`` if listed."""
        if tradition:
            norm = _normalize_tradition(tradition)
            if norm in self.tradition_methods:
                return self.tradition_methods[norm]
        return self.tradition_methods.get("default", set())

    def can_use(self, method: str, tradition: str | None) -> bool:
        return method in self.methods_for(tradition)

    def display_name(self, method: str) -> str:
        return self.method_names.get(method, method)

    def to_dict(self) -> dict:
        """Reconstruct the raw ``paradigm`` block (for pickle / override round-trips)."""
        data: dict = {}
        if self.method_names:
            data["methods"] = dict(self.method_names)
        if self.tradition_methods:
            data["traditions"] = {
                trad: sorted(methods) for trad, methods in self.tradition_methods.items()
            }
        return data


class Schema:
    """Splat schema — trait categories, ranges, defaults, constraints, paradigm."""

    def __init__(self, data: dict):
        self.categories: dict[str, CategoryDef] = {}
        self.trait_lookup: dict[str, str] = {}
        self.constraints: list[Constraint] = []
        self.paradigm: Paradigm | None = None
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

        if data.get("paradigm"):
            self.paradigm = Paradigm(data["paradigm"])

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

    def can_use(self, method: str, tradition: str | None) -> bool:
        """Whether a Tradition may cast via ``method``.

        Returns ``True`` when no paradigm is configured — the optional system
        is simply off, so nothing is restricted.
        """
        if self.paradigm is None:
            return True
        return self.paradigm.can_use(method, tradition)

    def to_dict(self) -> dict:
        """Serialize back to a raw schema dict (categories, constraints, paradigm)."""
        data: dict = {"trait_categories": {}, "trait_constraints": []}
        for cat_name, cat in self.categories.items():
            cat_data: dict = {
                "display_name": cat.display_name,
                "range": list(cat.range),
                "default": cat.default,
            }
            if cat.groups is not None:
                cat_data["groups"] = {k: list(v) for k, v in cat.groups.items()}
            else:
                cat_data["traits"] = list(cat.trait_names)
            data["trait_categories"][cat_name] = cat_data
        for constraint in self.constraints:
            if isinstance(constraint, MaxLinkedConstraint):
                data["trait_constraints"].append({
                    "type": "max_linked",
                    "target_category": constraint.target_category,
                    "limited_by": constraint.limited_by,
                    "rule": constraint.rule,
                })
        if self.paradigm is not None:
            data["paradigm"] = self.paradigm.to_dict()
        return data


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
        # Compare against the base (permanent) value: a temporary buff to the
        # limiting trait must not let a capped trait be permanently raised.
        limit = character.base(self.limited_by)
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
        # Temporary trait modifiers, keyed by source name → {trait: delta}.
        # Applied at runtime by game logic (form-shifting, buffs); never saved.
        self.modifiers: dict[str, dict[str, int]] = {}

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
        """Effective trait value — base plus the sum of all active modifiers."""
        if name not in self.traits:
            raise KeyError(f"Unknown trait: {name!r}")
        return self.traits[name] + self.modifier_total(name)

    def base(self, name: str) -> int:
        """Permanent trait value, ignoring any temporary modifiers."""
        if name not in self.traits:
            raise KeyError(f"Unknown trait: {name!r}")
        return self.traits[name]

    def modifier_total(self, name: str) -> int:
        """Sum of every active modifier on a trait, across all sources."""
        return sum(source.get(name, 0) for source in self.modifiers.values())

    def apply_modifier(self, name: str, delta: int, source: str) -> None:
        """Add a temporary modifier to a trait, tracked by source name.

        Modifiers stack: multiple sources add together, and repeated calls
        from the same source accumulate. Remove them with remove_modifier().
        Modifiers are runtime-only and never persist in saves.
        """
        if not self.schema.has_trait(name):
            raise KeyError(f"Unknown trait: {name!r}")
        source_mods = self.modifiers.setdefault(source, {})
        source_mods[name] = source_mods.get(name, 0) + delta

    def remove_modifier(self, source: str) -> None:
        """Remove every modifier contributed by a source. No-op if absent."""
        self.modifiers.pop(source, None)

    def clear_modifiers(self) -> None:
        """Remove all temporary modifiers from every source."""
        self.modifiers.clear()

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
        # Advance the permanent base value, not the temporarily-modified one.
        self.set(name, self.base(name) + 1)

    def has(self, name: str) -> bool:
        return any(mf["name"] == name for mf in self.merits_flaws)

    def can_use(self, method: str) -> bool:
        """Whether this character's paradigm permits casting via ``method``.

        Resolves the character's Tradition from ``identity["tradition"]``. Returns
        ``True`` when the schema defines no paradigm (the optional system is off).
        """
        return self.schema.can_use(method, self.identity.get("tradition"))

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

    def __getstate__(self):
        """Exclude Schema object from pickle — store reconstructable raw data instead."""
        state = self.__dict__.copy()
        # Temporary modifiers are reapplied by game logic — never persisted.
        state.pop("modifiers", None)
        # Schema is large and reconstructable — store the raw data instead
        if "schema" in state:
            schema = state.pop("schema")
            state["_schema_data"] = schema.to_dict() if schema is not None else None
        return state

    def __setstate__(self, state):
        """Reconstruct Schema from stored raw data."""
        schema_data = state.pop("_schema_data", None)
        self.__dict__.update(state)
        if schema_data:
            self.schema = Schema(schema_data)
        else:
            self.schema = None
        # Modifiers are never persisted; a loaded character always starts clean.
        self.modifiers = {}

    def spend(self, name: str, amount: int) -> bool:
        if self.resources is None:
            raise RuntimeError("No resources configured for this character")
        return self.resources.spend(name, amount)

    def gain(self, name: str, amount: int) -> int:
        if self.resources is None:
            raise RuntimeError("No resources configured for this character")
        return self.resources.gain(name, amount)
