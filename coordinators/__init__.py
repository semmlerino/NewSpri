"""
Coordinators package for SpriteViewer refactoring.
Provides base classes and implementations for extracting responsibilities from main window.
"""

from .base import CoordinatorBase, CoordinatorRegistry
from .ui_setup_helper import UISetupHelper
from .view_coordinator import ViewCoordinator

__all__ = ['CoordinatorBase', 'CoordinatorRegistry', 'UISetupHelper', 'ViewCoordinator']