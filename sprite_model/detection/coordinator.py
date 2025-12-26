#!/usr/bin/env python3
"""
Detection Coordinator Module
============================

Comprehensive auto-detection workflow that coordinates margin, frame size, and spacing detection.
Extracted from monolithic SpriteModel for better separation of concerns and testability.
"""


from PySide6.QtGui import QPixmap

from .frame_detector import FrameDetector
from .margin_detector import MarginDetector
from .spacing_detector import SpacingDetector


class DetectionResult:
    """Container for detection results."""

    def __init__(self):
        self.frame_width: int = 0
        self.frame_height: int = 0
        self.offset_x: int = 0
        self.offset_y: int = 0
        self.spacing_x: int = 0
        self.spacing_y: int = 0
        self.success: bool = False
        self._confidence: float = 0.0
        self.messages: list = []

    @property
    def confidence(self) -> float:
        """Get confidence score."""
        return self._confidence

    @confidence.setter
    def confidence(self, value: float) -> None:
        """Set confidence score, clamping to valid range [0.0, 1.0]."""
        self._confidence = max(0.0, min(1.0, float(value)))


class DetectionCoordinator:
    """
    Comprehensive auto-detection coordinator.

    Orchestrates margin detection, frame size detection, and spacing detection
    in optimal order with cross-validation and fallback strategies.
    """

    def __init__(self):
        """Initialize detection coordinator with sub-detectors."""
        self.frame_detector = FrameDetector()
        self.margin_detector = MarginDetector()
        self.spacing_detector = SpacingDetector()

    def comprehensive_auto_detect(self, sprite_sheet: QPixmap, sprite_sheet_path: str | None = None) -> tuple[bool, str, DetectionResult]:
        """
        Comprehensive one-click auto-detection workflow.
        Detects margins, frame size, and spacing in optimal order with cross-validation.

        Args:
            sprite_sheet: Source sprite sheet pixmap
            sprite_sheet_path: Optional path for CCL detection integration

        Returns:
            Tuple of (success, detailed_status_message, detection_result)
        """
        if not sprite_sheet or sprite_sheet.isNull():
            return False, "No sprite sheet provided", DetectionResult()

        result = DetectionResult()
        results = []
        confidence_scores = []
        overall_success = True

        try:
            # Step 1: Detect margins first (affects all other calculations)
            results.append("🔍 Step 1: Detecting margins...")

            try:
                margin_success, offset_x, offset_y, margin_msg = self.margin_detector.detect_margins(sprite_sheet)
                result.offset_x = offset_x
                result.offset_y = offset_y
            except Exception as e:
                margin_success, offset_x, offset_y, margin_msg = False, 0, 0, f"Error: {e!s}"
                result.offset_x = 0
                result.offset_y = 0

            if margin_success:
                results.append(f"   ✓ {margin_msg}")
                confidence_scores.append(0.9)  # Margin detection is usually reliable
            else:
                results.append(f"   ⚠ Margin detection failed: {margin_msg}")
                results.append("   → Using default margins (0, 0)")
                confidence_scores.append(0.3)

            # Step 2: Detect optimal frame size with multiple fallback strategies
            results.append("\n🔍 Step 2: Detecting frame size...")

            # Try content-based detection first
            try:
                content_success, frame_width, frame_height, content_msg = self.frame_detector.detect_content_based(sprite_sheet)

                if content_success:
                    result.frame_width = frame_width
                    result.frame_height = frame_height
                    results.append(f"   ✓ {content_msg}")
                    confidence_scores.append(0.95)  # Content-based detection is very reliable
                else:
                    results.append(f"   ⚠ Content-based detection failed: {content_msg}")
                    results.append("   → Falling back to rectangular detection...")

                    # Fall back to rectangular detection
                    try:
                        rect_success, frame_width, frame_height, frame_msg = self.frame_detector.detect_rectangular_frames(sprite_sheet)

                        if rect_success:
                            result.frame_width = frame_width
                            result.frame_height = frame_height
                            results.append(f"   ✓ {frame_msg}")
                            # Extract confidence from message if available
                            if "score:" in frame_msg:
                                confidence_scores.append(0.8)
                            else:
                                confidence_scores.append(0.7)
                        else:
                            results.append(f"   ⚠ Rectangular detection failed: {frame_msg}")
                            results.append("   → Falling back to basic square detection...")

                            # Try basic square detection as final fallback
                            try:
                                basic_success, basic_width, basic_height, basic_msg = self.frame_detector.detect_frame_size(sprite_sheet)
                                if basic_success:
                                    result.frame_width = basic_width
                                    result.frame_height = basic_height
                                    results.append(f"   ✓ Basic detection: {basic_msg}")
                                    confidence_scores.append(0.6)
                                else:
                                    results.append(f"   ✗ All frame detection failed: {basic_msg}")
                                    overall_success = False
                                    confidence_scores.append(0.1)
                            except Exception as e:
                                results.append(f"   ✗ Basic detection error: {e!s}")
                                overall_success = False
                                confidence_scores.append(0.1)
                    except Exception as e:
                        results.append(f"   ✗ Rectangular detection error: {e!s}")
                        overall_success = False
                        confidence_scores.append(0.1)
            except Exception as e:
                results.append(f"   ✗ Content-based detection error: {e!s}")
                overall_success = False
                confidence_scores.append(0.1)

            # Step 3: Detect spacing (only if frame size detection succeeded)
            if result.frame_width > 0 and result.frame_height > 0:
                results.append("\n🔍 Step 3: Detecting frame spacing...")

                try:
                    spacing_success, spacing_x, spacing_y, spacing_msg = self.spacing_detector.detect_spacing(
                        sprite_sheet, result.frame_width, result.frame_height, result.offset_x, result.offset_y)

                    if spacing_success:
                        result.spacing_x = spacing_x
                        result.spacing_y = spacing_y
                        results.append(f"   ✓ {spacing_msg}")
                        # Extract confidence from message
                        if "confidence: high" in spacing_msg:
                            confidence_scores.append(0.9)
                        elif "confidence: medium" in spacing_msg:
                            confidence_scores.append(0.7)
                        else:
                            confidence_scores.append(0.5)
                    else:
                        results.append(f"   ⚠ Spacing detection failed: {spacing_msg}")
                        results.append("   → Using default spacing (0, 0)")
                        result.spacing_x = 0
                        result.spacing_y = 0
                        confidence_scores.append(0.3)
                except Exception as e:
                    results.append(f"   ✗ Spacing detection error: {e!s}")
                    results.append("   → Using default spacing (0, 0)")
                    result.spacing_x = 0
                    result.spacing_y = 0
                    confidence_scores.append(0.2)
            else:
                results.append("\n⚠ Step 3: Skipped spacing detection (no valid frame size)")
                confidence_scores.append(0.1)

            # Step 4: Cross-validation and final verification
            results.append("\n🔍 Step 4: Cross-validation...")
            try:
                validation_success, validation_msg = self._validate_detection_consistency(sprite_sheet, result)

                if validation_success:
                    results.append(f"   ✓ {validation_msg}")
                    confidence_scores.append(0.8)
                else:
                    results.append(f"   ⚠ {validation_msg}")
                    confidence_scores.append(0.4)
            except Exception as e:
                results.append(f"   ✗ Validation error: {e!s}")
                confidence_scores.append(0.3)

            # Step 5: Calculate overall confidence and summary
            overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
            confidence_text = "high" if overall_confidence >= 0.8 else "medium" if overall_confidence >= 0.6 else "low"

            results.append("\n📊 Overall Result:")
            results.append(f"   • Frame Size: {result.frame_width}×{result.frame_height}")
            results.append(f"   • Margins: X={result.offset_x}, Y={result.offset_y}")
            results.append(f"   • Spacing: X={result.spacing_x}, Y={result.spacing_y}")
            results.append(f"   • Confidence: {confidence_text} ({overall_confidence:.1%})")

            if overall_success and overall_confidence >= 0.6:
                results.append("   🎉 Auto-detection completed successfully!")
                result.success = True
            elif overall_confidence >= 0.4:
                results.append("   ⚠ Auto-detection completed with warnings")
                result.success = True
            else:
                results.append("   ❌ Auto-detection completed with low confidence")
                overall_success = False
                result.success = False

            result.confidence = overall_confidence
            result.messages = results

            return overall_success, "\n".join(results), result

        except Exception as e:
            error_msg = f"❌ Comprehensive auto-detection failed: {e!s}"
            results.append(error_msg)
            result.messages = results
            return False, "\n".join(results), result

    def _validate_detection_consistency(self, sprite_sheet: QPixmap, result: DetectionResult) -> tuple[bool, str]:
        """
        Validate that all detected parameters work together consistently.

        Args:
            sprite_sheet: Source sprite sheet pixmap
            result: Detection result to validate

        Returns:
            Tuple of (success, status_message)
        """
        try:
            # Check basic parameter validity
            if result.frame_width <= 0 or result.frame_height <= 0:
                return False, "Invalid frame dimensions detected"

            # Check that frame fits within sheet dimensions after applying offsets
            sheet_width = sprite_sheet.width()
            sheet_height = sprite_sheet.height()

            if result.offset_x + result.frame_width > sheet_width:
                return False, f"Frame width + margin ({result.offset_x + result.frame_width}) exceeds sheet width ({sheet_width})"

            if result.offset_y + result.frame_height > sheet_height:
                return False, f"Frame height + margin ({result.offset_y + result.frame_height}) exceeds sheet height ({sheet_height})"

            # Calculate expected frame count
            available_width = sheet_width - result.offset_x
            available_height = sheet_height - result.offset_y

            if result.spacing_x > 0:
                frames_x = (available_width + result.spacing_x) // (result.frame_width + result.spacing_x)
            else:
                frames_x = available_width // result.frame_width

            if result.spacing_y > 0:
                frames_y = (available_height + result.spacing_y) // (result.frame_height + result.spacing_y)
            else:
                frames_y = available_height // result.frame_height

            expected_frames = frames_x * frames_y

            # Check if frame count is reasonable
            from config import Config
            if expected_frames < Config.FrameExtraction.MIN_REASONABLE_FRAMES:
                return False, f"Too few frames detected ({expected_frames})"

            if expected_frames > Config.FrameExtraction.MAX_REASONABLE_FRAMES:
                return False, f"Too many frames detected ({expected_frames})"

            return True, f"Validation passed: {frames_x}×{frames_y} = {expected_frames} frames"

        except Exception as e:
            return False, f"Validation error: {e!s}"


# Convenience function for direct usage
def comprehensive_auto_detect(sprite_sheet: QPixmap, sprite_sheet_path: str | None = None) -> tuple[bool, str, DetectionResult]:
    """
    Convenience function for comprehensive auto-detection.

    Args:
        sprite_sheet: Source sprite sheet pixmap
        sprite_sheet_path: Optional path for CCL detection integration

    Returns:
        Tuple of (success, detailed_status_message, detection_result)
    """
    coordinator = DetectionCoordinator()
    return coordinator.comprehensive_auto_detect(sprite_sheet, sprite_sheet_path)
