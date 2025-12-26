"""
UI tests for ExportDialog.
Tests meaningful export dialog behavior, not just widget existence.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from export import ExportDialog


class TestExportDialog:
    """Test ExportDialog core functionality."""

    def test_dialog_creation_smoke(self, qtbot):
        """Smoke test: dialog creates with expected configuration."""
        dialog = ExportDialog(frame_count=10, current_frame=5)
        qtbot.addWidget(dialog)

        assert dialog.windowTitle() == "Export Sprites"
        assert dialog.isModal()
        assert dialog.frame_count == 10
        assert dialog.current_frame == 5

    def test_export_requested_signal_exists(self, qtbot):
        """Test that exportRequested signal can be connected."""
        dialog = ExportDialog(frame_count=1)
        qtbot.addWidget(dialog)

        # Verify signal exists and can be connected
        signal_received = []
        dialog.exportRequested.connect(lambda s: signal_received.append(s))

        # Signal should be connectable without error
        assert hasattr(dialog, 'exportRequested')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
