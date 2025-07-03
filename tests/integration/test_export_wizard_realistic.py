"""
Realistic Integration Tests for Export Wizard
Tests with minimal mocking - uses real components and file operations.
"""

import pytest
import tempfile
import os
import time
from pathlib import Path
from PySide6.QtWidgets import QApplication, QPushButton, QListWidgetItem
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtTest import QTest

from export import ExportDialog
from export.core.frame_exporter import get_frame_exporter
from sprite_viewer import SpriteViewer
from sprite_model.core import SpriteModel
from config import Config


class TestRealisticExportWizardIntegration:
    """Test export wizard with real components and minimal mocking."""
    
    @pytest.mark.integration
    def test_complete_export_workflow_individual_frames(self, qtbot, tmp_path):
        """Test complete individual frames export with real files."""
        # Create real sprites
        sprites = self._create_test_sprites(4)
        
        # Create dialog with real data
        dialog = ExportDialog(
            frame_count=len(sprites),
            current_frame=0
        )
        dialog.set_sprites(sprites)
        qtbot.addWidget(dialog)
        dialog.show()
        
        # Step 1: Select individual frames preset
        type_step = dialog.type_step
        individual_card = None
        for card in type_step._cards:
            if card.preset.name == "individual_frames":
                individual_card = card
                break
        
        assert individual_card is not None
        qtbot.mouseClick(individual_card, Qt.LeftButton)
        
        # Verify selection
        assert type_step._selected_preset is not None
        assert type_step._selected_preset.name == "individual_frames"
        
        # Navigate to settings
        assert dialog.wizard.next_button.isEnabled()
        qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
        
        # Step 2: Configure real output directory
        settings_step = dialog.settings_step
        
        # Wait for UI to be set up after entering the step
        QApplication.processEvents()
        qtbot.wait(100)  # Give time for on_entering to complete
        
        # Now the widgets should exist
        assert hasattr(settings_step, 'directory_selector'), "directory_selector not created"
        settings_step.directory_selector.set_directory(str(tmp_path))
        settings_step.base_name_edit.setText("test_sprite")
        
        # Verify settings are valid
        assert settings_step.validate()
        
        # Navigate to preview
        qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
        
        # Step 3: Verify preview shows correct info
        preview_step = dialog.preview_step
        
        # Wait for preview to be generated
        QApplication.processEvents()
        qtbot.wait(100)
        
        # Preview should show correct type
        assert "Individual Frames" in preview_step.preview_type_label.text() or "individual" in preview_step.preview_type_label.text().lower()
        
        # Check summary shows correct info
        assert "Individual Frames" in preview_step.summary_labels['type'].text()
        
        # Actually export the frames
        export_requested = False
        export_settings = None
        export_completed = False
        
        def on_export_requested(settings):
            nonlocal export_requested, export_settings
            export_requested = True
            export_settings = settings
            
            # Perform actual export using the exporter
            exporter = get_frame_exporter()
            
            # Connect to exporter signals to track completion
            def on_finished(success, message):
                nonlocal export_completed
                export_completed = True
                # Notify the dialog of completion
                dialog._on_export_finished(success, message)
            
            exporter.exportFinished.connect(on_finished)
            
            # Start the export
            success = exporter.export_frames(
                frames=sprites,
                output_dir=settings['output_dir'],
                base_name=settings['base_name'],
                format=settings.get('format', 'PNG'),
                mode=settings.get('mode', 'individual'),
                scale_factor=settings.get('scale', 1.0),
                pattern=settings.get('pattern', Config.Export.DEFAULT_PATTERN)
            )
        
        dialog.exportRequested.connect(on_export_requested)
        
        # Click export
        preview_step.export_now_button.click()
        
        # Wait for export to be requested
        qtbot.waitUntil(lambda: export_requested, timeout=2000)
        
        # Verify export was requested
        assert export_requested, "Export was not requested"
        assert export_settings is not None
        
        # Wait for export to complete
        qtbot.waitUntil(lambda: export_completed, timeout=5000)
        
        # Verify files were actually created
        exported_files = list(tmp_path.glob("*.png"))
        assert len(exported_files) == 4
        
        # Verify file names match pattern
        expected_names = ["test_sprite_000.png", "test_sprite_001.png", 
                         "test_sprite_002.png", "test_sprite_003.png"]
        actual_names = sorted([f.name for f in exported_files])
        assert actual_names == expected_names
        
        # Verify files have content (not empty)
        for file in exported_files:
            assert file.stat().st_size > 0
        
        dialog.close()
    
    @pytest.mark.integration
    def test_complete_sprite_sheet_export(self, qtbot, tmp_path):
        """Test sprite sheet export with real image generation."""
        sprites = self._create_test_sprites(16)
        
        dialog = ExportDialog(
            frame_count=len(sprites),
            current_frame=0
        )
        dialog.set_sprites(sprites)
        qtbot.addWidget(dialog)
        dialog.show()
        
        # Select sprite sheet preset
        type_step = dialog.type_step
        sheet_card = self._find_preset_card(type_step, "sprite_sheet")
        qtbot.mouseClick(sheet_card, Qt.LeftButton)
        
        # Navigate to settings
        qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
        
        # Configure sprite sheet
        settings_step = dialog.settings_step
        settings_step.directory_selector.set_directory(str(tmp_path))
        settings_step.single_filename_edit.setText("spritesheet")
        settings_step.layout_mode_combo.setCurrentText("Square (Auto)")
        settings_step.spacing_spin.setValue(2)
        settings_step.padding_spin.setValue(4)
        
        # Navigate to preview
        qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
        
        # Verify preview
        preview_step = dialog.preview_step
        assert "Sprite Sheet" in preview_step.preview_type_label.text()
        assert preview_step.preview_view is not None
        
        # Export sprite sheet
        export_completed = False
        
        def on_export_finished(success, message):
            nonlocal export_completed
            export_completed = True
        
        dialog._exporter.exportFinished.connect(on_export_finished)
        preview_step.export_now_button.click()
        
        # Wait for export
        qtbot.waitUntil(lambda: export_completed, timeout=5000)
        
        # Verify sprite sheet was created
        sheet_file = tmp_path / "spritesheet.png"
        assert sheet_file.exists()
        assert sheet_file.stat().st_size > 0
        
        # Load and verify dimensions
        pixmap = QPixmap(str(sheet_file))
        assert not pixmap.isNull()
        
        # For 16 sprites in square layout = 4x4
        # Each sprite is 32x32, spacing is 2, padding is 4
        expected_width = 4 * 2 + 4 * 32 + 3 * 2  # padding + sprites + spacing
        expected_height = expected_width  # Square layout
        
        assert pixmap.width() == expected_width
        assert pixmap.height() == expected_height
        
        dialog.close()
    
    @pytest.mark.integration
    def test_selected_frames_export(self, qtbot, tmp_path):
        """Test exporting only selected frames."""
        sprites = self._create_test_sprites(10)
        
        dialog = ExportDialog(
            frame_count=len(sprites),
            current_frame=2
        )
        dialog.set_sprites(sprites)
        qtbot.addWidget(dialog)
        dialog.show()
        
        # Select selected frames preset
        type_step = dialog.type_step
        selected_card = self._find_preset_card(type_step, "selected_frames")
        qtbot.mouseClick(selected_card, Qt.LeftButton)
        
        # Navigate to settings
        qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
        
        # Configure and select specific frames
        settings_step = dialog.settings_step
        settings_step.directory_selector.set_directory(str(tmp_path))
        settings_step.base_name_edit.setText("selected")
        
        # Select frames 0, 2, 4, 6
        frame_list = settings_step.frame_list
        frame_list.clearSelection()
        for i in [0, 2, 4, 6]:
            frame_list.item(i).setSelected(True)
        
        # Verify selection
        selected_items = [item.row() for item in frame_list.selectedItems()]
        assert sorted(selected_items) == [0, 2, 4, 6]
        assert "4 frames selected" in settings_step.selection_info_label.text()
        
        # Navigate to preview
        qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
        
        # Export
        export_completed = False
        
        def on_export_finished(success, message):
            nonlocal export_completed
            export_completed = True
        
        dialog._exporter.exportFinished.connect(on_export_finished)
        dialog.preview_step.export_now_button.click()
        
        qtbot.waitUntil(lambda: export_completed, timeout=5000)
        
        # Verify only selected frames were exported
        exported_files = list(tmp_path.glob("*.png"))
        assert len(exported_files) == 4
        
        # Files should be numbered 0, 1, 2, 3 (not the original indices)
        expected_names = ["selected_000.png", "selected_001.png",
                         "selected_002.png", "selected_003.png"]
        actual_names = sorted([f.name for f in exported_files])
        assert actual_names == expected_names
        
        dialog.close()
    
    @pytest.mark.integration
    def test_wizard_navigation_and_validation(self, qtbot):
        """Test wizard navigation and validation without mocking."""
        dialog = ExportDialog(frame_count=8, current_frame=0)
        qtbot.addWidget(dialog)
        dialog.show()
        
        # Initially, next button should be disabled (no preset selected)
        assert not dialog.wizard.next_button.isEnabled()
        
        # Select a preset
        type_step = dialog.type_step
        card = type_step._cards[0]
        qtbot.mouseClick(card, Qt.LeftButton)
        
        # Now next should be enabled
        assert dialog.wizard.next_button.isEnabled()
        
        # Go to settings
        qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
        
        # Clear directory to make invalid
        dialog.settings_step.directory_selector.set_directory("")
        assert not dialog.wizard.next_button.isEnabled()
        
        # Set valid directory
        dialog.settings_step.directory_selector.set_directory("/tmp")
        assert dialog.wizard.next_button.isEnabled()
        
        # Test back navigation
        qtbot.mouseClick(dialog.wizard.back_button, Qt.LeftButton)
        assert dialog.wizard.current_step_index == 0
        
        # Preset should still be selected
        assert type_step._selected_preset is not None
        
        dialog.close()
    
    @pytest.mark.integration
    def test_export_with_real_sprite_viewer(self, qtbot, tmp_path):
        """Test export triggered from actual sprite viewer."""
        # Create sprite viewer
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # Load real sprites into model
        sprites = self._create_test_sprites(8)
        model = viewer._sprite_model
        model.sprite_frames = sprites
        model.frameChanged.emit(0, len(sprites))
        
        # Track dialog creation
        dialog_created = False
        created_dialog = None
        
        # Override exec to prevent blocking
        original_exec = ExportDialog.exec
        
        def non_blocking_exec(self):
            nonlocal dialog_created, created_dialog
            dialog_created = True
            created_dialog = self
            self.show()
            return True
        
        ExportDialog.exec = non_blocking_exec
        
        try:
            # Trigger export action
            viewer._export_frames()
            
            # Verify dialog was created with correct data
            assert dialog_created
            assert created_dialog is not None
            assert created_dialog.frame_count == 8
            assert len(created_dialog.sprites) == 8
            
            # Actually use the dialog
            qtbot.addWidget(created_dialog)
            
            # Select preset and export
            type_step = created_dialog.type_step
            card = self._find_preset_card(type_step, "individual_frames")
            qtbot.mouseClick(card, Qt.LeftButton)
            
            qtbot.mouseClick(created_dialog.wizard.next_button, Qt.LeftButton)
            
            created_dialog.settings_step.directory_selector.set_directory(str(tmp_path))
            
            qtbot.mouseClick(created_dialog.wizard.next_button, Qt.LeftButton)
            
            # Export
            export_completed = False
            
            def on_export_finished(success, message):
                nonlocal export_completed
                export_completed = True
            
            created_dialog._exporter.exportFinished.connect(on_export_finished)
            created_dialog.preview_step.export_now_button.click()
            
            qtbot.waitUntil(lambda: export_completed, timeout=5000)
            
            # Verify files
            assert len(list(tmp_path.glob("*.png"))) == 8
            
            created_dialog.close()
            
        finally:
            # Restore original exec
            ExportDialog.exec = original_exec
    
    @pytest.mark.integration
    def test_error_handling_with_real_filesystem(self, qtbot):
        """Test error handling with real filesystem operations."""
        dialog = ExportDialog(frame_count=4, current_frame=0)
        qtbot.addWidget(dialog)
        dialog.show()
        
        # Navigate to export
        type_step = dialog.type_step
        card = type_step._cards[0]
        qtbot.mouseClick(card, Qt.LeftButton)
        qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
        
        # Set invalid directory (doesn't exist and can't be created)
        invalid_dir = "/root/cannot_create_this_12345"
        dialog.settings_step.directory_selector.set_directory(invalid_dir)
        dialog.settings_step.base_name_edit.setText("test")
        
        qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
        
        # Try to export
        export_error_received = False
        error_message = ""
        
        def on_export_error(msg):
            nonlocal export_error_received, error_message
            export_error_received = True
            error_message = msg
        
        dialog._exporter.exportError.connect(on_export_error)
        dialog.preview_step.export_now_button.click()
        
        # Wait for error
        qtbot.waitUntil(lambda: export_error_received, timeout=2000)
        
        # Verify error was handled
        assert export_error_received
        assert "Permission denied" in error_message or "cannot create" in error_message.lower()
        
        # UI should be re-enabled
        assert dialog.wizard.isEnabled()
        assert dialog.preview_step.export_now_button.isEnabled()
        
        dialog.close()
    
    # Helper methods
    def _create_test_sprites(self, count):
        """Create real test sprite pixmaps."""
        sprites = []
        for i in range(count):
            pixmap = QPixmap(32, 32)
            # Create unique colors for each sprite
            color = QColor.fromHsv(int(i * 360 / count), 200, 200)
            pixmap.fill(color)
            sprites.append(pixmap)
        return sprites
    
    def _find_preset_card(self, type_step, preset_name):
        """Find a preset card by name."""
        for card in type_step._cards:
            if card.preset.name == preset_name:
                return card
        return None


class TestRealisticPerformance:
    """Performance tests with real components."""
    
    @pytest.mark.integration
    @pytest.mark.performance
    def test_large_sprite_export_performance(self, qtbot, tmp_path, benchmark):
        """Test performance with large number of sprites."""
        # Create 100 sprites
        sprites = []
        for i in range(100):
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor.fromHsv(int(i * 360 / 100), 200, 200))
            sprites.append(pixmap)
        
        def export_large_sprite_sheet():
            dialog = ExportDialog(
                frame_count=len(sprites),
                current_frame=0
            )
            dialog.set_sprites(sprites)
            qtbot.addWidget(dialog)
            
            # Select sprite sheet
            card = None
            for c in dialog.type_step._cards:
                if c.preset.name == "sprite_sheet":
                    card = c
                    break
            
            # Quick navigation through wizard
            qtbot.mouseClick(card, Qt.LeftButton)
            qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
            
            dialog.settings_step.directory_selector.set_directory(str(tmp_path))
            dialog.settings_step.single_filename_edit.setText("large_sheet")
            
            qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
            
            # Export
            export_completed = False
            
            def on_export_finished(success, message):
                nonlocal export_completed
                export_completed = True
            
            dialog._exporter.exportFinished.connect(on_export_finished)
            dialog.preview_step.export_now_button.click()
            
            # Wait for completion
            timeout = 10000  # 10 seconds for large export
            start = qtbot.wait(0)
            while not export_completed and qtbot.wait(0) - start < timeout:
                QApplication.processEvents()
                qtbot.wait(10)
            
            dialog.close()
            
            # Verify file was created
            assert (tmp_path / "large_sheet.png").exists()
        
        # Benchmark the export
        result = benchmark(export_large_sprite_sheet)
        
        # Should complete in reasonable time (under 5 seconds)
        assert result.stats['mean'] < 5.0