"""
Coordinators package for SpriteViewer.
Provides implementations for extracting responsibilities from main window.
"""

from .animation_coordinator import AnimationCoordinator
from .event_coordinator import EventCoordinator
from .export_coordinator import ExportCoordinator
from .ui_setup_helper import UISetupHelper

__all__ = ['AnimationCoordinator', 'EventCoordinator', 'ExportCoordinator', 'UISetupHelper']
