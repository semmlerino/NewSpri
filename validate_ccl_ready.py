#!/usr/bin/env python3
"""
Validate that CCL integration is ready for user testing.
"""

def check_ccl_availability():
    """Check if CCL dependencies are available."""
    try:
        import numpy as np
        import scipy.ndimage
        from PIL import Image
        print("✅ All CCL dependencies available:")
        print(f"   📦 NumPy: {np.__version__}")
        print(f"   📦 SciPy: {scipy.__version__}")
        print(f"   📦 Pillow: {Image.__version__}")
        return True
    except ImportError as e:
        print(f"❌ CCL dependencies missing: {e}")
        return False

def check_syntax():
    """Check if sprite_model.py has valid syntax."""
    try:
        import py_compile
        py_compile.compile('sprite_model.py', doraise=True)
        print("✅ sprite_model.py syntax is valid")
        return True
    except py_compile.PyCompileError as e:
        print(f"❌ Syntax error in sprite_model.py: {e}")
        return False

def check_file_existence():
    """Check if test sprite files exist."""
    import os
    test_files = [
        "spritetests/Lancer_Run.png",
        "spritetests/Lancer_Idle.png", 
        "spritetests/Archer_Run.png",
        "spritetests/test_sprite_sheet.png"
    ]
    
    existing = []
    missing = []
    
    for file_path in test_files:
        if os.path.exists(file_path):
            existing.append(file_path)
        else:
            missing.append(file_path)
    
    print(f"✅ Test sprites available: {len(existing)}")
    for file_path in existing:
        print(f"   📁 {file_path}")
        
    if missing:
        print(f"⚠️  Missing test sprites: {len(missing)}")
        for file_path in missing:
            print(f"   ❌ {file_path}")
    
    return len(existing) > 0

def main():
    """Run all validation checks."""
    print("🔍 CCL Integration Readiness Check")
    print("=" * 50)
    
    ccl_ready = check_ccl_availability()
    syntax_ok = check_syntax()
    files_exist = check_file_existence()
    
    print("\n" + "=" * 50)
    print("📋 READINESS SUMMARY:")
    
    if ccl_ready and syntax_ok and files_exist:
        print("🎉 CCL Integration is READY for testing!")
        print("\n🚀 TO TEST:")
        print("1. Launch sprite viewer: `python sprite_viewer.py`")
        print("2. Load a Lancer sprite (e.g., Lancer_Run.png)")
        print("3. Click 'Auto-Detect All' button")
        print("4. Check detailed results dialog for CCL debug logs")
        print("\n🔍 EXPECTED RESULTS:")
        print("• Lancer_Run: ~64×140 frames, 6 sprites")
        print("• Lancer_Idle: ~66×149 frames, 12 sprites")
        print("• Detailed CCL debug logs in results dialog")
    else:
        print("❌ CCL Integration is NOT ready:")
        if not ccl_ready:
            print("   - Install missing dependencies")
        if not syntax_ok:
            print("   - Fix syntax errors")
        if not files_exist:
            print("   - Add test sprite files")

if __name__ == "__main__":
    main()