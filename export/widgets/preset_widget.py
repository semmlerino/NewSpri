"""
Export Preset Widget
Visual preset selection cards for the redesigned export dialog.
Part of Phase 1: Export Dialog Redesign implementation.
"""

from typing import Optional, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy, QGraphicsDropShadowEffect, QButtonGroup
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QRect, QTimer
from PySide6.QtGui import QFont, QPalette, QColor, QPainter, QPen, QBrush

from ..core.export_presets import ExportPreset, ExportPresetType, get_preset_manager


class ExportPresetCard(QFrame):
    """Individual preset card with visual design and selection state."""
    
    selected = Signal(ExportPreset)
    
    def __init__(self, preset: ExportPreset, parent=None):
        super().__init__(parent)
        self.preset = preset
        self.selected_state = False
        self._hover_state = False
        
        self._setup_ui()
        self._setup_styling()
        self._setup_animations()
    
    def _setup_ui(self):
        """Set up the card UI elements."""
        self.setFixedSize(180, 120)
        self.setFrameStyle(QFrame.Box)
        self.setCursor(Qt.PointingHandCursor)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)
        
        # Icon and title row
        top_layout = QHBoxLayout()
        top_layout.setSpacing(8)
        
        # Large emoji icon
        self.icon_label = QLabel(self.preset.icon)
        icon_font = QFont()
        icon_font.setPointSize(24)
        self.icon_label.setFont(icon_font)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedSize(32, 32)
        top_layout.addWidget(self.icon_label)
        
        # Title
        self.title_label = QLabel(self.preset.display_name)
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setWordWrap(True)
        top_layout.addWidget(self.title_label, 1)
        
        layout.addLayout(top_layout)
        
        # Description
        self.desc_label = QLabel(self.preset.description)
        desc_font = QFont()
        desc_font.setPointSize(9)
        self.desc_label.setFont(desc_font)
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("color: #666;")
        layout.addWidget(self.desc_label, 1)
        
        # Technical details
        tech_text = f"{self.preset.format} • {self.preset.scale}x"
        self.tech_label = QLabel(tech_text)
        tech_font = QFont()
        tech_font.setPointSize(8)
        self.tech_label.setFont(tech_font)
        self.tech_label.setStyleSheet("color: #888; font-weight: 500;")
        self.tech_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.tech_label)
        
        # Set tooltip
        self.setToolTip(self._create_detailed_tooltip())
    
    def _setup_styling(self):
        """Set up visual styling for the card."""
        self._update_style()
        
        # Add subtle shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setOffset(2, 2)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)
    
    def _setup_animations(self):
        """Set up hover and selection animations."""
        # For future enhancement - smooth transitions
        pass
    
    def _update_style(self):
        """Update card styling based on state."""
        if self.selected_state:
            # Selected state - blue theme
            self.setStyleSheet("""
                ExportPresetCard {
                    background-color: #e3f2fd;
                    border: 2px solid #1976d2;
                    border-radius: 8px;
                }
            """)
            self.title_label.setStyleSheet("color: #0d47a1;")
        elif self._hover_state:
            # Hover state - subtle highlight
            self.setStyleSheet("""
                ExportPresetCard {
                    background-color: #f5f5f5;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                }
            """)
            self.title_label.setStyleSheet("color: #333;")
        else:
            # Default state
            self.setStyleSheet("""
                ExportPresetCard {
                    background-color: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                }
            """)
            self.title_label.setStyleSheet("color: #333;")
    
    def _create_detailed_tooltip(self) -> str:
        """Create detailed tooltip with use cases."""
        tooltip_parts = [
            f"<b>{self.preset.display_name}</b>",
            f"<i>{self.preset.tooltip}</i>",
            "",
            "<b>Best for:</b>",
        ]
        
        for use_case in self.preset.use_cases[:3]:  # Show first 3 use cases
            tooltip_parts.append(f"• {use_case}")
        
        tooltip_parts.extend([
            "",
            f"<b>Format:</b> {self.preset.format}",
            f"<b>Scale:</b> {self.preset.scale}x",
        ])
        
        return "<br>".join(tooltip_parts)
    
    def set_selected(self, selected: bool):
        """Set the selection state of the card."""
        if self.selected_state != selected:
            self.selected_state = selected
            self._update_style()
    
    def is_selected(self) -> bool:
        """Check if card is selected."""
        return self.selected_state
    
    def mousePressEvent(self, event):
        """Handle mouse click to select preset."""
        if event.button() == Qt.LeftButton:
            self.selected.emit(self.preset)
        super().mousePressEvent(event)
    
    def enterEvent(self, event):
        """Handle mouse enter for hover effect."""
        self._hover_state = True
        if not self.selected_state:
            self._update_style()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave to remove hover effect."""
        self._hover_state = False
        self._update_style()
        super().leaveEvent(event)


class ExportPresetSelector(QWidget):
    """Widget for selecting export presets with visual cards."""
    
    presetSelected = Signal(ExportPreset)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._cards: List[ExportPresetCard] = []
        self._selected_card: Optional[ExportPresetCard] = None
        
        self._setup_ui()
        self._load_presets()
    
    def _setup_ui(self):
        """Set up the preset selector UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Section title
        title_label = QLabel("Quick Export - Choose a preset:")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Cards container
        self.cards_layout = QHBoxLayout()
        self.cards_layout.setSpacing(12)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self.cards_layout)
        
        # Add stretch to center cards if there are fewer than expected
        self.cards_layout.addStretch()
    
    def _load_presets(self):
        """Load and create cards for built-in presets."""
        preset_manager = get_preset_manager()
        
        # Get the most commonly used presets for the main display
        main_presets = [
            ExportPresetType.INDIVIDUAL_FRAMES,
            ExportPresetType.SPRITE_SHEET,
            ExportPresetType.WEB_GAME_ATLAS,
            ExportPresetType.SPACED_SPRITE_SHEET
        ]
        
        for preset_type in main_presets:
            preset = preset_manager.get_preset(preset_type)
            if preset:
                self._add_preset_card(preset)
        
        # Select the first card by default and emit signal
        if self._cards:
            self._select_card(self._cards[0])
            # Emit signal to notify the export dialog
            self.presetSelected.emit(self._cards[0].preset)
    
    def _add_preset_card(self, preset: ExportPreset):
        """Add a preset card to the selector."""
        card = ExportPresetCard(preset)
        card.selected.connect(self._on_card_selected)
        
        # Insert before the stretch
        self.cards_layout.insertWidget(len(self._cards), card)
        self._cards.append(card)
    
    def _on_card_selected(self, preset: ExportPreset):
        """Handle preset card selection."""
        # Find and select the corresponding card
        for card in self._cards:
            if card.preset.name == preset.name:
                self._select_card(card)
                break
        
        self.presetSelected.emit(preset)
    
    def _select_card(self, selected_card: ExportPresetCard):
        """Select a specific card and deselect others."""
        # Deselect all cards
        for card in self._cards:
            card.set_selected(False)
        
        # Select the chosen card
        selected_card.set_selected(True)
        self._selected_card = selected_card
    
    def get_selected_preset(self) -> Optional[ExportPreset]:
        """Get the currently selected preset."""
        if self._selected_card:
            return self._selected_card.preset
        return None
    
    def select_preset_by_type(self, preset_type: ExportPresetType):
        """Select a preset by its type."""
        for card in self._cards:
            if card.preset.name == preset_type.value:
                self._select_card(card)
                self.presetSelected.emit(card.preset)
                break
    
    def add_custom_preset_option(self):
        """Add a 'Custom' option for advanced users."""
        # This could be implemented to show the advanced dialog
        custom_card = QFrame()
        custom_card.setFixedSize(180, 120)
        custom_card.setFrameStyle(QFrame.Box)
        custom_card.setStyleSheet("""
            QFrame {
                background-color: #f9f9f9;
                border: 2px dashed #ccc;
                border-radius: 8px;
            }
        """)
        
        custom_layout = QVBoxLayout(custom_card)
        custom_layout.setContentsMargins(12, 10, 12, 10)
        
        # Plus icon
        plus_label = QLabel("⚙️")
        plus_font = QFont()
        plus_font.setPointSize(24)
        plus_label.setFont(plus_font)
        plus_label.setAlignment(Qt.AlignCenter)
        custom_layout.addWidget(plus_label)
        
        # Custom label
        custom_label = QLabel("Custom Settings")
        custom_font = QFont()
        custom_font.setPointSize(10)
        custom_font.setBold(True)
        custom_label.setFont(custom_font)
        custom_label.setAlignment(Qt.AlignCenter)
        custom_layout.addWidget(custom_label)
        
        # Description
        desc_label = QLabel("Advanced options")
        desc_label.setStyleSheet("color: #666; font-size: 9px;")
        desc_label.setAlignment(Qt.AlignCenter)
        custom_layout.addWidget(desc_label)
        
        self.cards_layout.insertWidget(len(self._cards), custom_card)


class PresetRecommendationWidget(QWidget):
    """Widget that shows preset recommendations based on context."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the recommendation widget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        
        self.recommendation_label = QLabel()
        self.recommendation_label.setStyleSheet("""
            QLabel {
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 4px;
                padding: 8px;
                color: #856404;
                font-size: 11px;
            }
        """)
        self.recommendation_label.setWordWrap(True)
        self.recommendation_label.hide()
        
        layout.addWidget(self.recommendation_label)
    
    def show_recommendation(self, frame_count: int, use_case: str = ""):
        """Show a preset recommendation based on context."""
        preset_manager = get_preset_manager()
        recommended = preset_manager.get_recommended_preset(frame_count, use_case)
        
        if recommended:
            message = f"💡 <b>Recommendation:</b> For {frame_count} frames, try <b>{recommended.display_name}</b> - {recommended.tooltip}"
            self.recommendation_label.setText(message)
            self.recommendation_label.show()
    
    def hide_recommendation(self):
        """Hide the recommendation."""
        self.recommendation_label.hide()


# Convenience function for easy integration
def create_preset_selector_with_recommendation(parent=None) -> tuple[ExportPresetSelector, PresetRecommendationWidget]:
    """Create both preset selector and recommendation widgets."""
    selector = ExportPresetSelector(parent)
    recommendation = PresetRecommendationWidget(parent)
    
    return selector, recommendation