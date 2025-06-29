"""
Command Pattern Implementation
Provides undo/redo capability for sprite viewer operations.
Part of Phase 4 refactoring: Design Pattern Implementation.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional, Dict
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal


class Command(ABC):
    """Abstract base class for all commands."""
    
    @abstractmethod
    def execute(self) -> bool:
        """
        Execute the command.
        
        Returns:
            bool: True if execution successful, False otherwise
        """
        pass
    
    @abstractmethod
    def undo(self) -> bool:
        """
        Undo the command.
        
        Returns:
            bool: True if undo successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get human-readable description of the command."""
        pass
    
    def can_merge_with(self, other: 'Command') -> bool:
        """
        Check if this command can be merged with another.
        Used for combining related commands (e.g., multiple zoom steps).
        """
        return False
    
    def merge(self, other: 'Command') -> 'Command':
        """Merge this command with another. Override in subclasses."""
        raise NotImplementedError("This command doesn't support merging")


@dataclass
class CommandContext:
    """Context object passed to commands for execution."""
    canvas: Any  # Avoid circular imports
    model: Any
    controllers: Dict[str, Any]
    ui_elements: Dict[str, Any]


# Concrete Command Implementations

class ZoomCommand(Command):
    """Command for zoom operations."""
    
    def __init__(self, context: CommandContext, zoom_factor: float):
        self.context = context
        self.new_zoom = zoom_factor
        self.old_zoom = None
        self.description = f"Zoom to {zoom_factor:.1f}x"
    
    def execute(self) -> bool:
        try:
            canvas = self.context.canvas
            self.old_zoom = canvas.zoom_factor
            canvas.set_zoom(self.new_zoom)
            return True
        except Exception as e:
            print(f"Zoom command failed: {e}")
            return False
    
    def undo(self) -> bool:
        try:
            if self.old_zoom is not None:
                self.context.canvas.set_zoom(self.old_zoom)
                return True
            return False
        except Exception as e:
            print(f"Zoom undo failed: {e}")
            return False
    
    def get_description(self) -> str:
        return self.description
    
    def can_merge_with(self, other: Command) -> bool:
        return isinstance(other, ZoomCommand)
    
    def merge(self, other: 'ZoomCommand') -> 'ZoomCommand':
        """Merge consecutive zoom commands."""
        merged = ZoomCommand(self.context, other.new_zoom)
        merged.old_zoom = self.old_zoom  # Keep original zoom level
        merged.description = f"Zoom from {self.old_zoom:.1f}x to {other.new_zoom:.1f}x"
        return merged


class PanCommand(Command):
    """Command for pan operations."""
    
    def __init__(self, context: CommandContext, delta_x: float, delta_y: float):
        self.context = context
        self.delta_x = delta_x
        self.delta_y = delta_y
        self.description = f"Pan by ({delta_x:.0f}, {delta_y:.0f})"
    
    def execute(self) -> bool:
        try:
            canvas = self.context.canvas
            canvas.pan_offset[0] += self.delta_x
            canvas.pan_offset[1] += self.delta_y
            canvas.update()
            return True
        except Exception as e:
            print(f"Pan command failed: {e}")
            return False
    
    def undo(self) -> bool:
        try:
            canvas = self.context.canvas
            canvas.pan_offset[0] -= self.delta_x
            canvas.pan_offset[1] -= self.delta_y
            canvas.update()
            return True
        except Exception as e:
            print(f"Pan undo failed: {e}")
            return False
    
    def get_description(self) -> str:
        return self.description
    
    def can_merge_with(self, other: Command) -> bool:
        return isinstance(other, PanCommand)
    
    def merge(self, other: 'PanCommand') -> 'PanCommand':
        """Merge consecutive pan commands."""
        total_x = self.delta_x + other.delta_x
        total_y = self.delta_y + other.delta_y
        merged = PanCommand(self.context, total_x, total_y)
        return merged


class FrameChangeCommand(Command):
    """Command for changing the current frame."""
    
    def __init__(self, context: CommandContext, new_frame: int):
        self.context = context
        self.new_frame = new_frame
        self.old_frame = None
        self.description = f"Go to frame {new_frame + 1}"  # 1-indexed for display
    
    def execute(self) -> bool:
        try:
            model = self.context.model
            self.old_frame = model.current_frame_index
            model.set_current_frame(self.new_frame)
            return True
        except Exception as e:
            print(f"Frame change command failed: {e}")
            return False
    
    def undo(self) -> bool:
        try:
            if self.old_frame is not None:
                self.context.model.set_current_frame(self.old_frame)
                return True
            return False
        except Exception as e:
            print(f"Frame change undo failed: {e}")
            return False
    
    def get_description(self) -> str:
        return self.description


class SettingsChangeCommand(Command):
    """Command for changing extraction settings."""
    
    def __init__(self, context: CommandContext, setting_name: str, 
                 new_value: Any, old_value: Any = None):
        self.context = context
        self.setting_name = setting_name
        self.new_value = new_value
        self.old_value = old_value
        self.description = f"Change {setting_name}"
    
    def execute(self) -> bool:
        try:
            model = self.context.model
            
            # Store old value if not provided
            if self.old_value is None:
                self.old_value = getattr(model, f"_{self.setting_name}")
            
            # Apply new value
            setter = getattr(model, f"set_{self.setting_name}", None)
            if setter:
                setter(self.new_value)
            else:
                setattr(model, f"_{self.setting_name}", self.new_value)
            
            # Trigger re-extraction if needed
            if hasattr(model, 'extract_frames'):
                model.extract_frames()
            
            return True
        except Exception as e:
            print(f"Settings change command failed: {e}")
            return False
    
    def undo(self) -> bool:
        try:
            if self.old_value is not None:
                model = self.context.model
                setter = getattr(model, f"set_{self.setting_name}", None)
                if setter:
                    setter(self.old_value)
                else:
                    setattr(model, f"_{self.setting_name}", self.old_value)
                
                if hasattr(model, 'extract_frames'):
                    model.extract_frames()
                
                return True
            return False
        except Exception as e:
            print(f"Settings undo failed: {e}")
            return False
    
    def get_description(self) -> str:
        return f"{self.description}: {self.new_value}"


class MacroCommand(Command):
    """Command that executes multiple commands as one unit."""
    
    def __init__(self, commands: List[Command], description: str):
        self.commands = commands
        self.description = description
        self.executed_commands = []
    
    def execute(self) -> bool:
        """Execute all commands in sequence."""
        self.executed_commands = []
        
        for command in self.commands:
            if command.execute():
                self.executed_commands.append(command)
            else:
                # Rollback on failure
                self.undo()
                return False
        
        return True
    
    def undo(self) -> bool:
        """Undo all executed commands in reverse order."""
        success = True
        
        for command in reversed(self.executed_commands):
            if not command.undo():
                success = False
        
        self.executed_commands = []
        return success
    
    def get_description(self) -> str:
        return self.description


class CommandManager(QObject):
    """Manages command execution, undo, and redo."""
    
    # Signals
    commandExecuted = Signal(Command)
    commandUndone = Signal(Command)
    commandRedone = Signal(Command)
    historyChanged = Signal()
    
    def __init__(self, max_history: int = 100):
        super().__init__()
        self._history: List[Command] = []
        self._redo_stack: List[Command] = []
        self._max_history = max_history
        self._macro_recording: Optional[List[Command]] = None
        self._merge_timeout_ms = 500  # Time window for merging commands
        self._last_command_time = 0
    
    def execute(self, command: Command) -> bool:
        """
        Execute a command and add it to history.
        
        Returns:
            bool: True if execution successful
        """
        if not command.execute():
            return False
        
        # Check for command merging
        import time
        current_time = time.time() * 1000
        
        if (self._history and 
            current_time - self._last_command_time < self._merge_timeout_ms and
            self._history[-1].can_merge_with(command)):
            # Merge with previous command
            merged = self._history[-1].merge(command)
            self._history[-1] = merged
        else:
            # Add as new command
            self._history.append(command)
            
            # Trim history if needed
            if len(self._history) > self._max_history:
                self._history.pop(0)
        
        self._last_command_time = current_time
        
        # Clear redo stack
        self._redo_stack.clear()
        
        # Add to macro if recording
        if self._macro_recording is not None:
            self._macro_recording.append(command)
        
        self.commandExecuted.emit(command)
        self.historyChanged.emit()
        
        return True
    
    def undo(self) -> bool:
        """Undo the last command."""
        if not self.can_undo():
            return False
        
        command = self._history.pop()
        
        if command.undo():
            self._redo_stack.append(command)
            self.commandUndone.emit(command)
            self.historyChanged.emit()
            return True
        else:
            # Restore to history if undo failed
            self._history.append(command)
            return False
    
    def redo(self) -> bool:
        """Redo the last undone command."""
        if not self.can_redo():
            return False
        
        command = self._redo_stack.pop()
        
        if command.execute():
            self._history.append(command)
            self.commandRedone.emit(command)
            self.historyChanged.emit()
            return True
        else:
            # Restore to redo stack if execute failed
            self._redo_stack.append(command)
            return False
    
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self._history) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self._redo_stack) > 0
    
    def get_undo_description(self) -> str:
        """Get description of command to be undone."""
        if self.can_undo():
            return self._history[-1].get_description()
        return ""
    
    def get_redo_description(self) -> str:
        """Get description of command to be redone."""
        if self.can_redo():
            return self._redo_stack[-1].get_description()
        return ""
    
    def clear_history(self):
        """Clear all command history."""
        self._history.clear()
        self._redo_stack.clear()
        self.historyChanged.emit()
    
    def start_macro(self, description: str):
        """Start recording a macro command."""
        self._macro_recording = []
        self._macro_description = description
    
    def end_macro(self) -> Optional[MacroCommand]:
        """End macro recording and return the macro command."""
        if self._macro_recording is None:
            return None
        
        if len(self._macro_recording) > 0:
            macro = MacroCommand(self._macro_recording, self._macro_description)
            self._macro_recording = None
            return macro
        
        self._macro_recording = None
        return None
    
    def is_recording_macro(self) -> bool:
        """Check if currently recording a macro."""
        return self._macro_recording is not None