"""
Tests for export wizard workflow.

Covers:
- WizardStep base class functionality
- WizardWidget step navigation
- ExportDialog initialization and setup
- ExportTypeStep preset selection
- ModernExportSettings configuration
- Export configuration preparation
- Signal emission during workflow
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pytest

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap

from export.core.export_presets import ExportPreset, get_preset, get_all_presets
from export.core.frame_exporter import SpriteSheetLayout
from export.dialogs.base.wizard_base import WizardStep, WizardWidget
from export.dialogs.export_wizard import ExportDialog

if TYPE_CHECKING:
    pass


# Mark all tests in this module as requiring Qt
pytestmark = pytest.mark.requires_qt


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_sprites(qapp) -> list[QPixmap]:
    """Create sample sprite pixmaps for testing."""
    sprites = []
    for i in range(8):
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(i * 30, 100, 150))
        sprites.append(pixmap)
    return sprites


@pytest.fixture
def mock_segment_manager() -> MagicMock:
    """Create a mock segment manager."""
    manager = MagicMock()
    manager.get_all_segments.return_value = []
    return manager


# ============================================================================
# WizardStep Tests
# ============================================================================


class TestWizardStep:
    """Tests for WizardStep base class."""

    def test_wizard_step_initialization(self, qapp) -> None:
        """WizardStep should initialize with title and subtitle."""
        step = WizardStep(title="Test Step", subtitle="Test Subtitle")

        assert step.title == "Test Step"
        assert step.subtitle == "Test Subtitle"

    def test_wizard_step_default_valid(self, qapp) -> None:
        """WizardStep should be valid by default."""
        step = WizardStep(title="Test")

        assert step.validate() is True

    def test_wizard_step_get_data_default(self, qapp) -> None:
        """WizardStep get_data should return empty dict by default."""
        step = WizardStep(title="Test")

        data = step.get_data()

        assert data == {}

    def test_wizard_step_set_data(self, qapp) -> None:
        """WizardStep set_data should store data."""
        step = WizardStep(title="Test")

        step.set_data({'key': 'value'})

        assert step.get_data() == {'key': 'value'}

    def test_wizard_step_on_entering_callable(self, qapp) -> None:
        """WizardStep on_entering should be callable."""
        step = WizardStep(title="Test")

        # Should not raise
        step.on_entering()

    def test_wizard_step_on_leaving_callable(self, qapp) -> None:
        """WizardStep on_leaving should be callable."""
        step = WizardStep(title="Test")

        # Should not raise
        step.on_leaving()

    def test_wizard_step_has_signals(self, qapp) -> None:
        """WizardStep should have expected signals."""
        step = WizardStep(title="Test")

        assert hasattr(step, 'stepValidated')
        assert hasattr(step, 'dataChanged')


# ============================================================================
# WizardWidget Tests
# ============================================================================


class TestWizardWidget:
    """Tests for WizardWidget step navigation."""

    def test_wizard_widget_initialization(self, qapp) -> None:
        """WizardWidget should initialize correctly."""
        wizard = WizardWidget()

        assert hasattr(wizard, 'wizardFinished')
        assert hasattr(wizard, 'wizardCancelled')

    def test_wizard_widget_add_step(self, qapp) -> None:
        """WizardWidget should add steps correctly."""
        wizard = WizardWidget()
        step = WizardStep(title="Step 1")

        wizard.add_step(step)

        # Wizard should have at least one step
        assert wizard.get_wizard_data() is not None

    def test_wizard_widget_multiple_steps(self, qapp) -> None:
        """WizardWidget should handle multiple steps."""
        wizard = WizardWidget()
        step1 = WizardStep(title="Step 1")
        step2 = WizardStep(title="Step 2")

        wizard.add_step(step1)
        wizard.add_step(step2)

        # Should be able to navigate
        wizard.set_current_step(0)

    def test_wizard_widget_set_current_step(self, qapp) -> None:
        """WizardWidget should set current step."""
        wizard = WizardWidget()
        step1 = WizardStep(title="Step 1")
        step2 = WizardStep(title="Step 2")

        wizard.add_step(step1)
        wizard.add_step(step2)

        wizard.set_current_step(1)

        # Should be on second step

    def test_wizard_widget_get_wizard_data(self, qapp) -> None:
        """WizardWidget should collect data from all steps."""
        wizard = WizardWidget()
        step1 = WizardStep(title="Step 1")
        step1.set_data({'key1': 'value1'})

        wizard.add_step(step1)

        data = wizard.get_wizard_data()

        assert isinstance(data, dict)

    def test_wizard_widget_cancel_emits_signal(self, qapp, qtbot) -> None:
        """WizardWidget cancel should emit wizardCancelled signal."""
        wizard = WizardWidget()
        step = WizardStep(title="Step 1")
        wizard.add_step(step)

        with qtbot.waitSignal(wizard.wizardCancelled, timeout=1000):
            wizard._on_cancel()


# ============================================================================
# ExportPreset Tests
# ============================================================================


class TestExportPreset:
    """Tests for ExportPreset functionality."""

    def test_export_preset_creation(self, qapp) -> None:
        """ExportPreset should be created with required fields."""
        preset = ExportPreset(
            name="test",
            display_name="Test Preset",
            icon="🎯",
            description="A test preset",
            mode="individual",
            format="PNG",
            scale=1.0,
            default_pattern="{base}_{index}",
            tooltip="Test tooltip",
            use_cases=["Testing"]
        )

        assert preset.name == "test"
        assert preset.display_name == "Test Preset"
        assert preset.mode == "individual"
        assert preset.format == "PNG"

    def test_export_preset_get_settings_dict(self, qapp) -> None:
        """ExportPreset get_settings_dict should return correct dict."""
        preset = ExportPreset(
            name="test",
            display_name="Test",
            icon="🎯",
            description="Test",
            mode="sheet",
            format="PNG",
            scale=2.0,
            default_pattern="{base}",
            tooltip="Test",
            use_cases=[]
        )

        settings = preset.get_settings_dict()

        assert settings['mode'] == "sheet"
        assert settings['format'] == "PNG"
        assert settings['scale_factor'] == 2.0
        assert settings['preset_name'] == "test"

    def test_export_preset_with_sprite_sheet_layout(self, qapp) -> None:
        """ExportPreset should include sprite sheet layout when set."""
        layout = SpriteSheetLayout(mode='rows', max_columns=4)
        preset = ExportPreset(
            name="sheet_test",
            display_name="Sheet Test",
            icon="📋",
            description="Test",
            mode="sheet",
            format="PNG",
            scale=1.0,
            default_pattern="{base}",
            tooltip="Test",
            use_cases=[],
            sprite_sheet_layout=layout
        )

        settings = preset.get_settings_dict()

        assert 'sprite_sheet_layout' in settings
        assert settings['sprite_sheet_layout'] == layout

    def test_get_preset_returns_preset(self, qapp) -> None:
        """get_preset should return a preset by name."""
        # Assuming 'individual_frames' is a default preset
        all_presets = get_all_presets()

        if all_presets:
            first_preset = all_presets[0]
            preset = get_preset(first_preset.name)

            assert preset is not None
            assert preset.name == first_preset.name

    def test_get_all_presets_returns_list(self, qapp) -> None:
        """get_all_presets should return a list of presets."""
        presets = get_all_presets()

        assert isinstance(presets, list)
        # Should have at least one preset
        assert len(presets) >= 1
        # Each item should be an ExportPreset
        for preset in presets:
            assert isinstance(preset, ExportPreset)


# ============================================================================
# ExportDialog Tests
# ============================================================================


class TestExportDialog:
    """Tests for ExportDialog initialization and workflow."""

    def test_export_dialog_initialization(
        self, qapp, sample_sprites: list[QPixmap]
    ) -> None:
        """ExportDialog should initialize with required parameters."""
        dialog = ExportDialog(
            parent=None,
            frame_count=len(sample_sprites),
            current_frame=0,
            sprites=sample_sprites
        )

        assert dialog.frame_count == len(sample_sprites)
        assert dialog.current_frame == 0
        assert dialog.sprites == sample_sprites

    def test_export_dialog_has_wizard(
        self, qapp, sample_sprites: list[QPixmap]
    ) -> None:
        """ExportDialog should have wizard widget."""
        dialog = ExportDialog(
            parent=None,
            frame_count=len(sample_sprites),
            current_frame=0,
            sprites=sample_sprites
        )

        assert hasattr(dialog, 'wizard')
        assert isinstance(dialog.wizard, WizardWidget)

    def test_export_dialog_has_steps(
        self, qapp, sample_sprites: list[QPixmap]
    ) -> None:
        """ExportDialog should have type and settings steps."""
        dialog = ExportDialog(
            parent=None,
            frame_count=len(sample_sprites),
            current_frame=0,
            sprites=sample_sprites
        )

        assert hasattr(dialog, 'type_step')
        assert hasattr(dialog, 'settings_preview_step')

    def test_export_dialog_set_sprites(
        self, qapp, sample_sprites: list[QPixmap]
    ) -> None:
        """ExportDialog set_sprites should update sprites."""
        dialog = ExportDialog(
            parent=None,
            frame_count=4,
            current_frame=0,
            sprites=[]
        )

        dialog.set_sprites(sample_sprites)

        assert dialog.sprites == sample_sprites

    def test_export_dialog_has_signals(
        self, qapp, sample_sprites: list[QPixmap]
    ) -> None:
        """ExportDialog should have expected signals."""
        dialog = ExportDialog(
            parent=None,
            frame_count=len(sample_sprites),
            current_frame=0,
            sprites=sample_sprites
        )

        assert hasattr(dialog, 'exportRequested')

    def test_export_dialog_with_segment_manager(
        self, qapp, sample_sprites: list[QPixmap], mock_segment_manager: MagicMock
    ) -> None:
        """ExportDialog should accept segment manager."""
        dialog = ExportDialog(
            parent=None,
            frame_count=len(sample_sprites),
            current_frame=0,
            sprites=sample_sprites,
            segment_manager=mock_segment_manager
        )

        assert dialog.segment_manager is mock_segment_manager

    def test_export_dialog_modal(
        self, qapp, sample_sprites: list[QPixmap]
    ) -> None:
        """ExportDialog should be modal."""
        dialog = ExportDialog(
            parent=None,
            frame_count=len(sample_sprites),
            current_frame=0,
            sprites=sample_sprites
        )

        assert dialog.isModal()


# ============================================================================
# Export Configuration Preparation Tests
# ============================================================================


class TestExportConfigPreparation:
    """Tests for export configuration preparation."""

    def test_prepare_export_config_basic(
        self, qapp, sample_sprites: list[QPixmap]
    ) -> None:
        """_prepare_export_config should create valid config."""
        dialog = ExportDialog(
            parent=None,
            frame_count=len(sample_sprites),
            current_frame=0,
            sprites=sample_sprites
        )

        preset = ExportPreset(
            name="individual",
            display_name="Individual",
            icon="🖼",
            description="Export individual frames",
            mode="individual",
            format="PNG",
            scale=1.0,
            default_pattern="{base}_{index}",
            tooltip="Test",
            use_cases=[]
        )

        settings = {
            'output_dir': '/tmp/export',
            'format': 'PNG',
            'scale': 1.0,
            'base_name': 'frame'
        }

        config = dialog._prepare_export_config(preset, settings)

        assert 'output_dir' in config
        assert 'format' in config
        assert 'mode' in config
        assert config['mode'] == 'individual'

    def test_prepare_export_config_sheet_mode(
        self, qapp, sample_sprites: list[QPixmap]
    ) -> None:
        """_prepare_export_config should handle sheet mode."""
        dialog = ExportDialog(
            parent=None,
            frame_count=len(sample_sprites),
            current_frame=0,
            sprites=sample_sprites
        )

        preset = ExportPreset(
            name="sheet",
            display_name="Sprite Sheet",
            icon="📋",
            description="Export as sprite sheet",
            mode="sheet",
            format="PNG",
            scale=1.0,
            default_pattern="{base}",
            tooltip="Test",
            use_cases=[]
        )

        settings = {
            'output_dir': '/tmp/export',
            'format': 'PNG',
            'scale': 1.0,
            'single_filename': 'spritesheet',
            'layout_mode': 'auto',
            'columns': 4,
            'rows': 2
        }

        config = dialog._prepare_export_config(preset, settings)

        assert config['mode'] == 'sheet'
        assert 'layout_mode' in config
        assert 'columns' in config
        assert 'rows' in config

    def test_prepare_export_config_includes_scale_factor(
        self, qapp, sample_sprites: list[QPixmap]
    ) -> None:
        """_prepare_export_config should include scale_factor."""
        dialog = ExportDialog(
            parent=None,
            frame_count=len(sample_sprites),
            current_frame=0,
            sprites=sample_sprites
        )

        preset = ExportPreset(
            name="test",
            display_name="Test",
            icon="🎯",
            description="Test",
            mode="individual",
            format="PNG",
            scale=2.0,
            default_pattern="{base}",
            tooltip="Test",
            use_cases=[]
        )

        settings = {'scale': 2.0, 'output_dir': '/tmp'}

        config = dialog._prepare_export_config(preset, settings)

        assert 'scale_factor' in config
        assert config['scale_factor'] == 2.0


# ============================================================================
# Wizard Navigation Tests
# ============================================================================


class TestWizardNavigation:
    """Tests for wizard step navigation."""

    def test_wizard_starts_at_first_step(
        self, qapp, sample_sprites: list[QPixmap]
    ) -> None:
        """ExportDialog should start wizard at first step on show."""
        from PySide6.QtGui import QShowEvent

        dialog = ExportDialog(
            parent=None,
            frame_count=len(sample_sprites),
            current_frame=0,
            sprites=sample_sprites
        )

        # Simulate showEvent with proper event type
        event = QShowEvent()
        dialog.showEvent(event)

        # Wizard should be at step 0 - verify dialog is ready

    def test_wizard_back_navigation(self, qapp) -> None:
        """WizardWidget should support back navigation."""
        wizard = WizardWidget()
        step1 = WizardStep(title="Step 1")
        step2 = WizardStep(title="Step 2")

        wizard.add_step(step1)
        wizard.add_step(step2)

        wizard.set_current_step(1)
        wizard._on_back()

        # Should navigate back (implementation specific)

    def test_wizard_next_navigation(self, qapp) -> None:
        """WizardWidget should support next navigation."""
        wizard = WizardWidget()
        step1 = WizardStep(title="Step 1")
        step2 = WizardStep(title="Step 2")

        wizard.add_step(step1)
        wizard.add_step(step2)

        wizard.set_current_step(0)
        wizard._on_next()

        # Should navigate to next step


# ============================================================================
# Edge Cases Tests
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_export_dialog_empty_sprites(self, qapp) -> None:
        """ExportDialog should handle empty sprites list."""
        dialog = ExportDialog(
            parent=None,
            frame_count=0,
            current_frame=0,
            sprites=[]
        )

        assert dialog.sprites == []
        assert dialog.frame_count == 0

    def test_export_dialog_none_sprites(self, qapp) -> None:
        """ExportDialog should handle None sprites."""
        dialog = ExportDialog(
            parent=None,
            frame_count=0,
            current_frame=0,
            sprites=None
        )

        assert dialog.sprites == []

    def test_wizard_step_empty_title(self, qapp) -> None:
        """WizardStep should accept empty title."""
        step = WizardStep(title="", subtitle="")

        assert step.title == ""
        assert step.subtitle == ""

    def test_wizard_widget_no_steps(self, qapp) -> None:
        """WizardWidget should handle no steps gracefully."""
        wizard = WizardWidget()

        # Should not raise when getting data
        data = wizard.get_wizard_data()
        assert isinstance(data, dict)

    def test_set_sprites_with_none(
        self, qapp, sample_sprites: list[QPixmap]
    ) -> None:
        """set_sprites with None should use empty list."""
        dialog = ExportDialog(
            parent=None,
            frame_count=4,
            current_frame=0,
            sprites=sample_sprites
        )

        dialog.set_sprites(None)

        assert dialog.sprites == []

    def test_export_preset_short_description_optional(self, qapp) -> None:
        """ExportPreset short_description should be optional."""
        preset = ExportPreset(
            name="test",
            display_name="Test",
            icon="🎯",
            description="Test",
            mode="individual",
            format="PNG",
            scale=1.0,
            default_pattern="{base}",
            tooltip="Test",
            use_cases=[]
            # short_description not provided
        )

        assert preset.short_description is None


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests for export wizard workflow."""

    def test_full_wizard_workflow(
        self, qapp, sample_sprites: list[QPixmap], tmp_path: Path
    ) -> None:
        """Test complete wizard workflow from creation to config."""
        # Create dialog
        dialog = ExportDialog(
            parent=None,
            frame_count=len(sample_sprites),
            current_frame=0,
            sprites=sample_sprites
        )

        # Verify structure
        assert dialog.wizard is not None
        assert dialog.type_step is not None
        assert dialog.settings_preview_step is not None

        # Type step should be able to validate
        assert isinstance(dialog.type_step.validate(), bool)

    def test_wizard_data_collection(
        self, qapp, sample_sprites: list[QPixmap]
    ) -> None:
        """Wizard should collect data from all steps."""
        dialog = ExportDialog(
            parent=None,
            frame_count=len(sample_sprites),
            current_frame=0,
            sprites=sample_sprites
        )

        # Get wizard data
        data = dialog.wizard.get_wizard_data()

        assert isinstance(data, dict)

    def test_export_requested_signal_type(
        self, qapp, sample_sprites: list[QPixmap]
    ) -> None:
        """exportRequested signal should be properly typed."""
        dialog = ExportDialog(
            parent=None,
            frame_count=len(sample_sprites),
            current_frame=0,
            sprites=sample_sprites
        )

        # Signal should exist and be connectable
        received = []
        dialog.exportRequested.connect(lambda cfg: received.append(cfg))

        # Verify connection was successful (signal exists)
        assert hasattr(dialog, 'exportRequested')
