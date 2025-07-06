#!/usr/bin/env python3
"""
Alternative runner using uvicorn programmatically
"""

import sys
import subprocess

# Check if virtual environment is activated
if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    print("⚠️  Virtual environment not activated!")
    print("Please activate it first:")
    print("  source venv/bin/activate  # Linux/Mac")
    print("  venv\\Scripts\\activate     # Windows")
    sys.exit(1)

# Check if required packages are installed
try:
    import fastapi
    import uvicorn
except ImportError:
    print("⚠️  Required packages not installed!")
    print("Installing web dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("✅ Dependencies installed!")
    import uvicorn

print("🚀 Starting Sprite Viewer Web Server...")
print("📱 Open http://localhost:8000 in your browser")
print("Press Ctrl+C to stop the server")
print("-" * 40)

# Run uvicorn programmatically
if __name__ == "__main__":
    uvicorn.run(
        "web_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )