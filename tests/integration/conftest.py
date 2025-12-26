"""
Shared fixtures for integration tests.

Performance Note:
  The reset_singletons fixture runs before/after EVERY integration test (autouse=True).
  This adds ~14 function calls per test but ensures proper test isolation.
  If test count grows significantly, consider making this opt-in via a marker.
"""

import pytest


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests to avoid Qt object reuse."""
    # Import reset functions for all singletons
    from managers.action_manager import reset_actionmanager
    from managers.menu_manager import reset_menu_manager
    from managers.shortcut_manager import reset_shortcut_manager
    from managers.settings_manager import reset_settings_manager
    from managers.recent_files_manager import reset_recent_files_manager
    from export.core.frame_exporter import reset_frame_exporter
    # Note: export_presets uses a simple compatibility wrapper, no reset needed

    # Reset all managers using their reset functions
    reset_actionmanager()
    reset_menu_manager()
    reset_shortcut_manager()
    reset_settings_manager()
    reset_recent_files_manager()
    reset_frame_exporter()

    yield

    # Reset again after test
    reset_actionmanager()
    reset_menu_manager()
    reset_shortcut_manager()
    reset_settings_manager()
    reset_recent_files_manager()
    reset_frame_exporter()