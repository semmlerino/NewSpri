#!/usr/bin/env python3
"""
Frame Extractor Widget
Frame extraction settings widget for sprite sheet processing.
Part of Python Sprite Viewer - Phase 5: UI Component Extraction.
"""

from typing import Tuple

from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
    QButtonGroup, QRadioButton, QFrame, QSpinBox, QPushButton, QCheckBox
)
from PySide6.QtCore import Signal

from config import Config
from styles import StyleManager


class FrameExtractor(QGroupBox):
    """Frame extraction settings widget."""
    
    settingsChanged = Signal()
    presetSelected = Signal(int, int)
    
    def __init__(self):
        super().__init__("Frame Extraction")
        self.setStyleSheet(StyleManager.get_frame_extractor_groupbox())
        
        layout = QVBoxLayout(self)
        
        # Quick presets as radio buttons
        preset_label = QLabel("Quick Presets:")
        preset_label.setStyleSheet(StyleManager.get_preset_label())
        layout.addWidget(preset_label)
        
        presets_layout = QGridLayout()
        presets_layout.setSpacing(Config.UI.PRESET_GRID_SPACING)
        
        self.preset_group = QButtonGroup()
        preset_data = Config.FrameExtraction.FRAME_PRESETS
        
        for i, (label, width, height, tooltip) in enumerate(preset_data):
            btn = QRadioButton(label)
            btn.setToolTip(tooltip)
            btn.clicked.connect(lambda checked, w=width, h=height: self.presetSelected.emit(w, h))
            self.preset_group.addButton(btn, i)
            presets_layout.addWidget(btn, i // 3, i % 3)
        
        # Default to 192×192
        self.preset_group.button(Config.FrameExtraction.DEFAULT_PRESET_INDEX).setChecked(True)
        
        layout.addLayout(presets_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameStyle(QFrame.HLine | QFrame.Sunken)
        layout.addWidget(separator)
        
        # Custom size controls
        custom_label = QLabel("Custom Size:")
        custom_label.setStyleSheet(StyleManager.get_custom_label())
        layout.addWidget(custom_label)
        
        size_layout = QHBoxLayout()
        size_layout.setSpacing(Config.UI.SIZE_LAYOUT_SPACING)
        
        self.width_spin = QSpinBox()
        self.width_spin.setRange(Config.FrameExtraction.MIN_FRAME_SIZE, Config.FrameExtraction.MAX_FRAME_SIZE)
        self.width_spin.setValue(Config.FrameExtraction.DEFAULT_FRAME_WIDTH)
        self.width_spin.setSuffix(" px")
        self.width_spin.valueChanged.connect(self._on_custom_size_changed)
        size_layout.addWidget(self.width_spin)
        
        size_layout.addWidget(QLabel("×"))
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(Config.FrameExtraction.MIN_FRAME_SIZE, Config.FrameExtraction.MAX_FRAME_SIZE)
        self.height_spin.setValue(Config.FrameExtraction.DEFAULT_FRAME_HEIGHT)
        self.height_spin.setSuffix(" px")
        self.height_spin.valueChanged.connect(self._on_custom_size_changed)
        size_layout.addWidget(self.height_spin)
        
        # Auto-detect button
        self.auto_btn = QPushButton("Auto")
        self.auto_btn.setMaximumWidth(Config.UI.AUTO_BUTTON_MAX_WIDTH)
        self.auto_btn.setToolTip("Auto-detect frame size")
        size_layout.addWidget(self.auto_btn)
        
        layout.addLayout(size_layout)
        
        # Offset controls
        offset_label = QLabel("Offset (if needed):")
        offset_label.setStyleSheet(StyleManager.get_offset_label())
        layout.addWidget(offset_label)
        
        offset_layout = QHBoxLayout()
        offset_layout.setSpacing(Config.UI.SIZE_LAYOUT_SPACING)
        
        offset_layout.addWidget(QLabel("X:"))
        self.offset_x = QSpinBox()
        self.offset_x.setRange(Config.FrameExtraction.DEFAULT_OFFSET, Config.FrameExtraction.MAX_OFFSET)
        self.offset_x.setValue(Config.FrameExtraction.DEFAULT_OFFSET)
        self.offset_x.setSuffix(" px")
        self.offset_x.valueChanged.connect(self.settingsChanged)
        offset_layout.addWidget(self.offset_x)
        
        offset_layout.addWidget(QLabel("Y:"))
        self.offset_y = QSpinBox()
        self.offset_y.setRange(Config.FrameExtraction.DEFAULT_OFFSET, Config.FrameExtraction.MAX_OFFSET)
        self.offset_y.setValue(Config.FrameExtraction.DEFAULT_OFFSET)
        self.offset_y.setSuffix(" px")
        self.offset_y.valueChanged.connect(self.settingsChanged)
        offset_layout.addWidget(self.offset_y)
        
        # Auto-detect margins button
        self.auto_margins_btn = QPushButton("Auto")
        self.auto_margins_btn.setMaximumWidth(Config.UI.AUTO_BUTTON_MAX_WIDTH)
        self.auto_margins_btn.setToolTip("Auto-detect margins")
        offset_layout.addWidget(self.auto_margins_btn)
        
        layout.addLayout(offset_layout)
        
        # Grid overlay checkbox
        self.grid_checkbox = QCheckBox("Show grid overlay")
        self.grid_checkbox.setStyleSheet(StyleManager.get_grid_checkbox())
        layout.addWidget(self.grid_checkbox)
    
    def _on_custom_size_changed(self):
        """Handle custom size change."""
        # Uncheck all preset buttons when custom size is used
        for button in self.preset_group.buttons():
            button.setChecked(False)
        self.settingsChanged.emit()
    
    def get_frame_size(self) -> Tuple[int, int]:
        """Get current frame size."""
        return self.width_spin.value(), self.height_spin.value()
    
    def get_offset(self) -> Tuple[int, int]:
        """Get current offset."""
        return self.offset_x.value(), self.offset_y.value()
    
    def set_frame_size(self, width: int, height: int):
        """Set frame size programmatically."""
        self.width_spin.setValue(width)
        self.height_spin.setValue(height)
        
        # Check corresponding preset if it matches
        for i, btn in enumerate(self.preset_group.buttons()):
            preset_text = btn.text()
            if preset_text == f"{width}×{height}":
                btn.setChecked(True)
                break


# Export for easy importing
__all__ = ['FrameExtractor']