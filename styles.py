#!/usr/bin/env python3
"""
Style Manager for Sprite Viewer
Centralizes all CSS styling and theming for better maintainability.
"""

from config import Config


class StyleManager:
    """Centralized style management for all UI components."""
    
    # ============================================================================
    # CANVAS STYLES
    # ============================================================================
    
    @staticmethod
    def get_canvas_normal() -> str:
        """Default canvas appearance."""
        return """
            QLabel {
                border: 2px solid #ccc;
                border-radius: 4px;
                background-color: #f5f5f5;
            }
        """
    
    @staticmethod
    def get_canvas_drag_hover() -> str:
        """Canvas appearance during drag and drop hover."""
        return """
            QLabel {
                border: 4px dashed #4CAF50;
                border-radius: 8px;
                background-color: #e8f5e9;
            }
        """
    
    # ============================================================================
    # BUTTON STYLES
    # ============================================================================
    
    @staticmethod
    def get_play_button_stopped() -> str:
        """Play button when stopped (green theme)."""
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
    def get_play_button_playing() -> str:
        """Play button when playing (orange pause theme)."""
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
    def get_navigation_buttons() -> str:
        """Navigation buttons (first, prev, next, last)."""
        return f"""
            QPushButton {{
                font-size: 12pt;
                min-width: {Config.UI.NAV_BUTTON_WIDTH_PX};
                min-height: {Config.UI.NAV_BUTTON_HEIGHT_PX};
                background-color: #e0e0e0;
                border: 1px solid #bbb;
                border-radius: 4px;
            }}
            QPushButton:hover:enabled {{
                background-color: #d0d0d0;
            }}
            QPushButton:pressed {{
                background-color: #c0c0c0;
            }}
            QPushButton:disabled {{
                color: #999;
                background-color: #f0f0f0;
            }}
        """
    
    # ============================================================================
    # CONTAINER STYLES
    # ============================================================================
    
    @staticmethod
    def get_playback_controls_frame() -> str:
        """Main playback controls container."""
        return """
            QFrame {
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 10px;
            }
        """
    
    @staticmethod
    def get_frame_extractor_groupbox() -> str:
        """Frame extraction section container."""
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
    def get_main_toolbar() -> str:
        """Main application toolbar."""
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
    
    # ============================================================================
    # TEXT & LABEL STYLES
    # ============================================================================
    
    @staticmethod
    def get_info_label() -> str:
        """Sprite sheet information text."""
        return "color: #666; font-size: 10pt;"
    
    @staticmethod
    def get_help_label() -> str:
        """Bottom help text."""
        return "color: #888; font-style: italic; padding: 10px;"
    
    @staticmethod
    def get_speed_label() -> str:
        """Speed/FPS label."""
        return "font-weight: bold;"
    
    @staticmethod
    def get_zoom_display() -> str:
        """Zoom percentage display."""
        return """
            QLabel {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
                font-weight: bold;
            }
        """
    
    # ============================================================================
    # WIDGET-SPECIFIC STYLES
    # ============================================================================
    
    @staticmethod
    def get_preset_label() -> str:
        """Quick presets label in frame extractor."""
        return "font-weight: normal; margin-bottom: 5px;"
    
    @staticmethod
    def get_custom_label() -> str:
        """Custom size label in frame extractor."""
        return "font-weight: normal; margin-top: 10px;"
    
    @staticmethod
    def get_offset_label() -> str:
        """Offset label in frame extractor."""
        return "font-weight: normal; margin-top: 10px;"
    
    @staticmethod
    def get_grid_checkbox() -> str:
        """Grid overlay checkbox."""
        return "margin-top: 10px;"
    
    # ============================================================================
    # THEME COLLECTIONS
    # ============================================================================
    
    @staticmethod
    def get_all_canvas_styles() -> dict:
        """Get all canvas-related styles as a dictionary."""
        return {
            'normal': StyleManager.get_canvas_normal(),
            'drag_hover': StyleManager.get_canvas_drag_hover(),
        }
    
    @staticmethod
    def get_all_button_styles() -> dict:
        """Get all button-related styles as a dictionary."""
        return {
            'play_stopped': StyleManager.get_play_button_stopped(),
            'play_playing': StyleManager.get_play_button_playing(), 
            'navigation': StyleManager.get_navigation_buttons(),
        }
    
    @staticmethod
    def get_all_container_styles() -> dict:
        """Get all container-related styles as a dictionary."""
        return {
            'playback_frame': StyleManager.get_playback_controls_frame(),
            'extractor_groupbox': StyleManager.get_frame_extractor_groupbox(),
            'toolbar': StyleManager.get_main_toolbar(),
        }
    
    @staticmethod
    def get_all_text_styles() -> dict:
        """Get all text and label styles as a dictionary."""
        return {
            'info_label': StyleManager.get_info_label(),
            'help_label': StyleManager.get_help_label(),
            'speed_label': StyleManager.get_speed_label(),
            'zoom_display': StyleManager.get_zoom_display(),
            'preset_label': StyleManager.get_preset_label(),
            'custom_label': StyleManager.get_custom_label(),
            'offset_label': StyleManager.get_offset_label(),
            'grid_checkbox': StyleManager.get_grid_checkbox(),
        }
    
    # ============================================================================
    # THEME MANAGEMENT
    # ============================================================================
    
    @staticmethod
    def get_color_palette() -> dict:
        """Get the current color palette used throughout the application."""
        return {
            # Primary colors
            'primary_green': '#4CAF50',
            'primary_orange': '#ff9800',
            
            # Background colors  
            'bg_light': '#f5f5f5',
            'bg_lighter': '#f8f8f8',
            'bg_white': 'white',
            'bg_drag_hover': '#e8f5e9',
            
            # Border colors
            'border_light': '#ddd',
            'border_normal': '#ccc',
            'border_dark': '#bbb',
            
            # Button colors
            'button_normal': '#e0e0e0',
            'button_hover': '#d0d0d0',
            'button_pressed': '#c0c0c0',
            'button_disabled': '#f0f0f0',
            
            # Text colors
            'text_normal': '#666',
            'text_muted': '#888',
            'text_disabled': '#999',
            'text_white': 'white',
            
            # State colors
            'success': '#4CAF50',
            'warning': '#ff9800',
            'error': '#f44336',
            'info': '#2196F3',
        }
    
    @staticmethod
    def apply_theme_to_app(app):
        """Apply global application theme (future enhancement)."""
        # Placeholder for future theming capabilities
        # Could apply dark mode, high contrast, etc.
        pass


# Export for easy importing
__all__ = ['StyleManager']