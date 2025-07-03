"""
UI Tests for Export Dialog Wizard
Comprehensive tests for the new wizard-based export dialog.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QPushButton
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QColor

from export import ExportDialog
from export.dialogs.base.wizard_base import WizardWidget, WizardStep
from export.steps.type_selection import ExportTypeStepSimple as ExportTypeStep
from export.steps.settings_preview import ExportSettingsPreviewStep
from export.core.export_presets import ExportPreset, ExportPresetType, get_preset_manager


class TestWizardWidget:
    """Test the base wizard widget functionality."""
    
    @pytest.mark.ui
    def test_wizard_creation(self, qtbot):
        """Test basic wizard widget creation."""
        wizard = WizardWidget()
        qtbot.addWidget(wizard)
        
        assert wizard.current_step_index == 0
        assert len(wizard.steps) == 0
        assert wizard.back_button.isEnabled() is False
        assert wizard.next_button.text() == "Next →"
    
    @pytest.mark.ui
    def test_add_steps(self, qtbot):
        """Test adding steps to the wizard."""
        wizard = WizardWidget()
        qtbot.addWidget(wizard)
        
        # Create test steps
        step1 = WizardStep("Step 1", "First step")
        step2 = WizardStep("Step 2", "Second step")
        step3 = WizardStep("Step 3", "Final step")
        
        # Add steps
        wizard.add_step(step1)
        wizard.add_step(step2)
        wizard.add_step(step3)
        
        assert len(wizard.steps) == 3
        assert wizard.current_step_index == 0
        assert wizard.step_title_label.text() == "Step 1"
        assert wizard.progress_bar.value() > 0
    
    @pytest.mark.ui
    def test_navigation(self, qtbot):
        """Test wizard navigation between steps."""
        wizard = WizardWidget()
        qtbot.addWidget(wizard)
        
        # Add steps
        for i in range(3):
            step = WizardStep(f"Step {i+1}", f"Step {i+1} subtitle")
            wizard.add_step(step)
        
        # Test forward navigation
        assert wizard.current_step_index == 0
        qtbot.mouseClick(wizard.next_button, Qt.LeftButton)
        assert wizard.current_step_index == 1
        assert wizard.back_button.isEnabled() is True
        
        # Navigate to last step
        qtbot.mouseClick(wizard.next_button, Qt.LeftButton)
        assert wizard.current_step_index == 2
        assert wizard.next_button.text() == "Finish"
        
        # Test backward navigation
        qtbot.mouseClick(wizard.back_button, Qt.LeftButton)
        assert wizard.current_step_index == 1
        assert wizard.next_button.text() == "Next →"
    
    @pytest.mark.ui
    def test_step_validation(self, qtbot):
        """Test step validation prevents navigation."""
        wizard = WizardWidget()
        qtbot.addWidget(wizard)
        
        # Create step with validation
        class ValidatedStep(WizardStep):
            def __init__(self):
                super().__init__("Validated", "Requires validation")
                self._is_valid = False
            
            def validate(self):
                return self._is_valid
        
        step = ValidatedStep()
        wizard.add_step(step)
        wizard.add_step(WizardStep("Step 2", "Second"))
        
        # Should not advance when invalid
        assert wizard.next_button.isEnabled() is False
        
        # Make valid and try again
        step._is_valid = True
        step.stepValidated.emit(True)
        assert wizard.next_button.isEnabled() is True
        
        qtbot.mouseClick(wizard.next_button, Qt.LeftButton)
        assert wizard.current_step_index == 1


class TestExportTypeStep:
    """Test the export type selection step."""
    
    @pytest.mark.ui
    def test_export_type_step_creation(self, qtbot):
        """Test creating export type step."""
        step = ExportTypeStep(frame_count=16)
        qtbot.addWidget(step)
        
        assert step.title == "Choose Export Type"
        assert step.frame_count == 16
        assert step._selected_preset is None
        assert len(step._cards) > 0
    
    @pytest.mark.ui
    def test_preset_card_creation(self, qtbot):
        """Test visual preset card creation."""
        preset = ExportPreset(
            name="test_preset",
            display_name="Test Preset",
            icon="🧪",
            description="Test description",
            mode="individual",
            format="PNG",
            scale=1.0,
            default_pattern="{name}_{index}",
            tooltip="Test tooltip",
            use_cases=["Testing"],
            short_description="For testing",
            recommended_for=["Unit tests"]
        )
        
        card = VisualPresetCard(preset)
        qtbot.addWidget(card)
        
        assert card.preset == preset
        assert card.width() == 220
        assert card.height() == 160
        assert not card._is_selected
    
    @pytest.mark.ui
    def test_preset_selection(self, qtbot):
        """Test selecting a preset card."""
        step = ExportTypeStep(frame_count=16)
        qtbot.addWidget(step)
        
        # Get first card
        card = step._cards[0] if step._cards else None
        assert card is not None
        
        # Click the card
        with qtbot.waitSignal(step.dataChanged, timeout=1000):
            qtbot.mouseClick(card, Qt.LeftButton)
        
        assert step._selected_preset is not None
        assert card._is_selected
        assert step.validate() is True
    
    @pytest.mark.ui
    def test_quick_export_buttons(self, qtbot):
        """Test quick export button functionality."""
        step = ExportTypeStep(frame_count=16)
        qtbot.addWidget(step)
        
        # Find quick export buttons
        quick_buttons = step.findChildren(QPushButton)
        quick_export_buttons = [btn for btn in quick_buttons if "PNG" in btn.text() or "Sheet" in btn.text() or "GIF" in btn.text()]
        
        assert len(quick_export_buttons) >= 3  # Should have at least 3 quick buttons
        
        # Test clicking a quick button
        if quick_export_buttons:
            with qtbot.waitSignal(step.dataChanged, timeout=1000):
                qtbot.mouseClick(quick_export_buttons[0], Qt.LeftButton)
            
            assert step._selected_preset is not None


class TestExportSettingsStep:
    """Test the export settings configuration step."""
    
    @pytest.mark.ui
    def test_settings_step_creation(self, qtbot):
        """Test creating settings step."""
        step = ExportSettingsStep(frame_count=16, current_frame=0)
        qtbot.addWidget(step)
        
        assert step.title == "Configure Export Settings"
        assert step.frame_count == 16
        assert step.current_frame == 0
    
    @pytest.mark.ui
    def test_contextual_ui_individual_frames(self, qtbot):
        """Test UI shows correct options for individual frames export."""
        step = ExportSettingsStep(frame_count=16, current_frame=0)
        qtbot.addWidget(step)
        
        # Create individual frames preset
        preset = get_preset_manager().get_preset("individual_frames")
        step._setup_for_preset(preset)
        
        # Check expected widgets exist
        assert hasattr(step, 'directory_selector')
        assert hasattr(step, 'base_name_edit')
        assert hasattr(step, 'format_combo')
        assert hasattr(step, 'scale_spin')
        
        # Sprite sheet options should not exist
        assert not hasattr(step, 'layout_mode_combo')
        assert not hasattr(step, 'spacing_spin')
    
    @pytest.mark.ui
    def test_contextual_ui_sprite_sheet(self, qtbot):
        """Test UI shows correct options for sprite sheet export."""
        step = ExportSettingsStep(frame_count=16, current_frame=0)
        qtbot.addWidget(step)
        
        # Create sprite sheet preset
        preset = get_preset_manager().get_preset("sprite_sheet")
        step._setup_for_preset(preset)
        
        # Check sprite sheet specific widgets exist
        assert hasattr(step, 'layout_mode_combo')
        assert hasattr(step, 'spacing_spin')
        assert hasattr(step, 'padding_spin')
        assert hasattr(step, 'background_combo')
        
        # Check single file naming
        assert hasattr(step, 'single_filename_edit')
        assert not hasattr(step, 'base_name_edit')  # Multiple file naming not needed
    
    @pytest.mark.ui
    def test_validation(self, qtbot):
        """Test settings validation."""
        step = ExportSettingsStep(frame_count=16, current_frame=0)
        qtbot.addWidget(step)
        
        preset = get_preset_manager().get_preset("individual_frames")
        step._setup_for_preset(preset)
        
        # Should be valid with defaults
        assert step.validate() is True
        
        # Clear directory should make invalid
        step.directory_selector.set_directory("")
        assert step.validate() is False
        
        # Set valid directory
        step.directory_selector.set_directory("/tmp")
        assert step.validate() is True


class TestExportPreviewStep:
    """Test the export preview and confirmation step."""
    
    @pytest.mark.ui
    def test_preview_step_creation(self, qtbot):
        """Test creating preview step."""
        sprites = [QPixmap(32, 32) for _ in range(16)]
        step = ExportPreviewStep(sprites=sprites)
        qtbot.addWidget(step)
        
        assert step.title == "Preview & Export"
        assert len(step._sprites) == 16
        assert hasattr(step, 'preview_view')
        assert hasattr(step, 'export_now_button')
    
    @pytest.mark.ui
    def test_visual_preview_generation(self, qtbot):
        """Test generating visual preview."""
        # Create test sprites
        sprites = []
        for i in range(16):
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor.fromHsv(i * 20, 200, 200))
            sprites.append(pixmap)
        
        step = ExportPreviewStep(sprites=sprites)
        qtbot.addWidget(step)
        
        # Set up preview data
        preset = get_preset_manager().get_preset("sprite_sheet")
        step._current_preset = preset
        step._export_settings = {
            'layout_mode': 'auto',
            'spacing': 2,
            'padding': 4,
            'background_mode': 'transparent'
        }
        
        # Generate preview
        step._generate_preview()
        
        # Check scene has items
        assert step.preview_view.scene.items() != []
        assert "Sprite Sheet" in step.preview_type_label.text()
    
    @pytest.mark.ui 
    def test_export_summary(self, qtbot):
        """Test export summary display."""
        step = ExportPreviewStep()
        qtbot.addWidget(step)
        
        preset = get_preset_manager().get_preset("individual_frames")
        step._current_preset = preset
        step._export_settings = {
            'output_dir': '/tmp/sprites',
            'format': 'PNG',
            'scale': 2.0
        }
        
        step._update_summary()
        
        # Check summary labels updated
        assert "Individual Frames" in step.summary_labels['type'].text()
        assert "/tmp/sprites" in step.summary_labels['output'].text()
        assert "PNG @ 2.0x" in step.summary_labels['format'].text()


class TestExportDialog:
    """Test the main export dialog wizard."""
    
    @pytest.mark.ui
    def test_wizard_dialog_creation(self, qtbot):
        """Test creating the wizard dialog."""
        sprites = [QPixmap(32, 32) for _ in range(16)]
        dialog = ExportDialog(
            frame_count=16,
            current_frame=0,
            sprites=sprites
        )
        qtbot.addWidget(dialog)
        
        assert dialog.frame_count == 16
        assert dialog.current_frame == 0
        assert len(dialog.sprites) == 16
        assert isinstance(dialog.wizard, WizardWidget)
        assert len(dialog.wizard.steps) == 3
    
    @pytest.mark.ui
    def test_dialog_sizing(self, qtbot):
        """Test dialog has improved sizing."""
        dialog = ExportDialog()
        qtbot.addWidget(dialog)
        
        # Check minimum size is larger than old dialog
        assert dialog.minimumWidth() >= 800
        assert dialog.minimumHeight() >= 600
        
        # Check default size
        assert dialog.width() >= 800
        assert dialog.height() >= 600
    
    @pytest.mark.ui
    def test_complete_export_flow(self, qtbot):
        """Test complete export flow through wizard."""
        sprites = [QPixmap(32, 32) for _ in range(4)]
        dialog = ExportDialog(
            frame_count=4,
            current_frame=0,
            sprites=sprites
        )
        qtbot.addWidget(dialog)
        
        # Step 1: Select export type
        type_step = dialog.type_step
        preset_card = type_step._cards[0] if type_step._cards else None
        assert preset_card is not None
        
        qtbot.mouseClick(preset_card, Qt.LeftButton)
        assert type_step.validate() is True
        
        # Navigate to step 2
        qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
        assert dialog.wizard.current_step_index == 1
        
        # Step 2: Configure settings (should have defaults)
        assert dialog.settings_step.validate() is True
        
        # Navigate to step 3
        qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
        assert dialog.wizard.current_step_index == 2
        
        # Step 3: Preview
        assert dialog.preview_step.validate() is True
        assert dialog.wizard.next_button.text() == "Finish"
    
    @pytest.mark.ui
    def test_export_signal(self, qtbot):
        """Test export signal is emitted with correct data."""
        dialog = ExportDialog(frame_count=4)
        qtbot.addWidget(dialog)
        
        # Mock the gathering of settings
        test_settings = {
            'mode': 'individual',
            'output_dir': '/tmp',
            'format': 'PNG',
            'scale': 1.0
        }
        
        with patch.object(dialog, '_gather_export_settings', return_value=test_settings):
            with qtbot.waitSignal(dialog.exportRequested, timeout=1000) as blocker:
                dialog._on_export_now()
            
            assert blocker.args[0] == test_settings


class TestExportPresets:
    """Test export preset functionality."""
    
    def test_preset_manager_singleton(self):
        """Test preset manager is a singleton."""
        manager1 = get_preset_manager()
        manager2 = get_preset_manager()
        assert manager1 is manager2
    
    def test_get_standard_presets(self):
        """Test getting standard presets for wizard."""
        manager = get_preset_manager()
        standard_presets = manager.get_presets_by_type(ExportPresetType.STANDARD)
        
        assert len(standard_presets) == 4
        preset_names = [p.name for p in standard_presets]
        assert "individual_frames" in preset_names
        assert "sprite_sheet" in preset_names
        assert "animation_gif" in preset_names
        assert "selected_frames" in preset_names
    
    def test_preset_properties(self):
        """Test preset has required properties for wizard."""
        manager = get_preset_manager()
        preset = manager.get_preset("individual_frames")
        
        assert preset is not None
        assert hasattr(preset, 'short_description')
        assert hasattr(preset, 'recommended_for')
        assert preset.short_description is not None
        assert isinstance(preset.recommended_for, list)
    
    def test_get_preset_by_name(self):
        """Test getting preset by string name."""
        manager = get_preset_manager()
        
        # Test with string name
        preset = manager.get_preset("sprite_sheet")
        assert preset is not None
        assert preset.name == "sprite_sheet"
        
        # Test with enum type
        preset2 = manager.get_preset(ExportPresetType.SPRITE_SHEET)
        assert preset2 is not None
        assert preset2.name == "sprite_sheet"


@pytest.mark.performance
class TestWizardPerformance:
    """Performance tests for the wizard."""
    
    def test_wizard_creation_time(self, qtbot, benchmark):
        """Benchmark wizard creation time."""
        def create_wizard():
            dialog = ExportDialog(frame_count=100)
            qtbot.addWidget(dialog)
            dialog.close()
        
        # Should create in under 500ms
        result = benchmark(create_wizard)
        assert result.stats['mean'] < 0.5
    
    def test_step_switching_time(self, qtbot, benchmark):
        """Benchmark step switching performance."""
        dialog = ExportDialog(frame_count=50)
        qtbot.addWidget(dialog)
        
        def switch_steps():
            # Forward
            dialog.wizard.set_current_step(1)
            dialog.wizard.set_current_step(2)
            # Backward
            dialog.wizard.set_current_step(1)
            dialog.wizard.set_current_step(0)
        
        # Should switch in under 100ms per step
        result = benchmark(switch_steps)
        assert result.stats['mean'] < 0.4  # 4 switches * 100ms


# Fixtures for common test data
@pytest.fixture
def test_sprites():
    """Create test sprite pixmaps."""
    sprites = []
    for i in range(16):
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor.fromHsv(i * 22, 200, 200))
        sprites.append(pixmap)
    return sprites


@pytest.fixture
def mock_preset():
    """Create a mock export preset."""
    return ExportPreset(
        name="test_preset",
        display_name="Test Preset",
        icon="🧪",
        description="Test preset for unit tests",
        mode="individual",
        format="PNG",
        scale=1.0,
        default_pattern="{name}_{index:03d}",
        tooltip="Test tooltip",
        use_cases=["Testing"],
        short_description="Test short description",
        recommended_for=["Unit testing", "Integration testing"]
    )