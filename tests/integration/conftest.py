"""
Shared fixtures for integration tests.

Performance Note:
  The reset_singletons fixture runs before/after EVERY integration test (autouse=True).
  This ensures proper test isolation for utility managers that use the singleton pattern.
"""

import pytest


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests to avoid state leakage.

    Note: Core managers (ActionManager, MenuManager, ShortcutManager) no longer use
    singletons - they use dependency injection. Only utility managers (SettingsManager,
    RecentFilesManager) still use the singleton pattern.
    """
    # Import reset functions for utility singletons
    from managers.settings_manager import reset_settings_manager
    from managers.recent_files_manager import reset_recent_files_manager
    from export.core.frame_exporter import reset_frame_exporter

    # Reset utility managers
    reset_settings_manager()
    reset_recent_files_manager()
    reset_frame_exporter()

    yield

    # Reset again after test
    reset_settings_manager()
    reset_recent_files_manager()
    reset_frame_exporter()
