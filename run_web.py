#!/usr/bin/env python3
"""
Run the Sprite Viewer Web Application
=====================================

This script starts the FastAPI web server for the sprite viewer.
Access the application at http://localhost:8000
"""

import sys
import os
import subprocess

def main():
    # Check if virtual environment is activated
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Virtual environment not activated!")
        print("Please activate it first:")
        print("  source venv/bin/activate  # Linux/Mac")
        print("  venv\\Scripts\\activate     # Windows")
        return 1
    
    # Check if required packages are installed
    try:
        import fastapi
        import uvicorn
    except ImportError:
        print("⚠️  Required packages not installed!")
        print("Installing web dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed!")
    
    # Start the web server
    print("🚀 Starting Sprite Viewer Web Server...")
    print("📱 Open http://localhost:8000 in your browser")
    print("Press Ctrl+C to stop the server")
    print("-" * 40)
    
    # Run uvicorn with proper import string
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "web_api:app",  # Import string format
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
    ])

if __name__ == "__main__":
    sys.exit(main())