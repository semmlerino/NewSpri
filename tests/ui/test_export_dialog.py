"""
UI tests for ExportDialog.
Tests meaningful export dialog behavior, not just widget existence.
"""

import pytest

from export import ExportDialog

pytestmark = pytest.mark.smoke


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
