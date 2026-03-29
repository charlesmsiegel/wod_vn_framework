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
