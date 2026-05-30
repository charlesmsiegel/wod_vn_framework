"""Resource pool system — spend, gain, linked pools."""

from __future__ import annotations

# Wound-penalty severity tiers for "levels" tracks such as Health. The UI maps
# each tier to a color in the gothic theme so a damaged track reads at a glance:
#   none -> green, minor -> yellow, moderate -> orange,
#   severe -> red, incapacitated -> black.
SEVERITY_NONE = "none"
SEVERITY_MINOR = "minor"
SEVERITY_MODERATE = "moderate"
SEVERITY_SEVERE = "severe"
SEVERITY_INCAPACITATED = "incapacitated"


def penalty_severity(penalty) -> str:
    """Classify a health-level wound penalty into a severity tier.

    ``None`` marks an Incapacitated level (no further action possible). A
    penalty of 0 is unpenalized; otherwise a deeper penalty yields a more
    severe tier. Standard World of Darkness tracks use 0 / -1 / -2 / -5.
    """
    if penalty is None:
        return SEVERITY_INCAPACITATED
    if penalty >= 0:
        return SEVERITY_NONE
    if penalty >= -1:
        return SEVERITY_MINOR
    if penalty >= -2:
        return SEVERITY_MODERATE
    return SEVERITY_SEVERE


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

    def severity_at(self, index: int) -> str:
        """Severity tier of the track level at ``index`` (0-based, least to most severe).

        Used by the HUD to color damaged health boxes. Levels are ordered from
        least to most severe, matching how a health track fills top-down. Falls
        back to ``severe`` when ``index`` has no defined level, so unexpected
        damage still reads as harmful rather than unmarked.
        """
        if 0 <= index < len(self.levels):
            return penalty_severity(self.levels[index].get("penalty"))
        return SEVERITY_SEVERE


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
