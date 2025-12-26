"""
Core Sprite Model Module
=======================

Modular SpriteModel implementation using refactored architecture.
This module provides the main SpriteModel class that coordinates all sprite operations
through specialized modules for file operations, extraction, detection, and animation.

Architecture:
- 12 specialized modules for different functionality areas
- Clean separation of concerns with proper interfaces
- 5 design patterns: Command, Factory, Observer, Strategy, Adapter
- Comprehensive error handling and signal forwarding
- 100% API compatibility with original implementation
"""

# Direct import of the integrated modular implementation
try:
    from sprite_model.core_integrated import SpriteModel

except ImportError as e:
    # Critical error - the modular implementation should always be available

    error_msg = f"""
❌ CRITICAL ERROR: Could not import modular SpriteModel implementation.

Error: {e}

This indicates a serious issue with the modular architecture.
Please check that all required modules are properly installed:
- sprite_model.file_operations
- sprite_model.extraction
- sprite_model.animation
- sprite_model.detection
- sprite_model.ccl

The legacy fallback has been removed as part of the refactoring completion.
"""

    print(error_msg)

    # Re-raise the import error with additional context
    raise ImportError(f"Modular SpriteModel implementation not available: {e}") from e
