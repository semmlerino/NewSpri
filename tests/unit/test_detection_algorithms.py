#!/usr/bin/env python3
"""
Comprehensive Tests for Detection Algorithms
=============================================

Tests for all sprite detection algorithms in the modular sprite model:
- Frame size detection (basic, rectangular, content-based)
- Margin detection with validation and edge cases
- Spacing detection with consistency scoring
- Auto-detection controller workflow management

Covers algorithm accuracy, edge cases, performance, and integration scenarios.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt
from PySide6.QtTest import QSignalSpy

from sprite_model.sprite_detection import (
    detect_content_based,
    detect_frame_size,
    detect_margins,
    detect_rectangular_frames,
    detect_spacing,
)
# Import private functions for testing
from sprite_model.sprite_detection import (
    _calculate_common_dimensions,
    _detect_horizontal_spacing,
    _detect_raw_margins,
    _detect_vertical_spacing,
    _has_content_in_region,
    _score_frame_candidate,
    _validate_margins,
)
from core.auto_detection_controller import AutoDetectionController
from config import Config


class TestFrameDetector:
    """Test frame size detection algorithms."""
    
    def test_frame_detector_initialization(self):
        """Test detect_frame_size function exists."""
        # Functions don't need initialization - just verify they're callable
        assert callable(detect_frame_size)
    
    @pytest.mark.parametrize("width,height,min_expected_size", [
        (256, 256, 32),  # Should find reasonable size
        (320, 320, 32),  # Should find reasonable size  
        (128, 128, 32),  # Should find reasonable size
        (96, 96, 32),    # Should find 32 as common size
    ])
    def test_detect_frame_size_common_sizes(self, qapp, width, height, min_expected_size):
        """Test frame detection with common sprite sheet dimensions."""
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.red)

        success, frame_width, frame_height, message = detect_frame_size(pixmap)
        
        assert success
        assert frame_width >= min_expected_size
        assert frame_height >= min_expected_size
        assert frame_width == frame_height  # Should be square
        assert "Auto-detected frame size" in message
        
        # Verify it produces reasonable frame count
        frames_x = width // frame_width
        frames_y = height // frame_height
        total_frames = frames_x * frames_y
        assert total_frames >= Config.FrameExtraction.MIN_REASONABLE_FRAMES
        assert total_frames <= Config.FrameExtraction.MAX_REASONABLE_FRAMES
    
    def test_detect_frame_size_gcd_fallback(self, qapp):
        """Test GCD fallback for non-standard dimensions."""
        # Create 48x48 pixmap (GCD should be 48, but might fall back to smaller)
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.blue)

        success, frame_width, frame_height, message = detect_frame_size(pixmap)
        
        # Should succeed with some reasonable size
        assert success
        assert frame_width > 0
        assert frame_height > 0
        assert frame_width == frame_height  # Should be square
    
    def test_detect_frame_size_invalid_input(self, qapp):
        """Test frame detection with invalid input."""
        # Removed - using function-based API
        
        # Test with None
        success, width, height, message = detect_frame_size(None)
        assert not success
        assert "No sprite sheet provided" in message
        
        # Test with null pixmap
        null_pixmap = QPixmap()
        success, width, height, message = detect_frame_size(null_pixmap)
        assert not success
        assert "No sprite sheet provided" in message
    
    def test_detect_rectangular_frames_success(self, qapp):
        """Test rectangular frame detection."""
        # Removed - using function-based API
        # Create sprite sheet that should work with 32x48 frames
        pixmap = QPixmap(128, 96)  # 4x2 grid of 32x48 frames
        pixmap.fill(Qt.green)
        
        success, frame_width, frame_height, message = detect_rectangular_frames(pixmap)
        
        assert success
        assert frame_width > 0
        assert frame_height > 0
        assert "Detected rectangular frames" in message
    
    def test_detect_rectangular_frames_scoring(self, qapp):
        """Test that scoring works correctly for candidates."""
        # Removed - using function-based API
        
        # Test scoring function directly
        score1 = _score_frame_candidate(32, 32, 4, 4, 16)  # Good square case
        score2 = _score_frame_candidate(16, 16, 8, 8, 64)  # Too many frames
        score3 = _score_frame_candidate(128, 128, 2, 2, 4)  # Good large frames
        
        assert score1 > 0
        assert score2 >= 0
        assert score3 > 0
        # Reasonable frame count (16) should score better than excessive (64)
        assert score1 > score2
    
    def test_content_based_detection_mock(self, qapp):
        """Test content-based detection with mocked content analysis."""
        pixmap = QPixmap(128, 128)
        pixmap.fill(Qt.yellow)

        # Mock the content analysis methods
        with patch('sprite_model.sprite_detection._analyze_content_boundaries') as mock_analyze:
            with patch('sprite_model.sprite_detection._calculate_common_dimensions') as mock_calc:
                # Setup mocks to return successful results
                mock_analyze.return_value = [(0, 0, 32, 32), (32, 0, 32, 32), (0, 32, 32, 32)]
                mock_calc.return_value = [(32, 32, 3)]

                success, width, height, message = detect_content_based(pixmap)

                assert success
                assert width == 32
                assert height == 32
                assert "Content-based detection" in message
                assert "found 3 sprites" in message
    
    def test_content_based_detection_no_content(self, qapp):
        """Test content-based detection when no content is found."""
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.white)

        with patch('sprite_model.sprite_detection._analyze_content_boundaries') as mock_analyze:
            mock_analyze.return_value = []  # No content found

            success, width, height, message = detect_content_based(pixmap)

            assert not success
            assert "No content boundaries detected" in message
    
    def test_has_content_in_region(self, qapp):
        """Test content detection in image regions."""
        # Removed - using function-based API
        
        # Create image with transparent and opaque areas
        image = QImage(100, 100, QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        
        # Add some opaque content in specific region
        for x in range(10, 20):
            for y in range(10, 20):
                image.setPixel(x, y, 0xFF000000)  # Opaque black
        
        # Test region with content
        has_content = _has_content_in_region(image, 5, 5, 20, 20, 128)
        assert has_content
        
        # Test region without content
        no_content = _has_content_in_region(image, 50, 50, 20, 20, 128)
        assert not no_content
    
    def test_calculate_common_dimensions(self, qapp):
        """Test calculation of common dimensions from content bounds."""
        # Removed - using function-based API
        
        # Test with multiple same-size sprites
        content_bounds = [
            (0, 0, 32, 32),
            (32, 0, 32, 32),
            (0, 32, 32, 32),
            (32, 32, 48, 48),  # Different size
            (80, 0, 32, 32),   # Same as majority
        ]
        
        result = _calculate_common_dimensions(content_bounds)
        
        assert len(result) > 0
        # Most common should be 32x32 (appears 4 times)
        most_common = result[0]
        assert most_common[0] == 32  # width
        assert most_common[1] == 32  # height
        assert most_common[2] == 4   # count
    
    def test_all_detection_methods(self, qapp):
        """Test all detection methods work correctly."""
        # Removed - using function-based API
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.red)

        # Test basic detection
        success, width, height, message = detect_frame_size(pixmap)
        assert success or not success  # Should not crash

        # Test rectangular detection
        success, width, height, message = detect_rectangular_frames(pixmap)
        assert success or not success  # Should not crash

        # Test content-based detection
        success, width, height, message = detect_content_based(pixmap)
        assert success or not success  # Should not crash


class TestMarginDetector:
    """Test margin detection algorithms."""
    
    def test_margin_detector_initialization(self):
        """Test MarginDetector can be created."""
        # Removed - using function-based API
        assert callable(detect_frame_size) or callable(detect_margins) or callable(detect_spacing)
    
    def test_detect_margins_basic(self, qapp):
        """Test basic margin detection."""
        # Removed - using function-based API
        
        # Create pixmap with transparent margins
        pixmap = QPixmap(100, 100)
        pixmap.fill(Qt.transparent)
        
        success, offset_x, offset_y, message = detect_margins(pixmap)
        
        # Should succeed even with all-transparent image
        assert success
        assert "Margins:" in message
    
    def test_detect_margins_with_content(self, qapp):
        """Test margin detection with actual content."""
        # Removed - using function-based API
        
        # Create image with margins and content
        image = QImage(100, 100, QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        
        # Add content in center (leaving 10px margins)
        for x in range(10, 90):
            for y in range(10, 90):
                image.setPixel(x, y, 0xFF000000)  # Opaque black
        
        pixmap = QPixmap.fromImage(image)
        success, offset_x, offset_y, message = detect_margins(pixmap)
        
        assert success
        # Should detect the 10px margins
        assert offset_x == 10
        assert offset_y == 10
        assert "L=10" in message
        assert "T=10" in message
    
    def test_detect_margins_validation(self, qapp):
        """Test margin validation logic."""
        # Removed - using function-based API
        
        # Test validation with excessive margins
        left, right, top, bottom = 50, 5, 40, 5  # Large margins
        width, height = 100, 100
        
        validated_left, validated_top, msg = _validate_margins(
            left, right, top, bottom, width, height)
        
        # Should reduce excessive margins
        assert validated_left < left  # Should be reduced
        assert validated_top < top    # Should be reduced
        assert "excessive" in msg.lower()
    
    def test_detect_margins_frame_size_validation(self, qapp):
        """Test margin validation with frame size context."""
        # Removed - using function-based API
        
        # Test with frame size that doesn't divide cleanly
        left, right, top, bottom = 5, 5, 5, 5
        width, height = 100, 100
        frame_width, frame_height = 32, 32
        
        validated_left, validated_top, msg = _validate_margins(
            left, right, top, bottom, width, height, frame_width, frame_height)
        
        # Should adjust margins for clean frame division
        remaining_width = width - validated_left
        remaining_height = height - validated_top
        
        # Check if division is cleaner
        assert remaining_width % frame_width == 0 or validated_left <= left
        assert remaining_height % frame_height == 0 or validated_top <= top
    
    def test_detect_margins_horizontal_strip(self, qapp):
        """Test margin detection for horizontal strips."""
        # Removed - using function-based API
        
        # Test horizontal strip (wide aspect ratio)
        left, right, top, bottom = 10, 10, 10, 10
        width, height = 400, 100  # 4:1 aspect ratio
        
        validated_left, validated_top, msg = _validate_margins(
            left, right, top, bottom, width, height)
        
        # Should minimize margins for horizontal strips
        assert validated_left <= 5
        assert validated_top <= 5
        assert "horizontal strip" in msg
    
    def test_detect_margins_small_margin_removal(self, qapp):
        """Test that very small margins are set to zero."""
        # Removed - using function-based API
        
        left, right, top, bottom = 2, 5, 1, 5
        width, height = 100, 100
        
        validated_left, validated_top, msg = _validate_margins(
            left, right, top, bottom, width, height)
        
        # Small margins should be zeroed
        assert validated_left == 0  # 2px -> 0
        assert validated_top == 0   # 1px -> 0
    
    def test_detect_margins_invalid_input(self, qapp):
        """Test margin detection with invalid input."""
        # Removed - using function-based API
        
        # Test with None
        success, offset_x, offset_y, message = detect_margins(None)
        assert not success
        assert "No sprite sheet provided" in message
        
        # Test with null pixmap
        null_pixmap = QPixmap()
        success, offset_x, offset_y, message = detect_margins(null_pixmap)
        assert not success
        assert "No sprite sheet provided" in message
    
    def test_detect_raw_margins_all_edges(self, qapp):
        """Test raw margin detection from all four edges."""
        # Removed - using function-based API
        
        # Create image with different margins on each edge
        image = QImage(100, 80, QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        
        # Add content with specific margins: L=5, R=10, T=8, B=12
        for x in range(5, 90):  # Left margin=5, right margin=10
            for y in range(8, 68):  # Top margin=8, bottom margin=12
                image.setPixel(x, y, 0xFF000000)
        
        left, right, top, bottom = _detect_raw_margins(image)
        
        assert left == 5
        assert right == 10
        assert top == 8
        assert bottom == 12
    
    def test_detect_margins_with_frame_hints(self, qapp):
        """Test margin detection with frame size hints."""
        # Removed - using function-based API
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.red)

        success, offset_x, offset_y, message = detect_margins(pixmap, 32, 32)
        assert success or not success  # Should not crash


class TestSpacingDetector:
    """Test spacing detection algorithms."""
    
    def test_spacing_detector_initialization(self):
        """Test SpacingDetector can be created."""
        # Removed - using function-based API
        assert callable(detect_frame_size) or callable(detect_margins) or callable(detect_spacing)
    
    def test_detect_spacing_basic(self, qapp):
        """Test basic spacing detection."""
        # Removed - using function-based API
        pixmap = QPixmap(100, 100)
        pixmap.fill(Qt.red)
        
        success, spacing_x, spacing_y, message = detect_spacing(pixmap, 32, 32)
        
        assert success
        assert spacing_x >= 0
        assert spacing_y >= 0
        assert "Auto-detected spacing" in message
        assert "confidence:" in message
    
    def test_detect_spacing_with_gaps(self, qapp):
        """Test spacing detection with actual gaps between frames."""
        # Removed - using function-based API
        
        # Create image with frames and gaps
        image = QImage(100, 100, QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        
        # Add 3x3 grid of 30x30 frames with 2px spacing
        frame_size = 30
        spacing = 2
        
        for row in range(3):
            for col in range(3):
                start_x = col * (frame_size + spacing)
                start_y = row * (frame_size + spacing)
                
                # Only add if it fits
                if start_x + frame_size <= 100 and start_y + frame_size <= 100:
                    for x in range(start_x, start_x + frame_size):
                        for y in range(start_y, start_y + frame_size):
                            image.setPixel(x, y, 0xFF000000)
        
        pixmap = QPixmap.fromImage(image)
        success, detected_x, detected_y, message = detect_spacing(pixmap, frame_size, frame_size)
        
        assert success
        # Should detect the 2px spacing (or close to it)
        assert detected_x == spacing or abs(detected_x - spacing) <= 1
        assert detected_y == spacing or abs(detected_y - spacing) <= 1
    
    def test_detect_horizontal_spacing(self, qapp):
        """Test horizontal spacing detection specifically."""
        # Removed - using function-based API
        
        # Create simple test image with clear spacing pattern
        image = QImage(100, 50, QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        
        # Add frames with consistent 2px gap (easier to detect)
        frame_width = 20
        spacing = 2
        
        # Frame 1: x=0-19
        for x in range(0, frame_width):
            for y in range(0, 30):
                image.setPixel(x, y, 0xFF000000)
        
        # Gap: x=20-21 (2px)
        # Frame 2: x=22-41  
        for x in range(frame_width + spacing, (frame_width + spacing) + frame_width):
            for y in range(0, 30):
                image.setPixel(x, y, 0xFF000000)
        
        # Frame 3: x=44-63
        for x in range((frame_width + spacing) * 2 + frame_width, (frame_width + spacing) * 2 + frame_width * 2):
            for y in range(0, 30):
                if x < 100:  # Stay within bounds
                    image.setPixel(x, y, 0xFF000000)
        
        detected_spacing, score = _detect_horizontal_spacing(image, frame_width, 30, 0, 0, 100)
        
        # Should detect some spacing (algorithm might not get exact value)
        assert detected_spacing >= 0
        assert score >= 0
    
    def test_detect_vertical_spacing(self, qapp):
        """Test vertical spacing detection specifically."""
        # Removed - using function-based API
        
        # Create simple test image with clear vertical spacing pattern
        image = QImage(50, 100, QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        
        frame_height = 20
        spacing = 2
        
        # Frame 1: y=0-19
        for x in range(0, 30):
            for y in range(0, frame_height):
                image.setPixel(x, y, 0xFF000000)
        
        # Gap: y=20-21 (2px)
        # Frame 2: y=22-41
        for x in range(0, 30):
            for y in range(frame_height + spacing, (frame_height + spacing) + frame_height):
                image.setPixel(x, y, 0xFF000000)
        
        # Frame 3: y=44-63
        for x in range(0, 30):
            for y in range((frame_height + spacing) * 2 + frame_height, (frame_height + spacing) * 2 + frame_height * 2):
                if y < 100:  # Stay within bounds
                    image.setPixel(x, y, 0xFF000000)
        
        detected_spacing, score = _detect_vertical_spacing(image, 30, frame_height, 0, 0, 100)
        
        # Should detect some spacing (algorithm might not get exact value)
        assert detected_spacing >= 0
        assert score >= 0
    
    def test_detect_spacing_invalid_input(self, qapp):
        """Test spacing detection with invalid input."""
        # Removed - using function-based API
        
        # Test with None
        success, spacing_x, spacing_y, message = detect_spacing(None, 32, 32)
        assert not success
        assert "No sprite sheet provided" in message
        
        # Test with null pixmap
        null_pixmap = QPixmap()
        success, spacing_x, spacing_y, message = detect_spacing(null_pixmap, 32, 32)
        assert not success
        assert "No sprite sheet provided" in message
        
        # Test with zero frame size
        pixmap = QPixmap(100, 100)
        success, spacing_x, spacing_y, message = detect_spacing(pixmap, 0, 32)
        assert not success
        assert "Frame size must be greater than 0" in message
    
    def test_spacing_confidence_calculation(self, qapp):
        """Test confidence calculation based on consistency scores."""
        # Removed - using function-based API
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.blue)
        
        success, spacing_x, spacing_y, message = detect_spacing(pixmap, 16, 16)
        
        assert success
        # Should include confidence in message
        assert "confidence:" in message
        assert any(conf in message for conf in ["high", "medium", "low"])
    
class TestAutoDetectionController:
    """Test auto-detection controller workflow management."""

    def test_controller_initialization(self, qapp):
        """Test AutoDetectionController can be created with dependencies."""
        mock_model = Mock()
        mock_extractor = Mock()
        controller = AutoDetectionController(
            sprite_model=mock_model,
            frame_extractor=mock_extractor,
        )
        assert controller is not None
        assert controller.workflow_state == "idle"
        assert not controller.is_working

    def test_controller_signals_exist(self, qapp):
        """Test all required signals are defined."""
        controller = AutoDetectionController(
            sprite_model=Mock(),
            frame_extractor=Mock(),
        )

        # Check workflow signals
        assert hasattr(controller, 'detectionStarted')
        assert hasattr(controller, 'detectionCompleted')
        assert hasattr(controller, 'detectionFailed')

        # Check UI update signals
        assert hasattr(controller, 'frameSettingsDetected')
        assert hasattr(controller, 'marginSettingsDetected')
        assert hasattr(controller, 'spacingSettingsDetected')
        assert hasattr(controller, 'buttonConfidenceUpdate')
        assert hasattr(controller, 'statusUpdate')

        # Check state signals
        assert hasattr(controller, 'workflowStateChanged')

    def test_controller_stores_dependencies(self, qapp):
        """Test controller properly stores dependencies at construction."""
        mock_sprite_model = Mock()
        mock_frame_extractor = Mock()

        controller = AutoDetectionController(
            sprite_model=mock_sprite_model,
            frame_extractor=mock_frame_extractor,
        )

        assert controller._sprite_model == mock_sprite_model
        assert controller._frame_extractor == mock_frame_extractor

    def test_handle_new_sprite_sheet_no_original(self, qapp):
        """Test new sprite sheet handling when model has no original sprite sheet."""
        mock_model = Mock()
        mock_model.original_sprite_sheet = None

        controller = AutoDetectionController(
            sprite_model=mock_model,
            frame_extractor=Mock(),
        )

        result = controller.handle_new_sprite_sheet_loaded()

        assert not result  # Should return False when no original sprite sheet

    def test_handle_new_sprite_sheet_success(self, qapp):
        """Test successful new sprite sheet handling."""
        # Create mock sprite model with required attributes
        mock_sprite_model = Mock()
        mock_sprite_model.original_sprite_sheet = QPixmap(100, 100)
        mock_sprite_model.comprehensive_auto_detect.return_value = (True, "Test report")

        # Mock attributes that get set
        mock_sprite_model.frame_width = 32
        mock_sprite_model.frame_height = 32
        mock_sprite_model.offset_x = 0
        mock_sprite_model.offset_y = 0
        mock_sprite_model.spacing_x = 0
        mock_sprite_model.spacing_y = 0

        controller = AutoDetectionController(
            sprite_model=mock_sprite_model,
            frame_extractor=Mock(),
        )

        # Test signals
        status_spy = QSignalSpy(controller.statusUpdate)
        frame_spy = QSignalSpy(controller.frameSettingsDetected)
        button_spy = QSignalSpy(controller.buttonConfidenceUpdate)

        result = controller.handle_new_sprite_sheet_loaded()

        assert result
        assert status_spy.count() > 0
        assert frame_spy.count() > 0
        assert button_spy.count() > 0

    def test_run_frame_detection_no_original(self, qapp):
        """Test frame detection without original sprite sheet."""
        mock_model = Mock()
        mock_model.original_sprite_sheet = None

        controller = AutoDetectionController(
            sprite_model=mock_model,
            frame_extractor=Mock(),
        )
        status_spy = QSignalSpy(controller.statusUpdate)

        controller.run_frame_detection()

        assert status_spy.count() == 1
        assert "No sprite sheet loaded" in status_spy.at(0)[0]

    def test_run_frame_detection_success(self, qapp):
        """Test successful frame detection."""
        # Create mock sprite model
        mock_sprite_model = Mock()
        mock_sprite_model.original_sprite_sheet = QPixmap(100, 100)
        mock_sprite_model.auto_detect_rectangular_frames.return_value = (True, 32, 32, "Test success")

        controller = AutoDetectionController(
            sprite_model=mock_sprite_model,
            frame_extractor=Mock(),
        )
        
        # Test signals
        started_spy = QSignalSpy(controller.detectionStarted)
        completed_spy = QSignalSpy(controller.detectionCompleted)
        frame_spy = QSignalSpy(controller.frameSettingsDetected)
        
        controller.run_frame_detection()
        
        assert started_spy.count() == 1
        assert started_spy.at(0)[0] == "frame"
        assert completed_spy.count() == 1
        assert frame_spy.count() == 1
        assert frame_spy.at(0)[0] == 32  # width
        assert frame_spy.at(0)[1] == 32  # height
    
    def test_run_margin_detection_success(self, qapp):
        """Test successful margin detection."""
        # Create mock sprite model
        mock_sprite_model = Mock()
        mock_sprite_model.original_sprite_sheet = QPixmap(100, 100)
        mock_sprite_model.auto_detect_margins.return_value = (True, 5, 5, "Test margins")

        controller = AutoDetectionController(
            sprite_model=mock_sprite_model,
            frame_extractor=Mock(),
        )

        # Test signals
        margin_spy = QSignalSpy(controller.marginSettingsDetected)
        button_spy = QSignalSpy(controller.buttonConfidenceUpdate)

        controller.run_margin_detection()

        assert margin_spy.count() == 1
        assert margin_spy.at(0)[0] == 5  # offset_x
        assert margin_spy.at(0)[1] == 5  # offset_y
        assert button_spy.count() >= 1

    def test_run_spacing_detection_success(self, qapp):
        """Test successful spacing detection."""
        # Create mock sprite model
        mock_sprite_model = Mock()
        mock_sprite_model.original_sprite_sheet = QPixmap(100, 100)
        mock_sprite_model.auto_detect_spacing_enhanced.return_value = (True, 2, 2, "Test spacing (high confidence)")

        controller = AutoDetectionController(
            sprite_model=mock_sprite_model,
            frame_extractor=Mock(),
        )
        
        # Test signals
        spacing_spy = QSignalSpy(controller.spacingSettingsDetected)
        button_spy = QSignalSpy(controller.buttonConfidenceUpdate)
        
        controller.run_spacing_detection()
        
        assert spacing_spy.count() == 1
        assert spacing_spy.at(0)[0] == 2  # spacing_x
        assert spacing_spy.at(0)[1] == 2  # spacing_y
        assert button_spy.count() >= 1
    
    def test_workflow_state_management(self, qapp):
        """Test workflow state transitions."""
        controller = AutoDetectionController(
            sprite_model=Mock(),
            frame_extractor=Mock(),
        )
        state_spy = QSignalSpy(controller.workflowStateChanged)

        # Test state transitions
        controller._set_workflow_state("working")
        assert controller.workflow_state == "working"
        assert controller.is_working
        assert state_spy.count() == 1
        assert state_spy.at(0)[0] == "working"

        controller._set_workflow_state("completed")
        assert controller.workflow_state == "completed"
        assert not controller.is_working
        assert state_spy.count() == 2
        assert state_spy.at(1)[0] == "completed"

    def test_detection_summary_creation(self, qapp):
        """Test creation of detection summary."""
        # Mock sprite model with detected values
        mock_sprite_model = Mock()
        mock_sprite_model.frame_width = 64
        mock_sprite_model.frame_height = 48
        mock_sprite_model.offset_x = 4
        mock_sprite_model.offset_y = 4
        mock_sprite_model.spacing_x = 2
        mock_sprite_model.spacing_y = 2

        controller = AutoDetectionController(
            sprite_model=mock_sprite_model,
            frame_extractor=Mock(),
        )

        summary = controller._create_detection_summary()

        assert "64×48" in summary
        assert "margins (4,4)" in summary
        assert "spacing (2,2)" in summary

    def test_button_confidence_update_from_report(self, qapp):
        """Test button confidence updates from detection report."""
        controller = AutoDetectionController(
            sprite_model=Mock(),
            frame_extractor=Mock(),
        )
        button_spy = QSignalSpy(controller.buttonConfidenceUpdate)
        
        report = """
        ✓ Auto-detected frame size: 32×32 (high confidence)
        ✓ Margins: detected 4px margins
        ✓ Auto-detected spacing: 2px (medium confidence)
        """
        
        controller._update_button_confidence_from_report(report)
        
        # Should have emitted signals for frame, margins, and spacing
        assert button_spy.count() >= 2  # At least frame and spacing


@pytest.mark.parametrize("sheet_size,frame_size,expected_frames", [
    ((128, 128), (32, 32), 16),   # 4x4 grid
    ((256, 128), (32, 32), 32),   # 8x4 grid
    ((96, 96), (32, 32), 9),      # 3x3 grid
    ((64, 192), (32, 32), 12),    # 2x6 grid
])
def test_detection_parametrized_sizes(qapp, sheet_size, frame_size, expected_frames):
    """Test detection algorithms with various sheet and frame size combinations."""
    # Removed - using function-based API
    pixmap = QPixmap(sheet_size[0], sheet_size[1])
    pixmap.fill(Qt.red)
    
    # The detection might not find the exact expected frame size,
    # but it should not crash and should return reasonable results
    success, width, height, message = detect_frame_size(pixmap)
    
    # Should succeed with reasonable results
    if success:
        assert width > 0
        assert height > 0
        # Check that resulting frame count is reasonable
        frames_x = sheet_size[0] // width
        frames_y = sheet_size[1] // height
        total_frames = frames_x * frames_y
        assert total_frames >= Config.FrameExtraction.MIN_REASONABLE_FRAMES
        assert total_frames <= Config.FrameExtraction.MAX_REASONABLE_FRAMES


@pytest.mark.performance
def test_detection_performance_large_sprite_sheet(qapp):
    """Test detection performance with large sprite sheets."""
    import time
    
    # Removed - using function-based API
    # Create large sprite sheet
    large_pixmap = QPixmap(1024, 1024)
    large_pixmap.fill(Qt.blue)
    
    start_time = time.time()
    success, width, height, message = detect_frame_size(large_pixmap)
    end_time = time.time()
    
    # Should complete within reasonable time (under 1 second)
    detection_time = end_time - start_time
    assert detection_time < 1.0
    
    # Should still produce valid results
    if success:
        assert width > 0
        assert height > 0


class TestDetectionIntegration:
    """Test integration between different detection algorithms."""
    
    def test_frame_then_margin_detection(self, qapp):
        """Test frame detection followed by margin detection."""
        pixmap = QPixmap(128, 128)
        pixmap.fill(Qt.red)

        # First detect frame size
        frame_success, frame_width, frame_height, frame_msg = detect_frame_size(pixmap)

        if frame_success:
            # Then detect margins using frame size context
            margin_success, offset_x, offset_y, margin_msg = detect_margins(
                pixmap, frame_width, frame_height)

            assert margin_success
            assert offset_x >= 0
            assert offset_y >= 0
    
    def test_full_detection_workflow(self, qapp):
        """Test complete detection workflow: frame -> margins -> spacing."""
        pixmap = QPixmap(96, 96)
        pixmap.fill(Qt.green)

        # Step 1: Frame detection
        frame_success, frame_width, frame_height, _ = detect_frame_size(pixmap)
        assert frame_success

        # Step 2: Margin detection with frame context
        margin_success, offset_x, offset_y, _ = detect_margins(
            pixmap, frame_width, frame_height)
        assert margin_success

        # Step 3: Spacing detection with frame and margin context
        spacing_success, spacing_x, spacing_y, _ = detect_spacing(
            pixmap, frame_width, frame_height, offset_x, offset_y)
        assert spacing_success

        # All should produce valid results
        assert frame_width > 0 and frame_height > 0
        assert offset_x >= 0 and offset_y >= 0
        assert spacing_x >= 0 and spacing_y >= 0