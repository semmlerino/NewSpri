"""
Modern Export Settings with Live Preview
Redesigned for better usability and modern aesthetics.
"""

import logging
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from managers.animation_segment_manager import AnimationSegmentManager
    from managers.settings_manager import SettingsManager

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPixmap, QWheelEvent
from PySide6.QtWidgets import (
    QAbstractButton,
    QButtonGroup,
    QComboBox,
    QFrame,
    QGraphicsScene,
    QGraphicsView,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from config import Config
from utils.styles import StyleManager

from ..core.export_presets import ExportPreset
from ..core.frame_exporter import BackgroundMode, ExportFormat, ExportMode, LayoutMode
from ..dialogs.base.wizard_base import _WizardStep, _WizardWidget
from .export_mode_ui_registry import get_ui_mode_spec
from .export_preview_renderer import ExportPreviewRenderer, ExportPreviewRequest
from .export_settings_data import (
    LAYOUT_MODES,
    NAMING_PATTERNS,
    ExportSettingsDataCollector,
    ExportSettingsSummary,
)

logger = logging.getLogger(__name__)


class _CompactLivePreview(QGraphicsView):
    """Modern preview widget with integrated controls."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Modern frame style
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setStyleSheet(StyleManager.graphics_view_preview())

        # Checkerboard for transparency
        self.setBackgroundBrush(self._create_checkerboard())

        # Scene setup - use _preview_scene to avoid shadowing inherited scene() method
        self._preview_scene = QGraphicsScene()
        self.setScene(self._preview_scene)

        # Preview state
        self._zoom_level = 1.0
        self._pixmap_item = None

    def _create_checkerboard(self) -> QBrush:
        """Create subtle checkerboard pattern."""
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(250, 250, 250))
        painter = QPainter(pixmap)
        painter.fillRect(0, 0, 8, 8, QColor(240, 240, 240))
        painter.fillRect(8, 8, 8, 8, QColor(240, 240, 240))
        painter.end()
        return QBrush(pixmap)

    def wheelEvent(self, event: QWheelEvent):
        """Smooth zoom with mouse wheel."""
        zoom_in = 1.1
        zoom_out = 1 / zoom_in

        if event.angleDelta().y() > 0:
            self._zoom_level *= zoom_in
            self.scale(zoom_in, zoom_in)
        else:
            self._zoom_level *= zoom_out
            self.scale(zoom_out, zoom_out)

        # Limit zoom range
        if self._zoom_level < 0.1:
            self._zoom_level = 0.1
            self.resetTransform()
            self.scale(0.1, 0.1)
        elif self._zoom_level > 10:
            self._zoom_level = 10
            self.resetTransform()
            self.scale(10, 10)

    def update_preview(self, pixmap: QPixmap):
        """Update preview with modern styling."""
        self._preview_scene.clear()

        if pixmap and not pixmap.isNull():
            # Add pixmap
            self._pixmap_item = self._preview_scene.addPixmap(pixmap)

            # Auto-fit on first load
            QTimer.singleShot(50, self.fit_to_view)
        else:
            # Show placeholder
            text = self._preview_scene.addText("No preview available")
            text.setDefaultTextColor(QColor(108, 117, 125))
            font = QFont("Segoe UI", 12)
            text.setFont(font)

    def fit_to_view(self):
        """Fit preview to view with padding."""
        if self._pixmap_item:
            self.fitInView(self._pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
            self._zoom_level = 1.0
            # Add some padding
            self.scale(0.9, 0.9)
            self._zoom_level *= 0.9

    def reset_zoom(self):
        """Reset to 100% zoom."""
        self.resetTransform()
        self._zoom_level = 1.0


@dataclass
class _SettingsPanelBase:
    """Common boilerplate shared by sheet/individual/selected settings panels.

    Subclasses implement ``build()`` to construct the per-mode QWidget. The
    method is declared here so the dialog-side mode registry can return the
    base type and keep dispatch type-clean.
    """

    _parent: "_ModernExportSettings"

    def _create_panel(self) -> tuple[QWidget, QVBoxLayout]:
        """Create the standard widget + vertical layout with shared chrome."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        return widget, layout

    def build(self) -> QWidget:  # pragma: no cover - overridden by subclasses
        raise NotImplementedError("subclass must implement build()")


class _SheetSettingsPanel(_SettingsPanelBase):
    """Helper class to build sheet settings widget for sprite sheet export."""

    def build(self) -> QWidget:
        """Create sprite sheet specific settings widget."""
        widget, layout = self._create_panel()

        # Filename
        filename_label = QLabel("Filename")
        filename_label.setStyleSheet(StyleManager.label_field())
        layout.addWidget(filename_label)

        self._parent.sheet_filename = QLineEdit()
        self._parent.sheet_filename.setText("spritesheet")
        self._parent.sheet_filename.setPlaceholderText("Enter filename (no extension)")
        self._parent.sheet_filename.setStyleSheet(StyleManager.line_edit_standard())
        self._parent.sheet_filename.textChanged.connect(self._parent._on_setting_changed)
        layout.addWidget(self._parent.sheet_filename)

        # Layout tabs
        self._parent.layout_tabs = QTabWidget()
        self._parent.layout_tabs.setStyleSheet(StyleManager.tab_widget())

        # Layout tab
        layout_tab = self._create_layout_tab()
        self._parent.layout_tabs.addTab(layout_tab, "Layout")

        # Style tab
        style_tab = self._create_style_tab()
        self._parent.layout_tabs.addTab(style_tab, "Style")

        layout.addWidget(self._parent.layout_tabs, 1)

        self._parent._settings_widgets["sheet_filename"] = self._parent.sheet_filename

        return widget

    def _create_layout_tab(self) -> QWidget:
        """Create layout configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Grid mode
        mode_group = QButtonGroup()
        mode_layout = QGridLayout()
        mode_layout.setSpacing(8)

        modes = [
            ("Auto", LAYOUT_MODES[0], "Best fit"),
            ("Fixed Columns", LAYOUT_MODES[1], "Set columns"),
            ("Fixed Rows", LAYOUT_MODES[2], "Set rows"),
            ("Square", LAYOUT_MODES[3], "Force square"),
        ]

        for i, (label, value, tooltip) in enumerate(modes):
            radio = QRadioButton(label)
            radio.setToolTip(tooltip)
            if value is LayoutMode.AUTO:
                radio.setChecked(True)
            mode_group.addButton(radio, i)
            mode_layout.addWidget(radio, i // 2, i % 2)

        layout.addLayout(mode_layout)

        # Manual controls (hidden by default)
        self._parent.manual_controls = QWidget()
        manual_layout = QHBoxLayout(self._parent.manual_controls)
        manual_layout.setContentsMargins(0, 0, 0, 0)

        self._parent.cols_spin = QSpinBox()
        self._parent.cols_spin.setRange(1, 50)
        self._parent.cols_spin.setValue(8)
        self._parent.cols_spin.setPrefix("Columns: ")
        self._parent.cols_spin.setEnabled(False)
        manual_layout.addWidget(self._parent.cols_spin)

        self._parent.rows_spin = QSpinBox()
        self._parent.rows_spin.setRange(1, 50)
        self._parent.rows_spin.setValue(8)
        self._parent.rows_spin.setPrefix("Rows: ")
        self._parent.rows_spin.setEnabled(False)
        manual_layout.addWidget(self._parent.rows_spin)

        manual_layout.addStretch()

        layout.addWidget(self._parent.manual_controls)

        # Connect signals
        mode_group.buttonClicked.connect(
            lambda btn: self._parent._on_layout_mode_changed(modes[mode_group.id(btn)][1])
        )
        self._parent.cols_spin.valueChanged.connect(self._parent._on_setting_changed)
        self._parent.rows_spin.valueChanged.connect(self._parent._on_setting_changed)

        layout.addStretch()

        self._parent._settings_widgets["layout_mode"] = mode_group
        self._parent._settings_widgets["cols_spin"] = self._parent.cols_spin
        self._parent._settings_widgets["rows_spin"] = self._parent.rows_spin

        return widget

    def _create_style_tab(self) -> QWidget:
        """Create style configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        # Spacing
        spacing_layout = QHBoxLayout()
        spacing_label = QLabel("Spacing:")
        spacing_layout.addWidget(spacing_label)

        self._parent.spacing_slider = QSlider(Qt.Orientation.Horizontal)
        self._parent.spacing_slider.setRange(0, 32)
        self._parent.spacing_slider.setValue(0)
        self._parent.spacing_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._parent.spacing_slider.setTickInterval(8)
        spacing_layout.addWidget(self._parent.spacing_slider, 1)

        self._parent.spacing_value = QLabel("0 px")
        self._parent.spacing_value.setMinimumWidth(40)
        spacing_layout.addWidget(self._parent.spacing_value)

        layout.addLayout(spacing_layout)

        # Background
        bg_layout = QHBoxLayout()
        bg_label = QLabel("Background:")
        bg_layout.addWidget(bg_label)

        self._parent.bg_combo = QComboBox()
        # Each entry stores its (BackgroundMode, fill_rgba) so consumers don't
        # have to pattern-match on the visible label or combo index.
        self._parent.bg_combo.addItem("Transparent", (BackgroundMode.TRANSPARENT, None))
        self._parent.bg_combo.addItem("White", (BackgroundMode.SOLID, (255, 255, 255, 255)))
        self._parent.bg_combo.addItem("Black", (BackgroundMode.SOLID, (0, 0, 0, 255)))
        bg_layout.addWidget(self._parent.bg_combo, 1)

        layout.addLayout(bg_layout)

        # Connect signals
        self._parent.spacing_slider.valueChanged.connect(
            lambda v: self._parent.spacing_value.setText(f"{v} px")
        )
        self._parent.spacing_slider.valueChanged.connect(self._parent._on_setting_changed)
        self._parent.bg_combo.currentIndexChanged.connect(self._parent._on_setting_changed)

        layout.addStretch()

        self._parent._settings_widgets["spacing"] = self._parent.spacing_slider
        self._parent._settings_widgets["background"] = self._parent.bg_combo

        return widget


class _IndividualSettingsPanel(_SettingsPanelBase):
    """Helper class to build individual frames settings widget."""

    def build(self) -> QWidget:
        """Create individual frames settings widget."""
        widget, layout = self._create_panel()

        # Base name
        name_label = QLabel("Base Name")
        name_label.setStyleSheet(StyleManager.label_field())
        layout.addWidget(name_label)

        self._parent.base_name = QLineEdit()
        self._parent.base_name.setText("frame")
        self._parent.base_name.setPlaceholderText("Base filename")
        self._parent.base_name.setStyleSheet(StyleManager.line_edit_standard())
        self._parent.base_name.textChanged.connect(self._on_base_name_changed)
        layout.addWidget(self._parent.base_name)

        # Naming pattern
        pattern_label = QLabel("Naming Pattern")
        pattern_label.setStyleSheet(StyleManager.label_field())
        layout.addWidget(pattern_label)

        pattern_group = QButtonGroup()
        # Clear any existing pattern radios before adding new ones
        self._parent._pattern_radios.clear()

        for i, pattern in enumerate(NAMING_PATTERNS):
            # Generate initial display text
            display_text = self._parent._generate_pattern_display(pattern, "frame")
            radio = QRadioButton(display_text)
            if i == 0:
                radio.setChecked(True)
            pattern_group.addButton(radio, i)
            radio.setProperty("pattern", pattern)  # Store pattern for later use
            self._parent._pattern_radios.append(radio)
            layout.addWidget(radio)

        pattern_group.buttonClicked.connect(self._parent._on_setting_changed)

        layout.addStretch()

        self._parent._settings_widgets["base_name"] = self._parent.base_name
        self._parent._settings_widgets["pattern_group"] = pattern_group

        return widget

    def _on_base_name_changed(self, text: str):
        """Handle base name change - update pattern displays."""
        self._parent._refresh_pattern_radios(base_name_override=text or "frame")
        self._parent._on_setting_changed()


class _SelectedSettingsPanel(_SettingsPanelBase):
    """Helper class to build selected frames settings widget."""

    def build(self) -> QWidget:
        """Create selected frames settings widget."""
        widget, layout = self._create_panel()

        # Frame selection
        selection_label = QLabel("Select Frames")
        selection_label.setStyleSheet(StyleManager.label_field())
        layout.addWidget(selection_label)

        # Quick select buttons
        quick_layout = QHBoxLayout()

        select_all = QPushButton("Select All")
        select_all.clicked.connect(self._select_all_frames)
        quick_layout.addWidget(select_all)

        select_none = QPushButton("Clear")
        select_none.clicked.connect(self._clear_frame_selection)
        quick_layout.addWidget(select_none)

        quick_layout.addStretch()
        layout.addLayout(quick_layout)

        # Frame list
        self._parent.frame_list = QListWidget()
        self._parent.frame_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self._parent.frame_list.setStyleSheet(StyleManager.list_widget())

        # Populate frames
        for i in range(self._parent.frame_count):
            item = QListWidgetItem(f"Frame {i + 1}")
            item.setData(Qt.ItemDataRole.UserRole, i)
            self._parent.frame_list.addItem(item)
            if i == self._parent.current_frame:
                item.setSelected(True)

        self._parent.frame_list.itemSelectionChanged.connect(self._on_frame_selection_changed)
        layout.addWidget(self._parent.frame_list, 1)

        # Selection info
        self._parent.selection_info = QLabel()
        self._parent.selection_info.setStyleSheet(StyleManager.label_info())
        layout.addWidget(self._parent.selection_info)

        self._update_selection_info()

        # Base name
        name_layout = QHBoxLayout()
        name_label = QLabel("Base name:")
        name_layout.addWidget(name_label)

        self._parent.selected_base_name = QLineEdit("frame")
        self._parent.selected_base_name.textChanged.connect(self._parent._on_setting_changed)
        name_layout.addWidget(self._parent.selected_base_name, 1)

        layout.addLayout(name_layout)

        self._parent._settings_widgets["frame_list"] = self._parent.frame_list
        self._parent._settings_widgets["selected_base_name"] = self._parent.selected_base_name

        return widget

    def _on_frame_selection_changed(self):
        """Handle frame selection change."""
        self._update_selection_info()
        self._parent._on_setting_changed()

    def _update_selection_info(self):
        """Update frame selection info."""
        count = len(self._parent.frame_list.selectedItems())
        self._parent.selection_info.setText(
            f"{count} of {self._parent.frame_count} frames selected"
        )

    def _select_all_frames(self):
        """Select all frames."""
        self._parent.frame_list.selectAll()

    def _clear_frame_selection(self):
        """Clear frame selection."""
        self._parent.frame_list.clearSelection()


class _SettingsValidator:
    """Per-mode settings validation for ModernExportSettings.

    Reads current widget state and reports whether the export button should be
    enabled. Mode-specific checks dispatch on the current preset's mode.
    """

    def __init__(self, parent: "_ModernExportSettings") -> None:
        self._parent = parent

    def validate(self) -> bool:
        """Run validation, update the export button, and emit stepValidated."""
        valid = self._compute_validity()
        self._parent.export_btn.setEnabled(valid)
        self._parent.stepValidated.emit(valid)
        return valid

    def _compute_validity(self) -> bool:
        parent = self._parent
        if not parent.path_edit.text():
            return False
        preset = parent._current_preset
        if preset is None:
            return True
        if preset.mode is ExportMode.SPRITE_SHEET:
            return self._has_text("sheet_filename")
        if preset.mode is ExportMode.INDIVIDUAL_FRAMES:
            return self._has_text("base_name")
        if preset.mode is ExportMode.SELECTED_FRAMES:
            frame_list = self._parent._settings_widgets.get("frame_list")
            has_selection = frame_list is not None and len(frame_list.selectedItems()) > 0
            return has_selection and self._has_text("selected_base_name")
        return True

    def _has_text(self, widget_key: str) -> bool:
        w = self._parent._settings_widgets.get(widget_key)
        return bool(w.text() if w is not None else "")


class _PreviewOrchestrator:
    """Owns preview request wiring and the debounce timer for ModernExportSettings.

    ``schedule_update`` (re)starts the debounce; ``update_now`` runs the
    renderer immediately and pushes the resulting pixmap into the preview
    widget.
    """

    DEBOUNCE_MS = 100

    def __init__(self, parent: "_ModernExportSettings") -> None:
        self._parent = parent
        self._renderer = ExportPreviewRenderer()
        # Parent the timer to the widget so Qt cleans it up alongside the
        # widget tree, preventing the timer from outliving the C++ preview view
        # if Python GC delays orchestrator collection.
        self._timer = QTimer(parent)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.update_now)

    @property
    def renderer(self) -> ExportPreviewRenderer:
        """Direct access to the underlying renderer (used by tests / shim)."""
        return self._renderer

    @property
    def timer(self) -> QTimer:
        """Public handle on the debounce timer (used by tests / shim)."""
        return self._timer

    def schedule_update(self) -> None:
        """Restart the debounce timer; the actual update runs ``DEBOUNCE_MS`` later."""
        self._timer.stop()
        self._timer.start(self.DEBOUNCE_MS)

    def update_now(self) -> None:
        """Generate and display the preview synchronously."""
        parent = self._parent
        if not parent._current_preset or not parent._sprites:
            parent.preview_view.update_preview(QPixmap())
            return

        result = self._renderer.render(self._build_request())
        if result.info_text:
            parent._update_preview_info(result.info_text)
        parent.preview_view.update_preview(result.pixmap)

    def _build_request(self) -> ExportPreviewRequest:
        """Snapshot the current widget state for the preview renderer."""
        parent = self._parent
        assert parent._current_preset is not None

        background_mode = BackgroundMode.TRANSPARENT
        background_color: tuple[int, int, int, int] | None = None
        bg_widget = parent._settings_widgets.get("background")
        if bg_widget is not None:
            bg_data = bg_widget.currentData()
            if bg_data is not None:
                background_mode, background_color = bg_data

        selected_indices: list[int] = []
        frame_list = parent._settings_widgets.get("frame_list")
        if frame_list is not None:
            selected_indices.extend(
                item.data(Qt.ItemDataRole.UserRole) for item in frame_list.selectedItems()
            )

        segments = (
            parent._segment_manager.get_all_segments()
            if parent._segment_manager is not None
            else []
        )

        cols_widget = parent._settings_widgets.get("cols_spin")
        rows_widget = parent._settings_widgets.get("rows_spin")
        spacing_widget = parent._settings_widgets.get("spacing")

        return ExportPreviewRequest(
            mode=parent._current_preset.mode,
            sprites=tuple(parent._sprites),
            layout_mode=parent._data_collector.layout_mode(),
            columns=cols_widget.value() if cols_widget is not None else 8,
            rows=rows_widget.value() if rows_widget is not None else 8,
            spacing=spacing_widget.value() if spacing_widget is not None else 0,
            background_mode=background_mode,
            background_color=background_color,
            selected_indices=tuple(selected_indices),
            segments=tuple(segments),
            segments_available=parent._segment_manager is not None,
        )


class _ModernExportSettings(_WizardStep):
    """
    Modern, compact export settings with live preview.
    """

    def __init__(
        self,
        frame_count: int = 0,
        current_frame: int = 0,
        sprites: list[QPixmap] | None = None,
        segment_manager: "AnimationSegmentManager | None" = None,
        parent: QWidget | None = None,
        settings_manager: "SettingsManager | None" = None,
    ):
        super().__init__(title="Export Settings", subtitle="Configure your export", parent=parent)
        self.frame_count = frame_count
        self.current_frame = current_frame
        self._sprites = sprites or []
        self._segment_manager = segment_manager
        # Constructor-injected settings manager (singleton fallback for tests
        # that build the wizard standalone without going through SpriteViewer).
        if settings_manager is None:
            from managers.settings_manager import get_settings_manager

            settings_manager = get_settings_manager()
        self._settings_manager = settings_manager
        self._current_preset: ExportPreset | None = None
        self._settings_widgets: dict[str, Any] = {}
        self._pattern_radios: list[QRadioButton] = []  # Track pattern radio buttons for updates

        # Validation + preview collaborators (own the per-mode logic that used
        # to be inlined into _validate_settings / _update_preview / _on_setting_changed).
        self._validator = _SettingsValidator(self)
        self._preview = _PreviewOrchestrator(self)
        self._data_collector = ExportSettingsDataCollector(self)
        self._summary_builder = ExportSettingsSummary(self)
        # Backwards-compat aliases for code/tests that reach for the underlying
        # preview renderer or the preview-debounce timer.
        self._preview_generator = self._preview.renderer
        self._preview_renderer = self._preview.renderer
        self._preview_timer = self._preview.timer

        # Declare dynamic widget attributes (set by helper builders during _setup_for_preset)
        # These are typed without None since they're always set before use
        self.sheet_filename: QLineEdit
        self.layout_tabs: QTabWidget
        self.manual_controls: QWidget
        self.cols_spin: QSpinBox
        self.rows_spin: QSpinBox
        self.spacing_slider: QSlider
        self.spacing_value: QLabel
        self.bg_combo: QComboBox
        self.base_name: QLineEdit
        self.frame_list: QListWidget
        self.selection_info: QLabel
        self.selected_base_name: QLineEdit

        self._setup_ui()

    def _setup_ui(self):
        """Create modern, compact UI."""
        # Remove default margins for full width
        self.setContentsMargins(0, 0, 0, 0)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Content splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setHandleWidth(1)
        self.splitter.setStyleSheet(StyleManager.splitter())

        # Left: Settings panel
        settings_panel = self._create_settings_panel()
        self.splitter.addWidget(settings_panel)

        # Right: Preview panel
        preview_panel = self._create_preview_panel()
        self.splitter.addWidget(preview_panel)

        # Set proportions (40% settings, 60% preview)
        self.splitter.setSizes([350, 525])

        main_layout.addWidget(self.splitter, 1)

        # Bottom bar
        bottom_bar = self._create_bottom_bar()
        main_layout.addWidget(bottom_bar)

    def _create_settings_panel(self) -> QWidget:
        """Create compact settings panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.NoFrame)
        panel.setStyleSheet(StyleManager.settings_panel())

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Essential settings (always visible)
        essential_widget = self._create_essential_settings()
        layout.addWidget(essential_widget)

        # Separator
        separator = QFrame()
        separator.setFrameStyle(QFrame.Shape.HLine)
        separator.setStyleSheet(StyleManager.separator_line())
        separator.setFixedHeight(1)
        layout.addWidget(separator)

        # Mode-specific settings (dynamic)
        self.mode_stack = QStackedWidget()
        self.mode_stack.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.mode_stack, 1)

        return panel

    def _create_essential_settings(self) -> QWidget:
        """Create always-visible essential settings."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Output location
        output_label = QLabel("Output Location")
        output_label.setStyleSheet(StyleManager.label_field())
        layout.addWidget(output_label)

        output_layout = QHBoxLayout()
        output_layout.setSpacing(8)

        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setPlaceholderText("Select output folder...")
        self.path_edit.setStyleSheet(StyleManager.line_edit_readonly())

        # Load last used export directory from settings
        last_export_dir = self._settings_manager.get_value("export/last_directory")

        if last_export_dir and os.path.exists(last_export_dir):
            self.path_edit.setText(last_export_dir)
            self.path_edit.setToolTip(last_export_dir)
        else:
            # Use default export directory
            default_dir = str(Config.File.get_default_export_directory())
            self.path_edit.setText(default_dir)
            self.path_edit.setToolTip(default_dir)

        output_layout.addWidget(self.path_edit, 1)

        self.browse_btn = QPushButton("Browse")
        self.browse_btn.setFixedSize(70, 32)
        self.browse_btn.setStyleSheet(StyleManager.browse_button())
        self.browse_btn.clicked.connect(self._browse_output)
        output_layout.addWidget(self.browse_btn)

        layout.addLayout(output_layout)

        # Format selection
        format_layout = QHBoxLayout()
        format_layout.setSpacing(12)

        format_label = QLabel("Format:")
        format_label.setStyleSheet(StyleManager.label_secondary())
        format_layout.addWidget(format_label)

        self.format_combo = QComboBox()
        self.format_combo.addItems([f.value for f in ExportFormat])
        self.format_combo.setMinimumWidth(100)
        self.format_combo.setStyleSheet(StyleManager.combo_standard())
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        format_layout.addWidget(self.format_combo)

        # Transparency warning for JPG format
        self._transparency_warning = QLabel("⚠ JPG does not support transparency")
        self._transparency_warning.setStyleSheet(StyleManager.warning_label())
        self._transparency_warning.hide()  # Hidden by default
        format_layout.addWidget(self._transparency_warning)

        format_layout.addStretch()

        # Scale selection (inline buttons)
        scale_label = QLabel("Scale:")
        scale_label.setStyleSheet(StyleManager.label_secondary())
        format_layout.addWidget(scale_label)

        self.scale_group = QButtonGroup()
        for scale in [1, 2, 4]:
            btn = QPushButton(f"{scale}x")
            btn.setCheckable(True)
            btn.setFixedSize(40, 28)
            btn.setStyleSheet(StyleManager.scale_button_toggle())
            if scale == 1:
                btn.setChecked(True)
            self.scale_group.addButton(btn, scale)
            format_layout.addWidget(btn)

        self.scale_group.buttonClicked.connect(self._on_scale_changed)

        layout.addLayout(format_layout)

        self._settings_widgets["output_path"] = self.path_edit
        self._settings_widgets["format"] = self.format_combo
        self._settings_widgets["scale_group"] = self.scale_group

        return widget

    def _create_preview_panel(self) -> QWidget:
        """Create modern preview panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.NoFrame)
        panel.setStyleSheet(StyleManager.preview_panel())

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header with controls
        header_layout = QHBoxLayout()

        preview_label = QLabel("Preview")
        preview_label.setStyleSheet(StyleManager.preview_header())
        header_layout.addWidget(preview_label)

        header_layout.addStretch()

        # Zoom controls
        zoom_controls = self._create_zoom_controls()
        header_layout.addLayout(zoom_controls)

        layout.addLayout(header_layout)

        # Preview view
        self.preview_view = _CompactLivePreview()
        self.preview_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.preview_view, 1)

        # Info overlay (floating)
        self.info_label = QLabel()
        self.info_label.setParent(self.preview_view)
        self.info_label.setStyleSheet(StyleManager.info_overlay())
        self.info_label.hide()

        return panel

    def _create_zoom_controls(self) -> QHBoxLayout:
        """Create compact zoom controls."""
        layout = QHBoxLayout()
        layout.setSpacing(4)

        # Fit button
        fit_btn = QToolButton()
        fit_btn.setText("Fit")
        fit_btn.setStyleSheet(StyleManager.tool_button())
        fit_btn.clicked.connect(lambda: self.preview_view.fit_to_view())
        layout.addWidget(fit_btn)

        # 100% button
        reset_btn = QToolButton()
        reset_btn.setText("100%")
        reset_btn.setStyleSheet(fit_btn.styleSheet())
        reset_btn.clicked.connect(lambda: self.preview_view.reset_zoom())
        layout.addWidget(reset_btn)

        return layout

    def _create_bottom_bar(self) -> QWidget:
        """Create bottom action bar."""
        bar = QFrame()
        bar.setFrameStyle(QFrame.Shape.NoFrame)
        bar.setFixedHeight(70)
        bar.setStyleSheet(StyleManager.bottom_bar())

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 15, 20, 15)

        # Export summary
        self.summary_label = QLabel()
        self.summary_label.setStyleSheet(StyleManager.label_muted())
        layout.addWidget(self.summary_label)

        layout.addStretch()

        # Export button
        self.export_btn = QPushButton("Export Now")
        self.export_btn.setFixedHeight(40)
        self.export_btn.setMinimumWidth(120)
        self.export_btn.setStyleSheet(StyleManager.export_button())
        layout.addWidget(self.export_btn)

        return bar

    def _setup_for_preset(self, preset: ExportPreset):
        """Configure UI for selected preset."""
        logger.debug("_setup_for_preset called with: %s (mode: %s)", preset.name, preset.mode)
        self._current_preset = preset

        # Clear mode stack
        while self.mode_stack.count():
            widget = self.mode_stack.widget(0)
            if widget is not None:
                self.mode_stack.removeWidget(widget)

        # Create the appropriate settings panel via the registry
        spec = get_ui_mode_spec(preset.mode)
        logger.debug("Creating panel via registry for mode: %s", preset.mode)
        settings = spec.build_panel(self)

        self.mode_stack.addWidget(settings)

        # Update UI
        logger.debug("Updating preview and summary after preset setup")
        self._update_preview()
        self._update_summary()

    # Event handlers
    def _browse_output(self):
        """Browse for output directory."""
        from PySide6.QtWidgets import QFileDialog

        current = self.path_edit.text() or str(Config.File.get_default_export_directory())

        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory", current)

        if directory:
            self.path_edit.setText(directory)
            self.path_edit.setToolTip(directory)

            # Save last used directory to settings
            self._settings_manager.set_value("export/last_directory", directory)

            self._on_setting_changed()

    def _on_format_changed(self, format: str):
        """Handle format change."""
        self._refresh_pattern_radios()
        self._update_transparency_warning(format)
        self._on_setting_changed()

    def _refresh_pattern_radios(self, *, base_name_override: str | None = None) -> None:
        """Re-render the pattern radio labels with the current base name."""
        if not self._pattern_radios or not hasattr(self, "base_name"):
            return

        if base_name_override is not None:
            base_name = base_name_override
        else:
            base_name = self.base_name.text() or "frame"

        try:
            for radio in self._pattern_radios:
                pattern = radio.property("pattern")
                if pattern:
                    radio.setText(self._generate_pattern_display(pattern, base_name))
        except Exception as e:
            logger.warning("Error updating pattern displays: %s", e, exc_info=True)

    def _update_transparency_warning(self, format: str):
        """Show warning when exporting transparent sprites to JPG."""
        try:
            export_format = ExportFormat.from_string(format)
        except ValueError:
            export_format = None
        show_warning = export_format is ExportFormat.JPG and any(
            sprite and not sprite.isNull() and sprite.hasAlphaChannel() for sprite in self._sprites
        )
        self._transparency_warning.setVisible(show_warning)

    def _on_scale_changed(self, button: QAbstractButton):
        """Handle scale change."""
        self._on_setting_changed()

    def _on_layout_mode_changed(self, mode: LayoutMode):
        """Handle layout mode change."""
        self.cols_spin.setEnabled(mode is LayoutMode.COLUMNS)
        self.rows_spin.setEnabled(mode is LayoutMode.ROWS)
        self._on_setting_changed()

    def _on_setting_changed(self):
        """Handle any setting change — schedule preview, validate, refresh summary."""
        self._preview.schedule_update()
        self._validator.validate()
        self._update_summary()

    def _validate_settings(self):
        """Validate current settings (delegated to _SettingsValidator)."""
        self._validator.validate()

    def _update_preview(self):
        """Update preview based on settings (delegated to _PreviewOrchestrator)."""
        self._preview.update_now()

    def _update_preview_info(self, text: str):
        """Update preview info overlay."""
        self.info_label.setText(text)
        self.info_label.adjustSize()
        self.info_label.move(10, 10)
        self.info_label.show()

        # Auto-hide after 3 seconds
        QTimer.singleShot(3000, self.info_label.hide)

    def _update_summary(self):
        """Update export summary."""
        self.summary_label.setText(self._summary_builder.text(self._current_preset))

    def on_entering(self):
        """Called when entering this step."""
        logger.debug("ModernExportSettings.on_entering called")

        # Get preset from wizard
        wizard = self.parent()
        while wizard and not hasattr(wizard, "get_wizard_data"):
            wizard = wizard.parent()

        if wizard:
            wizard_data = cast("_WizardWidget", wizard).get_wizard_data()
            logger.debug("Wizard data keys: %s", list(wizard_data.keys()))

            step_0_data = wizard_data.get("step_0", {})
            logger.debug("Step 0 data keys: %s", list(step_0_data.keys()))

            preset = step_0_data.get("preset")
            logger.debug("Retrieved preset: %s", preset.name if preset else "None")

            if preset:
                self._setup_for_preset(preset)
            else:
                logger.debug("No preset found in wizard data")
        else:
            logger.debug("No wizard found in parent hierarchy")

    def validate(self) -> bool:
        """Validate the step."""
        return self.export_btn.isEnabled()

    def get_data(self) -> dict[str, Any]:
        """Get all settings data."""
        logger.debug("ModernExportSettings.get_data() called")
        logger.debug(
            "Current preset: %s", self._current_preset.name if self._current_preset else "None"
        )
        logger.debug(
            "Current preset mode: %s", self._current_preset.mode if self._current_preset else "None"
        )

        data = self._data_collector.base_data()

        logger.debug(
            "Base data: output_dir='%s', format='%s', scale=%s",
            data["output_dir"],
            data["format"],
            data["scale"],
        )

        if self._current_preset:
            spec = get_ui_mode_spec(self._current_preset.mode)
            data.update(spec.collect_data(self))

        logger.debug("Final get_data() result: %s", data)
        logger.debug("Data keys: %s", list(data.keys()))
        return data

    def _generate_pattern_display(self, pattern: str, base_name: str) -> str:
        """Generate display text for a pattern with the given base name."""
        format_ext = (
            self.format_combo.currentText().lower() if hasattr(self, "format_combo") else "png"
        )
        return f"{pattern.format(name=base_name, index=1)}.{format_ext}"
