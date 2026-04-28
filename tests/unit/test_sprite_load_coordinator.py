"""Tests for sprite load coordinator boundaries."""

from __future__ import annotations

from unittest.mock import MagicMock

from coordinators.sprite_load_coordinator import SpriteLoadCoordinator, SpriteLoadDependencies


def _make_dependencies(sprite_model: MagicMock) -> SpriteLoadDependencies:
    return SpriteLoadDependencies(
        parent=MagicMock(),
        sprite_model=sprite_model,
        frame_extractor=MagicMock(),
        auto_detection_controller=MagicMock(),
        segment_manager=MagicMock(),
        segment_controller=MagicMock(),
        canvas=MagicMock(),
        grid_view=MagicMock(),
        segment_preview=MagicMock(),
        status_bar=MagicMock(),
        info_label=MagicMock(),
        slicing_debounce_timer=MagicMock(),
        add_recent_file=MagicMock(),
        update_recent_files_menu=MagicMock(),
        update_has_frames_actions=MagicMock(),
        update_playback_for_extraction=MagicMock(),
    )


def test_coordinator_has_explicit_dependencies_instead_of_full_view() -> None:
    sprite_model = MagicMock()
    sprite_model.file_path = None
    sprite_model.load_sprite_sheet.return_value = (True, "")

    coordinator = SpriteLoadCoordinator(_make_dependencies(sprite_model))

    assert not hasattr(coordinator, "_view")
    assert coordinator.load("sprite.png") is True
    sprite_model.load_sprite_sheet.assert_called_once_with("sprite.png")


def test_load_guard_is_owned_by_coordinator() -> None:
    sprite_model = MagicMock()
    sprite_model.file_path = None
    coordinator = SpriteLoadCoordinator(_make_dependencies(sprite_model))

    def load_with_reentrant_attempt(path: str) -> tuple[bool, str]:
        assert coordinator.load("nested.png") is False
        return True, ""

    sprite_model.load_sprite_sheet.side_effect = load_with_reentrant_attempt

    assert coordinator.load("sprite.png") is True
    assert coordinator.load("again.png") is True
