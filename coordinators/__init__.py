"""
Coordinators package for SpriteViewer refactoring.
Provides base classes and implementations for extracting responsibilities from main window.
"""

from .animation_coordinator import AnimationCoordinator
from .base import CoordinatorBase, CoordinatorRegistry
from .event_coordinator import EventCoordinator
from .export_coordinator import ExportCoordinator
from .ui_setup_helper import UISetupHelper
from .view_coordinator import ViewCoordinator

__all__ = ['AnimationCoordinator', 'CoordinatorBase', 'CoordinatorRegistry', 'EventCoordinator', 'ExportCoordinator', 'UISetupHelper', 'ViewCoordinator']
