"""
Shared fixtures for integration tests.
"""

import pytest


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests to avoid Qt object reuse."""
    # Import reset functions for all singletons
    from managers.action_manager import reset_actionmanager
    from managers.menu_manager import reset_menu_manager
    from managers.shortcut_manager import reset_shortcut_manager
    
    # Reset all managers using their reset functions
    reset_actionmanager()
    reset_menu_manager()
    reset_shortcut_manager()
    
    yield
    
    # Reset again after test
    reset_actionmanager()
    reset_menu_manager()
    reset_shortcut_manager()