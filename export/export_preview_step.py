"""
Export Preview Step
Final step of the export wizard - visual preview and confirmation.
Part of Export Dialog Usability Improvements.
"""

from typing import Optional, Dict, Any, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGroupBox, QSizePolicy, QScrollArea, QGridLayout,
    QGraphicsScene, QGraphicsView, QGraphicsPixmapItem,
    QMessageBox
)
from PySide6.QtCore import Qt, Signal, QTimer, QSize, QRectF
from PySide6.QtGui import QFont, QPixmap, QPainter, QBrush, QColor, QPen

from .wizard_widget import WizardStep
from .export_presets import ExportPreset
from .frame_exporter import SpriteSheetLayout
from config import Config
import os


class SpriteSheetPreviewView(QGraphicsView):
    """Custom graphics view for sprite sheet preview."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Set background pattern
        self.setBackgroundBrush(self._create_checkerboard_brush())
        
        # Create scene
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        self._zoom_level = 1.0
    
    def _create_checkerboard_brush(self) -> QBrush:
        """Create a checkerboard pattern for transparent background."""
        pixmap = QPixmap(20, 20)
        pixmap.fill(Qt.white)
        painter = QPainter(pixmap)
        painter.fillRect(0, 0, 10, 10, QColor(220, 220, 220))
        painter.fillRect(10, 10, 10, 10, QColor(220, 220, 220))
        painter.end()
        return QBrush(pixmap)
    
    def wheelEvent(self, event):
        """Handle mouse wheel for zooming."""
        # Get the zoom factor
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        
        # Calculate zoom
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
        
        # Limit zoom levels
        new_zoom = self._zoom_level * zoom_factor
        if 0.1 <= new_zoom <= 5.0:
            self._zoom_level = new_zoom
            self.scale(zoom_factor, zoom_factor)
    
    def fit_preview_in_view(self):
        """Fit the preview in the view."""
        self.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)
        self._zoom_level = 1.0


class ExportPreviewStep(WizardStep):
    """
    Final step of export wizard - preview and confirmation.
    Shows visual preview of what will be exported.
    """
    
    def __init__(self, sprites: List[QPixmap] = None, parent=None):
        super().__init__(
            title="Preview & Export",
            subtitle="Review your export settings and preview the output",
            parent=parent
        )
        self._sprites = sprites or []
        self._current_preset: Optional[ExportPreset] = None
        self._export_settings: Dict[str, Any] = {}
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the preview UI."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)
        
        # Visual preview section
        preview_group = self._create_visual_preview_section()
        layout.addWidget(preview_group, 2)
        
        # Export summary section
        summary_group = self._create_summary_section()
        layout.addWidget(summary_group, 1)
        
        # Tips section
        tips_widget = self._create_tips_section()
        layout.addWidget(tips_widget)
    
    def _create_visual_preview_section(self) -> QGroupBox:
        """Create the visual preview section."""
        group = QGroupBox("🖼️ Visual Preview")
        group.setStyleSheet(self._get_group_style())
        layout = QVBoxLayout(group)
        layout.setSpacing(8)
        
        # Preview controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)
        
        # Zoom controls
        zoom_label = QLabel("Zoom:")
        controls_layout.addWidget(zoom_label)
        
        zoom_fit_btn = QPushButton("Fit to View")
        zoom_fit_btn.setFixedHeight(26)
        zoom_fit_btn.setStyleSheet(self._get_control_button_style())
        zoom_fit_btn.clicked.connect(self._fit_preview)
        controls_layout.addWidget(zoom_fit_btn)
        
        zoom_100_btn = QPushButton("100%")
        zoom_100_btn.setFixedHeight(26)
        zoom_100_btn.setStyleSheet(self._get_control_button_style())
        zoom_100_btn.clicked.connect(self._zoom_100)
        controls_layout.addWidget(zoom_100_btn)
        
        controls_layout.addStretch()
        
        # Preview type label
        self.preview_type_label = QLabel("Generating preview...")
        self.preview_type_label.setStyleSheet("color: #6c757d; font-size: 12px;")
        controls_layout.addWidget(self.preview_type_label)
        
        layout.addLayout(controls_layout)
        
        # Preview area
        self.preview_view = SpriteSheetPreviewView()
        self.preview_view.setMinimumHeight(300)
        self.preview_view.setFrameStyle(QFrame.Box)
        self.preview_view.setStyleSheet("""
            QGraphicsView {
                border: 2px solid #dee2e6;
                border-radius: 8px;
                background-color: #f8f9fa;
            }
        """)
        layout.addWidget(self.preview_view)
        
        return group
    
    def _create_summary_section(self) -> QGroupBox:
        """Create the export summary section."""
        group = QGroupBox("📊 Export Summary")
        group.setStyleSheet(self._get_group_style())
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        
        # Summary grid
        summary_widget = QWidget()
        summary_layout = QGridLayout(summary_widget)
        summary_layout.setSpacing(8)
        summary_layout.setColumnStretch(1, 1)
        
        # Summary labels (will be populated in on_entering)
        self.summary_labels = {
            'type': QLabel(),
            'output': QLabel(),
            'format': QLabel(),
            'dimensions': QLabel(),
            'file_size': QLabel(),
            'extras': QLabel()
        }
        
        # Add labels to grid
        row = 0
        for key, label in self.summary_labels.items():
            label.setWordWrap(True)
            label.setStyleSheet("color: #495057; font-size: 12px;")
            summary_layout.addWidget(label, row, 0, 1, 2)
            row += 1
        
        layout.addWidget(summary_widget)
        
        # Export button (prominent)
        self.export_now_button = QPushButton("🚀 Export Now!")
        self.export_now_button.setFixedHeight(44)
        self.export_now_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                padding: 10px 24px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
        """)
        layout.addWidget(self.export_now_button)
        
        return group
    
    def _create_tips_section(self) -> QWidget:
        """Create helpful tips section."""
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setSpacing(4)
        
        # Tips icon and title
        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)
        
        tips_icon = QLabel("💡")
        tips_icon.setFont(QFont("", 16))
        title_layout.addWidget(tips_icon)
        
        tips_title = QLabel("Tips")
        tips_title.setStyleSheet("font-weight: bold; color: #856404;")
        title_layout.addWidget(tips_title)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # Dynamic tips based on export type
        self.tips_label = QLabel()
        self.tips_label.setWordWrap(True)
        self.tips_label.setStyleSheet("color: #856404; font-size: 11px;")
        layout.addWidget(self.tips_label)
        
        return container
    
    def on_entering(self):
        """Called when entering this step - generate preview."""
        # Get data from previous steps
        # Get the wizard widget, not just parent
        wizard = self.parent()
        while wizard and not hasattr(wizard, 'get_wizard_data'):
            wizard = wizard.parent()
        
        if not wizard:
            return
        
        wizard_data = wizard.get_wizard_data()
        
        # Get preset from step 0
        step0_data = wizard_data.get('step_0', {})
        self._current_preset = step0_data.get('preset')
        
        # Get settings from step 1
        step1_data = wizard_data.get('step_1', {})
        self._export_settings = step1_data
        
        # Generate preview based on export type
        if self._current_preset:
            self._generate_preview()
            self._update_summary()
            self._update_tips()
    
    def _generate_preview(self):
        """Generate visual preview based on export type."""
        if not self._current_preset or not self._sprites:
            self.preview_type_label.setText("No preview available")
            return
        
        # Clear previous preview
        self.preview_view.scene.clear()
        
        if self._current_preset.mode == "sheet":
            self._generate_sprite_sheet_preview()
        elif self._current_preset.mode == "individual":
            self._generate_individual_frames_preview()
        elif self._current_preset.mode == "selected":
            self._generate_selected_frames_preview()
        else:
            self.preview_type_label.setText("Preview not available for this export type")
        
        # Fit preview in view
        QTimer.singleShot(100, self.preview_view.fit_preview_in_view)
    
    def _generate_sprite_sheet_preview(self):
        """Generate sprite sheet preview."""
        self.preview_type_label.setText("Sprite Sheet Layout")
        
        # Get layout settings
        layout_mode = self._export_settings.get('layout_mode', 'auto')
        spacing = self._export_settings.get('spacing', 0)
        padding = self._export_settings.get('padding', 0)
        columns = self._export_settings.get('columns', 8)
        rows = self._export_settings.get('rows', 8)
        
        # Calculate grid dimensions
        frame_count = len(self._sprites)
        if layout_mode == 'auto':
            # Auto-calculate optimal grid
            import math
            cols = math.ceil(math.sqrt(frame_count))
            rows = math.ceil(frame_count / cols)
        elif layout_mode == 'columns':
            cols = columns
            rows = math.ceil(frame_count / cols)
        elif layout_mode == 'rows':
            rows = rows
            cols = math.ceil(frame_count / rows)
        elif layout_mode == 'square':
            import math
            side = math.ceil(math.sqrt(frame_count))
            cols = rows = side
        else:  # custom
            cols = columns
            rows = rows
        
        # Get frame dimensions (assume uniform size)
        if self._sprites:
            frame_width = self._sprites[0].width()
            frame_height = self._sprites[0].height()
        else:
            frame_width = frame_height = 32
        
        # Calculate sheet dimensions
        sheet_width = padding * 2 + cols * frame_width + (cols - 1) * spacing
        sheet_height = padding * 2 + rows * frame_height + (rows - 1) * spacing
        
        # Create sheet pixmap
        sheet_pixmap = QPixmap(sheet_width, sheet_height)
        
        # Fill background
        bg_mode = self._export_settings.get('background_mode', 'transparent')
        if bg_mode == 'transparent':
            sheet_pixmap.fill(Qt.transparent)
        elif bg_mode == 'solid':
            bg_color_tuple = self._export_settings.get('background_color', (255, 255, 255, 255))
            bg_color = QColor(*bg_color_tuple[:3])
            sheet_pixmap.fill(bg_color)
        else:  # checkerboard
            sheet_pixmap.fill(Qt.white)
            painter = QPainter(sheet_pixmap)
            # Draw checkerboard pattern
            check_size = 10
            for y in range(0, sheet_height, check_size * 2):
                for x in range(0, sheet_width, check_size * 2):
                    painter.fillRect(x, y, check_size, check_size, QColor(220, 220, 220))
                    painter.fillRect(x + check_size, y + check_size, check_size, check_size, QColor(220, 220, 220))
            painter.end()
        
        # Draw sprites on sheet
        painter = QPainter(sheet_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        frame_index = 0
        for row in range(rows):
            for col in range(cols):
                if frame_index >= frame_count:
                    break
                
                x = padding + col * (frame_width + spacing)
                y = padding + row * (frame_height + spacing)
                
                if frame_index < len(self._sprites):
                    painter.drawPixmap(x, y, self._sprites[frame_index])
                else:
                    # Draw placeholder
                    painter.fillRect(x, y, frame_width, frame_height, QColor(200, 200, 200, 100))
                
                frame_index += 1
        
        # Draw grid lines (for preview only)
        painter.setPen(QPen(QColor(100, 100, 100, 50), 1, Qt.DashLine))
        for row in range(rows + 1):
            y = padding + row * (frame_height + spacing) - spacing / 2
            painter.drawLine(0, y, sheet_width, y)
        for col in range(cols + 1):
            x = padding + col * (frame_width + spacing) - spacing / 2
            painter.drawLine(x, 0, x, sheet_height)
        
        painter.end()
        
        # Add to scene
        pixmap_item = self.preview_view.scene.addPixmap(sheet_pixmap)
        
        # Update info
        self.preview_type_label.setText(f"Sprite Sheet: {cols}×{rows} grid, {sheet_width}×{sheet_height}px")
    
    def _generate_individual_frames_preview(self):
        """Generate preview for individual frames export."""
        self.preview_type_label.setText("Individual Frame Files")
        
        # Show a grid of frame previews with filenames
        frame_count = len(self._sprites)
        display_count = min(frame_count, 12)  # Show up to 12 frames
        
        # Calculate grid
        import math
        cols = min(4, display_count)
        rows = math.ceil(display_count / cols)
        
        # Frame dimensions
        if self._sprites:
            frame_width = min(self._sprites[0].width(), 100)
            frame_height = min(self._sprites[0].height(), 100)
        else:
            frame_width = frame_height = 64
        
        spacing = 20
        margin = 20
        
        # Get naming pattern
        base_name = self._export_settings.get('base_name', 'frame')
        pattern = self._export_settings.get('pattern', '{name}_{index:03d}')
        format_ext = self._export_settings.get('format', 'PNG').lower()
        
        # Create frames
        for i in range(display_count):
            row = i // cols
            col = i % cols
            
            x = margin + col * (frame_width + spacing + 60)  # Extra space for filename
            y = margin + row * (frame_height + spacing + 20)  # Extra space for label
            
            # Frame container
            container = QGraphicsPixmapItem()
            
            # Frame preview (scaled if needed)
            if i < len(self._sprites):
                scaled_pixmap = self._sprites[i].scaled(
                    frame_width, frame_height, 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                frame_item = self.preview_view.scene.addPixmap(scaled_pixmap)
                frame_item.setPos(x, y)
                
                # Frame border
                rect_item = self.preview_view.scene.addRect(
                    x - 1, y - 1, 
                    scaled_pixmap.width() + 2, 
                    scaled_pixmap.height() + 2,
                    QPen(QColor(200, 200, 200), 1)
                )
            
            # Filename label
            try:
                filename = pattern.format(name=base_name, index=i, frame=i+1)
                filename_text = f"{filename}.{format_ext}"
            except:
                filename_text = f"{base_name}_{i}.{format_ext}"
            
            text_item = self.preview_view.scene.addText(filename_text)
            text_item.setPos(x, y + frame_height + 5)
            font = QFont()
            font.setPointSize(9)
            text_item.setFont(font)
            text_item.setDefaultTextColor(QColor(100, 100, 100))
        
        if frame_count > display_count:
            # Add "..." indicator
            more_text = self.preview_view.scene.addText(f"... and {frame_count - display_count} more files")
            more_text.setPos(margin, margin + rows * (frame_height + spacing + 20))
            font = QFont()
            font.setPointSize(11)
            font.setItalic(True)
            more_text.setFont(font)
            more_text.setDefaultTextColor(QColor(150, 150, 150))
    
    def _generate_selected_frames_preview(self):
        """Generate preview for selected frames export."""
        selected_indices = self._export_settings.get('selected_indices', [])
        self.preview_type_label.setText(f"Selected Frames ({len(selected_indices)} of {len(self._sprites)})")
        
        # Similar to individual frames but only show selected ones
        display_count = min(len(selected_indices), 12)
        
        import math
        cols = min(4, display_count)
        rows = math.ceil(display_count / cols)
        
        if self._sprites:
            frame_width = min(self._sprites[0].width(), 100)
            frame_height = min(self._sprites[0].height(), 100)
        else:
            frame_width = frame_height = 64
        
        spacing = 20
        margin = 20
        
        base_name = self._export_settings.get('base_name', 'frame')
        pattern = self._export_settings.get('pattern', '{name}_{index:03d}')
        format_ext = self._export_settings.get('format', 'PNG').lower()
        
        for i, frame_index in enumerate(selected_indices[:display_count]):
            row = i // cols
            col = i % cols
            
            x = margin + col * (frame_width + spacing + 60)
            y = margin + row * (frame_height + spacing + 20)
            
            if frame_index < len(self._sprites):
                scaled_pixmap = self._sprites[frame_index].scaled(
                    frame_width, frame_height,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                frame_item = self.preview_view.scene.addPixmap(scaled_pixmap)
                frame_item.setPos(x, y)
                
                # Highlight border for selected frames
                rect_item = self.preview_view.scene.addRect(
                    x - 2, y - 2,
                    scaled_pixmap.width() + 4,
                    scaled_pixmap.height() + 4,
                    QPen(QColor(0, 123, 255), 2)
                )
            
            # Filename
            try:
                filename = pattern.format(name=base_name, index=i, frame=frame_index+1)
                filename_text = f"{filename}.{format_ext}"
            except:
                filename_text = f"{base_name}_{i}.{format_ext}"
            
            text_item = self.preview_view.scene.addText(filename_text)
            text_item.setPos(x, y + frame_height + 5)
            font = QFont()
            font.setPointSize(9)
            text_item.setFont(font)
            text_item.setDefaultTextColor(QColor(100, 100, 100))
    
    def _update_summary(self):
        """Update the export summary display."""
        if not self._current_preset:
            return
        
        # Export type
        self.summary_labels['type'].setText(
            f"<b>Export Type:</b> {self._current_preset.display_name}"
        )
        
        # Output location
        output_dir = self._export_settings.get('output_dir', '')
        output_dir_short = self._shorten_path(output_dir)
        self.summary_labels['output'].setText(
            f"<b>Output:</b> {output_dir_short}"
        )
        
        # Format and scale
        format_str = self._export_settings.get('format', 'PNG')
        scale = self._export_settings.get('scale', 1.0)
        self.summary_labels['format'].setText(
            f"<b>Format:</b> {format_str} @ {scale}x scale"
        )
        
        # Dimensions/count
        if self._current_preset.mode == "sheet":
            # Calculate sheet dimensions
            self.summary_labels['dimensions'].setText(
                f"<b>Dimensions:</b> Calculating..."
            )
        elif self._current_preset.mode == "selected":
            selected_count = len(self._export_settings.get('selected_indices', []))
            self.summary_labels['dimensions'].setText(
                f"<b>Files:</b> {selected_count} frames selected"
            )
        else:
            self.summary_labels['dimensions'].setText(
                f"<b>Files:</b> {len(self._sprites)} frames"
            )
        
        # Estimated size
        self._estimate_file_size()
        
        # Mode-specific extras
        extras = []
        if self._current_preset.mode == "sheet":
            spacing = self._export_settings.get('spacing', 0)
            if spacing > 0:
                extras.append(f"{spacing}px spacing")
        
        if extras:
            self.summary_labels['extras'].setText(
                f"<b>Options:</b> {', '.join(extras)}"
            )
        else:
            self.summary_labels['extras'].setText("")
    
    def _update_tips(self):
        """Update tips based on export type."""
        if not self._current_preset:
            return
        
        tips = []
        
        if self._current_preset.mode == "sheet":
            tips.append("• Power-of-2 dimensions are optimal for game engines")
            tips.append("• Use PNG format for transparency support")
            tips.append("• Consider spacing between sprites to avoid bleeding")
        elif self._current_preset.mode == "individual":
            tips.append("• Use consistent naming for easy import in other tools")
            tips.append("• PNG format preserves transparency")
            tips.append("• Higher scales are useful for print or detailed work")
        elif self._current_preset.mode == "selected":
            tips.append("• Double-check your frame selection before exporting")
            tips.append("• Selected frames will be renumbered starting from 0")
        
        self.tips_label.setText("\n".join(tips))
    
    def _estimate_file_size(self):
        """Estimate the output file size."""
        if not self._sprites:
            self.summary_labels['file_size'].setText("<b>Size:</b> Unknown")
            return
        
        # Basic estimation based on format and dimensions
        format_str = self._export_settings.get('format', 'PNG')
        scale = self._export_settings.get('scale', 1.0)
        
        # Average bytes per pixel estimation
        bytes_per_pixel = {
            'PNG': 4,  # RGBA
            'JPG': 3,  # RGB
            'JPEG': 3,
            'BMP': 4,
        }.get(format_str, 4)
        
        if self._sprites:
            width = int(self._sprites[0].width() * scale)
            height = int(self._sprites[0].height() * scale)
            pixels_per_frame = width * height
            
            if self._current_preset.mode == "sheet":
                # Estimate sheet size
                total_pixels = pixels_per_frame * len(self._sprites)
                # Add overhead for spacing/padding
                overhead = 1.1
            else:
                # Individual files have more overhead
                total_pixels = pixels_per_frame * len(self._sprites)
                overhead = 1.2
            
            estimated_bytes = int(total_pixels * bytes_per_pixel * overhead)
            
            # Compression factor
            if format_str == 'PNG':
                estimated_bytes = int(estimated_bytes * 0.6)  # Typical compression
            elif format_str in ['JPG', 'JPEG']:
                quality = self._export_settings.get('quality', 95)
                compression_factor = quality / 100 * 0.3 + 0.1
                estimated_bytes = int(estimated_bytes * compression_factor)
            
            # Format file size
            if estimated_bytes < 1024:
                size_str = f"{estimated_bytes} bytes"
            elif estimated_bytes < 1024 * 1024:
                size_str = f"{estimated_bytes / 1024:.1f} KB"
            else:
                size_str = f"{estimated_bytes / (1024 * 1024):.1f} MB"
            
            self.summary_labels['file_size'].setText(f"<b>Estimated Size:</b> ~{size_str}")
        else:
            self.summary_labels['file_size'].setText("<b>Size:</b> Unknown")
    
    def _shorten_path(self, path: str, max_length: int = 50) -> str:
        """Shorten a file path for display."""
        if len(path) <= max_length:
            return path
        
        # Try to show beginning and end
        parts = path.split(os.sep)
        if len(parts) > 3:
            return f"{parts[0]}{os.sep}...{os.sep}{os.sep.join(parts[-2:])}"
        else:
            return f"...{path[-max_length:]}"
    
    def _fit_preview(self):
        """Fit preview to view."""
        self.preview_view.fit_preview_in_view()
    
    def _zoom_100(self):
        """Reset zoom to 100%."""
        self.preview_view.resetTransform()
        self.preview_view._zoom_level = 1.0
    
    def set_sprites(self, sprites: List[QPixmap]):
        """Set the sprite frames for preview."""
        self._sprites = sprites
        if self._current_preset:
            self._generate_preview()
    
    def validate(self) -> bool:
        """This step is always valid (preview only)."""
        return True
    
    def get_data(self) -> Dict[str, Any]:
        """Get final confirmation data."""
        return {
            'confirmed': True,
            'preview_completed': True
        }
    
    def _get_group_style(self) -> str:
        """Get consistent group box styling."""
        return """
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                background-color: #ffffff;
                color: #212529;
            }
        """
    
    def _get_control_button_style(self) -> str:
        """Get control button styling."""
        return """
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
                color: #495057;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border-color: #adb5bd;
            }
            QPushButton:pressed {
                background-color: #e9ecef;
            }
        """