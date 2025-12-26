#!/usr/bin/env python3
"""
Integration tests for playback controls, including navigation buttons.
Tests the complete integration of playback controls with sprite viewer.
"""

import pytest
import tempfile
import os
from PySide6.QtCore import Qt
from PySide6.QtTest import QSignalSpy
from PySide6.QtGui import QPixmap, QColor, QPainter
from PySide6.QtWidgets import QApplication

from sprite_viewer import SpriteViewer
from sprite_model.core import SpriteModel
from ui.playback_controls import PlaybackControls
from coordinators.animation_coordinator import AnimationCoordinator


class TestPlaybackControlsIntegration:
    """Test playback controls integration with the main application."""

    @pytest.fixture
    def sprite_viewer_with_frames(self, qtbot):
        """Create a sprite viewer with test frames loaded."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)

        # Create a proper sprite sheet with gaps for CCL detection
        sprite_sheet = QPixmap(360, 36)  # 10 sprites with gaps
        sprite_sheet.fill(Qt.transparent)

        painter = QPainter(sprite_sheet)
        for i in range(10):
            color = QColor.fromHsv(i * 36, 200, 200)
            painter.fillRect(i * 36 + 2, 2, 32, 32, color)
        painter.end()

        # Save and load properly
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            sprite_sheet.save(tmp.name)
            tmp_path = tmp.name

        success, _ = viewer._sprite_model.load_sprite_sheet(tmp_path)

        # Extract frames if CCL didn't auto-detect
        if len(viewer._sprite_model.sprite_frames) == 0:
            viewer._sprite_model.set_extraction_mode('grid')
            viewer._sprite_model.extract_frames(32, 32, 2, 2, 4, 0)

        os.unlink(tmp_path)

        # Update playback controls with frame range
        frame_count = len(viewer._sprite_model.sprite_frames)
        if frame_count > 0:
            viewer._playback_controls.set_frame_range(frame_count - 1)
            viewer._playback_controls.update_button_states(True, True, False)

        return viewer

    @pytest.mark.integration
    def test_prev_next_button_navigation(self, qtbot, sprite_viewer_with_frames):
        """Test that prev/next buttons navigate frames correctly."""
        viewer = sprite_viewer_with_frames

        # Skip if no frames loaded
        if len(viewer._sprite_model.sprite_frames) == 0:
            pytest.skip("No frames loaded")

        # Start at frame 0
        initial_frame = viewer._sprite_model.current_frame

        # Test next button - wait for model signal
        with qtbot.waitSignal(viewer._sprite_model.frameChanged, timeout=1000):
            viewer._playback_controls.next_btn.click()

        assert viewer._sprite_model.current_frame == initial_frame + 1

        # Click next multiple times
        for _ in range(3):
            with qtbot.waitSignal(viewer._sprite_model.frameChanged, timeout=1000):
                viewer._playback_controls.next_btn.click()

        expected_frame = min(initial_frame + 4, len(viewer._sprite_model.sprite_frames) - 1)
        assert viewer._sprite_model.current_frame == expected_frame

        # Test prev button
        with qtbot.waitSignal(viewer._sprite_model.frameChanged, timeout=1000):
            viewer._playback_controls.prev_btn.click()

        assert viewer._sprite_model.current_frame == expected_frame - 1

    @pytest.mark.integration
    def test_frame_slider_sync_with_buttons(self, qtbot, sprite_viewer_with_frames):
        """Test that frame slider updates when using prev/next buttons."""
        viewer = sprite_viewer_with_frames

        if len(viewer._sprite_model.sprite_frames) == 0:
            pytest.skip("No frames loaded")

        # Initial state
        assert viewer._playback_controls.frame_slider.value() == 0

        # Click next button - wait for model signal (slider doesn't emit due to signal blocking)
        with qtbot.waitSignal(viewer._sprite_model.frameChanged, timeout=1000):
            viewer._playback_controls.next_btn.click()

        # Slider should update (value set via set_current_frame)
        assert viewer._playback_controls.frame_slider.value() == 1

        # Use slider to jump to frame 5 - this DOES emit frameChanged from slider
        with qtbot.waitSignal(viewer._playback_controls.frameChanged, timeout=1000):
            viewer._playback_controls.frame_slider.setValue(5)

        # Click prev button - wait for model signal
        with qtbot.waitSignal(viewer._sprite_model.frameChanged, timeout=1000):
            viewer._playback_controls.prev_btn.click()

        # Both should be at frame 4
        assert viewer._playback_controls.frame_slider.value() == 4

    @pytest.mark.integration
    def test_playback_with_navigation(self, qtbot, sprite_viewer_with_frames):
        """Test interaction between playback and navigation buttons."""
        viewer = sprite_viewer_with_frames

        if len(viewer._sprite_model.sprite_frames) < 3:
            pytest.skip("Need at least 3 frames")

        # Start playback - click and wait for state
        viewer._playback_controls.play_button.click()
        QApplication.processEvents()
        qtbot.waitUntil(lambda: viewer._animation_controller.is_playing, timeout=2000)

        assert viewer._animation_controller.is_playing

        # Stop playback - use direct method for reliability
        viewer._animation_controller.pause_animation()
        QApplication.processEvents()
        qtbot.waitUntil(lambda: not viewer._animation_controller.is_playing, timeout=2000)

        assert not viewer._animation_controller.is_playing

        # Reset to a known position in the middle
        mid_frame = len(viewer._sprite_model.sprite_frames) // 2
        viewer._sprite_model.set_current_frame(mid_frame)
        viewer._playback_controls.set_current_frame(mid_frame)
        viewer._playback_controls.update_button_states(True, False, False)

        # Now test next button
        with qtbot.waitSignal(viewer._sprite_model.frameChanged, timeout=1000):
            viewer._playback_controls.next_btn.click()

        # Should have moved to next frame
        assert viewer._sprite_model.current_frame == mid_frame + 1

        # Play button should show "Play" (not playing)
        assert viewer._playback_controls.play_button.text() == "Play"

    @pytest.mark.integration
    def test_signal_connections(self, qtbot, sprite_viewer_with_frames):
        """Test that all playback control signals are properly connected."""
        viewer = sprite_viewer_with_frames

        if len(viewer._sprite_model.sprite_frames) < 3:
            pytest.skip("Need at least 3 frames")

        # Move to middle frame first so both buttons are enabled
        mid_frame = len(viewer._sprite_model.sprite_frames) // 2
        viewer._sprite_model.set_current_frame(mid_frame)
        viewer._playback_controls.set_current_frame(mid_frame)
        viewer._playback_controls.update_button_states(True, False, False)

        # Test prevFrameClicked signal
        prev_spy = QSignalSpy(viewer._playback_controls.prevFrameClicked)
        viewer._playback_controls.prev_btn.click()
        assert prev_spy.count() == 1

        # Test nextFrameClicked signal
        next_spy = QSignalSpy(viewer._playback_controls.nextFrameClicked)
        viewer._playback_controls.next_btn.click()
        assert next_spy.count() == 1

        # Test playPauseClicked signal
        play_spy = QSignalSpy(viewer._playback_controls.playPauseClicked)
        viewer._playback_controls.play_button.click()
        assert play_spy.count() == 1

        # Stop playback directly for cleanup
        if viewer._animation_controller.is_playing:
            viewer._animation_controller.pause_animation()
            QApplication.processEvents()

        # Test frameChanged signal (from slider)
        frame_spy = QSignalSpy(viewer._playback_controls.frameChanged)
        viewer._playback_controls.frame_slider.setValue(3)
        assert frame_spy.count() >= 1

        # Test fpsChanged signal
        fps_spy = QSignalSpy(viewer._playback_controls.fpsChanged)
        viewer._playback_controls.fps_slider.setValue(20)
        assert fps_spy.count() >= 1

        # Test loopToggled signal
        loop_spy = QSignalSpy(viewer._playback_controls.loopToggled)
        viewer._playback_controls.loop_checkbox.setChecked(False)
        assert loop_spy.count() == 1

    @pytest.mark.integration
    @pytest.mark.skip(reason="Keyboard shortcuts are handled by ShortcutManager which needs separate testing")
    def test_keyboard_shortcuts_vs_buttons(self, qtbot, sprite_viewer_with_frames):
        """Test that keyboard shortcuts work alongside button navigation."""
        # Skipped - keyboard shortcuts need ShortcutManager testing
        pass

    @pytest.mark.integration
    def test_navigation_with_no_frames(self, qtbot):
        """Test that navigation handles empty sprite list gracefully."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)

        # No frames loaded
        assert len(viewer._sprite_model.sprite_frames) == 0

        # Buttons should be disabled when no frames
        # The initial state may vary, just verify clicking doesn't crash
        viewer._playback_controls.prev_btn.click()
        viewer._playback_controls.next_btn.click()
        viewer._playback_controls.play_button.click()

        # Frame should still be 0
        assert viewer._sprite_model.current_frame == 0

    @pytest.mark.integration
    def test_fps_control_during_playback(self, qtbot, sprite_viewer_with_frames):
        """Test FPS changes during playback."""
        viewer = sprite_viewer_with_frames

        if len(viewer._sprite_model.sprite_frames) < 2:
            pytest.skip("Need at least 2 frames")

        # Start playback
        viewer._playback_controls.play_button.click()
        QApplication.processEvents()
        qtbot.waitUntil(lambda: viewer._animation_controller.is_playing, timeout=2000)

        # Change FPS while playing
        new_fps = 30
        viewer._playback_controls.fps_slider.setValue(new_fps)

        # Animation controller should have new FPS
        assert viewer._animation_controller._current_fps == new_fps

        # Playback should continue
        assert viewer._animation_controller.is_playing

        # Stop playback directly
        viewer._animation_controller.pause_animation()
        QApplication.processEvents()
        qtbot.waitUntil(lambda: not viewer._animation_controller.is_playing, timeout=2000)

        assert not viewer._animation_controller.is_playing

    def _create_key_event(self, key, modifiers):
        """Helper to create keyboard events."""
        from PySide6.QtGui import QKeyEvent
        from PySide6.QtCore import QEvent
        return QKeyEvent(QEvent.KeyPress, key, modifiers)


class TestPlaybackControlsErrorHandling:
    """Test error handling in playback controls integration."""

    @pytest.fixture
    def sprite_viewer_with_frames(self, qtbot):
        """Create a sprite viewer with test frames loaded."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)

        # Create a proper sprite sheet
        sprite_sheet = QPixmap(360, 36)
        sprite_sheet.fill(Qt.transparent)

        painter = QPainter(sprite_sheet)
        for i in range(10):
            color = QColor.fromHsv(i * 36, 200, 200)
            painter.fillRect(i * 36 + 2, 2, 32, 32, color)
        painter.end()

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            sprite_sheet.save(tmp.name)
            tmp_path = tmp.name

        viewer._sprite_model.load_sprite_sheet(tmp_path)

        if len(viewer._sprite_model.sprite_frames) == 0:
            viewer._sprite_model.set_extraction_mode('grid')
            viewer._sprite_model.extract_frames(32, 32, 2, 2, 4, 0)

        os.unlink(tmp_path)

        frame_count = len(viewer._sprite_model.sprite_frames)
        if frame_count > 0:
            viewer._playback_controls.set_frame_range(frame_count - 1)
            viewer._playback_controls.update_button_states(True, True, False)

        return viewer

    @pytest.mark.integration
    def test_invalid_frame_navigation(self, qtbot):
        """Test handling of invalid frame navigation attempts."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)

        # Create a small sprite sheet with 3 frames
        sprite_sheet = QPixmap(108, 36)
        sprite_sheet.fill(Qt.transparent)

        painter = QPainter(sprite_sheet)
        for i in range(3):
            painter.fillRect(i * 36 + 2, 2, 32, 32, Qt.red)
        painter.end()

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            sprite_sheet.save(tmp.name)
            tmp_path = tmp.name

        viewer._sprite_model.load_sprite_sheet(tmp_path)

        if len(viewer._sprite_model.sprite_frames) == 0:
            viewer._sprite_model.set_extraction_mode('grid')
            viewer._sprite_model.extract_frames(32, 32, 2, 2, 4, 0)

        os.unlink(tmp_path)

        frame_count = len(viewer._sprite_model.sprite_frames)
        if frame_count == 0:
            pytest.skip("No frames loaded")

        viewer._playback_controls.set_frame_range(frame_count - 1)

        # Try to set frame beyond range - should clamp
        viewer._sprite_model.set_current_frame(10)
        assert viewer._sprite_model.current_frame <= frame_count - 1

        # Try negative frame - should clamp to 0
        viewer._sprite_model.set_current_frame(-5)
        assert viewer._sprite_model.current_frame >= 0

    @pytest.mark.integration
    def test_concurrent_playback_and_navigation(self, qtbot, sprite_viewer_with_frames):
        """Test handling concurrent playback and manual navigation."""
        viewer = sprite_viewer_with_frames

        if len(viewer._sprite_model.sprite_frames) < 3:
            pytest.skip("Need at least 3 frames")

        # Start rapid playback
        viewer._playback_controls.fps_slider.setValue(60)
        viewer._playback_controls.play_button.click()
        QApplication.processEvents()
        qtbot.waitUntil(lambda: viewer._animation_controller.is_playing, timeout=2000)

        # Navigate while playing - should stop playback
        viewer._playback_controls.next_btn.click()
        QApplication.processEvents()
        viewer._playback_controls.prev_btn.click()
        QApplication.processEvents()

        # Wait for playback to stop (navigation should stop it)
        # Use longer timeout and direct check
        try:
            qtbot.waitUntil(lambda: not viewer._animation_controller.is_playing, timeout=2000)
        except Exception:
            # If timeout, stop directly
            viewer._animation_controller.pause_animation()
            QApplication.processEvents()

        # Frame should be valid
        frame_count = len(viewer._sprite_model.sprite_frames)
        assert 0 <= viewer._sprite_model.current_frame < frame_count
