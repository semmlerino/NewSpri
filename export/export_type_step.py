"""
Export Type Selection Step
First step of the export wizard - choosing export type with visual cards.
Part of Export Dialog Usability Improvements.
"""

from typing import Optional, List, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QButtonGroup, QGraphicsDropShadowEffect,
    QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QSize, QTimer
from PySide6.QtGui import QFont, QPalette, QColor, QPainter, QPixmap, QBrush, QPen

from .wizard_widget import WizardStep
from .export_presets import ExportPreset, ExportPresetType, get_preset_manager
from config import Config


class VisualPresetCard(QFrame):
    """Enhanced preset card with visual preview and better UX."""
    
    clicked = Signal(ExportPreset)
    
    def __init__(self, preset: ExportPreset, parent=None):
        super().__init__(parent)
        self.preset = preset
        self._is_selected = False
        self._hover_animation = None
        
        self._setup_ui()
        self._setup_styling()
    
    def _setup_ui(self):
        """Set up the enhanced card UI."""
        # Larger size for better visual impact
        self.setFixedSize(220, 160)
        self.setCursor(Qt.PointingHandCursor)
        
        # Main layout with better spacing
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        # Visual preview area
        self.preview_widget = self._create_visual_preview()
        layout.addWidget(self.preview_widget, 1)
        
        # Title with icon
        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)
        
        # Icon
        icon_label = QLabel(self.preset.icon)
        icon_font = QFont()
        icon_font.setPointSize(20)
        icon_label.setFont(icon_font)
        icon_label.setFixedSize(28, 28)
        title_layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(self.preset.display_name)
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_layout.addWidget(title_label, 1)
        
        layout.addLayout(title_layout)
        
        # Short description
        desc_label = QLabel(self.preset.short_description)
        desc_font = QFont()
        desc_font.setPointSize(10)
        desc_label.setFont(desc_font)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #6c757d;")
        layout.addWidget(desc_label)
        
        # Hover tooltip with detailed info
        tooltip_text = f"<b>{self.preset.display_name}</b><br>"
        tooltip_text += f"<i>{self.preset.description}</i><br><br>"
        tooltip_text += f"Format: {self.preset.format}<br>"
        tooltip_text += f"Default scale: {self.preset.scale}x"
        if self.preset.recommended_for:
            tooltip_text += f"<br><br>Recommended for:<br>• " + "<br>• ".join(self.preset.recommended_for)
        self.setToolTip(tooltip_text)
    
    def _create_visual_preview(self) -> QWidget:
        """Create a visual preview showing what this export type produces."""
        preview = QLabel()
        preview.setAlignment(Qt.AlignCenter)
        preview.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
            }
        """)
        
        # Create a simple visual representation
        pixmap = QPixmap(188, 60)  # Account for padding
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if self.preset.name == "individual_frames":
            # Show multiple frame icons
            self._draw_individual_frames_preview(painter)
        elif self.preset.name == "sprite_sheet":
            # Show grid layout
            self._draw_sprite_sheet_preview(painter)
        elif self.preset.name == "animation_gif":
            # Show animation frames
            self._draw_animation_preview(painter)
        elif self.preset.name == "selected_frames":
            # Show selection indication
            self._draw_selected_frames_preview(painter)
        else:
            # Generic preview
            self._draw_generic_preview(painter)
        
        painter.end()
        
        preview.setPixmap(pixmap)
        return preview
    
    def _draw_individual_frames_preview(self, painter: QPainter):
        """Draw preview for individual frames export."""
        # Draw 3 separate frame files
        frame_color = QColor("#007bff")
        frame_color.setAlpha(180)
        painter.setBrush(QBrush(frame_color))
        painter.setPen(QPen(QColor("#0056b3"), 1))
        
        for i in range(3):
            x = 40 + i * 50
            y = 15
            painter.drawRoundedRect(x, y, 35, 35, 4, 4)
            
            # Add frame number
            painter.setPen(QPen(Qt.white, 1))
            font = QFont()
            font.setPointSize(10)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(x, y, 35, 35, Qt.AlignCenter, f"{i+1}")
    
    def _draw_sprite_sheet_preview(self, painter: QPainter):
        """Draw preview for sprite sheet export."""
        # Draw a grid of sprites
        sheet_color = QColor("#28a745")
        sheet_color.setAlpha(180)
        painter.setBrush(QBrush(sheet_color))
        painter.setPen(QPen(QColor("#1e7e34"), 1))
        
        # Draw background sheet
        painter.drawRoundedRect(44, 10, 100, 40, 4, 4)
        
        # Draw grid lines
        painter.setPen(QPen(Qt.white, 1, Qt.DotLine))
        for i in range(1, 4):
            x = 44 + i * 25
            painter.drawLine(x, 10, x, 50)
        painter.drawLine(44, 30, 144, 30)
    
    def _draw_animation_preview(self, painter: QPainter):
        """Draw preview for animation GIF export."""
        # Draw film strip style
        film_color = QColor("#dc3545")
        film_color.setAlpha(180)
        painter.setBrush(QBrush(film_color))
        painter.setPen(QPen(QColor("#bd2130"), 1))
        
        # Film strip background
        painter.drawRoundedRect(24, 20, 140, 25, 4, 4)
        
        # Film perforations
        painter.setBrush(QBrush(Qt.white))
        for i in range(5):
            x = 30 + i * 28
            painter.drawRect(x, 12, 20, 6)
            painter.drawRect(x, 47, 20, 6)
    
    def _draw_selected_frames_preview(self, painter: QPainter):
        """Draw preview for selected frames export."""
        # Draw frames with selection checkmarks
        frame_color = QColor("#17a2b8")
        frame_color.setAlpha(180)
        
        for i in range(3):
            x = 40 + i * 50
            y = 15
            
            # Different opacity for middle frame (unselected)
            if i == 1:
                frame_color.setAlpha(80)
            else:
                frame_color.setAlpha(180)
            
            painter.setBrush(QBrush(frame_color))
            painter.setPen(QPen(QColor("#138496"), 1))
            painter.drawRoundedRect(x, y, 35, 35, 4, 4)
            
            # Checkmark for selected frames
            if i != 1:
                painter.setPen(QPen(Qt.white, 2))
                painter.drawLine(x + 10, y + 20, x + 15, y + 25)
                painter.drawLine(x + 15, y + 25, x + 25, y + 10)
    
    def _draw_generic_preview(self, painter: QPainter):
        """Draw generic preview."""
        generic_color = QColor("#6c757d")
        generic_color.setAlpha(180)
        painter.setBrush(QBrush(generic_color))
        painter.setPen(QPen(QColor("#495057"), 1))
        painter.drawRoundedRect(64, 15, 60, 30, 4, 4)
    
    def _setup_styling(self):
        """Set up card styling with hover effects."""
        self._update_style()
        
        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(shadow)
    
    def _update_style(self):
        """Update card style based on selection state."""
        if self._is_selected:
            self.setStyleSheet("""
                VisualPresetCard {
                    background-color: #ffffff;
                    border: 3px solid #007bff;
                    border-radius: 12px;
                }
            """)
        else:
            self.setStyleSheet("""
                VisualPresetCard {
                    background-color: #ffffff;
                    border: 1px solid #dee2e6;
                    border-radius: 12px;
                }
                VisualPresetCard:hover {
                    border: 2px solid #007bff;
                    background-color: #f8f9fa;
                }
            """)
    
    def set_selected(self, selected: bool):
        """Set card selection state."""
        self._is_selected = selected
        self._update_style()
    
    def mousePressEvent(self, event):
        """Handle mouse press."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.preset)
        super().mousePressEvent(event)
    
    def enterEvent(self, event):
        """Handle mouse enter for hover effect."""
        if not self._is_selected:
            # Slightly elevate shadow on hover
            shadow = self.graphicsEffect()
            if shadow:
                shadow.setBlurRadius(16)
                shadow.setOffset(0, 4)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave."""
        if not self._is_selected:
            # Reset shadow
            shadow = self.graphicsEffect()
            if shadow:
                shadow.setBlurRadius(12)
                shadow.setOffset(0, 2)
        super().leaveEvent(event)


class ExportTypeStep(WizardStep):
    """
    First step of export wizard - selecting export type.
    Features enhanced visual cards with previews.
    """
    
    def __init__(self, frame_count: int = 0, parent=None):
        super().__init__(
            title="Choose Export Type",
            subtitle="Select how you want to export your sprite frames",
            parent=parent
        )
        self.frame_count = frame_count
        self._preset_manager = get_preset_manager()
        self._selected_preset: Optional[ExportPreset] = None
        self._cards: List[VisualPresetCard] = []
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the export type selection UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(24)
        
        # Quick export bar (for common operations)
        quick_bar = self._create_quick_export_bar()
        layout.addWidget(quick_bar)
        
        # Main preset cards in a grid
        cards_widget = self._create_preset_cards()
        layout.addWidget(cards_widget, 1)
        
        # Help text at bottom
        help_label = QLabel("Click on a card to select your export type. Each option is optimized for different use cases.")
        help_label.setWordWrap(True)
        help_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 12px;
                padding: 8px;
                background-color: #f8f9fa;
                border-radius: 6px;
            }
        """)
        layout.addWidget(help_label)
    
    def _create_quick_export_bar(self) -> QWidget:
        """Create quick export shortcuts bar."""
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #e3f2fd;
                border: 1px solid #bbdefb;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        
        layout = QHBoxLayout(container)
        layout.setSpacing(12)
        
        # Label
        label = QLabel("Quick Export:")
        label.setStyleSheet("color: #1565c0; font-weight: bold; font-size: 12px;")
        layout.addWidget(label)
        
        # Quick action buttons
        quick_actions = [
            ("📁 All as PNG", "individual_frames"),
            ("📋 Sprite Sheet", "sprite_sheet"),
            ("🎬 Animated GIF", "animation_gif")
        ]
        
        for text, preset_name in quick_actions:
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    border: 1px solid #90caf9;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-size: 12px;
                    color: #1565c0;
                }
                QPushButton:hover {
                    background-color: #e3f2fd;
                    border-color: #64b5f6;
                }
                QPushButton:pressed {
                    background-color: #bbdefb;
                }
            """)
            btn.clicked.connect(lambda checked, pn=preset_name: self._quick_select_preset(pn))
            layout.addWidget(btn)
        
        layout.addStretch()
        
        return container
    
    def _create_preset_cards(self) -> QWidget:
        """Create the main preset card grid."""
        container = QWidget()
        grid_layout = QGridLayout(container)
        grid_layout.setSpacing(20)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Get main presets (not quick export ones)
        presets = self._preset_manager.get_presets_by_type(ExportPresetType.STANDARD)
        
        # Arrange in a 2x2 grid (or adapt based on count)
        for i, preset in enumerate(presets[:4]):  # Show up to 4 main presets
            card = VisualPresetCard(preset)
            card.clicked.connect(self._on_card_clicked)
            self._cards.append(card)
            
            row = i // 2
            col = i % 2
            grid_layout.addWidget(card, row, col)
        
        # Center the grid
        grid_layout.setRowStretch(2, 1)
        grid_layout.setColumnStretch(2, 1)
        
        return container
    
    def _quick_select_preset(self, preset_name: str):
        """Handle quick export selection."""
        preset = self._preset_manager.get_preset(preset_name)
        if preset:
            self._select_preset(preset)
            # Auto-advance to next step after a brief delay
            QTimer.singleShot(300, lambda: self.dataChanged.emit(self.get_data()))
    
    def _on_card_clicked(self, preset: ExportPreset):
        """Handle card selection."""
        self._select_preset(preset)
    
    def _select_preset(self, preset: ExportPreset):
        """Select a preset and update UI."""
        self._selected_preset = preset
        
        # Update card selection states
        for card in self._cards:
            card.set_selected(card.preset == preset)
        
        # Emit validation change
        self.stepValidated.emit(True)
        
        # Emit data change
        self.dataChanged.emit(self.get_data())
    
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
        """Set step data (for going back)."""
        preset_name = data.get('preset_name')
        if preset_name:
            preset = self._preset_manager.get_preset(preset_name)
            if preset:
                self._select_preset(preset)


class EnhancedExportPreset(ExportPreset):
    """Enhanced export preset with additional UI properties."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.short_description = kwargs.get('short_description', self.description[:50] + '...')
        self.recommended_for = kwargs.get('recommended_for', [])