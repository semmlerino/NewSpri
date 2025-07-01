"""
Export Dialog Wizard with Integrated Settings and Preview
Simplified two-step wizard with live preview functionality.
"""

from typing import List, Optional, Dict, Any
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QWidget, QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QTimer, QSize
from PySide6.QtGui import QPixmap

from .wizard_widget import WizardWidget
from .export_type_step_simple import ExportTypeStepSimple as ExportTypeStep
from .export_settings_preview_step import ExportSettingsPreviewStep
from .frame_exporter import get_frame_exporter, SpriteSheetLayout
from config import Config


class ExportDialogWizardIntegrated(QDialog):
    """
    Integrated export dialog with live preview.
    Two steps: Type selection -> Settings with live preview.
    """
    
    # Signals
    exportCompleted = Signal(str)  # Emitted with output path when export completes
    
    def __init__(self, parent=None, frame_count: int = 0, current_frame: int = 0, 
                 sprites: List[QPixmap] = None):
        super().__init__(parent)
        
        self.frame_count = frame_count
        self.current_frame = current_frame
        self.sprites = sprites or []
        
        # Dialog settings
        self.setWindowTitle("Export Sprites")
        self.setModal(True)
        self.resize(1200, 800)  # Larger for split view
        
        # Initialize wizard
        self._setup_ui()
        self._setup_wizard()
        
        # Center on screen
        self._center_on_screen()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create wizard widget
        self.wizard = WizardWidget()
        layout.addWidget(self.wizard)
        
        # Connect wizard signals
        self.wizard.wizardFinished.connect(self._on_wizard_finished)
        self.wizard.wizardCancelled.connect(self.reject)
    
    def _setup_wizard(self):
        """Set up wizard steps."""
        # Step 1: Export type selection
        self.type_step = ExportTypeStep(
            frame_count=self.frame_count
        )
        self.wizard.add_step(self.type_step)
        
        # Step 2: Settings with live preview
        self.settings_preview_step = ExportSettingsPreviewStep(
            frame_count=self.frame_count,
            current_frame=self.current_frame,
            sprites=self.sprites
        )
        self.wizard.add_step(self.settings_preview_step)
        
        # Connect export button directly
        self.settings_preview_step.export_button.clicked.connect(self._on_export_clicked)
    
    def _on_export_clicked(self):
        """Handle export button click."""
        # Trigger wizard finish to collect all data
        self.wizard._on_finish()
    
    def _on_wizard_finished(self, data: Dict[str, Any]):
        """Handle wizard completion - perform export."""
        # Extract data from wizard steps
        preset = data.get('step_0', {}).get('preset')
        settings = data.get('step_1', {})
        
        if not preset:
            QMessageBox.warning(self, "Export Error", "No export type selected.")
            return
        
        # Prepare export configuration
        export_config = self._prepare_export_config(preset, settings)
        
        # Create progress dialog
        from .export_progress_dialog import ExportProgressDialog
        progress_dialog = ExportProgressDialog(
            export_type=preset.display_name,
            total_frames=len(self.sprites),
            parent=self
        )
        
        # Get exporter
        exporter = get_frame_exporter()
        
        # Connect progress signals
        exporter.exportProgress.connect(progress_dialog.update_progress)
        exporter.exportFinished.connect(lambda success, msg: self._on_export_finished(success, msg, progress_dialog))
        exporter.exportError.connect(lambda error: self._on_export_failed(error, progress_dialog))
        
        # Start export based on type
        if preset.mode == "sheet":
            self._export_sprite_sheet(exporter, export_config)
        elif preset.mode == "selected":
            self._export_selected_frames(exporter, export_config, settings.get('selected_indices', []))
        else:  # individual
            self._export_individual_frames(exporter, export_config)
        
        # Show progress dialog
        progress_dialog.show()
    
    def _prepare_export_config(self, preset, settings) -> Dict[str, Any]:
        """Prepare export configuration from settings."""
        config = {
            'output_dir': settings.get('output_dir', ''),
            'format': settings.get('format', 'PNG'),
            'scale': settings.get('scale', 1.0),
            'pattern': settings.get('pattern', Config.Export.DEFAULT_PATTERN),
            'quality': settings.get('quality', 95),
            'background_mode': settings.get('background_mode', 'transparent'),
            'background_color': settings.get('background_color', (255, 255, 255, 255))
        }
        
        # Add sprite sheet specific settings
        if preset.mode == "sheet":
            config.update({
                'layout_mode': settings.get('layout_mode', 'auto'),
                'columns': settings.get('columns', 8),
                'rows': settings.get('rows', 8),
                'spacing': settings.get('spacing', 0),
                'padding': settings.get('padding', 0),
                'single_filename': settings.get('single_filename', 'spritesheet')
            })
        else:
            config['base_name'] = settings.get('base_name', 'frame')
        
        return config
    
    def _export_individual_frames(self, exporter, config):
        """Export individual frames."""
        # Start export
        exporter.export_frames(
            frames=self.sprites,
            output_dir=config['output_dir'],
            base_name=config.get('base_name', 'frame'),
            format=config['format'],
            mode='individual',
            scale_factor=config['scale'],
            pattern=config['pattern']
        )
    
    def _export_sprite_sheet(self, exporter, config):
        """Export as sprite sheet."""
        # Create layout
        layout = SpriteSheetLayout(
            mode=config.get('layout_mode', 'auto'),
            spacing=config.get('spacing', 0),
            padding=config.get('padding', 0),
            max_columns=config.get('columns', 8) if config.get('layout_mode') == 'rows' else None,
            max_rows=config.get('rows', 8) if config.get('layout_mode') == 'columns' else None,
            custom_columns=config.get('columns', 8) if config.get('layout_mode') == 'custom' else None,
            custom_rows=config.get('rows', 8) if config.get('layout_mode') == 'custom' else None,
            background_mode=config.get('background_mode', 'transparent'),
            background_color=config.get('background_color', (255, 255, 255, 255))
        )
        
        # Construct full filename path
        filename = config.get('single_filename', 'spritesheet')
        
        # Start export - using the unified export_frames method
        exporter.export_frames(
            frames=self.sprites,
            output_dir=config['output_dir'],
            base_name=filename,
            format=config['format'],
            mode='sheet',
            scale_factor=config['scale'],
            sprite_sheet_layout=layout
        )
    
    def _export_selected_frames(self, exporter, config, selected_indices):
        """Export selected frames."""
        if not selected_indices:
            QMessageBox.warning(self, "Export Error", "No frames selected.")
            return
        
        # Start export
        exporter.export_frames(
            frames=self.sprites,
            output_dir=config['output_dir'],
            base_name=config.get('base_name', 'frame'),
            format=config['format'],
            mode='selected',
            scale_factor=config['scale'],
            pattern=config['pattern'],
            selected_indices=selected_indices
        )
    
    def _on_export_finished(self, success: bool, message: str, progress_dialog):
        """Handle export completion."""
        progress_dialog.close()
        
        if success:
            # Show success message
            QMessageBox.information(
                self,
                "Export Complete",
                f"Export completed successfully!\n\n{message}"
            )
            
            # Emit signal and close
            self.exportCompleted.emit(message)
            self.accept()
        else:
            # Show error message
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Export failed:\n\n{message}"
            )
    
    def _on_export_failed(self, error_message: str, progress_dialog):
        """Handle export failure."""
        progress_dialog.close()
        
        # Show error message
        QMessageBox.critical(
            self,
            "Export Failed",
            f"Export failed:\n\n{error_message}"
        )
    
    def _center_on_screen(self):
        """Center the dialog on screen."""
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            screen_rect = screen.availableGeometry()
            dialog_rect = self.frameGeometry()
            center_point = screen_rect.center()
            dialog_rect.moveCenter(center_point)
            self.move(dialog_rect.topLeft())
    
    def showEvent(self, event):
        """Handle dialog show event."""
        super().showEvent(event)
        # Ensure wizard starts at first step
        self.wizard.set_current_step(0)