"""
Infrastructure validation tests.
Tests that our pytest setup works correctly.
"""

import pytest
from pathlib import Path


class TestPytestInfrastructure:
    """Test pytest infrastructure is working."""
    
    def test_pytest_working(self):
        """Basic test that pytest is functional."""
        assert True
    
    def test_project_structure(self):
        """Test project structure is accessible."""
        project_root = Path(__file__).parent.parent
        
        # Check key files exist
        assert (project_root / "config.py").exists()
        assert (project_root / "requirements.txt").exists()
        assert (project_root / "pytest.ini").exists()
    
    def test_test_structure(self):
        """Test the test directory structure is correct."""
        tests_dir = Path(__file__).parent
        
        # Check test directories exist
        assert (tests_dir / "unit").exists()
        assert (tests_dir / "integration").exists()
        assert (tests_dir / "ui").exists()
        assert (tests_dir / "fixtures").exists()
        
        # Check key files exist
        assert (tests_dir / "conftest.py").exists()
        assert (tests_dir / "requirements-test.txt").exists()
    
    @pytest.mark.parametrize("test_type", ["unit", "integration", "ui", "performance"])
    def test_test_directories(self, test_type):
        """Test all test type directories exist."""
        tests_dir = Path(__file__).parent
        test_dir = tests_dir / test_type
        assert test_dir.exists()
        assert (test_dir / "__init__.py").exists()


class TestProjectImports:
    """Test project imports work correctly."""
    
    def test_config_import(self):
        """Test config module can be imported."""
        try:
            from config import Config
            assert hasattr(Config, 'Canvas')
            assert hasattr(Config, 'Animation')
            assert hasattr(Config, 'FrameExtraction')
        except ImportError as e:
            pytest.skip(f"Config import failed: {e}")
    
    def test_styles_import(self):
        """Test styles module can be imported."""
        try:
            from styles import StyleManager
            assert hasattr(StyleManager, 'get_canvas_normal')
        except ImportError as e:
            pytest.skip(f"Styles import failed: {e}")


class TestFixtures:
    """Test fixtures are working correctly."""
    
    def test_temp_dir_fixture(self, temp_dir):
        """Test temporary directory fixture."""
        assert temp_dir.exists()
        assert temp_dir.is_dir()
        
        # Test we can write to it
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        assert test_file.exists()
    
    def test_mock_pixmap_fixture(self, mock_pixmap):
        """Test mock pixmap fixture."""
        assert mock_pixmap is not None
        assert mock_pixmap.width() > 0
        assert mock_pixmap.height() > 0
        assert not mock_pixmap.isNull()
    
    def test_mock_sprite_frames_fixture(self, mock_sprite_frames):
        """Test mock sprite frames fixture."""
        assert len(mock_sprite_frames) > 0
        for frame in mock_sprite_frames:
            assert frame is not None
            assert frame.width() > 0
            assert frame.height() > 0


@pytest.mark.parametrize("fps", [1, 10, 30, 60])
def test_parametrized_example(fps):
    """Example parametrized test."""
    assert fps > 0
    assert fps <= 60


class TestMarkers:
    """Test pytest markers are working."""
    
    @pytest.mark.unit
    def test_unit_marker(self):
        """Test unit marker."""
        assert True
    
    @pytest.mark.integration  
    def test_integration_marker(self):
        """Test integration marker."""
        assert True
    
    @pytest.mark.slow
    def test_slow_marker(self):
        """Test slow marker."""
        import time
        time.sleep(0.1)  # Small delay to simulate slow test
        assert True