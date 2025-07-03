"""
Export Layout Configuration - Sprite sheet layout configuration UI components
Part of Phase 1 refactoring to split export_dialog.py into smaller modules.
"""

from typing import Optional, Tuple
from PySide6.QtWidgets import (
    QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QSpinBox, QPushButton, QColorDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPixmap

from config import Config
from ..core.frame_exporter import SpriteSheetLayout


class LayoutConfigurationWidget(QWidget):
    """Widget for configuring sprite sheet layout settings."""
    
    # Signals
    layoutChanged = Signal()
    previewRequested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._background_color = (255, 255, 255, 255)  # Default white
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Set up the layout configuration UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Top row: Layout mode and grid constraints
        mode_row = QWidget()
        mode_layout = QHBoxLayout(mode_row)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        mode_layout.setSpacing(12)
        
        # Layout mode selection
        mode_group = QGroupBox("Layout Mode")
        mode_group_layout = QVBoxLayout(mode_group)
        mode_group_layout.setSpacing(6)
        mode_group_layout.setContentsMargins(8, 12, 8, 8)
        
        self.layout_mode_combo = QComboBox()
        self.layout_mode_combo.addItems([
            "Auto (optimal)",
            "Rows (horizontal)",
            "Columns (vertical)", 
            "Square",
            "Custom grid"
        ])
        self.layout_mode_combo.setCurrentIndex(0)  # Default to auto
        mode_group_layout.addWidget(self.layout_mode_combo)
        
        # Grid constraints (visible based on mode)
        constraints_widget = QWidget()
        constraints_layout = QHBoxLayout(constraints_widget)
        constraints_layout.setContentsMargins(0, 0, 0, 0)
        constraints_layout.setSpacing(8)
        
        # Max columns (for rows mode)
        self.max_cols_label = QLabel("Max columns:")
        self.max_cols_spin = QSpinBox()
        self.max_cols_spin.setRange(1, Config.Export.MAX_GRID_SIZE)
        self.max_cols_spin.setValue(Config.Export.DEFAULT_MAX_COLUMNS)
        self.max_cols_spin.setMaximumWidth(60)
        
        # Max rows (for columns mode)
        self.max_rows_label = QLabel("Max rows:")
        self.max_rows_spin = QSpinBox()
        self.max_rows_spin.setRange(1, Config.Export.MAX_GRID_SIZE)
        self.max_rows_spin.setValue(Config.Export.DEFAULT_MAX_ROWS)
        self.max_rows_spin.setMaximumWidth(60)
        
        # Custom grid (for custom mode)
        self.custom_cols_label = QLabel("Columns:")
        self.custom_cols_spin = QSpinBox()
        self.custom_cols_spin.setRange(1, Config.Export.MAX_GRID_SIZE)
        self.custom_cols_spin.setValue(4)
        self.custom_cols_spin.setMaximumWidth(60)
        
        self.custom_rows_label = QLabel("Rows:")
        self.custom_rows_spin = QSpinBox()
        self.custom_rows_spin.setRange(1, Config.Export.MAX_GRID_SIZE)
        self.custom_rows_spin.setValue(4)
        self.custom_rows_spin.setMaximumWidth(60)
        
        # Add constraint controls to layout
        constraints_layout.addWidget(self.max_cols_label)
        constraints_layout.addWidget(self.max_cols_spin)
        constraints_layout.addWidget(self.max_rows_label)
        constraints_layout.addWidget(self.max_rows_spin)
        constraints_layout.addWidget(self.custom_cols_label)
        constraints_layout.addWidget(self.custom_cols_spin)
        constraints_layout.addWidget(self.custom_rows_label)
        constraints_layout.addWidget(self.custom_rows_spin)
        constraints_layout.addStretch()
        
        mode_group_layout.addWidget(constraints_widget)
        mode_layout.addWidget(mode_group)
        mode_layout.addStretch()
        
        layout.addWidget(mode_row)
        
        # Middle row: Spacing and padding controls
        spacing_row = QWidget()
        spacing_layout = QHBoxLayout(spacing_row)
        spacing_layout.setContentsMargins(0, 0, 0, 0)
        spacing_layout.setSpacing(12)
        
        # Spacing control
        spacing_group = QGroupBox("Spacing")
        spacing_group_layout = QVBoxLayout(spacing_group)
        spacing_group_layout.setSpacing(6)
        spacing_group_layout.setContentsMargins(8, 12, 8, 8)
        
        self.spacing_spin = QSpinBox()
        self.spacing_spin.setRange(0, Config.Export.MAX_SPRITE_SPACING)
        self.spacing_spin.setValue(Config.Export.DEFAULT_SPRITE_SPACING)
        self.spacing_spin.setSuffix(" px")
        self.spacing_spin.setMaximumWidth(80)
        spacing_group_layout.addWidget(self.spacing_spin)
        
        # Padding control
        padding_group = QGroupBox("Padding")
        padding_group_layout = QVBoxLayout(padding_group)
        padding_group_layout.setSpacing(6)
        padding_group_layout.setContentsMargins(8, 12, 8, 8)
        
        self.padding_spin = QSpinBox()
        self.padding_spin.setRange(0, Config.Export.MAX_SHEET_PADDING)
        self.padding_spin.setValue(Config.Export.DEFAULT_SHEET_PADDING)
        self.padding_spin.setSuffix(" px")
        self.padding_spin.setMaximumWidth(80)
        padding_group_layout.addWidget(self.padding_spin)
        
        spacing_layout.addWidget(spacing_group)
        spacing_layout.addWidget(padding_group)
        spacing_layout.addStretch()
        
        layout.addWidget(spacing_row)
        
        # Bottom row: Background mode and preview
        background_row = QWidget()
        background_layout = QHBoxLayout(background_row)
        background_layout.setContentsMargins(0, 0, 0, 0)
        background_layout.setSpacing(12)
        
        # Background mode
        bg_group = QGroupBox("Background")
        bg_group_layout = QVBoxLayout(bg_group)
        bg_group_layout.setSpacing(6)
        bg_group_layout.setContentsMargins(8, 12, 8, 8)
        
        bg_mode_layout = QHBoxLayout()
        bg_mode_layout.setSpacing(8)
        
        self.background_combo = QComboBox()
        self.background_combo.addItems([
            "Transparent",
            "Solid Color",
            "Checkerboard"
        ])
        self.background_combo.setCurrentIndex(0)
        bg_mode_layout.addWidget(self.background_combo)
        
        # Color picker button (initially hidden)
        self.background_color_button = QPushButton()
        self.background_color_button.setFixedSize(30, 30)
        self.background_color_button.setStyleSheet("""
            QPushButton {
                border: 2px solid #ccc;
                border-radius: 4px;
                background-color: white;
            }
            QPushButton:hover {
                border-color: #999;
            }
        """)
        self.background_color_button.setVisible(False)
        bg_mode_layout.addWidget(self.background_color_button)
        
        bg_group_layout.addLayout(bg_mode_layout)
        background_layout.addWidget(bg_group)
        
        # Layout preview info
        preview_group = QGroupBox("Layout Preview")
        preview_group_layout = QVBoxLayout(preview_group)
        preview_group_layout.setSpacing(4)
        preview_group_layout.setContentsMargins(8, 12, 8, 8)
        
        self.layout_preview_label = QLabel("Grid: Auto | Size: Calculating...")
        self.layout_preview_label.setStyleSheet("color: #666; font-size: 11px;")
        self.layout_preview_label.setWordWrap(True)
        preview_group_layout.addWidget(self.layout_preview_label)
        
        background_layout.addWidget(preview_group)
        layout.addWidget(background_row)
        
        # Initially update constraints visibility
        self._update_constraints_visibility()
    
    def _connect_signals(self):
        """Connect internal signals."""
        self.layout_mode_combo.currentIndexChanged.connect(self._on_layout_mode_changed)
        self.max_cols_spin.valueChanged.connect(self.layoutChanged)
        self.max_rows_spin.valueChanged.connect(self.layoutChanged)
        self.custom_cols_spin.valueChanged.connect(self.layoutChanged)
        self.custom_rows_spin.valueChanged.connect(self.layoutChanged)
        self.spacing_spin.valueChanged.connect(self.layoutChanged)
        self.padding_spin.valueChanged.connect(self.layoutChanged)
        self.background_combo.currentIndexChanged.connect(self._on_background_mode_changed)
        self.background_color_button.clicked.connect(self._on_background_color_clicked)
    
    def _on_layout_mode_changed(self, index: int):
        """Handle layout mode change."""
        self._update_constraints_visibility()
        self.layoutChanged.emit()
    
    def _update_constraints_visibility(self):
        """Update visibility of constraint controls based on layout mode."""
        mode_index = self.layout_mode_combo.currentIndex()
        
        # Hide all constraints first
        self.max_cols_label.setVisible(False)
        self.max_cols_spin.setVisible(False)
        self.max_rows_label.setVisible(False)
        self.max_rows_spin.setVisible(False)
        self.custom_cols_label.setVisible(False)
        self.custom_cols_spin.setVisible(False)
        self.custom_rows_label.setVisible(False)
        self.custom_rows_spin.setVisible(False)
        
        # Show relevant constraints
        if mode_index == 1:  # Rows mode
            self.max_cols_label.setVisible(True)
            self.max_cols_spin.setVisible(True)
        elif mode_index == 2:  # Columns mode
            self.max_rows_label.setVisible(True)
            self.max_rows_spin.setVisible(True)
        elif mode_index == 4:  # Custom mode
            self.custom_cols_label.setVisible(True)
            self.custom_cols_spin.setVisible(True)
            self.custom_rows_label.setVisible(True)
            self.custom_rows_spin.setVisible(True)
    
    def _on_background_mode_changed(self, index: int):
        """Handle background mode change."""
        # Show/hide color picker based on mode
        self.background_color_button.setVisible(index == 1)  # Solid Color mode
        self.layoutChanged.emit()
    
    def _on_background_color_clicked(self):
        """Handle background color picker click."""
        current_color = QColor(*self._background_color)
        color = QColorDialog.getColor(current_color, self, "Choose Background Color")
        
        if color.isValid():
            self._background_color = (color.red(), color.green(), color.blue(), color.alpha())
            
            # Update button color
            self.background_color_button.setStyleSheet(f"""
                QPushButton {{
                    border: 2px solid #ccc;
                    border-radius: 4px;
                    background-color: {color.name()};
                }}
                QPushButton:hover {{
                    border-color: #999;
                }}
            """)
            
            self.layoutChanged.emit()
    
    def get_layout_settings(self) -> Optional[SpriteSheetLayout]:
        """Get current layout settings as SpriteSheetLayout object."""
        try:
            mode_map = {
                0: 'auto',
                1: 'rows',
                2: 'columns', 
                3: 'square',
                4: 'custom'
            }
            
            mode = mode_map.get(self.layout_mode_combo.currentIndex(), 'auto')
            spacing = self.spacing_spin.value()
            padding = self.padding_spin.value()
            
            # Background settings
            bg_modes = ['transparent', 'solid', 'checkerboard']
            bg_index = self.background_combo.currentIndex()
            background_mode = bg_modes[bg_index] if 0 <= bg_index < len(bg_modes) else 'transparent'
            
            return SpriteSheetLayout(
                mode=mode,
                spacing=spacing,
                padding=padding,
                max_columns=self.max_cols_spin.value() if mode == 'rows' else None,
                max_rows=self.max_rows_spin.value() if mode == 'columns' else None,
                custom_columns=self.custom_cols_spin.value() if mode == 'custom' else None,
                custom_rows=self.custom_rows_spin.value() if mode == 'custom' else None,
                background_mode=background_mode,
                background_color=self._background_color if background_mode == 'solid' else None
            )
            
        except Exception as e:
            print(f"Error creating sprite sheet layout: {e}")
            return None
    
    def apply_layout_settings(self, layout: SpriteSheetLayout):
        """Apply layout settings from a SpriteSheetLayout object."""
        # Set layout mode
        mode_map = {
            'auto': 0,
            'rows': 1,
            'columns': 2,
            'square': 3,
            'custom': 4
        }
        
        if layout.mode in mode_map:
            self.layout_mode_combo.setCurrentIndex(mode_map[layout.mode])
        
        # Set spacing and padding
        self.spacing_spin.setValue(layout.spacing)
        self.padding_spin.setValue(layout.padding)
        
        # Set mode-specific values
        if layout.max_columns is not None:
            self.max_cols_spin.setValue(layout.max_columns)
        if layout.max_rows is not None:
            self.max_rows_spin.setValue(layout.max_rows)
        if layout.custom_columns is not None:
            self.custom_cols_spin.setValue(layout.custom_columns)
        if layout.custom_rows is not None:
            self.custom_rows_spin.setValue(layout.custom_rows)
        
        # Set background mode
        bg_map = {
            'transparent': 0,
            'solid': 1,
            'checkerboard': 2
        }
        
        if layout.background_mode in bg_map:
            self.background_combo.setCurrentIndex(bg_map[layout.background_mode])
        
        # Set background color
        if layout.background_color:
            self._background_color = layout.background_color
            color = QColor(*layout.background_color)
            self.background_color_button.setStyleSheet(f"""
                QPushButton {{
                    border: 2px solid #ccc;
                    border-radius: 4px;
                    background-color: {color.name()};
                }}
                QPushButton:hover {{
                    border-color: #999;
                }}
            """)
    
    def update_preview_label(self, text: str):
        """Update the layout preview label."""
        self.layout_preview_label.setText(text)