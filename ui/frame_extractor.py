#!/usr/bin/env python3
"""
Frame Extractor Widget
Frame extraction settings widget for sprite sheet processing.
Part of Python Sprite Viewer - Phase 5: UI Component Extraction.
"""


from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from config import Config
from utils.ui_common import AutoButtonManager


class FrameExtractor(QGroupBox):
    """Frame extraction settings widget."""

    settingsChanged = Signal()
    presetSelected = Signal(int, int)
    modeChanged = Signal(str)  # "grid" or "ccl"

    def __init__(self):
        super().__init__("Frame Extraction")
        self.setStyleSheet(Config.Styles.FRAME_EXTRACTOR_GROUPBOX)

        # Initialize button manager
        self._button_manager = AutoButtonManager()

        layout = QVBoxLayout(self)

        # Comprehensive auto-detect button (optimized)
        self.comprehensive_auto_btn = QPushButton("🔍 Auto-Detect All")
        self.comprehensive_auto_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
        """)
        self.comprehensive_auto_btn.setToolTip("Automatically detect margins, frame size, and spacing in one click")
        layout.addWidget(self.comprehensive_auto_btn)

        # Extraction Mode Toggle
        mode_label = QLabel("Extraction Mode:")
        mode_label.setStyleSheet(Config.Styles.PRESET_LABEL)
        layout.addWidget(mode_label)

        mode_layout = QHBoxLayout()
        self.mode_group = QButtonGroup()

        self.grid_mode_btn = QRadioButton("Grid Extraction")
        self.grid_mode_btn.setToolTip("Traditional grid-based extraction for regular animation frames")
        self.grid_mode_btn.setChecked(False)  # No longer default
        self.mode_group.addButton(self.grid_mode_btn, 0)
        mode_layout.addWidget(self.grid_mode_btn)

        self.ccl_mode_btn = QRadioButton("CCL Extraction")
        self.ccl_mode_btn.setToolTip("Connected-Component Labeling for irregular sprite collections")
        self.ccl_mode_btn.setChecked(True)  # Now the default mode
        self.ccl_mode_btn.setEnabled(True)  # Enable by default
        self.mode_group.addButton(self.ccl_mode_btn, 1)
        mode_layout.addWidget(self.ccl_mode_btn)

        # Mode status indicator
        self.mode_status = QLabel("🎯 CCL mode active")
        self.mode_status.setStyleSheet("""
            QLabel {
                color: #d32f2f;
                font-size: 11px;
                font-style: italic;
            }
        """)
        mode_layout.addWidget(self.mode_status)
        mode_layout.addStretch()

        layout.addLayout(mode_layout)

        # Enhanced presets with categories (collapsible)
        preset_label = QLabel("Quick Presets:")
        preset_label.setStyleSheet(Config.Styles.PRESET_LABEL)
        layout.addWidget(preset_label)

        self.preset_group = QButtonGroup()

        # Create collapsible square presets section
        square_content = QWidget()
        square_layout = QGridLayout(square_content)
        square_layout.setSpacing(Config.UI.PRESET_GRID_SPACING)
        square_layout.setContentsMargins(8, 5, 5, 5)  # Reduced indent for better space usage

        # Use consistent 3 columns for all presets
        cols = 3
        for i, (label, width, height, tooltip) in enumerate(Config.FrameExtraction.SQUARE_PRESETS):
            btn = QRadioButton(label)
            btn.setToolTip(tooltip)
            # Use default font size for better readability
            btn.clicked.connect(lambda checked, w=width, h=height: self.presetSelected.emit(w, h))
            self.preset_group.addButton(btn, i)
            square_layout.addWidget(btn, i // cols, i % cols)

        square_section = self._create_collapsible_section("Square Presets", square_content)
        layout.addWidget(square_section)

        # Create collapsible rectangular presets section
        rect_content = QWidget()
        rect_layout = QGridLayout(rect_content)
        rect_layout.setSpacing(Config.UI.PRESET_GRID_SPACING)
        rect_layout.setContentsMargins(8, 5, 5, 5)  # Reduced indent for better space usage

        # Use consistent 3 columns
        rect_cols = 3
        square_count = len(Config.FrameExtraction.SQUARE_PRESETS)
        for i, (label, width, height, tooltip) in enumerate(Config.FrameExtraction.RECTANGULAR_PRESETS):
            btn = QRadioButton(label)
            btn.setToolTip(tooltip)
            # Use default font size for better readability
            btn.clicked.connect(lambda checked, w=width, h=height: self.presetSelected.emit(w, h))
            self.preset_group.addButton(btn, square_count + i)
            rect_layout.addWidget(btn, i // rect_cols, i % rect_cols)

        rect_section = self._create_collapsible_section("Rectangular Presets", rect_content)
        layout.addWidget(rect_section)

        # Default to 192×192 (index 4 in square presets)
        self.preset_group.button(Config.FrameExtraction.DEFAULT_PRESET_INDEX).setChecked(True)

        # Separator removed - use spacing for visual separation

        # Custom size controls
        custom_label = QLabel("Custom Size:")
        custom_label.setStyleSheet(Config.Styles.CUSTOM_LABEL)
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
        self._button_manager.register_button('frame', self.auto_btn)

        layout.addLayout(size_layout)

        # Advanced Settings (consolidated offset and spacing)
        advanced_label = QLabel("Advanced Settings:")
        advanced_label.setStyleSheet(Config.Styles.OFFSET_LABEL)
        layout.addWidget(advanced_label)

        # Create compact 2-row layout for offset and spacing
        advanced_layout = QGridLayout()
        advanced_layout.setSpacing(Config.UI.SIZE_LAYOUT_SPACING)

        # Row 1: Offset controls
        advanced_layout.addWidget(QLabel("Offset:"), 0, 0)
        advanced_layout.addWidget(QLabel("X:"), 0, 1)
        self.offset_x = QSpinBox()
        self.offset_x.setRange(Config.FrameExtraction.DEFAULT_OFFSET, Config.FrameExtraction.MAX_OFFSET)
        self.offset_x.setValue(Config.FrameExtraction.DEFAULT_OFFSET)
        self.offset_x.setSuffix(" px")
        self.offset_x.valueChanged.connect(self.settingsChanged)
        advanced_layout.addWidget(self.offset_x, 0, 2)

        advanced_layout.addWidget(QLabel("Y:"), 0, 3)
        self.offset_y = QSpinBox()
        self.offset_y.setRange(Config.FrameExtraction.DEFAULT_OFFSET, Config.FrameExtraction.MAX_OFFSET)
        self.offset_y.setValue(Config.FrameExtraction.DEFAULT_OFFSET)
        self.offset_y.setSuffix(" px")
        self.offset_y.valueChanged.connect(self.settingsChanged)
        advanced_layout.addWidget(self.offset_y, 0, 4)

        self.auto_margins_btn = QPushButton("Auto")
        self.auto_margins_btn.setMaximumWidth(Config.UI.AUTO_BUTTON_MAX_WIDTH)
        self.auto_margins_btn.setToolTip("Auto-detect margins")
        advanced_layout.addWidget(self.auto_margins_btn, 0, 5)
        self._button_manager.register_button('margins', self.auto_margins_btn)

        # Row 2: Spacing controls
        advanced_layout.addWidget(QLabel("Spacing:"), 1, 0)
        advanced_layout.addWidget(QLabel("X:"), 1, 1)
        self.spacing_x = QSpinBox()
        self.spacing_x.setRange(Config.FrameExtraction.DEFAULT_SPACING, Config.FrameExtraction.MAX_SPACING)
        self.spacing_x.setValue(Config.FrameExtraction.DEFAULT_SPACING)
        self.spacing_x.setSuffix(" px")
        self.spacing_x.setToolTip("Horizontal gap between frames")
        self.spacing_x.valueChanged.connect(self.settingsChanged)
        advanced_layout.addWidget(self.spacing_x, 1, 2)

        advanced_layout.addWidget(QLabel("Y:"), 1, 3)
        self.spacing_y = QSpinBox()
        self.spacing_y.setRange(Config.FrameExtraction.DEFAULT_SPACING, Config.FrameExtraction.MAX_SPACING)
        self.spacing_y.setValue(Config.FrameExtraction.DEFAULT_SPACING)
        self.spacing_y.setSuffix(" px")
        self.spacing_y.setToolTip("Vertical gap between frames")
        self.spacing_y.valueChanged.connect(self.settingsChanged)
        advanced_layout.addWidget(self.spacing_y, 1, 4)

        self.auto_spacing_btn = QPushButton("Auto")
        self.auto_spacing_btn.setMaximumWidth(Config.UI.AUTO_BUTTON_MAX_WIDTH)
        self.auto_spacing_btn.setToolTip("Auto-detect frame spacing")
        advanced_layout.addWidget(self.auto_spacing_btn, 1, 5)
        self._button_manager.register_button('spacing', self.auto_spacing_btn)

        layout.addLayout(advanced_layout)

        # Grid overlay checkbox
        self.grid_checkbox = QCheckBox("Show grid overlay")
        self.grid_checkbox.setStyleSheet(Config.Styles.GRID_CHECKBOX)
        layout.addWidget(self.grid_checkbox)

        # Connect mode change signals
        self.mode_group.buttonClicked.connect(self._on_mode_changed)

        # Set initial state for CCL default mode (disable grid controls)
        self._set_grid_controls_enabled(False)

    def _on_mode_changed(self, button):
        """Handle extraction mode change."""
        if button == self.grid_mode_btn:
            mode = "grid"
            self.mode_status.setText("🔲 Grid mode active")
            self.mode_status.setStyleSheet("""
                QLabel {
                    color: #2e7d32;
                    font-size: 11px;
                    font-style: italic;
                }
            """)
            # Enable grid controls
            self._set_grid_controls_enabled(True)
        else:  # CCL mode
            mode = "ccl"
            self.mode_status.setText("🎯 CCL mode active")
            self.mode_status.setStyleSheet("""
                QLabel {
                    color: #d32f2f;
                    font-size: 11px;
                    font-style: italic;
                }
            """)
            # Disable grid controls since CCL uses exact boundaries
            self._set_grid_controls_enabled(False)

        self.modeChanged.emit(mode)

    def _set_grid_controls_enabled(self, enabled: bool):
        """Enable/disable grid-specific controls."""
        # Disable presets and custom size controls in CCL mode
        for button in self.preset_group.buttons():
            button.setEnabled(enabled)
        self.width_spin.setEnabled(enabled)
        self.height_spin.setEnabled(enabled)
        self.auto_btn.setEnabled(enabled)

        # Disable offset and spacing controls in CCL mode (CCL uses exact bounds)
        self.offset_x.setEnabled(enabled)
        self.offset_y.setEnabled(enabled)
        self.spacing_x.setEnabled(enabled)
        self.spacing_y.setEnabled(enabled)
        self.auto_margins_btn.setEnabled(enabled)
        self.auto_spacing_btn.setEnabled(enabled)

    def set_ccl_available(self, available: bool, sprite_count: int = 0):
        """Enable/disable CCL mode based on availability."""
        self.ccl_mode_btn.setEnabled(available)
        if available:
            if sprite_count > 0:
                self.ccl_mode_btn.setToolTip(f"CCL Extraction: Ready (auto-detection found {sprite_count} sprites)")
            else:
                self.ccl_mode_btn.setToolTip("CCL Extraction: Ready for irregular sprite collections")
        else:
            self.ccl_mode_btn.setToolTip("CCL Extraction: Load a sprite sheet first")

    def get_extraction_mode(self) -> str:
        """Get current extraction mode."""
        return "ccl" if self.ccl_mode_btn.isChecked() else "grid"

    def set_extraction_mode(self, mode: str):
        """Set extraction mode programmatically."""
        if mode == "ccl" and self.ccl_mode_btn.isEnabled():
            self.ccl_mode_btn.setChecked(True)
        else:
            self.grid_mode_btn.setChecked(True)
        self._on_mode_changed(self.ccl_mode_btn if mode == "ccl" else self.grid_mode_btn)

    def _create_collapsible_section(self, title: str, content_widget: QWidget) -> QWidget:
        """Create a collapsible section with expand/collapse button."""
        section_widget = QWidget()
        section_layout = QVBoxLayout(section_widget)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(5)

        # Header with toggle button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Toggle button (arrow)
        toggle_button = QToolButton()
        toggle_button.setArrowType(Qt.ArrowType.DownArrow)
        toggle_button.setAutoRaise(True)
        toggle_button.setFixedSize(16, 16)
        toggle_button.clicked.connect(lambda: self._toggle_section(toggle_button, content_widget))
        header_layout.addWidget(toggle_button)

        # Section title
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #555; font-weight: bold; margin-top: 2px;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()
        section_layout.addLayout(header_layout)

        # Content (initially visible)
        content_widget.setVisible(True)
        section_layout.addWidget(content_widget)

        return section_widget

    def _toggle_section(self, button: QToolButton, content: QWidget):
        """Toggle section visibility and button arrow direction."""
        is_visible = content.isVisible()
        content.setVisible(not is_visible)

        # Update arrow direction
        if is_visible:
            button.setArrowType(Qt.ArrowType.RightArrow)
        else:
            button.setArrowType(Qt.ArrowType.DownArrow)

    def _on_custom_size_changed(self):
        """Handle custom size change."""
        # Uncheck all preset buttons when custom size is used
        for button in self.preset_group.buttons():
            button.setChecked(False)
        self.settingsChanged.emit()

    def get_frame_size(self) -> tuple[int, int]:
        """Get current frame size."""
        return self.width_spin.value(), self.height_spin.value()

    def get_offset(self) -> tuple[int, int]:
        """Get current offset."""
        return self.offset_x.value(), self.offset_y.value()

    def get_spacing(self) -> tuple[int, int]:
        """Get current frame spacing."""
        return self.spacing_x.value(), self.spacing_y.value()

    def set_frame_size(self, width: int, height: int):
        """Set frame size programmatically."""
        self.width_spin.setValue(width)
        self.height_spin.setValue(height)

        # Check corresponding preset if it matches
        # First check square presets
        for i, (_label, w, h, _) in enumerate(Config.FrameExtraction.SQUARE_PRESETS):
            if w == width and h == height:
                self.preset_group.button(i).setChecked(True)
                return

        # Then check rectangular presets
        square_count = len(Config.FrameExtraction.SQUARE_PRESETS)
        for i, (_label, w, h, _) in enumerate(Config.FrameExtraction.RECTANGULAR_PRESETS):
            if w == width and h == height:
                self.preset_group.button(square_count + i).setChecked(True)
                return

        # If no preset matches, uncheck all
        for button in self.preset_group.buttons():
            button.setChecked(False)

    def update_auto_button_confidence(self, button_type: str, confidence: str, message: str = ""):
        """
        Update auto-detect button appearance based on confidence level.

        Args:
            button_type: 'frame', 'margins', or 'spacing'
            confidence: 'high', 'medium', 'low', or 'failed'
            message: Optional detailed message for tooltip
        """
        self._button_manager.update_confidence(button_type, confidence, message)

    def reset_auto_button_style(self, button_type: str):
        """Reset auto-detect button to default appearance."""
        self._button_manager.reset_button(button_type)


# Export for easy importing
__all__ = ['FrameExtractor']
