"""
Unit tests for new settings and export configuration classes.
Tests the configuration additions for settings persistence and export functionality.
"""

import pytest


def test_settings_config_import():
    """Test that SettingsConfig can be imported and has expected structure."""
    from config import ExportConfig, Config

    # Access SettingsConfig via Config (now nested under AppConfig)
    SettingsConfig = Config.Settings

    # Verify settings config structure
    assert hasattr(SettingsConfig, 'ORGANIZATION_NAME')
    assert hasattr(SettingsConfig, 'APPLICATION_NAME')
    assert hasattr(SettingsConfig, 'MAX_RECENT_FILES')
    assert hasattr(SettingsConfig, 'DEFAULTS')

    # Verify export config structure
    assert hasattr(ExportConfig, 'IMAGE_FORMATS')
    assert hasattr(ExportConfig, 'DEFAULT_FORMAT')

    # Verify integration with main Config class
    assert hasattr(Config, 'Settings')
    assert hasattr(Config, 'Export')
    assert Config.Export == ExportConfig


def test_settings_defaults_structure():
    """Test that settings defaults are properly structured."""
    from config import Config

    defaults = Config.Settings.DEFAULTS

    # Test required settings exist
    required_settings = [
        'window/geometry',
        'window/state',
        'window/splitter_state',
        'extraction/last_width',
        'extraction/last_height',
        'extraction/last_mode',
        'display/grid_visible',
        'display/last_zoom',
        'animation/last_fps',
        'recent/files'
    ]

    for setting in required_settings:
        assert setting in defaults, f"Missing default setting: {setting}"

    # Test setting types are reasonable
    assert isinstance(defaults['extraction/last_width'], int)
    assert isinstance(defaults['extraction/last_height'], int)
    assert isinstance(defaults['display/grid_visible'], bool)
    assert isinstance(defaults['recent/files'], list)
    assert isinstance(defaults['recent/max_count'], int)

    # Test reasonable default values
    assert defaults['extraction/last_width'] > 0
    assert defaults['extraction/last_height'] > 0
    assert defaults['recent/max_count'] > 0
    assert defaults['animation/last_fps'] > 0


def test_export_config_values():
    """Test export configuration values are reasonable."""
    from config import ExportConfig

    # Test image formats
    assert 'PNG' in ExportConfig.IMAGE_FORMATS
    assert 'JPG' in ExportConfig.IMAGE_FORMATS
    assert ExportConfig.DEFAULT_FORMAT in ExportConfig.IMAGE_FORMATS

    # Test naming pattern
    assert '{name}' in ExportConfig.DEFAULT_PATTERN
    assert '{index' in ExportConfig.DEFAULT_PATTERN

    # Test scale factors
    assert 1.0 in ExportConfig.DEFAULT_SCALE_FACTORS
    assert all(factor > 0 for factor in ExportConfig.DEFAULT_SCALE_FACTORS)

    # Test layout modes
    assert 'auto' in ExportConfig.LAYOUT_MODES
    assert ExportConfig.DEFAULT_LAYOUT_MODE == 'auto'


def test_config_integration():
    """Test that new configs integrate properly with existing Config class."""
    from config import Config

    # Test all config sections are accessible (Color was removed from Config)
    config_sections = [
        'Canvas', 'Animation', 'FrameExtraction', 'UI',
        'Drawing', 'File', 'Slider', 'Font',
        'App', 'Settings', 'Export'
    ]

    for section in config_sections:
        assert hasattr(Config, section), f"Missing config section: {section}"

    # Test Settings config access
    assert hasattr(Config.Settings, 'MAX_RECENT_FILES')
    assert hasattr(Config.Settings, 'DEFAULTS')

    # Test Export config access
    assert hasattr(Config.Export, 'IMAGE_FORMATS')
    assert hasattr(Config.Export, 'DEFAULT_FORMAT')


if __name__ == '__main__':
    # Add parent directory to path for direct execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    # Run tests directly
    test_settings_config_import()
    test_settings_defaults_structure()
    test_export_config_values()
    test_config_integration()
    print("All settings config tests passed!")
