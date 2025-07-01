"""
Export Type Selection Step (Simplified)
Clean, simple export type selection without clutter.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QRadioButton, QButtonGroup,
    QLabel, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .wizard_widget import WizardStep
from .export_presets import ExportPreset, get_preset_manager
from config import Config


class SimpleExportOption(QFrame):
    """Simple, clean export option widget."""
    
    clicked = Signal()
    
    def __init__(self, preset: ExportPreset, parent=None):
        super().__init__(parent)
        self.preset = preset
        self._is_selected = False
        self._radio_button = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the simple option UI."""
        self.setFrameStyle(QFrame.StyledPanel)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        
        # Radio button with icon and title
        title_text = f"{self.preset.icon} {self.preset.display_name}"
        self._radio_button = QRadioButton(title_text)
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        self._radio_button.setFont(title_font)
        layout.addWidget(self._radio_button)
        
        # Simple description
        desc_label = QLabel(self.preset.short_description or self.preset.description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #6c757d; margin-left: 23px;")
        layout.addWidget(desc_label)
        
        # Use cases (compact)
        if self.preset.use_cases and len(self.preset.use_cases) > 0:
            uses_text = "Best for: " + ", ".join(self.preset.use_cases[:3])
            uses_label = QLabel(uses_text)
            uses_label.setWordWrap(True)
            uses_label.setStyleSheet("color: #6c757d; font-size: 10px; margin-left: 23px;")
            layout.addWidget(uses_label)
        
        self._update_style()
    
    def _update_style(self):
        """Update frame style based on selection."""
        if self._is_selected:
            self.setStyleSheet("""
                SimpleExportOption {
                    background-color: #e7f3ff;
                    border: 2px solid #007bff;
                    border-radius: 8px;
                }
            """)
        else:
            self.setStyleSheet("""
                SimpleExportOption {
                    background-color: #ffffff;
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                }
                SimpleExportOption:hover {
                    background-color: #f8f9fa;
                    border: 1px solid #007bff;
                }
            """)
    
    def set_selected(self, selected: bool):
        """Set selection state."""
        self._is_selected = selected
        self._radio_button.setChecked(selected)
        self._update_style()
    
    def mousePressEvent(self, event):
        """Handle mouse press to select option."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class ExportTypeStepSimple(WizardStep):
    """
    Simplified export type selection step.
    Clean, focused interface without clutter.
    """
    
    # Signal emitted when a preset is selected
    presetSelected = Signal(ExportPreset)
    
    def __init__(self, frame_count: int = 0, parent=None):
        super().__init__(
            title="Choose Export Type",
            subtitle="Select how you want to export your sprite frames",
            parent=parent
        )
        self.frame_count = frame_count
        self._preset_manager = get_preset_manager()
        self._selected_preset: Optional[ExportPreset] = None
        self._options: List[SimpleExportOption] = []
        self._button_group = QButtonGroup()
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the simplified UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)
        
        # Main options
        options_widget = self._create_export_options()
        layout.addWidget(options_widget, 1)
        
        # Simple help text
        help_label = QLabel("Select an export type above to continue.")
        help_label.setStyleSheet("color: #6c757d; font-size: 11px;")
        layout.addWidget(help_label)
    
    def _create_export_options(self) -> QWidget:
        """Create the export options list."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)
        
        # Define which presets to show (no GIF)
        preset_names = [
            "individual_frames",
            "sprite_sheet", 
            "selected_frames"
        ]
        
        # Create option widgets
        for preset_name in preset_names:
            preset = self._preset_manager.get_preset(preset_name)
            if preset:
                option = SimpleExportOption(preset)
                option.clicked.connect(lambda p=preset: self._on_option_clicked(p))
                self._options.append(option)
                layout.addWidget(option)
                
                # Add radio button to group
                self._button_group.addButton(option._radio_button)
        
        layout.addStretch()
        return container
    
    def _on_option_clicked(self, preset: ExportPreset):
        """Handle option selection."""
        self._select_preset(preset)
    
    def _select_preset(self, preset: ExportPreset):
        """Select a preset and update UI."""
        self._selected_preset = preset
        
        # Update option selection states
        for option in self._options:
            option.set_selected(option.preset == preset)
        
        # Emit signals
        self.stepValidated.emit(True)
        self.dataChanged.emit(self.get_data())
        self.presetSelected.emit(preset)
    
    def validate(self) -> bool:
        """Validate that a preset is selected."""
        return self._selected_preset is not None
    
    def get_data(self) -> Dict[str, Any]:
        """Get the selected preset data."""
        if self._selected_preset:
            return {
                'preset': self._selected_preset,
                'preset_name': self._selected_preset.name,
                'export_mode': self._selected_preset.mode
            }
        return {}
    
    def set_data(self, data: Dict[str, Any]):
        """Set data (for going back in wizard)."""
        preset_name = data.get('preset_name')
        if preset_name:
            preset = self._preset_manager.get_preset(preset_name)
            if preset:
                self._select_preset(preset)


@dataclass
class EnhancedExportPreset(ExportPreset):
    """Enhanced export preset with additional metadata."""
    
    short_description: str = ""
    recommended_for: List[str] = None
    
    def __post_init__(self):
        if self.recommended_for is None:
            self.recommended_for = []