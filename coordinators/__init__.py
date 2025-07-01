"""
Coordinators package for SpriteViewer refactoring.
Provides base classes and implementations for extracting responsibilities from main window.
"""

from .base import CoordinatorBase, CoordinatorRegistry
from .ui_setup_helper import UISetupHelper

__all__ = ['CoordinatorBase', 'CoordinatorRegistry', 'UISetupHelper']