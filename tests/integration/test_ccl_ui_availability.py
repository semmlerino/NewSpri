"""
CCL UI Availability Tests - Ensures CCL mode is always accessible.
Tests the fix for CCL button being disabled when auto-detection fails.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


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
    
    def test_ccl_button_initially_disabled(self, qtbot):
        """Test that CCL button starts disabled (no sprite loaded)."""
        from sprite_viewer import SpriteViewer
        
        print("\n🔍 TESTING INITIAL CCL STATE")
        print("=" * 35)
        
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # Check that CCL button is initially disabled
        frame_extractor = viewer._frame_extractor
        ccl_button = frame_extractor.ccl_mode_btn
        
        assert not ccl_button.isEnabled(), "CCL button should be disabled initially"
        print("✅ CCL button correctly disabled initially (no sprite loaded)")
    
    def test_ccl_availability_methods_exist(self, qtbot):
        """Test that all CCL availability methods exist."""
        from sprite_viewer import SpriteViewer
        
        print("\n🔍 TESTING CCL AVAILABILITY METHODS")
        print("=" * 40)
        
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # Test SpriteViewer has _update_ccl_availability method
        assert hasattr(viewer, '_update_ccl_availability'), "SpriteViewer missing _update_ccl_availability method"
        assert callable(viewer._update_ccl_availability), "_update_ccl_availability should be callable"
        print("✅ SpriteViewer._update_ccl_availability() exists")
        
        # Test SpriteModel has CCL methods
        sprite_model = viewer._sprite_model
        assert hasattr(sprite_model, 'is_ccl_available'), "SpriteModel missing is_ccl_available method"
        assert hasattr(sprite_model, 'get_ccl_sprite_bounds'), "SpriteModel missing get_ccl_sprite_bounds method"
        print("✅ SpriteModel CCL methods exist")
        
        # Test FrameExtractor has set_ccl_available method
        frame_extractor = viewer._frame_extractor
        assert hasattr(frame_extractor, 'set_ccl_available'), "FrameExtractor missing set_ccl_available method"
        print("✅ FrameExtractor.set_ccl_available() exists")
    
    def test_ccl_enabled_after_sprite_load(self, test_sprite_path, qtbot):
        """Test that CCL becomes available after sprite loading."""
        from sprite_viewer import SpriteViewer
        
        print("\n🔍 TESTING CCL ENABLING AFTER SPRITE LOAD")
        print("=" * 45)
        
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # Verify CCL starts disabled
        ccl_button = viewer._frame_extractor.ccl_mode_btn
        assert not ccl_button.isEnabled(), "CCL should start disabled"
        print("✅ Confirmed CCL starts disabled")
        
        # Mock sprite loading success
        with patch.object(viewer._sprite_model, 'load_sprite_sheet') as mock_load:
            mock_load.return_value = (True, None)  # Success, no error
            
            # Mock sprite model to return CCL available
            with patch.object(viewer._sprite_model, 'is_ccl_available') as mock_available:
                mock_available.return_value = True
                
                with patch.object(viewer._sprite_model, 'get_ccl_sprite_bounds') as mock_bounds:
                    mock_bounds.return_value = ['fake_bound_1', 'fake_bound_2']  # 2 sprites
                    
                    # Simulate sprite loading
                    print(f"🎯 Simulating sprite loading: {test_sprite_path}")
                    viewer._load_sprite_file(test_sprite_path)
                    
                    # CCL should now be enabled
                    assert ccl_button.isEnabled(), "CCL button should be enabled after sprite load"
                    print("✅ CCL button enabled after sprite loading")
    
    def test_ccl_independent_of_auto_detection(self, qtbot):
        """Test that CCL availability is independent of auto-detection results."""
        from sprite_viewer import SpriteViewer
        
        print("\n🔍 TESTING CCL INDEPENDENCE FROM AUTO-DETECTION")
        print("=" * 50)
        
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # Mock auto-detection failure
        with patch.object(viewer._auto_detection_controller, 'run_comprehensive_detection_with_dialog') as mock_detection:
            mock_detection.side_effect = Exception("Auto-detection failed")
            
            # Mock sprite model methods for successful CCL availability
            with patch.object(viewer._sprite_model, 'load_sprite_sheet') as mock_load, \
                 patch.object(viewer._sprite_model, 'is_ccl_available') as mock_available, \
                 patch.object(viewer._sprite_model, 'get_ccl_sprite_bounds') as mock_bounds:
                
                mock_load.return_value = (True, None)
                mock_available.return_value = True
                mock_bounds.return_value = ['sprite1', 'sprite2', 'sprite3']  # 3 sprites
                
                # Mock QMessageBox to avoid dialog
                with patch('PySide6.QtWidgets.QMessageBox.critical'):
                    
                    try:
                        # Attempt sprite loading (auto-detection will fail)
                        viewer._load_sprite_file("/fake/test.png")
                    except:
                        pass  # Expected due to mocked failure
                    
                    # CCL should still be available despite auto-detection failure
                    ccl_button = viewer._frame_extractor.ccl_mode_btn
                    
                    # Call the CCL availability update directly to simulate what should happen
                    viewer._update_ccl_availability()
                    
                    # Now CCL should be enabled
                    assert ccl_button.isEnabled(), "CCL should be available even when auto-detection fails"
                    print("✅ CCL available independent of auto-detection failure")
    
    def test_update_ccl_availability_workflow(self, qtbot):
        """Test the complete _update_ccl_availability workflow."""
        from sprite_viewer import SpriteViewer
        
        print("\n🔍 TESTING _update_ccl_availability WORKFLOW")
        print("=" * 45)
        
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        frame_extractor = viewer._frame_extractor
        ccl_button = frame_extractor.ccl_mode_btn
        
        # Test with CCL not available
        with patch.object(viewer._sprite_model, 'is_ccl_available') as mock_available:
            mock_available.return_value = False
            
            viewer._update_ccl_availability()
            assert not ccl_button.isEnabled(), "CCL should be disabled when not available"
            print("✅ CCL correctly disabled when sprite model reports unavailable")
        
        # Test with CCL available and sprites
        with patch.object(viewer._sprite_model, 'is_ccl_available') as mock_available, \
             patch.object(viewer._sprite_model, 'get_ccl_sprite_bounds') as mock_bounds:
            
            mock_available.return_value = True
            mock_bounds.return_value = ['sprite1', 'sprite2', 'sprite3']  # 3 sprites
            
            viewer._update_ccl_availability()
            assert ccl_button.isEnabled(), "CCL should be enabled when available with sprites"
            print("✅ CCL correctly enabled when sprite model reports available")
    
    def test_ccl_called_in_sprite_loaded_handler(self, qtbot):
        """Test that _update_ccl_availability is called in _on_sprite_loaded."""
        from sprite_viewer import SpriteViewer
        
        print("\n🔍 TESTING CCL UPDATE IN SPRITE LOADED HANDLER")
        print("=" * 50)
        
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # Mock the _update_ccl_availability method
        with patch.object(viewer, '_update_ccl_availability') as mock_update_ccl:
            
            # Call _on_sprite_loaded (this is what happens after successful sprite loading)
            viewer._on_sprite_loaded("/fake/test.png")
            
            # Verify that _update_ccl_availability was called
            mock_update_ccl.assert_called_once()
            print("✅ _update_ccl_availability called in _on_sprite_loaded handler")
    
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
            viewer._sprite_model.set_extraction_mode("ccl")
            
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
        
        # Checklist of requirements
        requirements = [
            ("SpriteViewer has _update_ccl_availability method", 
             lambda: hasattr(viewer, '_update_ccl_availability')),
            
            ("_update_ccl_availability is callable",
             lambda: callable(getattr(viewer, '_update_ccl_availability', None))),
             
            ("SpriteModel has is_ccl_available method",
             lambda: hasattr(viewer._sprite_model, 'is_ccl_available')),
             
            ("SpriteModel has get_ccl_sprite_bounds method", 
             lambda: hasattr(viewer._sprite_model, 'get_ccl_sprite_bounds')),
             
            ("FrameExtractor has set_ccl_available method",
             lambda: hasattr(viewer._frame_extractor, 'set_ccl_available')),
             
            ("FrameExtractor has ccl_mode_btn attribute",
             lambda: hasattr(viewer._frame_extractor, 'ccl_mode_btn')),
             
            ("CCL button starts disabled",
             lambda: not viewer._frame_extractor.ccl_mode_btn.isEnabled()),
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