#!/usr/bin/env python3
"""
Auto-Detection Controller
Manages auto-detection workflows and UI feedback for sprite sheet analysis.
Extracted from sprite_viewer.py to reduce complexity and improve maintainability.
"""

import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox

from sprite_model.sprite_detection import DetectionResult

if TYPE_CHECKING:
    from sprite_model import SpriteModel

logger = logging.getLogger(__name__)


class AutoDetectionController(QObject):
    """
    Controller for managing auto-detection workflows and UI feedback.
    Provides clean separation between detection logic and UI updates.
    """

    # ============================================================================
    # SIGNALS FOR UI COMMUNICATION
    # ============================================================================

    # Detection workflow signals
    detectionStarted = Signal(str)  # workflow_type: "comprehensive", "frame", "margins", "spacing"
    detectionCompleted = Signal(str, bool, str)  # workflow_type, success, message
    detectionFailed = Signal(str, str)  # workflow_type, error_message

    # UI update signals
    frameSettingsDetected = Signal(int, int)  # width, height
    marginSettingsDetected = Signal(int, int)  # offset_x, offset_y
    spacingSettingsDetected = Signal(int, int)  # spacing_x, spacing_y
    buttonConfidenceUpdate = Signal(str, str, str)  # button_type, confidence, message
    statusUpdate = Signal(str, int)  # message, timeout_ms

    def __init__(self, sprite_model: "SpriteModel"):
        """
        Initialize controller with required dependencies.

        Args:
            sprite_model: The sprite data model
        """
        super().__init__()

        # References to external components
        self._sprite_model = sprite_model

    # ============================================================================
    # MANUAL AUTO-DETECTION WORKFLOWS
    # ============================================================================

    def run_comprehensive_detection_with_dialog(self):
        """Run comprehensive auto-detection with detailed user feedback."""
        if not self._sprite_model or not self._sprite_model.original_sprite_sheet:
            self.statusUpdate.emit("No sprite sheet loaded", 3000)
            return

        self.detectionStarted.emit("comprehensive")

        try:
            # Run the comprehensive workflow
            success, result = self._sprite_model.comprehensive_auto_detect()

            # Update UI with detected values
            self._emit_detected_settings()

            # Update button confidence indicators
            self._update_button_confidence_from_result(result)

            # Show detailed results dialog
            self._show_detection_results_dialog(success, result)

            if success:
                self.detectionCompleted.emit(
                    "comprehensive", True, "Auto-detection completed successfully"
                )
            else:
                self.detectionCompleted.emit(
                    "comprehensive", False, "Auto-detection completed with issues"
                )

        except Exception as e:
            self.detectionFailed.emit("comprehensive", str(e))

    def run_frame_detection(self):
        """Run frame size auto-detection."""
        if not self._sprite_model or not self._sprite_model.original_sprite_sheet:
            self.statusUpdate.emit("No sprite sheet loaded", 3000)
            return

        self.detectionStarted.emit("frame")

        try:
            # Try enhanced rectangular detection first
            success, width, height, message = self._sprite_model.auto_detect_rectangular_frames()

            if success:
                self.frameSettingsDetected.emit(width, height)

                confidence = "medium"
                self.buttonConfidenceUpdate.emit("frame", confidence, message)
                self.statusUpdate.emit(message, 3000)
                self.detectionCompleted.emit("frame", True, message)
            else:
                self.buttonConfidenceUpdate.emit("frame", "failed", message)
                self.statusUpdate.emit(f"Frame detection failed: {message}", 3000)
                self.detectionFailed.emit("frame", message)

        except Exception as e:
            self.detectionFailed.emit("frame", str(e))

    def run_margin_detection(self):
        """Run margin auto-detection."""
        if not self._sprite_model or not self._sprite_model.original_sprite_sheet:
            self.statusUpdate.emit("No sprite sheet loaded", 3000)
            return

        self.detectionStarted.emit("margins")

        try:
            success, offset_x, offset_y, message = self._sprite_model.auto_detect_margins()

            if success:
                self.marginSettingsDetected.emit(offset_x, offset_y)

                # Margin detection confidence based on results
                confidence = "high" if offset_x > 0 or offset_y > 0 else "medium"
                self.buttonConfidenceUpdate.emit("margins", confidence, message)
                self.statusUpdate.emit(message, 3000)
                self.detectionCompleted.emit("margins", True, message)
            else:
                self.buttonConfidenceUpdate.emit("margins", "failed", message)
                self.statusUpdate.emit(f"Margin detection failed: {message}", 3000)
                self.detectionFailed.emit("margins", message)

        except Exception as e:
            self.detectionFailed.emit("margins", str(e))

    def run_spacing_detection(self):
        """Run spacing auto-detection."""
        if not self._sprite_model or not self._sprite_model.original_sprite_sheet:
            self.statusUpdate.emit("No sprite sheet loaded", 3000)
            return

        self.detectionStarted.emit("spacing")

        try:
            success, spacing_x, spacing_y, message = (
                self._sprite_model.auto_detect_spacing_enhanced()
            )

            if success:
                self.spacingSettingsDetected.emit(spacing_x, spacing_y)

                confidence = "medium"
                self.buttonConfidenceUpdate.emit("spacing", confidence, message)
                self.statusUpdate.emit(message, 3000)
                self.detectionCompleted.emit("spacing", True, message)
            else:
                self.buttonConfidenceUpdate.emit("spacing", "failed", message)
                self.statusUpdate.emit(f"Spacing detection failed: {message}", 3000)
                self.detectionFailed.emit("spacing", message)

        except Exception as e:
            self.detectionFailed.emit("spacing", str(e))

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    def _emit_detected_settings(self):
        """Emit signals with current detected settings."""
        if self._sprite_model:
            self.frameSettingsDetected.emit(
                self._sprite_model.frame_width, self._sprite_model.frame_height
            )
            self.marginSettingsDetected.emit(
                self._sprite_model.offset_x, self._sprite_model.offset_y
            )
            self.spacingSettingsDetected.emit(
                self._sprite_model.spacing_x, self._sprite_model.spacing_y
            )

    def _create_detection_summary(self) -> str:
        """Create a brief summary of detected settings."""
        if not self._sprite_model:
            return "No detection results"

        summary = (
            f"Auto-detected: {self._sprite_model.frame_width}×{self._sprite_model.frame_height}"
        )

        if self._sprite_model.offset_x > 0 or self._sprite_model.offset_y > 0:
            summary += f", margins ({self._sprite_model.offset_x},{self._sprite_model.offset_y})"

        if self._sprite_model.spacing_x > 0 or self._sprite_model.spacing_y > 0:
            summary += f", spacing ({self._sprite_model.spacing_x},{self._sprite_model.spacing_y})"

        return summary

    def _update_button_confidence_from_result(self, result: DetectionResult) -> None:
        """Update button confidence indicators from structured detection result."""
        step_to_button = {
            "frame_size": "frame",
            "margins": "margins",
            "spacing": "spacing",
        }
        for step in result.step_results:
            button = step_to_button.get(step.step_name)
            if button:
                level = step.confidence_level if step.success else "failed"
                self.buttonConfidenceUpdate.emit(button, level, step.description)

    def _show_detection_results_dialog(self, success: bool, result: DetectionResult):
        """Show detailed detection results in a dialog."""
        dialog = QMessageBox()
        dialog.setWindowTitle("Comprehensive Auto-Detection Results")

        if success:
            dialog.setIcon(QMessageBox.Icon.Information)

            # Create user-friendly summary
            summary = self._create_detection_summary()
            dialog.setText(summary)
        else:
            dialog.setIcon(QMessageBox.Icon.Warning)
            dialog.setText("Auto-detection completed with some issues.")

        dialog.setDetailedText("\n".join(result.messages))
        dialog.exec()


# Export for easy importing
__all__ = ["AutoDetectionController"]
