# tests/test_resources.py
import pytest
from wod_core.resources import ResourcePool, ResourceManager


class TestResourcePool:
    """Test individual resource pool behavior."""

    def test_default_value(self):
        pool = ResourcePool("quintessence", {"range": [0, 20], "default": 0})
        assert pool.current() == 0

    def test_default_current_max_uses_explicit_max(self):
        pool = ResourcePool("willpower", {"range": [0, 10], "default_max": 5, "default_current": "max"})
        assert pool.current() == 5
        assert pool.max == 5

    def test_default_current_max_uses_range_upper(self):
        pool = ResourcePool("health", {"range": [0, 7], "default_current": "max"})
        assert pool.current() == 7
        assert pool.max == 7

    def test_spend_success(self):
        pool = ResourcePool("quintessence", {"range": [0, 20], "default": 10})
        assert pool.spend(3) is True
        assert pool.current() == 7

    def test_spend_insufficient_returns_false(self):
        pool = ResourcePool("quintessence", {"range": [0, 20], "default": 2})
        assert pool.spend(5) is False
        assert pool.current() == 2

    def test_gain(self):
        pool = ResourcePool("quintessence", {"range": [0, 20], "default": 10})
        gained = pool.gain(5)
        assert pool.current() == 15
        assert gained == 5

    def test_gain_capped_at_range_max(self):
        pool = ResourcePool("quintessence", {"range": [0, 20], "default": 18})
        gained = pool.gain(5)
        assert pool.current() == 20
        assert gained == 2

    def test_at_max(self):
        pool = ResourcePool("willpower", {"range": [0, 10], "default_max": 5, "default_current": "max"})
        assert pool.at_max() is True
        pool.spend(1)
        assert pool.at_max() is False

    def test_at_min(self):
        pool = ResourcePool("quintessence", {"range": [0, 20], "default": 0})
        assert pool.at_min() is True
        pool.gain(1)
        assert pool.at_min() is False

    def test_levels_stored(self):
        levels = [{"name": "Bruised", "penalty": 0}, {"name": "Hurt", "penalty": -1}]
        pool = ResourcePool("health", {"range": [0, 7], "default_current": "max", "track_type": "levels", "levels": levels})
        assert pool.track_type == "levels"
        assert len(pool.levels) == 2


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
        assert mgr.current("quintessence") == 12

    def test_gain_quintessence_reduces_paradox(self, mage_resource_data):
        mgr = ResourceManager(mage_resource_data)
        mgr.gain("paradox", 15)
        assert mgr.current("paradox") == 15
        mgr.gain("quintessence", 8)
        assert mgr.current("quintessence") == 8
        assert mgr.current("paradox") == 12

    def test_within_limit_no_reduction(self, mage_resource_data):
        mgr = ResourceManager(mage_resource_data)
        mgr.gain("quintessence", 10)
        mgr.gain("paradox", 5)
        assert mgr.current("quintessence") == 10
        assert mgr.current("paradox") == 5

    def test_at_limit_exact(self, mage_resource_data):
        mgr = ResourceManager(mage_resource_data)
        mgr.gain("quintessence", 12)
        mgr.gain("paradox", 8)
        assert mgr.current("quintessence") == 12
        assert mgr.current("paradox") == 8

    def test_unlinked_resources_not_affected(self, mage_resource_data):
        mgr = ResourceManager(mage_resource_data)
        original_wp = mgr.current("willpower")
        mgr.gain("quintessence", 20)
        assert mgr.current("willpower") == original_wp
