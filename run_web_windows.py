#!/usr/bin/env python3
"""
Windows runner for Sprite Viewer Web Application
===============================================

This script starts the FastAPI web server on Windows without requiring virtual environment.
Access the application at http://localhost:8000
"""

import sys
import subprocess

def main():
    print("🚀 Starting Sprite Viewer Web Server on Windows...")
    
    # Check if required packages are installed
    try:
        import fastapi
        import uvicorn
        print("✅ FastAPI and Uvicorn found!")
    except ImportError:
        print("⚠️  Required packages not installed!")
        print("Installing web dependencies...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "fastapi", "uvicorn[standard]", "python-multipart", "websockets"
            ])
            print("✅ Dependencies installed!")
            import uvicorn
        except Exception as e:
            print(f"❌ Failed to install dependencies: {e}")
            print("Please run: pip install fastapi uvicorn[standard] python-multipart websockets")
            return 1
    
    # Check for other required packages
    missing_packages = []
    try:
        import PySide6
    except ImportError:
        missing_packages.append("PySide6")
    
    try:
        import numpy
    except ImportError:
        missing_packages.append("numpy")
    
    try:
        import PIL
    except ImportError:
        missing_packages.append("Pillow")
    
    if missing_packages:
        print(f"⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            print("✅ All packages installed!")
        except Exception as e:
            print(f"❌ Failed to install packages: {e}")
            print(f"Please run: pip install {' '.join(missing_packages)}")
            return 1
    
    print("📱 Open http://localhost:8000 in your browser")
    print("Press Ctrl+C to stop the server")
    print("-" * 40)
    
    # Run uvicorn programmatically
    try:
        uvicorn.run(
            "web_api:app",
            host="0.0.0.0",
            port=8000,
            reload=True
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())