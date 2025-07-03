"""
Export Module - Consolidated and reorganized
Maintains backward compatibility while providing cleaner structure

Phase 1 Refactoring: Directory reorganization completed 2025-07-01
"""

# New organized imports from restructured directories
from .dialogs.export_wizard import ExportDialog
from .core.frame_exporter import FrameExporter, get_frame_exporter
from .core.export_handler import ExportHandler
from .core.export_presets import ExportPreset, get_preset_manager

# Deprecated dialogs removed - no backward compatibility

# Widget compatibility (some code may import these directly)
# Import all public names from widget modules
from .widgets.frame_selection import (
    FrameSelectionWidget, FrameSelectionCompact
)
from .widgets.preview_widget import ExportPreviewWidget
from .widgets.preset_widget import ExportPresetSelector
from .widgets.progress_dialog import ExportProgressDialog
from .widgets.segment_handling import SegmentExportWidget, SegmentExportHandler
from .widgets.sprite_preview_widget import SpriteSheetPreviewWidget

# Layout configuration (might be imported directly)
from .widgets.layout_config import LayoutConfigurationWidget

# Step imports for potential direct usage
from .steps.type_selection import ExportTypeStepSimple
from .steps.settings_preview import ExportSettingsPreviewStep

# Base classes that might be used for custom implementations
from .dialogs.base.dialog_base import ExportDialogBase
from .dialogs.base.wizard_base import WizardWidget

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
    'ExportPreviewWidget',
    'ExportPresetSelector',
    'ExportProgressDialog',
    'SegmentExportWidget',
    'SegmentExportHandler',
    'SpriteSheetPreviewWidget',
    'LayoutConfigurationWidget',
    
    # Step exports
    'ExportTypeStepSimple',
    'ExportSettingsPreviewStep',
    
    # Base classes
    'ExportDialogBase',
    'WizardWidget',
]

# Version marker for tracking refactoring progress
__refactoring_phase__ = "1.0"
__refactoring_date__ = "2025-07-01"