#!/usr/bin/env python3
"""
Auto-Detection Controller
Manages auto-detection workflows and UI feedback for sprite sheet analysis.
Extracted from sprite_viewer.py to reduce complexity and improve maintainability.
"""

from typing import Tuple, Dict, Optional
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox

from config import Config
from ui_common import DetectionResult, parse_detection_tuple, extract_confidence_from_message


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
    
    # Workflow state signals
    workflowStateChanged = Signal(str)  # state: "idle", "working", "completed", "failed"
    
    def __init__(self):
        super().__init__()
        
        # References to external components
        self._sprite_model = None
        self._frame_extractor = None
        
        # Workflow state
        self._current_workflow = None
        self._workflow_state = "idle"
    
    def initialize(self, sprite_model, frame_extractor):
        """Initialize with references to sprite model and frame extractor."""
        self._sprite_model = sprite_model
        self._frame_extractor = frame_extractor
    
    # ============================================================================
    # NEW SPRITE SHEET WORKFLOW
    # ============================================================================
    
    def handle_new_sprite_sheet_loaded(self) -> bool:
        """
        Handle new sprite sheet loading with proper auto-detection workflow.
        Returns True if auto-detection was run, False otherwise.
        """
        if not self._sprite_model or not self._sprite_model.original_sprite_sheet:
            return False
        
        # Always run auto-detection for new sprite sheets
        self._reset_settings_for_new_sheet()
        
        # Run comprehensive auto-detection silently (no dialog)
        success = self._run_silent_comprehensive_detection()
        
        if success:
            # Update UI with detected values
            self._emit_detected_settings()
            
            # Show brief status notification
            detected_info = self._create_detection_summary()
            self.statusUpdate.emit(detected_info, 5000)  # 5 seconds
            
            # Update comprehensive button to show success
            self._update_comprehensive_button_success()
        else:
            # Auto-detection failed, using defaults
            self.statusUpdate.emit("Auto-detection failed, using default settings", 3000)
            self._update_comprehensive_button_default()
        
        return True
    
    def _reset_settings_for_new_sheet(self):
        """Reset frame extraction settings to defaults for new sprite sheet."""
        # Reset to default frame size
        default_width = Config.FrameExtraction.DEFAULT_FRAME_WIDTH
        default_height = Config.FrameExtraction.DEFAULT_FRAME_HEIGHT
        
        # Update model with defaults
        if self._sprite_model:
            self._sprite_model._frame_width = default_width
            self._sprite_model._frame_height = default_height
            self._sprite_model._offset_x = 0
            self._sprite_model._offset_y = 0
            self._sprite_model._spacing_x = 0
            self._sprite_model._spacing_y = 0
        
        # Reset button styles
        self.buttonConfidenceUpdate.emit('frame', 'reset', '')
        self.buttonConfidenceUpdate.emit('margins', 'reset', '')
        self.buttonConfidenceUpdate.emit('spacing', 'reset', '')
    
    def _run_silent_comprehensive_detection(self) -> bool:
        """Run comprehensive auto-detection without user dialogs."""
        if not self._sprite_model:
            return False
        
        try:
            self._set_workflow_state("working")
            success, detailed_report = self._sprite_model.comprehensive_auto_detect()
            
            if success:
                # Parse and update button confidence from report
                self._update_button_confidence_from_report(detailed_report)
                self._set_workflow_state("completed")
            else:
                self._set_workflow_state("failed")
            
            return success
            
        except Exception as e:
            self._set_workflow_state("failed")
            return False
    
    # ============================================================================
    # MANUAL AUTO-DETECTION WORKFLOWS
    # ============================================================================
    
    def run_comprehensive_detection_with_dialog(self):
        """Run comprehensive auto-detection with detailed user feedback."""
        if not self._sprite_model or not self._sprite_model.original_sprite_sheet:
            self.statusUpdate.emit("No sprite sheet loaded", 3000)
            return
        
        self.detectionStarted.emit("comprehensive")
        self._set_workflow_state("working")
        
        try:
            # Run the comprehensive workflow
            success, detailed_report = self._sprite_model.comprehensive_auto_detect()
            
            # Update UI with detected values
            self._emit_detected_settings()
            
            # Update button confidence indicators
            self._update_button_confidence_from_report(detailed_report)
            
            # Show detailed results dialog
            self._show_detection_results_dialog(success, detailed_report)
            
            # Update workflow state
            if success:
                self._set_workflow_state("completed")
                self.detectionCompleted.emit("comprehensive", True, "Auto-detection completed successfully")
            else:
                self._set_workflow_state("failed")
                self.detectionCompleted.emit("comprehensive", False, "Auto-detection completed with issues")
                
        except Exception as e:
            self._set_workflow_state("failed")
            self.detectionFailed.emit("comprehensive", str(e))
    
    def run_frame_detection(self):
        """Run frame size auto-detection."""
        if not self._sprite_model or not self._sprite_model.original_sprite_sheet:
            self.statusUpdate.emit("No sprite sheet loaded", 3000)
            return
        
        self.detectionStarted.emit("frame")
        
        try:
            # Try enhanced rectangular detection first
            result_tuple = self._sprite_model.auto_detect_rectangular_frames()
            result = parse_detection_tuple(result_tuple)
            
            if result.success:
                width = result.parameters.get('value1', 0)
                height = result.parameters.get('value2', 0)
                self.frameSettingsDetected.emit(width, height)
                
                # Extract confidence and update button
                result.confidence = extract_confidence_from_message(result.message)
                self.buttonConfidenceUpdate.emit('frame', result.confidence, result.message)
                self.statusUpdate.emit(result.message, 3000)
                self.detectionCompleted.emit("frame", True, result.message)
            else:
                self.buttonConfidenceUpdate.emit('frame', 'failed', result.message)
                self.statusUpdate.emit(f"Frame detection failed: {result.message}", 3000)
                self.detectionFailed.emit("frame", result.message)
                
        except Exception as e:
            self.detectionFailed.emit("frame", str(e))
    
    def run_margin_detection(self):
        """Run margin auto-detection."""
        if not self._sprite_model or not self._sprite_model.original_sprite_sheet:
            self.statusUpdate.emit("No sprite sheet loaded", 3000)
            return
        
        self.detectionStarted.emit("margins")
        
        try:
            result_tuple = self._sprite_model.auto_detect_margins()
            result = parse_detection_tuple(result_tuple)
            
            if result.success:
                offset_x = result.parameters.get('value1', 0)
                offset_y = result.parameters.get('value2', 0)
                self.marginSettingsDetected.emit(offset_x, offset_y)
                
                # Margin detection confidence based on results
                result.confidence = "high" if offset_x > 0 or offset_y > 0 else "medium"
                self.buttonConfidenceUpdate.emit('margins', result.confidence, result.message)
                self.statusUpdate.emit(result.message, 3000)
                self.detectionCompleted.emit("margins", True, result.message)
            else:
                self.buttonConfidenceUpdate.emit('margins', 'failed', result.message)
                self.statusUpdate.emit(f"Margin detection failed: {result.message}", 3000)
                self.detectionFailed.emit("margins", result.message)
                
        except Exception as e:
            self.detectionFailed.emit("margins", str(e))
    
    def run_spacing_detection(self):
        """Run spacing auto-detection."""
        if not self._sprite_model or not self._sprite_model.original_sprite_sheet:
            self.statusUpdate.emit("No sprite sheet loaded", 3000)
            return
        
        self.detectionStarted.emit("spacing")
        
        try:
            result_tuple = self._sprite_model.auto_detect_spacing_enhanced()
            result = parse_detection_tuple(result_tuple)
            
            if result.success:
                spacing_x = result.parameters.get('value1', 0)
                spacing_y = result.parameters.get('value2', 0)
                self.spacingSettingsDetected.emit(spacing_x, spacing_y)
                
                # Extract confidence from message
                result.confidence = extract_confidence_from_message(result.message)
                self.buttonConfidenceUpdate.emit('spacing', result.confidence, result.message)
                self.statusUpdate.emit(result.message, 3000)
                self.detectionCompleted.emit("spacing", True, result.message)
            else:
                self.buttonConfidenceUpdate.emit('spacing', 'failed', result.message)
                self.statusUpdate.emit(f"Spacing detection failed: {result.message}", 3000)
                self.detectionFailed.emit("spacing", result.message)
                
        except Exception as e:
            self.detectionFailed.emit("spacing", str(e))
    
    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    
    def _emit_detected_settings(self):
        """Emit signals with current detected settings."""
        if self._sprite_model:
            self.frameSettingsDetected.emit(self._sprite_model._frame_width, self._sprite_model._frame_height)
            self.marginSettingsDetected.emit(self._sprite_model._offset_x, self._sprite_model._offset_y)
            self.spacingSettingsDetected.emit(self._sprite_model._spacing_x, self._sprite_model._spacing_y)
    
    def _create_detection_summary(self) -> str:
        """Create a brief summary of detected settings."""
        if not self._sprite_model:
            return "No detection results"
        
        summary = f"Auto-detected: {self._sprite_model._frame_width}×{self._sprite_model._frame_height}"
        
        if self._sprite_model._offset_x > 0 or self._sprite_model._offset_y > 0:
            summary += f", margins ({self._sprite_model._offset_x},{self._sprite_model._offset_y})"
        
        if self._sprite_model._spacing_x > 0 or self._sprite_model._spacing_y > 0:
            summary += f", spacing ({self._sprite_model._spacing_x},{self._sprite_model._spacing_y})"
        
        return summary
    
    def _update_button_confidence_from_report(self, detailed_report: str):
        """Update button confidence indicators based on detection report."""
        report_lines = detailed_report.split('\n')
        
        for line in report_lines:
            if "Auto-detected frame size:" in line or "Format-suggested size confirmed:" in line:
                confidence = extract_confidence_from_message(line)
                message = line.split('✓ ')[1] if '✓ ' in line else line
                self.buttonConfidenceUpdate.emit('frame', confidence, message)
                
            elif "Margins:" in line and "✓" in line:
                message = line.split('✓ ')[1]
                self.buttonConfidenceUpdate.emit('margins', 'high', message)
                
            elif "Auto-detected spacing:" in line:
                confidence = extract_confidence_from_message(line)
                message = line.split('✓ ')[1] if '✓ ' in line else line
                self.buttonConfidenceUpdate.emit('spacing', confidence, message)
    
    
    def _show_detection_results_dialog(self, success: bool, detailed_report: str):
        """Show detailed detection results in a dialog."""
        dialog = QMessageBox()
        dialog.setWindowTitle("Comprehensive Auto-Detection Results")
        
        if success:
            dialog.setIcon(QMessageBox.Information)
            
            # Create user-friendly summary
            summary = self._create_detection_summary()
            dialog.setText(summary)
        else:
            dialog.setIcon(QMessageBox.Warning)
            dialog.setText("Auto-detection completed with some issues.")
        
        dialog.setDetailedText(detailed_report)
        dialog.exec()
    
    def _update_comprehensive_button_success(self):
        """Signal to update comprehensive button for success state."""
        self.buttonConfidenceUpdate.emit('comprehensive', 'success', 'Auto-detection completed')
    
    def _update_comprehensive_button_default(self):
        """Signal to update comprehensive button to default state."""
        self.buttonConfidenceUpdate.emit('comprehensive', 'reset', '')
    
    def _set_workflow_state(self, state: str):
        """Update workflow state and emit signal."""
        self._workflow_state = state
        self.workflowStateChanged.emit(state)
    
    # ============================================================================
    # PROPERTIES
    # ============================================================================
    
    @property
    def workflow_state(self) -> str:
        """Get current workflow state."""
        return self._workflow_state
    
    @property
    def is_working(self) -> bool:
        """Check if currently running a detection workflow."""
        return self._workflow_state == "working"


# Export for easy importing
__all__ = ['AutoDetectionController']