"""
Export Dialog Wizard with Integrated Settings and Preview
Simplified two-step wizard with live preview functionality.
"""

import logging
from typing import List, Dict, Any
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QMessageBox
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QPixmap

from .base.wizard_base import WizardWidget
from ..steps.type_selection import ExportTypeStepSimple as ExportTypeStep
from ..steps.modern_settings_preview import ModernExportSettings
from ..core.frame_exporter import get_frame_exporter, SpriteSheetLayout
from config import Config

logger = logging.getLogger(__name__)


class ExportDialog(QDialog):
    """
    Integrated export dialog with live preview.
    Two steps: Type selection -> Settings with live preview.
    """
    
    # Signals
    exportCompleted = Signal(str)  # Emitted with output path when export completes
    exportRequested = Signal(dict)  # Emitted when export is requested (for compatibility)
    
    def __init__(self, parent=None, frame_count: int = 0, current_frame: int = 0, 
                 sprites: List[QPixmap] = None, segment_manager=None):
        super().__init__(parent)
        
        self.frame_count = frame_count
        self.current_frame = current_frame
        self.sprites = sprites or []
        self.segment_manager = segment_manager  # Store for compatibility
        
        # Dialog settings
        self.setWindowTitle("Export Sprites")
        self.setModal(True)
        self.resize(900, 650)  # Optimized for modern compact layout
        
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
            frame_count=self.frame_count,
            segment_manager=self.segment_manager
        )
        self.wizard.add_step(self.type_step)
        
        # Step 2: Settings with live preview
        self.settings_preview_step = ModernExportSettings(
            frame_count=self.frame_count,
            current_frame=self.current_frame,
            sprites=self.sprites,
            segment_manager=self.segment_manager
        )
        self.wizard.add_step(self.settings_preview_step)
        
        # Connect export button directly
        self.settings_preview_step.export_btn.clicked.connect(self._on_export_clicked)
    
    def _on_export_clicked(self):
        """Handle export button click."""
        logger.debug("Export button clicked")
        logger.debug("Segment manager available: %s", self.segment_manager is not None)
        if self.segment_manager:
            segments = self.segment_manager.get_all_segments()
            logger.debug("Number of segments available: %d", len(segments))
            for i, seg in enumerate(segments):
                logger.debug("  Segment %d: '%s' frames %d-%d", i, seg.name, seg.start_frame, seg.end_frame)

        # Trigger wizard finish to collect all data
        logger.debug("Triggering wizard finish to collect data")
        self.wizard._on_finish()
    
    def _on_wizard_finished(self, data: Dict[str, Any]):
        """Handle wizard completion - perform export."""
        logger.debug("_on_wizard_finished called")
        logger.debug("Wizard data keys: %s", list(data.keys()))

        # Extract data from wizard steps
        preset = data.get('step_0', {}).get('preset')
        settings = data.get('step_1', {})

        logger.debug("Preset: %s", preset)
        logger.debug("Preset mode: %s", preset.mode if preset else 'None')
        logger.debug("Settings keys: %s", list(settings.keys()))

        if not preset:
            QMessageBox.warning(self, "Export Error", "No export type selected.")
            return

        # Prepare export configuration
        logger.debug("Preparing export configuration")
        export_config = self._prepare_export_config(preset, settings)
        logger.debug("Export config keys: %s", list(export_config.keys()))
        logger.debug("Export config mode: %s", export_config.get('mode', 'None'))
        
        # Emit exportRequested for compatibility with sprite_viewer
        self.exportRequested.emit(export_config)
        
        # Create progress dialog
        from ..widgets.progress_dialog import ExportProgressDialog
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
        logger.debug("Starting export for mode: %s", preset.mode)
        if preset.mode == "sheet":
            logger.debug("Calling _export_sprite_sheet")
            self._export_sprite_sheet(exporter, export_config)
        elif preset.mode == "selected":
            selected_indices = settings.get('selected_indices', [])
            logger.debug("Calling _export_selected_frames with %d selected indices", len(selected_indices))
            self._export_selected_frames(exporter, export_config, selected_indices)
        elif preset.mode == "segments_sheet":
            logger.debug("Calling _export_segments_per_row")
            self._export_segments_per_row(exporter, export_config)
        else:  # individual
            logger.debug("Calling _export_individual_frames")
            self._export_individual_frames(exporter, export_config)
        
        # Show progress dialog
        progress_dialog.show()
    
    def _prepare_export_config(self, preset, settings) -> Dict[str, Any]:
        """Prepare export configuration from settings."""
        config = {
            'output_dir': settings.get('output_dir', ''),
            'format': settings.get('format', 'PNG'),
            'scale': settings.get('scale', 1.0),
            'scale_factor': settings.get('scale', 1.0),  # Export handler expects scale_factor
            'pattern': settings.get('pattern', Config.Export.DEFAULT_PATTERN),
            'quality': settings.get('quality', 95),
            'background_mode': settings.get('background_mode', 'transparent'),
            'background_color': settings.get('background_color', (255, 255, 255, 255)),
            'mode': preset.mode  # Add mode for export handler
        }
        
        # Add base_name for all export types
        if preset.mode == "sheet" or preset.mode == "segments_sheet":
            # For sprite sheets, use single_filename as base_name
            config['base_name'] = settings.get('single_filename', 'spritesheet')
            config.update({
                'layout_mode': settings.get('layout_mode', 'auto'),
                'columns': settings.get('columns', 8),
                'rows': settings.get('rows', 8),
                'spacing': settings.get('spacing', 0),
                'padding': settings.get('padding', 0),
                'single_filename': settings.get('single_filename', 'spritesheet')
            })
            # Special handling for segments per row
            if preset.mode == "segments_sheet":
                config['sprite_sheet_layout'] = preset.sprite_sheet_layout
        else:
            # For individual/selected frames
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
    
    def _export_segments_per_row(self, exporter, config):
        """Export sprite sheet with segments per row."""
        logger.debug("_export_segments_per_row called")
        logger.debug("segment_manager available: %s", self.segment_manager is not None)

        if not self.segment_manager:
            logger.debug("No segment manager available, showing error")
            QMessageBox.warning(self, "Export Error", "No segment manager available.")
            return

        # Get all segments
        segments = self.segment_manager.get_all_segments()
        logger.debug("Retrieved %d segments from manager", len(segments))

        if not segments:
            logger.debug("No segments found, showing error dialog")
            QMessageBox.warning(
                self,
                "Export Error",
                "No animation segments defined.\n\nPlease create segments using Animation > Manage Segments before using this export option."
            )
            return

        # Prepare segment info
        segment_info = []
        for i, segment in enumerate(segments):
            seg_info = {
                'name': segment.name,
                'start_frame': segment.start_frame,
                'end_frame': segment.end_frame
            }
            segment_info.append(seg_info)
            logger.debug("Segment %d: %s", i, seg_info)

        # Sort segments by start frame
        segment_info.sort(key=lambda s: s['start_frame'])
        logger.debug("Sorted segment info: %s", segment_info)
        
        # Create layout with segments_per_row mode
        from ..core.frame_exporter import SpriteSheetLayout
        layout = SpriteSheetLayout(
            mode='segments_per_row',
            spacing=config.get('spacing', 0),
            padding=config.get('padding', 0),
            background_mode=config.get('background_mode', 'transparent'),
            background_color=config.get('background_color', (255, 255, 255, 255))
        )
        
        # Make sure the layout is included in the config
        config['sprite_sheet_layout'] = layout

        # Start export
        logger.debug("Starting segment export with %d sprites total", len(self.sprites))
        logger.debug("Export config: output_dir=%s, base_name=%s", config['output_dir'], config['base_name'])
        logger.debug("Format=%s, scale=%s", config['format'], config['scale'])
        logger.debug("Layout mode: %s", layout.mode)
        
        exporter.export_frames(
            frames=self.sprites,
            output_dir=config['output_dir'],
            base_name=config['base_name'],
            format=config['format'],
            mode='sheet',
            scale_factor=config['scale'],
            sprite_sheet_layout=layout,
            segment_info=segment_info
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
    
    def set_sprites(self, sprites: List[QPixmap]):
        """Set sprite frames for export. Compatible with legacy API."""
        self.sprites = sprites or []
        # Update the settings step if it exists
        if hasattr(self, 'settings_preview_step') and self.settings_preview_step:
            self.settings_preview_step.set_sprites(self.sprites)