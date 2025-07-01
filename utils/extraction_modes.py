"""
Extraction Mode State Machine
Manages extraction mode transitions and behaviors.
Part of Phase 3 refactoring: Complex Logic Simplification.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Callable
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget, QLabel


class ExtractionMode(ABC):
    """Base class for extraction modes."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Mode name."""
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """User-friendly display name."""
        pass
    
    @property
    @abstractmethod
    def icon(self) -> str:
        """Mode icon."""
        pass
    
    @property
    @abstractmethod
    def status_color(self) -> str:
        """Status label color."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Mode description."""
        pass
    
    def on_enter(self, context: Dict):
        """Called when entering this mode."""
        self._update_ui_state(context, True)
    
    def on_exit(self, context: Dict):
        """Called when exiting this mode."""
        self._update_ui_state(context, False)
    
    def _update_ui_state(self, context: Dict, entering: bool):
        """Update UI elements for mode transition."""
        # Update status label if available
        if 'status_label' in context and context['status_label']:
            label: QLabel = context['status_label']
            if entering:
                label.setText(f"{self.icon} {self.display_name} active")
                label.setStyleSheet(f"""
                    QLabel {{
                        color: {self.status_color};
                        font-size: 11px;
                        padding: 2px 5px;
                        background-color: {self._get_bg_color()};
                        border-radius: 3px;
                    }}
                """)
            else:
                label.setText("")
                label.setStyleSheet("")
        
        # Update widget states
        self._configure_widgets(context, entering)
    
    def _get_bg_color(self) -> str:
        """Get background color based on status color."""
        color_map = {
            '#2e7d32': '#e8f5e9',  # Green -> Light green
            '#1976d2': '#e3f2fd',  # Blue -> Light blue
            '#d32f2f': '#ffebee',  # Red -> Light red
        }
        return color_map.get(self.status_color, '#f5f5f5')
    
    @abstractmethod
    def _configure_widgets(self, context: Dict, entering: bool):
        """Configure mode-specific widget states."""
        pass
    
    @abstractmethod
    def validate_settings(self, context: Dict) -> tuple[bool, str]:
        """Validate current settings for this mode."""
        pass


class GridExtractionMode(ExtractionMode):
    """Traditional grid-based extraction mode."""
    
    name = "grid"
    display_name = "Grid mode"
    icon = "🔲"
    status_color = "#2e7d32"
    description = "Traditional grid-based extraction for regular animation frames"
    
    def _configure_widgets(self, context: Dict, entering: bool):
        """Enable/disable grid-specific controls."""
        if entering:
            # Enable all grid-related controls
            for widget_name in ['frame_size_controls', 'offset_controls', 
                              'spacing_controls', 'grid_overlay']:
                if widget_name in context:
                    context[widget_name].setEnabled(True)
            
            # Show grid-specific presets
            if 'preset_widget' in context:
                context['preset_widget'].show()
        else:
            # Mode-specific cleanup if needed
            pass
    
    def validate_settings(self, context: Dict) -> tuple[bool, str]:
        """Validate grid extraction settings."""
        if 'frame_width' not in context or 'frame_height' not in context:
            return False, "Frame dimensions not set"
        
        width = context.get('frame_width', 0)
        height = context.get('frame_height', 0)
        
        if width <= 0 or height <= 0:
            return False, "Invalid frame dimensions"
        
        if width > 2048 or height > 2048:
            return False, "Frame dimensions too large"
        
        return True, "Grid settings valid"


class CCLExtractionMode(ExtractionMode):
    """Connected Component Labeling extraction mode."""
    
    name = "ccl"
    display_name = "CCL mode"
    icon = "🔍"
    status_color = "#1976d2"
    description = "Smart extraction using Connected Component Labeling for irregular sprites"
    
    def _configure_widgets(self, context: Dict, entering: bool):
        """Enable/disable CCL-specific controls."""
        if entering:
            # Disable manual controls not relevant for CCL
            for widget_name in ['frame_size_controls', 'spacing_controls']:
                if widget_name in context:
                    context[widget_name].setEnabled(False)
            
            # Keep offset controls enabled (still useful for CCL)
            if 'offset_controls' in context:
                context['offset_controls'].setEnabled(True)
            
            # Hide grid-specific presets
            if 'preset_widget' in context:
                context['preset_widget'].hide()
            
            # Enable CCL-specific controls if any
            if 'ccl_threshold' in context:
                context['ccl_threshold'].setEnabled(True)
        else:
            # Re-enable controls for other modes
            for widget_name in ['frame_size_controls', 'spacing_controls']:
                if widget_name in context:
                    context[widget_name].setEnabled(True)
            
            if 'preset_widget' in context:
                context['preset_widget'].show()
    
    def validate_settings(self, context: Dict) -> tuple[bool, str]:
        """Validate CCL extraction settings."""
        # CCL mainly needs the sprite sheet to be loaded
        if 'sprite_loaded' not in context or not context['sprite_loaded']:
            return False, "No sprite sheet loaded"
        
        # Check if alpha threshold is reasonable (if used)
        if 'alpha_threshold' in context:
            threshold = context['alpha_threshold']
            if not 0 <= threshold <= 255:
                return False, "Invalid alpha threshold"
        
        return True, "CCL settings valid"


class ExtractionModeStateMachine(QObject):
    """Manages extraction mode transitions and state."""
    
    # Signals
    modeChanged = Signal(str, str)  # old_mode, new_mode
    modeValidationFailed = Signal(str, str)  # mode, reason
    
    def __init__(self):
        super().__init__()
        
        # Initialize modes
        self._modes: Dict[str, ExtractionMode] = {
            'grid': GridExtractionMode(),
            'ccl': CCLExtractionMode()
        }
        
        # Current mode
        self._current_mode: Optional[ExtractionMode] = self._modes['grid']
        self._current_mode_name = 'grid'
        
        # UI context for mode operations
        self._context: Dict = {}
        
        # Transition callbacks
        self._transition_callbacks: Dict[str, Callable] = {}
    
    def register_mode(self, mode: ExtractionMode):
        """Register a new extraction mode."""
        self._modes[mode.name] = mode
    
    def set_context(self, context: Dict):
        """Set UI context for mode operations."""
        self._context.update(context)
    
    def transition_to(self, new_mode_name: str) -> bool:
        """
        Transition to a new mode.
        
        Returns:
            bool: True if transition successful, False otherwise
        """
        if new_mode_name not in self._modes:
            raise ValueError(f"Unknown mode: {new_mode_name}")
        
        if new_mode_name == self._current_mode_name:
            return True  # Already in this mode
        
        new_mode = self._modes[new_mode_name]
        old_mode_name = self._current_mode_name
        
        # Validate new mode settings
        valid, reason = new_mode.validate_settings(self._context)
        if not valid:
            self.modeValidationFailed.emit(new_mode_name, reason)
            return False
        
        # Perform transition
        if self._current_mode:
            self._current_mode.on_exit(self._context)
        
        self._current_mode = new_mode
        self._current_mode_name = new_mode_name
        
        new_mode.on_enter(self._context)
        
        # Execute transition callbacks
        if new_mode_name in self._transition_callbacks:
            self._transition_callbacks[new_mode_name]()
        
        # Emit signal
        self.modeChanged.emit(old_mode_name, new_mode_name)
        
        return True
    
    def get_current_mode(self) -> ExtractionMode:
        """Get current extraction mode."""
        return self._current_mode
    
    def get_current_mode_name(self) -> str:
        """Get current mode name."""
        return self._current_mode_name
    
    def get_available_modes(self) -> Dict[str, ExtractionMode]:
        """Get all available modes."""
        return self._modes.copy()
    
    def on_transition_to(self, mode_name: str, callback: Callable):
        """Register callback for mode transition."""
        self._transition_callbacks[mode_name] = callback
    
    def update_context(self, **kwargs):
        """Update context values."""
        self._context.update(kwargs)
    
    def validate_current_mode(self) -> tuple[bool, str]:
        """Validate settings for current mode."""
        if self._current_mode:
            return self._current_mode.validate_settings(self._context)
        return False, "No mode selected"


# Custom mode example
class AdvancedCCLMode(ExtractionMode):
    """Advanced CCL mode with extra features."""
    
    name = "advanced_ccl"
    display_name = "Advanced CCL"
    icon = "🔬"
    status_color = "#d32f2f"
    description = "Advanced CCL with clustering and sprite grouping"
    
    def _configure_widgets(self, context: Dict, entering: bool):
        """Configure advanced CCL controls."""
        # Similar to CCL but with additional options
        if entering:
            # Enable advanced options
            if 'clustering_controls' in context:
                context['clustering_controls'].setEnabled(True)
            if 'grouping_controls' in context:
                context['grouping_controls'].setEnabled(True)
    
    def validate_settings(self, context: Dict) -> tuple[bool, str]:
        """Validate advanced CCL settings."""
        # Basic CCL validation plus additional checks
        if 'sprite_loaded' not in context or not context['sprite_loaded']:
            return False, "No sprite sheet loaded"
        
        if 'min_cluster_size' in context:
            if context['min_cluster_size'] < 1:
                return False, "Invalid minimum cluster size"
        
        return True, "Advanced CCL settings valid"