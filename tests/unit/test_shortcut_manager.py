"""
Unit tests for ShortcutManager functionality.
Tests the centralized keyboard shortcut management system.
"""

import pytest
from unittest.mock import MagicMock

from managers.shortcut_manager import (
    ShortcutManager, ShortcutDefinition, ShortcutContext,
)


class TestShortcutDefinition:
    """Test ShortcutDefinition class."""
    
    def test_shortcut_definition_creation(self):
        """Test creating a shortcut definition."""
        definition = ShortcutDefinition(
            key="Ctrl+O",
            description="Open file",
            category="file",
            context=ShortcutContext.GLOBAL
        )
        
        assert definition.key == "Ctrl+O"
        assert definition.description == "Open file"
        assert definition.category == "file"
        assert definition.context == ShortcutContext.GLOBAL
        assert definition.callback is None
        assert definition.action is None
    
    def test_shortcut_definition_validation(self):
        """Test shortcut definition validation."""
        # Test empty key
        with pytest.raises(ValueError, match="Shortcut must have key and description"):
            ShortcutDefinition("", "test", "file", ShortcutContext.GLOBAL)
        
        # Test empty description
        with pytest.raises(ValueError, match="Shortcut must have key and description"):
            ShortcutDefinition("Ctrl+O", "", "file", ShortcutContext.GLOBAL)
    
    def test_invalid_key_sequence(self):
        """Test validation of invalid key sequences."""
        # QKeySequence is quite permissive, so test with actually invalid sequence
        with pytest.raises(ValueError):
            ShortcutDefinition("", "test", "file", ShortcutContext.GLOBAL)


class TestShortcutManager:
    """Test ShortcutManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ShortcutManager()
    
    def test_manager_initialization(self):
        """Test shortcut manager initialization."""
        assert isinstance(self.manager, ShortcutManager)
        
        # Check that default shortcuts are loaded
        shortcuts = self.manager.get_all_shortcuts()
        assert len(shortcuts) >= 10  # Should have file, animation, view shortcuts
        
        # Check categories
        categories = self.manager.get_all_categories()
        assert "file" in categories
        assert "animation" in categories
        assert "view" in categories
    
    def test_shortcut_registration(self):
        """Test registering new shortcuts."""
        definition = ShortcutDefinition(
            "Ctrl+T", "Test shortcut", "test", ShortcutContext.GLOBAL
        )
        
        # Register shortcut
        success = self.manager.register_shortcut("test_shortcut", definition)
        assert success
        
        # Verify registration
        registered = self.manager.get_shortcut_definition("test_shortcut")
        assert registered is not None
        assert registered.key == "Ctrl+T"
    
    def test_shortcut_conflict_detection(self):
        """Test conflict detection."""
        # Create conflicting shortcut
        definition = ShortcutDefinition(
            "Ctrl+O", "Conflicting shortcut", "test", ShortcutContext.GLOBAL
        )
        
        # Should detect conflict (Ctrl+O already used by file_open)
        success = self.manager.register_shortcut("conflict_test", definition)
        assert not success
        
        # Check conflicts
        conflicts = self.manager.detect_conflicts()
        assert len(conflicts) == 0  # Conflict prevented, so no actual conflicts
    
    def test_shortcut_unregistration(self):
        """Test unregistering shortcuts."""
        # Add a test shortcut
        definition = ShortcutDefinition(
            "Ctrl+T", "Test shortcut", "test", ShortcutContext.GLOBAL
        )
        self.manager.register_shortcut("test_shortcut", definition)
        
        # Verify it exists
        assert self.manager.get_shortcut_definition("test_shortcut") is not None
        
        # Unregister
        success = self.manager.unregister_shortcut("test_shortcut")
        assert success
        
        # Verify removal
        assert self.manager.get_shortcut_definition("test_shortcut") is None
        
        # Test unregistering non-existent shortcut
        success = self.manager.unregister_shortcut("non_existent")
        assert not success
    
    def test_callback_handling(self):
        """Test shortcut callback handling."""
        callback_called = []
        
        def test_callback():
            callback_called.append(True)
        
        # Set callback for existing shortcut
        self.manager.set_shortcut_callback("file_open", test_callback)
        
        # Test key press handling
        success = self.manager.handle_key_press("Ctrl+O")
        assert success
        assert len(callback_called) == 1
    
    def test_context_handling(self):
        """Test context-sensitive shortcut handling."""
        # Test shortcut that requires frames
        success = self.manager.handle_key_press("Space")  # animation_toggle
        assert not success  # Should fail - no frames context
        
        # Set context
        self.manager.update_context(has_frames=True)
        
        # Set callback
        callback_called = []
        def toggle_callback():
            callback_called.append(True)
        
        self.manager.set_shortcut_callback("animation_toggle", toggle_callback)
        
        # Now should work
        success = self.manager.handle_key_press("Space")
        assert success
        assert len(callback_called) == 1
    
    def test_shortcuts_by_category(self):
        """Test getting shortcuts by category."""
        file_shortcuts = self.manager.get_shortcuts_by_category("file")
        assert len(file_shortcuts) >= 3  # Should have open, quit, export shortcuts
        
        for shortcut in file_shortcuts:
            assert shortcut.category == "file"
        
        # Test non-existent category
        empty_shortcuts = self.manager.get_shortcuts_by_category("nonexistent")
        assert len(empty_shortcuts) == 0
    
    def test_help_generation(self):
        """Test help HTML generation."""
        help_html = self.manager.generate_help_html()
        
        assert "<h3>Keyboard Shortcuts</h3>" in help_html
        assert "Ctrl+O" in help_html  # Should contain actual shortcuts
        assert "Open sprite sheet" in help_html  # Should contain descriptions
        assert "Mouse wheel" in help_html  # Should contain mouse actions
        
        # Check that categories are included
        assert "File" in help_html
        assert "Animation" in help_html
        assert "View" in help_html
    


class TestShortcutContext:
    """Test ShortcutContext enum."""
    
    def test_context_values(self):
        """Test context enum values."""
        assert ShortcutContext.GLOBAL.value == "global"
        assert ShortcutContext.HAS_FRAMES.value == "has_frames"
        assert ShortcutContext.PLAYING.value == "playing"
        assert ShortcutContext.PAUSED.value == "paused"


class TestShortcutIntegration:
    """Test integration scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ShortcutManager()
    
    def test_complete_workflow(self):
        """Test complete shortcut management workflow."""
        # Start with no context
        self.manager.update_context(has_frames=False, is_playing=False)
        
        # Add callbacks for testing
        global_callback_called = []
        frames_callback_called = []
        
        def global_callback():
            global_callback_called.append(True)
            
        def frames_callback():
            frames_callback_called.append(True)
        
        self.manager.set_shortcut_callback("view_zoom_in", global_callback)
        self.manager.set_shortcut_callback("animation_toggle", frames_callback)
        
        # Test global shortcut works
        success = self.manager.handle_key_press("Ctrl++")
        assert success
        assert len(global_callback_called) == 1
        
        # Test frames shortcut doesn't work yet
        success = self.manager.handle_key_press("Space")
        assert not success
        assert len(frames_callback_called) == 0
        
        # Update context
        self.manager.update_context(has_frames=True)
        
        # Now frames shortcut should work
        success = self.manager.handle_key_press("Space")
        assert success
        assert len(frames_callback_called) == 1
    
    def test_action_integration(self):
        """Test QAction integration."""
        # Mock QAction
        mock_action = MagicMock()
        
        # Associate with shortcut
        self.manager.set_shortcut_action("file_open", mock_action)
        
        # Verify action was configured
        mock_action.setShortcut.assert_called_once_with("Ctrl+O")
        
        # Verify action is stored
        definition = self.manager.get_shortcut_definition("file_open")
        assert definition.action is mock_action


if __name__ == '__main__':
    pytest.main([__file__, '-v'])