"""
Coordinators module - handles cross-component coordination.
"""

from coordinators.signal_coordinator import SignalCoordinator
from coordinators.sprite_load_coordinator import SpriteLoadCoordinator, SpriteLoadDependencies

__all__ = ["SignalCoordinator", "SpriteLoadCoordinator", "SpriteLoadDependencies"]
