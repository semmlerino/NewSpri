"""
Core Sprite Model Module
=======================

This is a placeholder during the refactoring process.
The full SpriteModel class will be moved here piece by piece.
"""

# For now, import the original SpriteModel from the main file
# This maintains backwards compatibility during the refactor
import sys
import os

# Add parent directory to path to import original sprite_model
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

try:
    # Import directly from the original file to avoid circular import
    sys.path.insert(0, parent_dir)
    import sprite_model_original
    
    # For now, just re-export the original class
    # TODO: Move functionality here piece by piece  
    SpriteModel = sprite_model_original.SpriteModel
    
except ImportError:
    # Fallback if original can't be imported
    print("Warning: Could not import original SpriteModel")
    
    # Create a minimal placeholder
    from PySide6.QtCore import QObject, Signal
    
    class SpriteModel(QObject):
        """Minimal placeholder SpriteModel during refactor."""
        
        frameChanged = Signal(int, int)
        dataLoaded = Signal(str)
        extractionCompleted = Signal(int)
        playbackStateChanged = Signal(bool)
        errorOccurred = Signal(str)
        configurationChanged = Signal()
        
        def __init__(self):
            super().__init__()
            print("Warning: Using placeholder SpriteModel")