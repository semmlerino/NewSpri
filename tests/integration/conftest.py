"""
Shared fixtures for integration tests.

Performance Note:
  The reset_singletons fixture runs before/after EVERY integration test (autouse=True).
  This ensures proper test isolation for utility managers that use the singleton pattern.
"""

import pytest

import export.core.frame_exporter as _fe_mod
import managers.recent_files_manager as _rfm_mod
import managers.settings_manager as _sm_mod


def _reset_singletons():
    """Reset singleton instances for test isolation."""
    _sm_mod._settings_instance = None
    _rfm_mod._recent_files_instance = None

    inst = _fe_mod._exporter_instance
    if inst is not None:
        worker = inst._worker
        if worker is not None and worker.isRunning():
            worker.cancel()
            if not worker.wait(2000):
                raise AssertionError(
                    "ExportWorker did not finish within 2s during teardown — "
                    "test left a real thread running"
                )
    _fe_mod._exporter_instance = None


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests to avoid state leakage.

    Note: Core managers (ActionManager, MenuManager, ShortcutManager) no longer use
    singletons - they use dependency injection. Only utility managers (SettingsManager,
    RecentFilesManager) still use the singleton pattern.
    """
    _reset_singletons()

    yield

    # Reset again after test
    _reset_singletons()
