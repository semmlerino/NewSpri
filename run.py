#!/usr/bin/env python3
"""
Launcher script for Python Sprite Viewer
Handles virtual environment activation and starts the application.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Launch the sprite viewer application."""
    
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    
    # Check if virtual environment exists
    venv_dir = script_dir / "venv"
    if not venv_dir.exists():
        print("❌ Virtual environment not found!")
        print("Please run the following commands first:")
        print("python3 -m venv venv")
        print("source venv/bin/activate  # On Linux/Mac")
        print("pip install -r requirements.txt")
        return 1
    
    # Determine the python executable in the virtual environment
    if os.name == 'nt':  # Windows
        python_exe = venv_dir / "Scripts" / "python.exe"
        if not python_exe.exists():
            python_exe = venv_dir / "Scripts" / "python3.exe"
    else:  # Linux/Mac
        python_exe = venv_dir / "bin" / "python"
        if not python_exe.exists():
            python_exe = venv_dir / "bin" / "python3"
    
    if not python_exe.exists():
        print("❌ Python executable not found in virtual environment!")
        return 1
    
    # Path to the sprite viewer script
    sprite_viewer_script = script_dir / "sprite_viewer.py"
    if not sprite_viewer_script.exists():
        print("❌ sprite_viewer.py not found!")
        return 1
    
    # Launch the application
    print("🚀 Starting Python Sprite Viewer...")
    try:
        subprocess.run([str(python_exe), str(sprite_viewer_script)], 
                      cwd=str(script_dir), check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start sprite viewer: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n👋 Sprite viewer closed by user")
        return 0
    
    return 0

if __name__ == "__main__":
    sys.exit(main())