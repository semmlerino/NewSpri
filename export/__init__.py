"""
Export package - Frame and animation export functionality.

Contains all components for exporting sprites and animations:
- Export dialog and user interface
- Export presets and configuration
- Frame export engine with threading
- Export preview and validation

Available Export Dialog Modes:
- 'legacy': Original single-page dialog
- 'wizard': Three-step wizard (Type → Settings → Preview)
- 'integrated': Two-step wizard with live preview (Type → Settings+Preview)
"""

# Import main export components
from .export_dialog import ExportDialog as LegacyExportDialog
from .export_dialog_wizard import ExportDialogWizard
from .export_dialog_wizard_integrated import ExportDialogWizardIntegrated
from .frame_exporter import get_frame_exporter, FrameExporter
from .export_presets import ExportPresetManager

# Configuration for export dialog mode
# Options: 'legacy', 'wizard', 'integrated'
EXPORT_DIALOG_MODE = 'integrated'

# Export the appropriate dialog based on configuration
if EXPORT_DIALOG_MODE == 'integrated':
    ExportDialog = ExportDialogWizardIntegrated
elif EXPORT_DIALOG_MODE == 'wizard':
    ExportDialog = ExportDialogWizard
else:
    ExportDialog = LegacyExportDialog

__all__ = [
    'ExportDialog',
    'ExportDialogWizard',
    'ExportDialogWizardIntegrated',
    'LegacyExportDialog',
    'get_frame_exporter',
    'FrameExporter', 
    'ExportPresetManager',
    'EXPORT_DIALOG_MODE'
]