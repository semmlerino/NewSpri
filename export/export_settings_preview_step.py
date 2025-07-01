"""
Export Settings with Live Preview Step
Combined settings and preview for better user experience.
"""

import math
from typing import Optional, Dict, Any, List, Tuple
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel,
    QPushButton, QFrame, QGraphicsScene, QGraphicsView,
    QGraphicsPixmapItem, QSizePolicy, QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer, QRectF, QSize
from PySide6.QtGui import QPixmap, QPainter, QBrush, QColor, QPen, QFont

from .wizard_widget import WizardStep
from .export_settings_step_simple import (
    SettingsCard, SimpleDirectorySelector, QuickScaleButtons,
    GridLayoutSelector, QComboBox, QLineEdit, QSpinBox, QListWidget,
    QListWidgetItem, QCheckBox
)
from .export_presets import ExportPreset
from config import Config


class LivePreviewWidget(QGraphicsView):
    """Lightweight preview widget with zoom controls."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Checkerboard background for transparency
        self.setBackgroundBrush(self._create_checkerboard())
        
        # Scene
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # Preview items
        self._preview_pixmap = None
        self._info_text = None
        
    def _create_checkerboard(self) -> QBrush:
        """Create checkerboard pattern."""
        pixmap = QPixmap(20, 20)
        pixmap.fill(Qt.white)
        painter = QPainter(pixmap)
        painter.fillRect(0, 0, 10, 10, QColor(220, 220, 220))
        painter.fillRect(10, 10, 10, 10, QColor(220, 220, 220))
        painter.end()
        return QBrush(pixmap)
    
    def wheelEvent(self, event):
        """Handle zoom with mouse wheel."""
        zoom_in = 1.15
        zoom_out = 1 / zoom_in
        
        if event.angleDelta().y() > 0:
            self.scale(zoom_in, zoom_in)
        else:
            self.scale(zoom_out, zoom_out)
    
    def update_preview(self, pixmap: QPixmap, info: str = ""):
        """Update the preview display."""
        self.scene.clear()
        
        if pixmap and not pixmap.isNull():
            self._preview_pixmap = self.scene.addPixmap(pixmap)
            
            # Add info text
            if info:
                text = self.scene.addText(info)
                text.setDefaultTextColor(QColor(100, 100, 100))
                font = QFont()
                font.setPointSize(10)
                text.setFont(font)
                text.setPos(5, pixmap.height() + 10)
            
            # Fit in view
            self.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)
    
    def fit_to_view(self):
        """Fit the preview to the view."""
        if self.scene.items():
            self.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)


class ExportSettingsPreviewStep(WizardStep):
    """
    Combined settings and preview step with live updates.
    """
    
    # Signals
    previewUpdateRequested = Signal()
    
    def __init__(self, frame_count: int = 0, current_frame: int = 0, 
                 sprites: List[QPixmap] = None, parent=None):
        super().__init__(
            title="Configure & Preview Export",
            subtitle="Adjust settings and see live preview",
            parent=parent
        )
        self.frame_count = frame_count
        self.current_frame = current_frame
        self._sprites = sprites or []
        self._current_preset: Optional[ExportPreset] = None
        self._settings_widgets = {}
        
        # Debounce timer for preview updates
        self._preview_timer = QTimer()
        self._preview_timer.setSingleShot(True)
        self._preview_timer.timeout.connect(self._update_preview)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the combined UI."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(16)
        
        # Create splitter for settings and preview
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        
        # Left side: Settings
        settings_widget = self._create_settings_panel()
        splitter.addWidget(settings_widget)
        
        # Right side: Preview
        preview_widget = self._create_preview_panel()
        splitter.addWidget(preview_widget)
        
        # Set initial sizes (40% settings, 60% preview)
        splitter.setSizes([400, 600])
        
        layout.addWidget(splitter, 1)
        
        # Bottom: Export button
        export_button = self._create_export_button()
        layout.addWidget(export_button)
    
    def _create_settings_panel(self) -> QWidget:
        """Create the settings panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        panel.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Settings scroll area content
        self.settings_container = QWidget()
        self.settings_layout = QVBoxLayout(self.settings_container)
        self.settings_layout.setSpacing(12)
        
        # Scroll area for settings
        from PySide6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidget(self.settings_container)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        layout.addWidget(scroll)
        
        return panel
    
    def _create_preview_panel(self) -> QWidget:
        """Create the preview panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        panel.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Preview header
        header_layout = QHBoxLayout()
        
        preview_label = QLabel("🖼️ Live Preview")
        preview_font = QFont()
        preview_font.setPointSize(14)
        preview_font.setBold(True)
        preview_label.setFont(preview_font)
        header_layout.addWidget(preview_label)
        
        header_layout.addStretch()
        
        # Zoom controls
        zoom_fit_btn = QPushButton("Fit")
        zoom_fit_btn.setFixedSize(60, 28)
        zoom_fit_btn.clicked.connect(self._fit_preview)
        header_layout.addWidget(zoom_fit_btn)
        
        zoom_100_btn = QPushButton("100%")
        zoom_100_btn.setFixedSize(60, 28)
        zoom_100_btn.clicked.connect(self._reset_zoom)
        header_layout.addWidget(zoom_100_btn)
        
        layout.addLayout(header_layout)
        
        # Preview info
        self.preview_info_label = QLabel("Adjust settings to see preview")
        self.preview_info_label.setStyleSheet("color: #6c757d; font-size: 12px;")
        layout.addWidget(self.preview_info_label)
        
        # Preview view
        self.preview_view = LivePreviewWidget()
        self.preview_view.setMinimumHeight(400)
        layout.addWidget(self.preview_view, 1)
        
        # Preview stats
        self.preview_stats_label = QLabel()
        self.preview_stats_label.setStyleSheet("color: #495057; font-size: 11px;")
        self.preview_stats_label.setWordWrap(True)
        layout.addWidget(self.preview_stats_label)
        
        return panel
    
    def _create_export_button(self) -> QWidget:
        """Create the export button section."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Export summary
        self.export_summary_label = QLabel()
        self.export_summary_label.setStyleSheet("color: #495057;")
        layout.addWidget(self.export_summary_label)
        
        layout.addStretch()
        
        # Export button
        self.export_button = QPushButton("🚀 Export Now")
        self.export_button.setFixedHeight(44)
        self.export_button.setMinimumWidth(150)
        self.export_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                padding: 0 24px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        layout.addWidget(self.export_button)
        
        return container
    
    def on_entering(self):
        """Called when entering this step."""
        # Get preset from wizard data
        wizard = self.parent()
        while wizard and not hasattr(wizard, 'get_wizard_data'):
            wizard = wizard.parent()
        
        if wizard:
            wizard_data = wizard.get_wizard_data()
            preset = wizard_data.get('step_0', {}).get('preset')
            if preset:
                self._setup_for_preset(preset)
    
    def _setup_for_preset(self, preset: ExportPreset):
        """Set up UI based on selected preset."""
        self._current_preset = preset
        
        # Clear existing settings
        self._clear_settings()
        
        # Build settings based on export type
        if preset.mode == "sheet":
            self._build_sprite_sheet_settings()
        elif preset.mode == "selected":
            self._build_selected_frames_settings()
        else:  # individual
            self._build_individual_frames_settings()
        
        # Initial preview and summary
        self._request_preview_update()
        self._update_export_summary()
    
    def _clear_settings(self):
        """Clear all settings widgets."""
        while self.settings_layout.count():
            item = self.settings_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._settings_widgets.clear()
    
    def _build_individual_frames_settings(self):
        """Build settings for individual frames export."""
        # Output location
        location_card = self._create_location_card()
        self.settings_layout.addWidget(location_card)
        
        # File naming
        naming_card = self._create_naming_card()
        self.settings_layout.addWidget(naming_card)
        
        # Format & Scale
        format_card = self._create_format_card()
        self.settings_layout.addWidget(format_card)
        
        self.settings_layout.addStretch()
    
    def _build_sprite_sheet_settings(self):
        """Build settings for sprite sheet export."""
        # Output
        location_card = self._create_location_card(single_file=True)
        self.settings_layout.addWidget(location_card)
        
        # Layout
        layout_card = self._create_layout_card()
        self.settings_layout.addWidget(layout_card)
        
        # Style
        style_card = self._create_style_card()
        self.settings_layout.addWidget(style_card)
        
        # Format
        format_card = self._create_simple_format_card()
        self.settings_layout.addWidget(format_card)
        
        self.settings_layout.addStretch()
    
    def _build_selected_frames_settings(self):
        """Build settings for selected frames export."""
        # Frame selection
        selection_card = self._create_selection_card()
        self.settings_layout.addWidget(selection_card)
        
        # Output
        location_card = self._create_location_card()
        self.settings_layout.addWidget(location_card)
        
        # Naming
        naming_card = self._create_naming_card()
        self.settings_layout.addWidget(naming_card)
        
        # Format
        format_card = self._create_format_card()
        self.settings_layout.addWidget(format_card)
        
        self.settings_layout.addStretch()
    
    # Settings cards creation methods
    def _create_location_card(self, single_file: bool = False) -> SettingsCard:
        """Create output location card."""
        card = SettingsCard("📁 Output", "")
        
        # Directory
        self.directory_selector = SimpleDirectorySelector()
        self.directory_selector.directoryChanged.connect(self._on_setting_changed)
        self.directory_selector.set_directory(str(Config.File.get_default_export_directory()))
        card.add_row("Save to:", self.directory_selector)
        
        # Filename for single file
        if single_file:
            self.filename_edit = QLineEdit()
            self.filename_edit.setText("spritesheet")
            self.filename_edit.textChanged.connect(self._on_setting_changed)
            card.add_row("Filename:", self.filename_edit)
            self._settings_widgets['single_filename'] = self.filename_edit
        
        self._settings_widgets['directory'] = self.directory_selector
        return card
    
    def _create_naming_card(self) -> SettingsCard:
        """Create file naming card."""
        card = SettingsCard("📝 Naming", "")
        
        # Base name
        self.base_name_edit = QLineEdit()
        self.base_name_edit.setText("frame")
        self.base_name_edit.textChanged.connect(self._on_setting_changed)
        card.add_row("Base name:", self.base_name_edit)
        
        # Pattern
        self.pattern_combo = QComboBox()
        self.pattern_combo.addItems([
            "frame_001, frame_002...",
            "frame_0, frame_1...",
            "frame-1, frame-2..."
        ])
        self.pattern_combo.currentIndexChanged.connect(self._on_setting_changed)
        card.add_row("Pattern:", self.pattern_combo)
        
        self._settings_widgets['base_name'] = self.base_name_edit
        self._settings_widgets['pattern_combo'] = self.pattern_combo
        
        return card
    
    def _create_format_card(self) -> SettingsCard:
        """Create format and scale card."""
        card = SettingsCard("🖼️ Format", "")
        
        # Format
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPG", "BMP"])
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        card.add_row("Format:", self.format_combo)
        
        # Scale
        self.scale_buttons = QuickScaleButtons()
        self.scale_buttons.scaleChanged.connect(self._on_setting_changed)
        card.add_row("Scale:", self.scale_buttons)
        
        # Quality for JPG
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(95)
        self.quality_spin.setSuffix("%")
        self.quality_spin.valueChanged.connect(self._on_setting_changed)
        self.quality_row = card.add_row("Quality:", self.quality_spin)
        self.quality_row.setVisible(False)
        
        self._settings_widgets['format'] = self.format_combo
        self._settings_widgets['scale'] = self.scale_buttons
        self._settings_widgets['quality'] = self.quality_spin
        
        return card
    
    def _create_simple_format_card(self) -> SettingsCard:
        """Create simple format card for sprite sheets."""
        card = SettingsCard("💾 Format", "")
        
        self.sheet_format_combo = QComboBox()
        self.sheet_format_combo.addItems(["PNG", "JPG"])
        self.sheet_format_combo.currentTextChanged.connect(self._on_setting_changed)
        card.add_row("Format:", self.sheet_format_combo)
        
        self._settings_widgets['format'] = self.sheet_format_combo
        
        return card
    
    def _create_layout_card(self) -> SettingsCard:
        """Create sprite sheet layout card."""
        card = SettingsCard("📐 Layout", "")
        
        # Grid layout selector
        self.grid_layout = GridLayoutSelector()
        self.grid_layout.layoutChanged.connect(self._on_layout_changed)
        card.content_layout.addWidget(self.grid_layout)
        
        self._settings_widgets['grid_layout'] = self.grid_layout
        
        return card
    
    def _create_style_card(self) -> SettingsCard:
        """Create sprite sheet style card."""
        card = SettingsCard("🎨 Style", "")
        
        # Spacing
        spacing_widget = QWidget()
        spacing_layout = QHBoxLayout(spacing_widget)
        spacing_layout.setContentsMargins(0, 0, 0, 0)
        
        self.spacing_spin = QSpinBox()
        self.spacing_spin.setRange(0, 32)
        self.spacing_spin.setValue(0)
        self.spacing_spin.setSuffix(" px")
        self.spacing_spin.valueChanged.connect(self._on_setting_changed)
        spacing_layout.addWidget(self.spacing_spin)
        spacing_layout.addWidget(QLabel("between sprites"))
        spacing_layout.addStretch()
        
        card.add_row("Spacing:", spacing_widget)
        
        # Background
        self.bg_combo = QComboBox()
        self.bg_combo.addItems(["Transparent", "White", "Black"])
        self.bg_combo.currentIndexChanged.connect(self._on_setting_changed)
        card.add_row("Background:", self.bg_combo)
        
        self._settings_widgets['spacing'] = self.spacing_spin
        self._settings_widgets['background'] = self.bg_combo
        
        return card
    
    def _create_selection_card(self) -> SettingsCard:
        """Create frame selection card."""
        card = SettingsCard("🎯 Select Frames", "")
        
        # Quick buttons
        quick_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("All")
        select_all_btn.clicked.connect(lambda: self.frame_list.selectAll())
        quick_layout.addWidget(select_all_btn)
        
        clear_btn = QPushButton("None")
        clear_btn.clicked.connect(lambda: self.frame_list.clearSelection())
        quick_layout.addWidget(clear_btn)
        
        quick_layout.addStretch()
        card.content_layout.addLayout(quick_layout)
        
        # Frame list
        self.frame_list = QListWidget()
        self.frame_list.setSelectionMode(QListWidget.MultiSelection)
        self.frame_list.setMaximumHeight(200)
        
        # Populate
        for i in range(self.frame_count):
            item = QListWidgetItem(f"Frame {i + 1}")
            item.setData(Qt.UserRole, i)
            self.frame_list.addItem(item)
            if i == self.current_frame:
                item.setSelected(True)
        
        self.frame_list.itemSelectionChanged.connect(self._on_frame_selection_changed)
        card.content_layout.addWidget(self.frame_list)
        
        # Info
        self.selection_info = QLabel("1 frame selected")
        self.selection_info.setStyleSheet("color: #6c757d; font-size: 11px;")
        card.content_layout.addWidget(self.selection_info)
        
        self._settings_widgets['frame_list'] = self.frame_list
        
        return card
    
    # Event handlers
    def _on_setting_changed(self):
        """Handle any setting change."""
        self._request_preview_update()
        self._validate_settings()
    
    def _on_format_changed(self, format: str):
        """Handle format change."""
        if hasattr(self, 'quality_row') and self.quality_row:
            self.quality_row.setVisible(format == "JPG")
        self._on_setting_changed()
    
    def _on_layout_changed(self, mode: str, cols: int, rows: int):
        """Handle layout change."""
        self._on_setting_changed()
    
    def _on_frame_selection_changed(self):
        """Handle frame selection change."""
        count = len(self.frame_list.selectedItems())
        self.selection_info.setText(f"{count} frame{'s' if count != 1 else ''} selected")
        self._on_setting_changed()
    
    def _request_preview_update(self):
        """Request preview update with debouncing."""
        self._preview_timer.stop()
        self._preview_timer.start(150)  # 150ms debounce
    
    def _fit_preview(self):
        """Fit preview to view."""
        self.preview_view.fit_to_view()
    
    def _reset_zoom(self):
        """Reset preview zoom to 100%."""
        self.preview_view.resetTransform()
    
    def _update_preview(self):
        """Update the preview based on current settings."""
        if not self._current_preset or not self._sprites:
            self.preview_view.update_preview(QPixmap(), "No preview available")
            return
        
        # Generate preview based on export type
        if self._current_preset.mode == "sheet":
            pixmap, info = self._generate_sprite_sheet_preview()
        elif self._current_preset.mode == "selected":
            pixmap, info = self._generate_selected_preview()
        else:
            pixmap, info = self._generate_individual_preview()
        
        # Update preview
        self.preview_view.update_preview(pixmap, info)
        
        # Update info labels
        self.preview_info_label.setText(info)
        self._update_preview_stats()
        self._update_export_summary()
    
    def _generate_sprite_sheet_preview(self) -> Tuple[QPixmap, str]:
        """Generate sprite sheet preview."""
        # Get settings
        data = self.get_data()
        layout_mode = data.get('layout_mode', 'auto')
        spacing = data.get('spacing', 0)
        padding = data.get('padding', 0)
        cols = data.get('columns', 8)
        rows = data.get('rows', 8)
        
        # Calculate grid
        frame_count = len(self._sprites)
        if layout_mode == 'auto':
            cols = math.ceil(math.sqrt(frame_count))
            rows = math.ceil(frame_count / cols)
        elif layout_mode == 'columns':
            rows = math.ceil(frame_count / cols)
        elif layout_mode == 'rows':
            cols = math.ceil(frame_count / rows)
        elif layout_mode == 'square':
            side = math.ceil(math.sqrt(frame_count))
            cols = rows = side
        
        # Get frame size
        if self._sprites:
            fw = self._sprites[0].width()
            fh = self._sprites[0].height()
        else:
            fw = fh = 32
        
        # Calculate sheet size
        sheet_w = cols * fw + (cols - 1) * spacing + 2 * padding
        sheet_h = rows * fh + (rows - 1) * spacing + 2 * padding
        
        # Create pixmap
        pixmap = QPixmap(sheet_w, sheet_h)
        
        # Background
        bg_index = self._settings_widgets.get('background', QComboBox()).currentIndex()
        if bg_index == 0:  # Transparent
            pixmap.fill(Qt.transparent)
        elif bg_index == 1:  # White
            pixmap.fill(Qt.white)
        else:  # Black
            pixmap.fill(Qt.black)
        
        # Draw sprites
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        for i, sprite in enumerate(self._sprites[:frame_count]):
            row = i // cols
            col = i % cols
            x = padding + col * (fw + spacing)
            y = padding + row * (fh + spacing)
            painter.drawPixmap(x, y, sprite)
        
        painter.end()
        
        info = f"Sprite Sheet: {cols}×{rows} grid, {sheet_w}×{sheet_h}px"
        return pixmap, info
    
    def _generate_individual_preview(self) -> Tuple[QPixmap, str]:
        """Generate preview for individual frames."""
        # Show grid of first few frames
        display_count = min(len(self._sprites), 6)
        cols = min(3, display_count)
        rows = (display_count + cols - 1) // cols
        
        # Create composite preview
        if self._sprites:
            fw = min(self._sprites[0].width(), 80)
            fh = min(self._sprites[0].height(), 80)
        else:
            fw = fh = 64
        
        spacing = 10
        width = cols * fw + (cols - 1) * spacing
        height = rows * fh + (rows - 1) * spacing
        
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw frames
        for i in range(display_count):
            row = i // cols
            col = i % cols
            x = col * (fw + spacing)
            y = row * (fh + spacing)
            
            if i < len(self._sprites):
                scaled = self._sprites[i].scaled(fw, fh, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                painter.drawPixmap(x, y, scaled)
                
                # Frame number
                painter.setPen(QColor(100, 100, 100))
                painter.drawText(x, y + fh + 10, f"#{i+1}")
        
        painter.end()
        
        info = f"Individual Frames: {len(self._sprites)} files"
        if len(self._sprites) > display_count:
            info += f" (showing {display_count})"
        
        return pixmap, info
    
    def _generate_selected_preview(self) -> Tuple[QPixmap, str]:
        """Generate preview for selected frames."""
        selected_indices = []
        if 'frame_list' in self._settings_widgets:
            for item in self._settings_widgets['frame_list'].selectedItems():
                selected_indices.append(item.data(Qt.UserRole))
        
        if not selected_indices:
            return QPixmap(), "No frames selected"
        
        # Similar to individual but with selected frames
        display_count = min(len(selected_indices), 6)
        cols = min(3, display_count)
        rows = (display_count + cols - 1) // cols
        
        if self._sprites:
            fw = min(self._sprites[0].width(), 80)
            fh = min(self._sprites[0].height(), 80)
        else:
            fw = fh = 64
        
        spacing = 10
        width = cols * fw + (cols - 1) * spacing
        height = rows * fh + (rows - 1) * spacing
        
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        for i, frame_idx in enumerate(selected_indices[:display_count]):
            row = i // cols
            col = i % cols
            x = col * (fw + spacing)
            y = row * (fh + spacing)
            
            if frame_idx < len(self._sprites):
                scaled = self._sprites[frame_idx].scaled(fw, fh, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                painter.drawPixmap(x, y, scaled)
                
                # Selection highlight
                painter.setPen(QPen(QColor(0, 123, 255), 2))
                painter.drawRect(x - 1, y - 1, scaled.width() + 2, scaled.height() + 2)
        
        painter.end()
        
        info = f"Selected Frames: {len(selected_indices)} of {len(self._sprites)}"
        if len(selected_indices) > display_count:
            info += f" (showing {display_count})"
        
        return pixmap, info
    
    def _update_preview_stats(self):
        """Update preview statistics."""
        stats = []
        data = self.get_data()
        
        # Format info
        format = data.get('format', 'PNG')
        scale = data.get('scale', 1.0)
        stats.append(f"Format: {format} @ {scale}x")
        
        # Size estimation
        if self._sprites:
            if self._current_preset.mode == "sheet":
                # Estimate sheet size
                stats.append("Estimated size: ~1.2 MB")
            else:
                # Estimate total size
                file_count = len(data.get('selected_indices', self._sprites))
                stats.append(f"Files: {file_count}")
                stats.append("Total size: ~2.4 MB")
        
        self.preview_stats_label.setText(" • ".join(stats))
    
    def _update_export_summary(self):
        """Update export summary."""
        data = self.get_data()
        output_dir = data.get('output_dir', '')
        
        if output_dir:
            import os
            dir_name = os.path.basename(output_dir) or os.path.dirname(output_dir)
            self.export_summary_label.setText(f"Export to: {dir_name}/")
        else:
            self.export_summary_label.setText("Select output directory")
    
    def _validate_settings(self):
        """Validate current settings."""
        is_valid = True
        
        # Check directory
        if 'directory' in self._settings_widgets:
            is_valid &= self._settings_widgets['directory'].is_valid()
        
        # Check filenames
        if 'base_name' in self._settings_widgets:
            is_valid &= bool(self._settings_widgets['base_name'].text())
        if 'single_filename' in self._settings_widgets:
            is_valid &= bool(self._settings_widgets['single_filename'].text())
        
        # Check frame selection
        if self._current_preset and self._current_preset.mode == "selected":
            if 'frame_list' in self._settings_widgets:
                is_valid &= len(self._settings_widgets['frame_list'].selectedItems()) > 0
        
        self.export_button.setEnabled(is_valid)
        self.stepValidated.emit(is_valid)
    
    def validate(self) -> bool:
        """Validate the step."""
        return self._current_preset is not None
    
    def get_data(self) -> Dict[str, Any]:
        """Get all settings data."""
        data = {
            'output_dir': '',
            'format': 'PNG',
            'scale': 1.0
        }
        
        # Directory
        if 'directory' in self._settings_widgets:
            data['output_dir'] = self._settings_widgets['directory'].get_directory()
        
        # Filenames
        if 'base_name' in self._settings_widgets:
            data['base_name'] = self._settings_widgets['base_name'].text()
        if 'single_filename' in self._settings_widgets:
            data['single_filename'] = self._settings_widgets['single_filename'].text()
        
        # Format
        if 'format' in self._settings_widgets:
            data['format'] = self._settings_widgets['format'].currentText()
        
        # Scale
        if 'scale' in self._settings_widgets:
            data['scale'] = self._settings_widgets['scale'].get_scale()
        
        # Quality
        if 'quality' in self._settings_widgets and 'format' in self._settings_widgets:
            if self._settings_widgets['format'].currentText() == "JPG":
                data['quality'] = self._settings_widgets['quality'].value()
        
        # Pattern
        if 'pattern_combo' in self._settings_widgets:
            patterns = ["{name}_{index:03d}", "{name}_{index}", "{name}-{frame}"]
            data['pattern'] = patterns[self._settings_widgets['pattern_combo'].currentIndex()]
        
        # Frame selection
        if 'frame_list' in self._settings_widgets:
            selected_indices = []
            for item in self._settings_widgets['frame_list'].selectedItems():
                selected_indices.append(item.data(Qt.UserRole))
            data['selected_indices'] = selected_indices
        
        # Grid layout
        if 'grid_layout' in self._settings_widgets:
            mode, cols, rows = self._settings_widgets['grid_layout'].get_layout()
            data['layout_mode'] = mode
            if mode == 'columns':
                data['columns'] = cols
            elif mode == 'rows':
                data['rows'] = rows
        
        # Style
        if 'spacing' in self._settings_widgets:
            data['spacing'] = self._settings_widgets['spacing'].value()
            data['padding'] = 0
        
        if 'background' in self._settings_widgets:
            bg_index = self._settings_widgets['background'].currentIndex()
            if bg_index == 0:
                data['background_mode'] = 'transparent'
            elif bg_index == 1:
                data['background_mode'] = 'solid'
                data['background_color'] = (255, 255, 255, 255)
            else:
                data['background_mode'] = 'solid'
                data['background_color'] = (0, 0, 0, 255)
        
        return data
    
    def set_sprites(self, sprites: List[QPixmap]):
        """Set sprite frames."""
        self._sprites = sprites
        if self._current_preset:
            self._request_preview_update()