"""
Centralized style management for PySide6 widgets.

Provides color constants, pre-built stylesheets, and dynamic style builders
to ensure consistent theming across the application.
"""


class StyleManager:
    """Centralized style management for consistent theming."""

    class Colors:
        """Semantic color constants."""

        # Primary actions (blue)
        PRIMARY = "#1976D2"
        PRIMARY_HOVER = "#1565C0"
        PRIMARY_PRESSED = "#0D47A1"
        PRIMARY_LIGHT = "#e3f2fd"

        # Bootstrap primary (for wizard buttons)
        BOOTSTRAP_PRIMARY = "#007bff"
        BOOTSTRAP_PRIMARY_HOVER = "#0056b3"
        BOOTSTRAP_PRIMARY_PRESSED = "#004085"

        # Success / Play (green)
        SUCCESS = "#4CAF50"
        SUCCESS_HOVER = "#45a049"
        SUCCESS_PRESSED = "#3d8b40"
        SUCCESS_LIGHT = "#E8F5E8"

        # Warning / Playing (orange)
        WARNING = "#FF9800"
        WARNING_HOVER = "#F57C00"

        # Danger / Stop (red)
        DANGER = "#f44336"
        DANGER_HOVER = "#d32f2f"
        DANGER_PRESSED = "#c62828"

        # Backgrounds
        BG_LIGHT = "#f8f9fa"
        BG_WHITE = "#ffffff"
        BG_HOVER = "#e9ecef"
        BG_PANEL = "#FAFAFA"
        BG_SEGMENT_HOVER = "#F0F0F0"

        # Borders
        BORDER_LIGHT = "#dee2e6"
        BORDER_DEFAULT = "#ddd"
        BORDER_DARK = "#adb5bd"
        BORDER_ITEM = "#eee"

        # Text
        TEXT_PRIMARY = "#212529"
        TEXT_SECONDARY = "#6c757d"
        TEXT_MUTED = "#666"
        TEXT_DARK = "#495057"

        # Selection
        SELECTION_BG = "#e3f2fd"
        SELECTION_BORDER = "#2196F3"

        # Bootstrap success (for export buttons)
        BOOTSTRAP_SUCCESS = "#28a745"
        BOOTSTRAP_SUCCESS_HOVER = "#218838"

        # Neutral/disabled
        DISABLED_BG = "#cccccc"
        DISABLED_TEXT = "#adb5bd"

        # Specific UI elements
        ZOOM_BUTTON = "#666"
        ZOOM_BUTTON_HOVER = "#555"

    # =========================================================================
    # Pre-built Stylesheets
    # =========================================================================

    @classmethod
    def button_success(cls, border_radius: int = 16, font_size: int = 16) -> str:
        """Green success/play button."""
        return f"""
            QPushButton {{
                background-color: {cls.Colors.SUCCESS};
                color: white;
                border: none;
                border-radius: {border_radius}px;
                font-size: {font_size}px;
            }}
            QPushButton:hover {{
                background-color: {cls.Colors.SUCCESS_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {cls.Colors.SUCCESS_PRESSED};
            }}
        """

    @classmethod
    def button_warning(cls, border_radius: int = 16, font_size: int = 14) -> str:
        """Orange warning/playing button."""
        return f"""
            QPushButton {{
                background-color: {cls.Colors.WARNING};
                color: white;
                border: none;
                border-radius: {border_radius}px;
                font-size: {font_size}px;
            }}
            QPushButton:hover {{
                background-color: {cls.Colors.WARNING_HOVER};
            }}
        """

    @classmethod
    def button_danger(cls, border_radius: int = 10) -> str:
        """Red danger/remove button."""
        return f"""
            QToolButton {{
                background-color: {cls.Colors.DANGER};
                color: white;
                border: none;
                border-radius: {border_radius}px;
                font-size: 16px;
                font-weight: bold;
            }}
            QToolButton:hover {{
                background-color: {cls.Colors.DANGER_HOVER};
            }}
        """

    @classmethod
    def button_primary(cls, border_radius: int = 4) -> str:
        """Blue primary action button."""
        return f"""
            QPushButton {{
                background-color: {cls.Colors.SELECTION_BORDER};
                color: white;
                border: none;
                border-radius: {border_radius}px;
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                background-color: {cls.Colors.PRIMARY};
            }}
        """

    @classmethod
    def button_primary_bootstrap(cls, border_radius: int = 6) -> str:
        """Bootstrap-style primary button (for wizard)."""
        return f"""
            QPushButton {{
                background-color: {cls.Colors.BOOTSTRAP_PRIMARY};
                color: white;
                border: none;
                border-radius: {border_radius}px;
                padding: 8px 24px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {cls.Colors.BOOTSTRAP_PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {cls.Colors.BOOTSTRAP_PRIMARY_PRESSED};
            }}
            QPushButton:disabled {{
                background-color: {cls.Colors.TEXT_SECONDARY};
                color: {cls.Colors.DISABLED_TEXT};
            }}
        """

    @classmethod
    def button_secondary(cls, border_radius: int = 4) -> str:
        """Gray secondary/neutral button."""
        return f"""
            QPushButton {{
                background-color: {cls.Colors.BG_LIGHT};
                border: 1px solid {cls.Colors.BORDER_LIGHT};
                border-radius: {border_radius}px;
                padding: 4px 12px;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background-color: {cls.Colors.BG_HOVER};
            }}
        """

    @classmethod
    def button_secondary_large(cls, border_radius: int = 6) -> str:
        """Large secondary button (for wizard navigation)."""
        return f"""
            QPushButton {{
                background-color: {cls.Colors.BG_WHITE};
                border: 1px solid {cls.Colors.BORDER_LIGHT};
                border-radius: {border_radius}px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
                color: {cls.Colors.TEXT_DARK};
            }}
            QPushButton:hover {{
                background-color: {cls.Colors.BG_LIGHT};
                border-color: {cls.Colors.BORDER_DARK};
            }}
            QPushButton:pressed {{
                background-color: {cls.Colors.BG_HOVER};
            }}
            QPushButton:disabled {{
                background-color: {cls.Colors.BG_LIGHT};
                color: {cls.Colors.DISABLED_TEXT};
                border-color: {cls.Colors.BG_HOVER};
            }}
        """

    @classmethod
    def button_stop(cls, border_radius: int = 4) -> str:
        """Red stop button."""
        return f"""
            QPushButton {{
                background-color: {cls.Colors.DANGER};
                color: white;
                border: none;
                border-radius: {border_radius}px;
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                background-color: {cls.Colors.DANGER_HOVER};
            }}
        """

    @classmethod
    def button_zoom(cls) -> str:
        """Circular zoom button (+/-)."""
        return f"""
            QPushButton {{
                background-color: {cls.Colors.ZOOM_BUTTON};
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {cls.Colors.ZOOM_BUTTON_HOVER};
            }}
            QPushButton:disabled {{
                background-color: {cls.Colors.DISABLED_BG};
            }}
        """

    @classmethod
    def button_small_hold(cls) -> str:
        """Small hold button for animation controls."""
        return """
            QPushButton {
                font-size: 10px;
                padding: 2px;
                background-color: #E0E0E0;
                border: 1px solid #999;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #D0D0D0;
            }
        """

    # =========================================================================
    # Frame/Container Stylesheets
    # =========================================================================

    @classmethod
    def frame_empty_state(cls) -> str:
        """Dashed border frame for empty states."""
        return f"""
            QFrame {{
                background-color: {cls.Colors.BG_LIGHT};
                border: 2px dashed {cls.Colors.BORDER_LIGHT};
                border-radius: 8px;
                padding: 20px;
            }}
        """

    @classmethod
    def frame_title_bar(cls) -> str:
        """Title bar frame with bottom border."""
        return f"""
            QFrame {{
                background-color: {cls.Colors.PRIMARY_LIGHT};
                border-bottom: 2px solid {cls.Colors.SELECTION_BORDER};
                padding: 8px;
            }}
        """

    @classmethod
    def frame_panel(cls) -> str:
        """Standard panel frame."""
        return f"""
            QFrame {{
                background-color: {cls.Colors.BG_LIGHT};
            }}
        """

    @classmethod
    def frame_recommendation(cls) -> str:
        """Info/recommendation frame with blue border."""
        return f"""
            QFrame {{
                background-color: {cls.Colors.PRIMARY_LIGHT};
                border: 1px solid {cls.Colors.SELECTION_BORDER};
                border-radius: 4px;
                padding: 8px;
            }}
        """

    @classmethod
    def frame_wizard_header(cls) -> str:
        """Wizard header frame."""
        return f"""
            #wizardHeader {{
                background-color: {cls.Colors.BG_LIGHT};
                border-bottom: 1px solid {cls.Colors.BORDER_LIGHT};
            }}
        """

    @classmethod
    def frame_wizard_nav(cls) -> str:
        """Wizard navigation frame."""
        return f"""
            #wizardNav {{
                background-color: {cls.Colors.BG_LIGHT};
                border-top: 1px solid {cls.Colors.BORDER_LIGHT};
            }}
        """

    # =========================================================================
    # List/Input Stylesheets
    # =========================================================================

    @classmethod
    def list_widget(cls) -> str:
        """Standard list widget with selection styling."""
        return f"""
            QListWidget {{
                border: 1px solid {cls.Colors.BORDER_DEFAULT};
                border-radius: 6px;
                background-color: white;
                alternate-background-color: {cls.Colors.BG_LIGHT};
            }}
            QListWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {cls.Colors.BORDER_ITEM};
            }}
            QListWidget::item:selected {{
                background-color: {cls.Colors.SELECTION_BG};
                color: #1976d2;
                border-left: 3px solid #1976d2;
            }}
            QListWidget::item:hover {{
                background-color: #f5f5f5;
            }}
        """

    @classmethod
    def text_edit_readonly(cls) -> str:
        """Read-only text area."""
        return f"""
            QTextEdit {{
                border: 1px solid {cls.Colors.BORDER_DEFAULT};
                border-radius: 4px;
                background-color: {cls.Colors.BG_LIGHT};
                font-size: 10px;
                color: {cls.Colors.TEXT_DARK};
            }}
        """

    @classmethod
    def spinbox_compact(cls) -> str:
        """Compact spin box."""
        return f"""
            QSpinBox {{
                background-color: white;
                border: 1px solid {cls.Colors.BORDER_DEFAULT};
                border-radius: 4px;
                padding: 2px;
                font-size: 10px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                width: 12px;
            }}
        """

    @classmethod
    def line_edit_standard(cls) -> str:
        """Standard line edit."""
        return f"""
            QLineEdit {{
                border: 1px solid {cls.Colors.BORDER_LIGHT};
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 13px;
                background-color: {cls.Colors.BG_WHITE};
            }}
            QLineEdit:focus {{
                border-color: {cls.Colors.BOOTSTRAP_PRIMARY};
            }}
        """

    @classmethod
    def combo_standard(cls) -> str:
        """Standard combo box."""
        return f"""
            QComboBox {{
                border: 1px solid {cls.Colors.BORDER_LIGHT};
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 13px;
                background-color: {cls.Colors.BG_WHITE};
            }}
            QComboBox:focus {{
                border-color: {cls.Colors.BOOTSTRAP_PRIMARY};
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 8px;
            }}
        """

    @classmethod
    def progress_bar(cls) -> str:
        """Standard progress bar."""
        return f"""
            QProgressBar {{
                background-color: {cls.Colors.BG_HOVER};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {cls.Colors.BOOTSTRAP_PRIMARY};
                border-radius: 3px;
            }}
        """

    @classmethod
    def menu_standard(cls) -> str:
        """Standard context menu."""
        return """
            QMenu {
                background-color: white;
                border: 1px solid #ccc;
            }
            QMenu::item {
                padding: 4px 20px;
            }
            QMenu::item:selected {
                background-color: #e0e0e0;
            }
        """

    @classmethod
    def tab_widget(cls) -> str:
        """Tab widget styling."""
        return f"""
            QTabWidget::pane {{
                border: 1px solid {cls.Colors.BORDER_LIGHT};
                background-color: {cls.Colors.BG_WHITE};
                border-radius: 0 0 6px 6px;
            }}
            QTabBar::tab {{
                background-color: {cls.Colors.BG_LIGHT};
                border: 1px solid {cls.Colors.BORDER_LIGHT};
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {cls.Colors.BG_WHITE};
                border-bottom-color: {cls.Colors.BG_WHITE};
            }}
        """

    @classmethod
    def splitter(cls) -> str:
        """Splitter handle styling."""
        return f"""
            QSplitter::handle {{
                background-color: {cls.Colors.BORDER_LIGHT};
            }}
            QSplitter::handle:horizontal {{
                width: 2px;
            }}
        """

    # =========================================================================
    # Label Stylesheets
    # =========================================================================

    @classmethod
    def label_secondary(cls) -> str:
        """Secondary/muted label."""
        return f"color: {cls.Colors.TEXT_SECONDARY}; font-size: 10px;"

    @classmethod
    def label_muted(cls) -> str:
        """Muted label."""
        return f"color: {cls.Colors.TEXT_MUTED}; font-size: 10px;"

    @classmethod
    def label_bold(cls) -> str:
        """Bold label."""
        return "font-weight: bold;"

    @classmethod
    def label_title(cls) -> str:
        """Title label for panels."""
        return f"font-size: 14px; font-weight: bold; color: {cls.Colors.PRIMARY};"

    @classmethod
    def label_step_indicator(cls) -> str:
        """Step indicator label for wizard."""
        return f"""
            QLabel {{
                color: {cls.Colors.TEXT_DARK};
                font-size: 12px;
                font-weight: 500;
            }}
        """

    @classmethod
    def label_subtitle(cls) -> str:
        """Subtitle label."""
        return f"color: {cls.Colors.TEXT_SECONDARY};"

    @classmethod
    def label_empty_state(cls) -> str:
        """Empty state message label."""
        return """
            QLabel {
                color: #999;
                font-style: italic;
                padding: 40px;
            }
        """

    @classmethod
    def label_field(cls) -> str:
        """Form field label."""
        return f"font-weight: bold; color: {cls.Colors.TEXT_PRIMARY};"

    @classmethod
    def label_info(cls) -> str:
        """Info/summary label."""
        return f"color: {cls.Colors.TEXT_SECONDARY}; font-size: 12px;"

    # =========================================================================
    # Dynamic Style Builders
    # =========================================================================

    @classmethod
    def segment_frame(cls, border_color: str) -> str:
        """Frame with segment-colored border."""
        return f"""
            QFrame {{
                border: 2px solid {border_color};
                border-radius: 8px;
                background-color: {cls.Colors.BG_PANEL};
                margin: 4px;
                padding: 8px;
            }}
            QFrame:hover {{
                background-color: {cls.Colors.BG_SEGMENT_HOVER};
            }}
        """

    @classmethod
    def color_indicator(cls, color: str) -> str:
        """Small color indicator square."""
        return f"""
            QLabel {{
                background-color: {color};
                border: 1px solid {cls.Colors.TEXT_MUTED};
                border-radius: 3px;
            }}
        """

    @classmethod
    def thumbnail_style(
        cls,
        selected: bool = False,
        highlighted: bool = False,
        segment_color: str | None = None,
        segment_bg: str | None = None,
        is_segment_start: bool = False,
        is_segment_end: bool = False,
    ) -> str:
        """Build thumbnail style based on state.

        Args:
            selected: Whether the thumbnail is selected
            highlighted: Whether the thumbnail is highlighted (drag-over)
            segment_color: Hex color of the segment border, if in a segment
            segment_bg: Hex color for segment background (lighter version of segment_color)
            is_segment_start: Whether this is the first frame of a segment
            is_segment_end: Whether this is the last frame of a segment
        """
        if selected:
            border_color = cls.Colors.SUCCESS
            border_width = "3px"
            background = cls.Colors.SUCCESS_LIGHT
        elif highlighted:
            border_color = cls.Colors.SELECTION_BORDER
            border_width = "2px"
            background = cls.Colors.SELECTION_BG
        elif segment_color:
            border_color = segment_color
            border_width = "3px"
            background = segment_bg if segment_bg else "#F5F5F5"
        else:
            border_color = cls.Colors.DISABLED_BG
            border_width = "1px"
            background = "white"

        hover_style = ""
        if not selected and not highlighted:
            hover_style = f"""
                QLabel:hover {{
                    border-color: {cls.Colors.SELECTION_BORDER};
                    background-color: #F0F8FF;
                }}
            """

        overlay_style = ""
        if is_segment_start:
            overlay_style += "border-left-width: 5px; border-left-style: solid;"
        if is_segment_end:
            overlay_style += "border-right-width: 5px; border-right-style: solid;"

        return f"""
            QLabel {{
                border: {border_width} solid {border_color};
                background-color: {background};
                border-radius: 4px;
                margin: 2px;
                padding: 2px;
                {overlay_style}
            }}
            {hover_style}
        """

    @classmethod
    def export_option(cls, selected: bool = False) -> str:
        """Export option card style."""
        if selected:
            return f"""
                SimpleExportOption {{
                    background-color: #e7f3ff;
                    border: 2px solid {cls.Colors.BOOTSTRAP_PRIMARY};
                    border-radius: 8px;
                }}
            """
        else:
            return f"""
                SimpleExportOption {{
                    background-color: {cls.Colors.BG_WHITE};
                    border: 1px solid {cls.Colors.BORDER_LIGHT};
                    border-radius: 8px;
                }}
                SimpleExportOption:hover {{
                    background-color: {cls.Colors.BG_LIGHT};
                    border: 1px solid {cls.Colors.BOOTSTRAP_PRIMARY};
                }}
            """

    @classmethod
    def export_option_recommended(cls) -> str:
        """Recommended export option style."""
        return f"""
            SimpleExportOption {{
                border: 2px solid {cls.Colors.SELECTION_BORDER};
                background-color: #f5f5f5;
            }}
            SimpleExportOption:hover {{
                background-color: {cls.Colors.PRIMARY_LIGHT};
            }}
        """

    @classmethod
    def scale_button(cls, selected: bool = False) -> str:
        """Scale selection button."""
        if selected:
            return f"""
                QPushButton {{
                    background-color: {cls.Colors.BOOTSTRAP_PRIMARY};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 12px;
                    font-weight: bold;
                }}
            """
        else:
            return f"""
                QPushButton {{
                    background-color: {cls.Colors.BG_WHITE};
                    color: {cls.Colors.TEXT_DARK};
                    border: 1px solid {cls.Colors.BORDER_LIGHT};
                    border-radius: 4px;
                    padding: 8px 12px;
                }}
                QPushButton:hover {{
                    background-color: {cls.Colors.BG_LIGHT};
                    border-color: {cls.Colors.BOOTSTRAP_PRIMARY};
                }}
            """

    @classmethod
    def preview_label(cls) -> str:
        """Preview area label styling."""
        return f"""
            QLabel {{
                border: 1px solid {cls.Colors.BORDER_DEFAULT};
                background-color: white;
                border-radius: 4px;
                padding: 2px;
            }}
        """

    @classmethod
    def settings_panel(cls) -> str:
        """Settings panel with border on right."""
        return f"""
            QFrame {{
                background-color: {cls.Colors.BG_WHITE};
                border-right: 1px solid {cls.Colors.BORDER_LIGHT};
            }}
        """

    @classmethod
    def separator_line(cls) -> str:
        """Horizontal separator line."""
        return f"background-color: {cls.Colors.BORDER_DEFAULT};"

    @classmethod
    def line_edit_readonly(cls) -> str:
        """Read-only line edit with gray background."""
        return f"""
            QLineEdit {{
                padding: 8px;
                border: 1px solid {cls.Colors.BORDER_LIGHT};
                border-radius: 4px;
                background-color: {cls.Colors.BG_LIGHT};
            }}
        """

    @classmethod
    def browse_button(cls) -> str:
        """Browse/secondary button style."""
        return f"""
            QPushButton {{
                padding: 6px 12px;
                border: 1px solid {cls.Colors.BORDER_LIGHT};
                border-radius: 4px;
                background-color: {cls.Colors.BG_WHITE};
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {cls.Colors.BG_LIGHT};
                border-color: {cls.Colors.BORDER_DARK};
            }}
        """

    @classmethod
    def scale_button_toggle(cls) -> str:
        """Toggle button for scale selection."""
        return f"""
            QPushButton {{
                border: 1px solid {cls.Colors.BORDER_LIGHT};
                border-radius: 4px;
                background-color: {cls.Colors.BG_WHITE};
                font-weight: 500;
            }}
            QPushButton:checked {{
                background-color: {cls.Colors.BOOTSTRAP_PRIMARY};
                border-color: {cls.Colors.BOOTSTRAP_PRIMARY};
                color: white;
            }}
            QPushButton:hover {{
                border-color: {cls.Colors.BOOTSTRAP_PRIMARY};
            }}
        """

    @classmethod
    def preview_header(cls) -> str:
        """Preview section header."""
        return f"""
            font-weight: bold;
            color: {cls.Colors.TEXT_DARK};
            font-size: 14px;
        """

    @classmethod
    def preview_panel(cls) -> str:
        """Preview panel background."""
        return f"background-color: {cls.Colors.BG_LIGHT};"

    @classmethod
    def fit_button(cls) -> str:
        """Fit/Reset button in preview area."""
        return f"""
            QPushButton {{
                padding: 4px 12px;
                border: 1px solid {cls.Colors.BORDER_LIGHT};
                border-radius: 4px;
                font-size: 11px;
                background-color: {cls.Colors.BG_WHITE};
            }}
            QPushButton:hover {{
                background-color: {cls.Colors.BG_LIGHT};
            }}
        """

    @classmethod
    def export_button(cls) -> str:
        """Large export button."""
        return f"""
            QPushButton {{
                padding: 12px 24px;
                background-color: {cls.Colors.BOOTSTRAP_SUCCESS};
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {cls.Colors.BOOTSTRAP_SUCCESS_HOVER};
            }}
            QPushButton:disabled {{
                background-color: {cls.Colors.BORDER_LIGHT};
                color: {cls.Colors.TEXT_SECONDARY};
            }}
        """

    @classmethod
    def bottom_bar(cls) -> str:
        """Bottom action bar."""
        return f"""
            QFrame {{
                background-color: {cls.Colors.BG_WHITE};
                border-top: 1px solid {cls.Colors.BORDER_LIGHT};
            }}
        """

    @classmethod
    def info_overlay(cls) -> str:
        """Floating info overlay label."""
        return """
            QLabel {
                background-color: rgba(33, 37, 41, 0.9);
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
            }
        """

    @classmethod
    def tool_button(cls) -> str:
        """Compact tool button."""
        return f"""
            QToolButton {{
                padding: 4px 8px;
                border: 1px solid {cls.Colors.BORDER_LIGHT};
                border-radius: 4px;
                background-color: {cls.Colors.BG_WHITE};
            }}
            QToolButton:hover {{
                background-color: {cls.Colors.BG_LIGHT};
            }}
        """

    @classmethod
    def graphics_view_preview(cls) -> str:
        """Graphics view for live preview."""
        return f"""
            QGraphicsView {{
                background-color: {cls.Colors.BG_LIGHT};
                border: 1px solid {cls.Colors.BG_HOVER};
                border-radius: 8px;
            }}
        """

    # =========================================================================
    # Migrated from Config.Styles
    # =========================================================================

    @staticmethod
    def canvas_normal() -> str:
        """Normal canvas border and background."""
        return """
            QLabel {
                border: 2px solid #ccc;
                border-radius: 4px;
                background-color: #f5f5f5;
            }
        """

    @staticmethod
    def canvas_drag_hover() -> str:
        """Canvas style when a drag is hovering over it."""
        return """
            QLabel {
                border: 4px dashed #4CAF50;
                border-radius: 8px;
                background-color: #e8f5e9;
            }
        """

    @staticmethod
    def play_button_stopped() -> str:
        """Play button style when animation is stopped."""
        return """
            QPushButton {
                font-size: 14pt;
                font-weight: bold;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """

    @staticmethod
    def play_button_playing() -> str:
        """Play button style when animation is playing."""
        return """
            QPushButton {
                font-size: 14pt;
                font-weight: bold;
                background-color: #ff9800;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
            QPushButton:pressed {
                background-color: #cc7a00;
            }
        """

    @staticmethod
    def playback_controls_frame() -> str:
        """Playback controls container frame."""
        return """
            QFrame {
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 10px;
            }
        """

    @staticmethod
    def frame_extractor_groupbox() -> str:
        """Frame extractor group box."""
        return """
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """

    @staticmethod
    def main_toolbar() -> str:
        """Main toolbar style."""
        return """
            QToolBar {
                background-color: #f5f5f5;
                border-bottom: 1px solid #ddd;
                padding: 5px;
                spacing: 5px;
            }
            QToolButton {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
                margin: 2px;
            }
            QToolButton:hover {
                background-color: #e8e8e8;
                border-color: #bbb;
            }
            QToolButton:pressed {
                background-color: #ddd;
            }
        """

    @staticmethod
    def info_label() -> str:
        """Info label style."""
        return "color: #666; font-size: 10pt;"

    @staticmethod
    def help_label() -> str:
        """Help label style."""
        return "color: #888; font-style: italic; padding: 10px;"

    @staticmethod
    def speed_label() -> str:
        """Speed label style."""
        return "font-weight: bold;"

    @staticmethod
    def zoom_display() -> str:
        """Zoom display label style."""
        return """
            QLabel {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
                font-weight: bold;
            }
        """

    @staticmethod
    def preset_label() -> str:
        """Preset mode label style."""
        return "font-weight: normal; margin-bottom: 5px;"

    @staticmethod
    def custom_label() -> str:
        """Custom mode label style."""
        return "font-weight: normal; margin-top: 10px;"

    @staticmethod
    def offset_label() -> str:
        """Offset settings label style."""
        return "font-weight: normal; margin-top: 10px;"

    @staticmethod
    def grid_checkbox() -> str:
        """Grid overlay checkbox style."""
        return "margin-top: 10px;"

    @staticmethod
    def navigation_buttons() -> str:
        """Navigation (prev/next frame) button style."""
        return """
            QPushButton {
                font-size: 12pt;
                min-width: 28px;
                min-height: 28px;
                background-color: #e0e0e0;
                border: 1px solid #bbb;
                border-radius: 4px;
            }
            QPushButton:hover:enabled {
                background-color: #d0d0d0;
            }
            QPushButton:pressed {
                background-color: #c0c0c0;
            }
            QPushButton:disabled {
                color: #999;
                background-color: #f0f0f0;
            }
        """
