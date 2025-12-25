"""
Export Module - Consolidated and reorganized
Maintains backward compatibility while providing cleaner structure

Phase 1 Refactoring: Directory reorganization completed 2025-07-01
"""

# New organized imports from restructured directories
from .core.export_handler import ExportHandler
from .core.export_presets import ExportPreset, get_preset_manager
from .core.frame_exporter import FrameExporter, get_frame_exporter

# Base classes that might be used for custom implementations
from .dialogs.base.wizard_base import WizardWidget
from .dialogs.export_wizard import ExportDialog

# Step imports for potential direct usage
from .steps.type_selection import ExportTypeStepSimple

# Deprecated dialogs removed - no backward compatibility
# Widget compatibility (some code may import these directly)
# Import all public names from widget modules
from .widgets.frame_selection import FrameSelectionCompact, FrameSelectionWidget

# Layout configuration (might be imported directly)
from .widgets.layout_config import LayoutConfigurationWidget
from .widgets.preset_widget import ExportPresetSelector
from .widgets.progress_dialog import ExportProgressDialog
from .widgets.segment_handling import SegmentExportHandler, SegmentExportWidget
from .widgets.sprite_preview_widget import SpriteSheetPreviewWidget

# Maintain the same __all__ export list for API stability
__all__ = [
    # Primary exports
    'ExportDialog',
    'FrameExporter',
    'get_frame_exporter',
    'ExportHandler',
    'ExportPreset',
    'get_preset_manager',


    # Widget exports
    'FrameSelectionWidget',
    'FrameSelectionCompact',
    'ExportPresetSelector',
    'ExportProgressDialog',
    'SegmentExportWidget',
    'SegmentExportHandler',
    'SpriteSheetPreviewWidget',
    'LayoutConfigurationWidget',

    # Step exports
    'ExportTypeStepSimple',

    # Base classes
    'WizardWidget',
]

# Version marker for tracking refactoring progress
__refactoring_phase__ = "1.0"
__refactoring_date__ = "2025-07-01"
