"""
CCL UI Availability Tests - Ensures CCL mode is always accessible.
Tests the fix for CCL button being disabled when auto-detection fails.
"""

import pytest

# Mark all tests as integration tests (requires_files only for specific tests)
pytestmark = [pytest.mark.integration]
from pathlib import Path
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QApplication

from sprite_model.extraction_mode import ExtractionMode


class TestCCLUIAvailability:
    """Test that CCL extraction mode is always available when sprite is loaded."""
    
    @pytest.fixture
    def test_sprite_path(self):
        """Get a test sprite path."""
        # Try to find Ark.png since we know it works with CCL
        possible_paths = [
            Path("spritetests/Ark.png"),
            Path(__file__).parent.parent.parent / "spritetests" / "Ark.png"
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path.absolute())
        
        # Return fake path for UI testing
        return "/fake/test/sprite.png"
    
    def test_ccl_button_initially_enabled(self, qtbot):
        """Test that CCL button is enabled by default."""
        from sprite_viewer import SpriteViewer
        
        print("\n🔍 TESTING INITIAL CCL STATE")
        print("=" * 35)
        
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # Check that CCL button is enabled (new behavior - always available)
        frame_extractor = viewer._frame_extractor
        ccl_button = frame_extractor.ccl_mode_btn
        
        # CCL is now always available, so button should be enabled
        assert ccl_button.isEnabled(), "CCL button should be enabled by default"
        print("✅ CCL button correctly enabled (always available)")
    
    def test_ccl_availability_methods_exist(self, qtbot):
        """Test that all CCL availability methods exist."""
        from sprite_viewer import SpriteViewer
        
        print("\n🔍 TESTING CCL AVAILABILITY METHODS")
        print("=" * 40)
        
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # Test SpriteModel has CCL methods
        sprite_model = viewer._sprite_model
        assert hasattr(sprite_model, 'is_ccl_available'), "SpriteModel missing is_ccl_available method"
        assert hasattr(sprite_model, 'get_ccl_sprite_bounds'), "SpriteModel missing get_ccl_sprite_bounds method"
        assert hasattr(sprite_model, 'extract_ccl_frames'), "SpriteModel missing extract_ccl_frames method"
        assert hasattr(sprite_model, 'set_extraction_mode'), "SpriteModel missing set_extraction_mode method"
        print("✅ SpriteModel CCL methods exist")
        
        # Test FrameExtractor has set_ccl_available method
        frame_extractor = viewer._frame_extractor
        assert hasattr(frame_extractor, 'set_ccl_available'), "FrameExtractor missing set_ccl_available method"
        assert hasattr(frame_extractor, 'get_extraction_mode'), "FrameExtractor missing get_extraction_mode method"
        print("✅ FrameExtractor CCL methods exist")
    
    def test_ccl_remains_enabled_after_sprite_load(self, test_sprite_path, qtbot):
        """Test that CCL stays enabled after sprite loading."""
        from sprite_viewer import SpriteViewer
        
        print("\n🔍 TESTING CCL STATE AFTER SPRITE LOAD")
        print("=" * 45)
        
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # CCL should be enabled by default
        ccl_button = viewer._frame_extractor.ccl_mode_btn
        assert ccl_button.isEnabled(), "CCL should be enabled by default"
        print("✅ Confirmed CCL is enabled by default")
        
        # Mock sprite loading success
        with patch.object(viewer._sprite_model, 'load_sprite_sheet') as mock_load:
            mock_load.return_value = (True, None)  # Success, no error

            # Simulate loading directly through the viewer's load method
            viewer._load_sprite_file(test_sprite_path)

            # Process pending events
            QApplication.processEvents()

            # CCL should still be enabled
            assert ccl_button.isEnabled(), "CCL button should remain enabled after sprite load"
            print("✅ CCL button remains enabled after sprite loading")
    
    def test_ccl_independent_of_auto_detection(self, qtbot):
        """Test that CCL availability is always enabled (new design)."""
        from sprite_viewer import SpriteViewer
        
        print("\n🔍 TESTING CCL INDEPENDENCE FROM AUTO-DETECTION")
        print("=" * 50)
        
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # CCL should be enabled by default (new behavior)
        ccl_button = viewer._frame_extractor.ccl_mode_btn
        assert ccl_button.isEnabled(), "CCL should be enabled by default"
        
        # Mock auto-detection failure
        with patch.object(viewer._auto_detection_controller, 'run_comprehensive_detection_with_dialog') as mock_detection:
            mock_detection.side_effect = Exception("Auto-detection failed")

            # Mock sprite model methods
            with patch.object(viewer._sprite_model, 'load_sprite_sheet') as mock_load:
                mock_load.return_value = (True, None)

                # Simulate file loading directly through viewer
                viewer._load_sprite_file("/fake/test.png")
                QApplication.processEvents()

                # CCL should still be enabled despite auto-detection issues
                assert ccl_button.isEnabled(), "CCL should remain enabled regardless of auto-detection"
                print("✅ CCL remains enabled independent of auto-detection")
    
    def test_ccl_mode_switching(self, qtbot):
        """Test switching between Grid and CCL extraction modes."""
        from sprite_viewer import SpriteViewer
        
        print("\n🔍 TESTING CCL MODE SWITCHING")
        print("=" * 45)
        
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        frame_extractor = viewer._frame_extractor
        ccl_button = frame_extractor.ccl_mode_btn
        grid_button = frame_extractor.grid_mode_btn
        
        # Both buttons should be enabled
        assert ccl_button.isEnabled(), "CCL button should be enabled"
        assert grid_button.isEnabled(), "Grid button should be enabled"
        
        # Default is now CCL mode (new behavior)
        assert ccl_button.isChecked(), "CCL mode should be default"
        assert not grid_button.isChecked(), "Grid mode should not be checked by default"
        
        # Switch to Grid mode (from default CCL)
        grid_button.click()
        assert grid_button.isChecked(), "Grid mode should be checked after click"
        assert not ccl_button.isChecked(), "CCL mode should be unchecked"
        print("✅ Successfully switched to Grid mode")
        
        # Switch back to CCL mode
        ccl_button.click()
        assert ccl_button.isChecked(), "CCL mode should be checked after click"
        assert not grid_button.isChecked(), "Grid mode should be unchecked"
        print("✅ Successfully switched back to CCL mode")
    
    def test_ccl_enabled_in_sprite_loaded_handler(self, qtbot):
        """Test that CCL is enabled when sprite is loaded."""
        from sprite_viewer import SpriteViewer
        
        print("\n🔍 TESTING CCL ENABLEMENT IN SPRITE LOADED HANDLER")
        print("=" * 50)
        
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # Mock set_ccl_available to verify it's called
        with patch.object(viewer._frame_extractor, 'set_ccl_available') as mock_set_ccl:
            
            # Call _on_sprite_loaded (this is what happens after successful sprite loading)
            viewer._on_sprite_loaded("/fake/test.png")
            
            # Verify that set_ccl_available was called with True
            mock_set_ccl.assert_called_once_with(True, 0)
            print("✅ CCL enabled via set_ccl_available(True, 0) in _on_sprite_loaded handler")
    
    def test_real_ccl_workflow_with_ark_png(self, qtbot):
        """Test real CCL workflow with Ark.png if available.""" 
        from sprite_viewer import SpriteViewer
        
        # Try to find Ark.png
        ark_path = Path(__file__).parent.parent.parent / "spritetests" / "Ark.png"
        if not ark_path.exists():
            pytest.skip("Ark.png not available for real CCL testing")
        
        print("\n🔍 TESTING REAL CCL WORKFLOW WITH ARK.PNG")
        print("=" * 45)
        
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # Load Ark.png
        success, error = viewer._sprite_model.load_sprite_sheet(str(ark_path))
        
        if success:
            # Simulate the sprite loaded handler
            viewer._on_sprite_loaded(str(ark_path))
            
            # CCL should now be available
            ccl_button = viewer._frame_extractor.ccl_mode_btn
            assert ccl_button.isEnabled(), "CCL should be enabled with real sprite sheet"
            print("✅ CCL enabled with real Ark.png sprite sheet")
            
            # Test that we can actually set CCL mode
            ccl_button.setChecked(True)
            viewer._sprite_model.set_extraction_mode(ExtractionMode.CCL)
            
            # Should have sprites
            frames = viewer._sprite_model.sprite_frames
            frame_count = len(frames) if frames else 0
            assert frame_count > 0, "CCL should extract sprites from Ark.png"
            print(f"✅ CCL extracted {frame_count} sprites from Ark.png")
        else:
            print(f"⚠️  Could not load Ark.png: {error}")
            pytest.skip("Could not load Ark.png for testing")


class TestCCLRegressionPrevention:
    """Prevent regression of CCL availability issues."""
    
    def test_ccl_availability_integration_checklist(self, qtbot):
        """Comprehensive checklist to prevent CCL availability regressions."""
        from sprite_viewer import SpriteViewer
        
        print("\n📋 CCL AVAILABILITY REGRESSION PREVENTION CHECKLIST")
        print("=" * 55)
        
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # Checklist of requirements (updated for new behavior)
        requirements = [
            ("SpriteModel has is_ccl_available method",
             lambda: hasattr(viewer._sprite_model, 'is_ccl_available')),
             
            ("SpriteModel has get_ccl_sprite_bounds method", 
             lambda: hasattr(viewer._sprite_model, 'get_ccl_sprite_bounds')),
             
            ("SpriteModel has extract_ccl_frames method",
             lambda: hasattr(viewer._sprite_model, 'extract_ccl_frames')),
             
            ("SpriteModel has set_extraction_mode method",
             lambda: hasattr(viewer._sprite_model, 'set_extraction_mode')),
             
            ("FrameExtractor has set_ccl_available method",
             lambda: hasattr(viewer._frame_extractor, 'set_ccl_available')),
             
            ("FrameExtractor has ccl_mode_btn attribute",
             lambda: hasattr(viewer._frame_extractor, 'ccl_mode_btn')),
             
            ("CCL button is enabled by default",
             lambda: viewer._frame_extractor.ccl_mode_btn.isEnabled()),
             
            ("CCL mode is selected by default",
             lambda: viewer._frame_extractor.ccl_mode_btn.isChecked()),
        ]
        
        # Check all requirements
        for description, check_func in requirements:
            try:
                result = check_func()
                assert result, f"FAILED: {description}"
                print(f"✅ {description}")
            except Exception as e:
                pytest.fail(f"❌ {description} - Error: {e}")
        
        print("\n🎉 ALL CCL AVAILABILITY REQUIREMENTS MET!")
        print("🛡️  CCL availability regression prevented!")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])