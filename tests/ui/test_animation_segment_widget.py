"""Tests for ui/animation_segment_widget.py"""

from dataclasses import dataclass, field
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from ui.animation_segment_widget import AnimationSegmentSelector, create_segment_selector


@dataclass
class MockSegment:
    """Mock segment data matching AnimationSegment structure."""

    name: str
    start_frame: int
    end_frame: int
    color: QColor = field(default_factory=lambda: QColor(233, 30, 99))

    @property
    def frame_count(self) -> int:
        return self.end_frame - self.start_frame + 1


@pytest.fixture
def mock_manager():
    """Create a mock AnimationSegmentManager with test segments."""
    manager = MagicMock()
    manager.get_all_segments.return_value = [
        MockSegment("Walk", 0, 7),
        MockSegment("Run", 8, 15),
        MockSegment("Jump", 16, 23),
    ]

    def get_segment_impl(name: str) -> MockSegment | None:
        segments = {seg.name: seg for seg in manager.get_all_segments.return_value}
        return segments.get(name)

    manager.get_segment.side_effect = get_segment_impl
    return manager


@pytest.fixture
def empty_manager():
    """Create a mock manager with no segments."""
    manager = MagicMock()
    manager.get_all_segments.return_value = []
    manager.get_segment.return_value = None
    return manager


class TestAnimationSegmentSelectorConstruction:
    """Test widget construction scenarios."""

    def test_construction_with_none_manager(self, qtbot):
        """Widget constructs without error when segment_manager=None."""
        widget = AnimationSegmentSelector(segment_manager=None)
        qtbot.addWidget(widget)

        assert widget.segment_manager is None
        assert widget._selected_segments == []
        assert not widget.has_segments()

    def test_construction_with_empty_manager(self, qtbot, empty_manager):
        """Widget constructs with empty manager and shows no segments UI."""
        widget = AnimationSegmentSelector(segment_manager=empty_manager)
        qtbot.addWidget(widget)

        assert widget.segment_manager is empty_manager
        assert not widget.has_segments()
        assert not hasattr(widget, "segment_list")  # List not created when empty

    def test_construction_with_segments(self, qtbot, mock_manager):
        """Widget constructs with manager containing segments."""
        widget = AnimationSegmentSelector(segment_manager=mock_manager)
        qtbot.addWidget(widget)

        assert widget.segment_manager is mock_manager
        assert widget.has_segments()
        assert hasattr(widget, "segment_list")


class TestSegmentListPopulation:
    """Test segment list display and population."""

    def test_no_segments_state(self, qtbot, empty_manager):
        """When manager has no segments, has_segments() returns False."""
        widget = AnimationSegmentSelector(segment_manager=empty_manager)
        qtbot.addWidget(widget)

        assert not widget.has_segments()
        assert widget.get_selected_segments() == []

    def test_segment_list_population(self, qtbot, mock_manager):
        """When manager returns segments, the list widget shows them."""
        widget = AnimationSegmentSelector(segment_manager=mock_manager)
        qtbot.addWidget(widget)

        assert widget.segment_list.count() == 3
        assert "Walk" in widget.segment_list.item(0).text()
        assert "Frames 0-7" in widget.segment_list.item(0).text()
        assert "Run" in widget.segment_list.item(1).text()
        assert "Jump" in widget.segment_list.item(2).text()

    def test_segment_item_data(self, qtbot, mock_manager):
        """Segment items store name in UserRole data."""
        widget = AnimationSegmentSelector(segment_manager=mock_manager)
        qtbot.addWidget(widget)

        item0 = widget.segment_list.item(0)
        assert item0.data(Qt.ItemDataRole.UserRole) == "Walk"

        item1 = widget.segment_list.item(1)
        assert item1.data(Qt.ItemDataRole.UserRole) == "Run"


class TestSegmentSelection:
    """Test segment selection and retrieval."""

    def test_no_selection_by_default(self, qtbot, mock_manager):
        """Initially no segments are selected."""
        widget = AnimationSegmentSelector(segment_manager=mock_manager)
        qtbot.addWidget(widget)

        assert widget.get_selected_segments() == []
        assert not widget.has_selected_segments()

    def test_select_single_segment(self, qtbot, mock_manager):
        """Selecting a segment updates get_selected_segments()."""
        widget = AnimationSegmentSelector(segment_manager=mock_manager)
        qtbot.addWidget(widget)

        widget.segment_list.item(0).setSelected(True)
        qtbot.wait(10)  # Allow selection change signal to process

        selected = widget.get_selected_segments()
        assert "Walk" in selected
        assert len(selected) == 1
        assert widget.has_selected_segments()

    def test_select_multiple_segments(self, qtbot, mock_manager):
        """Multiple segments can be selected."""
        widget = AnimationSegmentSelector(segment_manager=mock_manager)
        qtbot.addWidget(widget)

        widget.segment_list.item(0).setSelected(True)
        widget.segment_list.item(2).setSelected(True)
        qtbot.wait(10)

        selected = widget.get_selected_segments()
        assert "Walk" in selected
        assert "Jump" in selected
        assert len(selected) == 2

    def test_deselect_segment(self, qtbot, mock_manager):
        """Deselecting updates selection list."""
        widget = AnimationSegmentSelector(segment_manager=mock_manager)
        qtbot.addWidget(widget)

        widget.segment_list.item(0).setSelected(True)
        qtbot.wait(10)
        assert widget.has_selected_segments()

        widget.segment_list.item(0).setSelected(False)
        qtbot.wait(10)

        assert not widget.has_selected_segments()
        assert widget.get_selected_segments() == []


class TestSelectionControls:
    """Test select all and clear buttons."""

    def test_select_all_button(self, qtbot, mock_manager):
        """Clicking select all checks all items."""
        widget = AnimationSegmentSelector(segment_manager=mock_manager)
        qtbot.addWidget(widget)

        widget._select_all_segments()
        qtbot.wait(10)

        selected = widget.get_selected_segments()
        assert len(selected) == 3
        assert "Walk" in selected
        assert "Run" in selected
        assert "Jump" in selected

    def test_clear_button(self, qtbot, mock_manager):
        """Clicking clear unchecks all items."""
        widget = AnimationSegmentSelector(segment_manager=mock_manager)
        qtbot.addWidget(widget)

        widget._select_all_segments()
        qtbot.wait(10)
        assert widget.has_selected_segments()

        widget._clear_selection()
        qtbot.wait(10)

        assert not widget.has_selected_segments()
        assert widget.get_selected_segments() == []

    def test_selection_summary_updates(self, qtbot, mock_manager):
        """Selection summary label updates with selection changes."""
        widget = AnimationSegmentSelector(segment_manager=mock_manager)
        qtbot.addWidget(widget)

        assert "0 of 3 segments selected" in widget.selection_summary.text()

        widget.segment_list.item(0).setSelected(True)
        qtbot.wait(10)

        assert "1 of 3 segments selected" in widget.selection_summary.text()

        widget._select_all_segments()
        qtbot.wait(10)

        assert "3 of 3 segments selected" in widget.selection_summary.text()


class TestHasSelectedSegments:
    """Test has_selected_segments() method."""

    def test_returns_false_when_none_selected(self, qtbot, mock_manager):
        """Returns False when no segments are selected."""
        widget = AnimationSegmentSelector(segment_manager=mock_manager)
        qtbot.addWidget(widget)

        assert not widget.has_selected_segments()

    def test_returns_true_when_segments_selected(self, qtbot, mock_manager):
        """Returns True when segments are selected."""
        widget = AnimationSegmentSelector(segment_manager=mock_manager)
        qtbot.addWidget(widget)

        widget.segment_list.item(0).setSelected(True)
        qtbot.wait(10)

        assert widget.has_selected_segments()


class TestExportSettings:
    """Test get_export_settings() method."""

    def test_export_settings_with_segments(self, qtbot, mock_manager):
        """Returns dict with expected keys when segments available."""
        widget = AnimationSegmentSelector(segment_manager=mock_manager)
        qtbot.addWidget(widget)

        widget.segment_list.item(0).setSelected(True)
        widget.segment_list.item(1).setSelected(True)
        qtbot.wait(10)

        settings = widget.get_export_settings()

        assert isinstance(settings, dict)
        assert "selected_segments" in settings
        assert "segment_mode" in settings
        assert "segment_mode_index" in settings
        assert "include_metadata" in settings

        assert "Walk" in settings["selected_segments"]
        assert "Run" in settings["selected_segments"]
        assert isinstance(settings["include_metadata"], bool)

    def test_export_settings_no_segments(self, qtbot, empty_manager):
        """Returns empty dict when no segments available."""
        widget = AnimationSegmentSelector(segment_manager=empty_manager)
        qtbot.addWidget(widget)

        settings = widget.get_export_settings()

        assert settings == {}

    def test_export_settings_segment_mode_values(self, qtbot, mock_manager):
        """segment_mode reflects combo box selection."""
        widget = AnimationSegmentSelector(segment_manager=mock_manager)
        qtbot.addWidget(widget)

        # Default should be first item
        settings = widget.get_export_settings()
        assert settings["segment_mode_index"] == 0
        assert "Individual segments" in settings["segment_mode"]

        # Change to second mode
        widget.segment_mode_combo.setCurrentIndex(1)
        settings = widget.get_export_settings()
        assert settings["segment_mode_index"] == 1
        assert "Combined sprite sheet" in settings["segment_mode"]

    def test_export_settings_metadata_checkbox(self, qtbot, mock_manager):
        """include_metadata reflects checkbox state."""
        widget = AnimationSegmentSelector(segment_manager=mock_manager)
        qtbot.addWidget(widget)

        # Should default to checked
        settings = widget.get_export_settings()
        assert settings["include_metadata"] is True

        # Uncheck
        widget.include_metadata_check.setChecked(False)
        settings = widget.get_export_settings()
        assert settings["include_metadata"] is False


class TestSegmentInfoDisplay:
    """Test segment information display functionality."""

    def test_info_updates_on_selection(self, qtbot, mock_manager):
        """Segment info text updates when selection changes."""
        widget = AnimationSegmentSelector(segment_manager=mock_manager)
        qtbot.addWidget(widget)

        widget.segment_list.item(0).setSelected(True)
        qtbot.wait(10)

        info_text = widget.segment_info.toPlainText()
        assert "Walk" in info_text
        assert "8 frames" in info_text or "0-7" in info_text

    def test_info_shows_multiple_segments(self, qtbot, mock_manager):
        """Segment info shows all selected segments."""
        widget = AnimationSegmentSelector(segment_manager=mock_manager)
        qtbot.addWidget(widget)

        widget.segment_list.item(0).setSelected(True)
        widget.segment_list.item(1).setSelected(True)
        qtbot.wait(10)

        info_text = widget.segment_info.toPlainText()
        assert "Walk" in info_text
        assert "Run" in info_text
        assert "Total:" in info_text


class TestSignalEmission:
    """Test signal emission on selection changes."""

    def test_selection_changed_signal_emitted(self, qtbot, mock_manager):
        """segmentSelectionChanged signal emits with selected names."""
        widget = AnimationSegmentSelector(segment_manager=mock_manager)
        qtbot.addWidget(widget)

        with qtbot.waitSignal(widget.segmentSelectionChanged, timeout=1000) as blocker:
            widget.segment_list.item(0).setSelected(True)

        emitted_segments = blocker.args[0]
        assert "Walk" in emitted_segments

    def test_signal_emits_on_clear(self, qtbot, mock_manager):
        """Signal emits when clearing selection."""
        widget = AnimationSegmentSelector(segment_manager=mock_manager)
        qtbot.addWidget(widget)

        widget.segment_list.item(0).setSelected(True)
        qtbot.wait(10)

        with qtbot.waitSignal(widget.segmentSelectionChanged, timeout=1000) as blocker:
            widget._clear_selection()

        emitted_segments = blocker.args[0]
        assert emitted_segments == []


class TestFactoryFunction:
    """Test create_segment_selector factory function."""

    def test_factory_returns_widget_instance(self, qtbot):
        """create_segment_selector() returns AnimationSegmentSelector instance."""
        widget = create_segment_selector(segment_manager=None)
        qtbot.addWidget(widget)

        assert isinstance(widget, AnimationSegmentSelector)

    def test_factory_with_manager(self, qtbot, mock_manager):
        """Factory function passes manager correctly."""
        widget = create_segment_selector(segment_manager=mock_manager)
        qtbot.addWidget(widget)

        assert widget.segment_manager is mock_manager
        assert widget.has_segments()


class TestUpdateSegmentList:
    """Test dynamic segment list updates."""

    def test_update_clears_previous_segments(self, qtbot, mock_manager):
        """Updating segment list clears previous items."""
        widget = AnimationSegmentSelector(segment_manager=mock_manager)
        qtbot.addWidget(widget)

        initial_count = widget.segment_list.count()
        assert initial_count == 3

        # Change manager return value
        mock_manager.get_all_segments.return_value = [MockSegment("NewSegment", 0, 5)]

        widget._update_segment_list()

        assert widget.segment_list.count() == 1
        assert "NewSegment" in widget.segment_list.item(0).text()

    def test_update_preserves_selection_summary(self, qtbot, mock_manager):
        """Updating segment list updates selection summary."""
        widget = AnimationSegmentSelector(segment_manager=mock_manager)
        qtbot.addWidget(widget)

        widget._update_segment_list()

        assert "0 of 3 segments selected" in widget.selection_summary.text()
