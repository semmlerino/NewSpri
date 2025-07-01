"""
Export Dialog Wizard
New wizard-based export dialog with improved usability.
Replaces the monolithic export dialog with a step-by-step interface.
"""

from typing import Optional, List, Dict, Any
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QApplication, QMessageBox,
    QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal, QTimer, QSize
from PySide6.QtGui import QPixmap

from .wizard_widget import WizardWidget
from .export_type_step_simple import ExportTypeStepSimple as ExportTypeStep
from .export_settings_step_simple import ExportSettingsStepSimple as ExportSettingsStep
from .export_preview_step import ExportPreviewStep
from .frame_exporter import get_frame_exporter, SpriteSheetLayout
from config import Config


class ExportDialogWizard(QDialog):
    """
    New wizard-based export dialog with improved usability.
    Features:
    - Step-by-step wizard interface
    - Contextual options based on export type
    - Visual preview before export
    - Better sizing and no scrolling needed
    """
    
    # Signals
    exportRequested = Signal(dict)  # Export settings when user confirms
    
    def __init__(self, parent=None, frame_count: int = 0, current_frame: int = 0,
                 segment_manager=None, sprites: List[QPixmap] = None):
        """
        Initialize the wizard-based export dialog.
        
        Args:
            parent: Parent widget
            frame_count: Total number of frames available
            current_frame: Currently selected frame index
            segment_manager: Optional animation segment manager
            sprites: Optional list of sprite pixmaps for preview
        """
        super().__init__(parent)
        self.frame_count = frame_count
        self.current_frame = current_frame
        self.segment_manager = segment_manager
        self.sprites = sprites or []
        self._exporter = get_frame_exporter()
        
        self._setup_ui()
        self._setup_steps()
        self._connect_signals()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Export Frames")
        self.setModal(True)
        
        # Better default sizing - no scrolling needed
        self._setup_dialog_size()
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create wizard widget
        self.wizard = WizardWidget()
        layout.addWidget(self.wizard)
        
        # Apply modern dialog styling
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
        """)
    
    def _setup_dialog_size(self):
        """Set up smart dialog sizing based on screen."""
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            
            # Calculate optimal size (larger than old dialog)
            width = min(900, int(screen_geometry.width() * 0.7))
            height = min(700, int(screen_geometry.height() * 0.85))
            
            # Minimum size to prevent cramping
            self.setMinimumSize(800, 600)
            
            # Set size
            self.resize(width, height)
            
            # Center on screen
            x = (screen_geometry.width() - width) // 2
            y = (screen_geometry.height() - height) // 2
            self.move(x, y)
        else:
            # Fallback size
            self.resize(850, 650)
    
    def _setup_steps(self):
        """Set up wizard steps."""
        # Step 1: Choose export type
        self.type_step = ExportTypeStep(frame_count=self.frame_count)
        self.wizard.add_step(self.type_step)
        
        # Step 2: Configure settings
        self.settings_step = ExportSettingsStep(
            frame_count=self.frame_count,
            current_frame=self.current_frame
        )
        self.wizard.add_step(self.settings_step)
        
        # Step 3: Preview and export
        self.preview_step = ExportPreviewStep(sprites=self.sprites)
        self.wizard.add_step(self.preview_step)
    
    def _connect_signals(self):
        """Connect internal signals."""
        # Wizard signals
        self.wizard.wizardFinished.connect(self._on_wizard_finished)
        self.wizard.wizardCancelled.connect(self.reject)
        
        # Step-specific signals
        self.wizard.currentStepChanged.connect(self._on_step_changed)
        
        # Exporter signals
        self._exporter.exportStarted.connect(self._on_export_started)
        self._exporter.exportProgress.connect(self._on_export_progress)
        self._exporter.exportFinished.connect(self._on_export_finished)
        self._exporter.exportError.connect(self._on_export_error)
        
        # Preview step export button
        self.preview_step.export_now_button.clicked.connect(self._on_export_now)
    
    def _on_step_changed(self, step_index: int):
        """Handle step changes."""
        # Update preview when reaching the preview step
        if step_index == 2 and self.sprites:  # Preview step
            self.preview_step.set_sprites(self.sprites)
    
    def _on_wizard_finished(self, wizard_data: Dict[str, Any]):
        """Handle wizard completion."""
        # This is called when user clicks Finish on the last step
        # But we handle export through the Export Now button instead
        pass
    
    def _on_export_now(self):
        """Handle Export Now button from preview step."""
        # Gather all settings from wizard steps
        settings = self._gather_export_settings()
        
        if not settings:
            QMessageBox.warning(self, "Export Error", "Unable to gather export settings.")
            return
        
        # Validate settings
        is_valid, error_message = self._validate_export_settings(settings)
        if not is_valid:
            QMessageBox.warning(self, "Export Error", error_message)
            return
        
        # Check for file overwrite
        if self._check_file_overwrite_risk(settings):
            reply = QMessageBox.question(
                self, "Overwrite Existing Files?",
                "Some files already exist in the target directory and will be overwritten.\n\n"
                "Do you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
        
        # Emit export request
        self.exportRequested.emit(settings)
    
    def _gather_export_settings(self) -> Dict[str, Any]:
        """Gather all export settings from wizard steps."""
        wizard_data = self.wizard.get_wizard_data()
        
        # Get preset from step 1
        preset = wizard_data.get('step_0', {}).get('preset')
        if not preset:
            return {}
        
        # Get settings from step 2
        settings = wizard_data.get('step_1', {}).copy()
        
        # Add preset info
        settings['preset'] = preset
        settings['preset_name'] = preset.name
        settings['mode'] = preset.mode
        
        # Ensure required fields
        if 'pattern' not in settings:
            settings['pattern'] = Config.Export.DEFAULT_PATTERN
        
        # Handle single file exports
        if preset.mode == 'sheet':
            if 'single_filename' in settings:
                settings['base_name'] = settings['single_filename']
        
        # Create sprite sheet layout for sheet exports
        if preset.mode == 'sheet':
            layout = self._create_sprite_sheet_layout(settings)
            if layout:
                settings['sprite_sheet_layout'] = layout
        
        return settings
    
    def _create_sprite_sheet_layout(self, settings: Dict[str, Any]) -> Optional[SpriteSheetLayout]:
        """Create sprite sheet layout from settings."""
        layout_mode = settings.get('layout_mode', 'auto')
        
        # Map layout mode to SpriteSheetLayout parameters
        max_columns = None
        max_rows = None
        custom_columns = None
        custom_rows = None
        
        if layout_mode == 'columns':
            max_columns = settings.get('columns', 8)
        elif layout_mode == 'rows':
            max_rows = settings.get('rows', 8)
        elif layout_mode == 'custom':
            custom_columns = settings.get('columns', 8)
            custom_rows = settings.get('rows', 8)
        
        return SpriteSheetLayout(
            mode=layout_mode,
            spacing=settings.get('spacing', 0),
            padding=settings.get('padding', 0),
            max_columns=max_columns,
            max_rows=max_rows,
            custom_columns=custom_columns,
            custom_rows=custom_rows,
            background_mode=settings.get('background_mode', 'transparent'),
            background_color=settings.get('background_color', (255, 255, 255, 255))
        )
    
    def _validate_export_settings(self, settings: Dict[str, Any]) -> tuple[bool, str]:
        """Validate export settings."""
        # Check output directory
        output_dir = settings.get('output_dir')
        if not output_dir:
            return False, "Please specify an output directory."
        
        # Check if directory is writable
        output_path = Path(output_dir)
        if output_path.exists() and not os.access(output_path, os.W_OK):
            return False, f"Output directory is not writable: {output_dir}"
        
        # Check base name
        base_name = settings.get('base_name')
        if not base_name:
            return False, "Please specify a base filename."
        
        # Check frame selection for selected mode
        if settings.get('mode') == 'selected':
            selected_indices = settings.get('selected_indices', [])
            if not selected_indices:
                return False, "Please select at least one frame to export."
        
        return True, ""
    
    def _check_file_overwrite_risk(self, settings: Dict[str, Any]) -> bool:
        """Check if export would overwrite existing files."""
        try:
            output_dir = Path(settings.get('output_dir', ''))
            if not output_dir.exists():
                return False
            
            base_name = settings.get('base_name', 'frame')
            format_ext = settings.get('format', 'PNG').lower()
            pattern = settings.get('pattern', '{name}_{index:03d}')
            
            # Check based on export mode
            mode = settings.get('mode')
            
            if mode == 'individual':
                # Check first few files
                for i in range(min(3, self.frame_count)):
                    filename = pattern.format(name=base_name, index=i, frame=i+1)
                    if (output_dir / f"{filename}.{format_ext}").exists():
                        return True
                        
            elif mode == 'sheet':
                # Single file
                filename = f"{base_name}.{format_ext}"
                if (output_dir / filename).exists():
                    return True
                    
            elif mode == 'selected':
                # Check first selected file
                selected_indices = settings.get('selected_indices', [])
                if selected_indices:
                    filename = pattern.format(name=base_name, index=0, frame=selected_indices[0]+1)
                    if (output_dir / f"{filename}.{format_ext}").exists():
                        return True
            
            return False
            
        except Exception:
            return False
    
    def _on_export_started(self):
        """Handle export start."""
        # Disable export button
        self.preview_step.export_now_button.setEnabled(False)
        self.preview_step.export_now_button.setText("Exporting...")
        
        # Disable wizard navigation
        self.wizard.setEnabled(False)
    
    def _on_export_progress(self, current: int, total: int, message: str):
        """Handle export progress."""
        # Update button text with progress
        percent = int((current / total) * 100) if total > 0 else 0
        self.preview_step.export_now_button.setText(f"Exporting... {percent}%")
    
    def _on_export_finished(self, success: bool, message: str):
        """Handle export completion."""
        # Re-enable UI
        self.wizard.setEnabled(True)
        self.preview_step.export_now_button.setEnabled(True)
        self.preview_step.export_now_button.setText("🚀 Export Now!")
        
        if success:
            # Show success message
            reply = QMessageBox.information(
                self, "Export Complete",
                f"{message}\n\nWould you like to open the output folder?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                settings = self._gather_export_settings()
                output_dir = settings.get('output_dir')
                if output_dir and Path(output_dir).exists():
                    try:
                        import os
                        import sys
                        if sys.platform == 'win32':
                            os.startfile(output_dir)
                        elif sys.platform == 'darwin':
                            os.system(f'open "{output_dir}"')
                        else:
                            os.system(f'xdg-open "{output_dir}"')
                    except Exception as e:
                        print(f"Could not open folder: {e}")
            
            # Close dialog after successful export
            QTimer.singleShot(1000, self.accept)
        else:
            QMessageBox.warning(self, "Export Failed", message)
    
    def _on_export_error(self, error_message: str):
        """Handle export error."""
        # Re-enable UI
        self.wizard.setEnabled(True)
        self.preview_step.export_now_button.setEnabled(True)
        self.preview_step.export_now_button.setText("🚀 Export Now!")
        
        QMessageBox.critical(self, "Export Error", error_message)
    
    def set_sprites(self, sprites: List[QPixmap]):
        """Set sprite frames for preview."""
        self.sprites = sprites
        if hasattr(self, 'preview_step'):
            self.preview_step.set_sprites(sprites)


import os