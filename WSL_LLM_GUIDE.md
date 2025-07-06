# WSL Development Guide for LLMs

This is a project-agnostic guide for AI assistants working in WSL (Windows Subsystem for Linux) environments. This guide provides essential patterns and commands that work across different projects.

## Environment Detection

```bash
# Check if running in WSL
if grep -q Microsoft /proc/version; then
    echo "Running in WSL"
fi

# Get Windows username
WINDOWS_USER=$(cmd.exe /c "echo %USERNAME%" 2>/dev/null | tr -d '\r')

# Get Windows home directory
WINDOWS_HOME="/mnt/c/Users/$WINDOWS_USER"
```

## File System Navigation

### WSL ↔ Windows Path Conversion
```bash
# Windows to WSL path
wslpath "C:\Users\username\Documents"  # → /mnt/c/Users/username/Documents

# WSL to Windows path  
wslpath -w "/home/user/file.txt"      # → \\wsl$\Ubuntu\home\user\file.txt

# Current directory in Windows format
wslpath -w $(pwd)
```

### Working with Windows Files
```bash
# Copy file to Windows desktop
cp file.txt "$WINDOWS_HOME/Desktop/"

# Open file in Windows default app
cmd.exe /c start file.pdf

# Open current directory in Windows Explorer
explorer.exe .
```

## GUI Applications in WSL

### Running GUI Apps Without Display

```bash
# For Qt/PyQt applications
export QT_QPA_PLATFORM=offscreen

# For GTK applications
export GDK_BACKEND=broadway

# For general X11 applications (requires X server)
export DISPLAY=:0
```

### Taking Screenshots of GUI Applications

```python
# Generic screenshot function for any GUI framework
def capture_screenshot_headless(widget_creation_func, output_path, size=(800, 600)):
    """
    Captures screenshot of GUI widget in headless environment
    
    Args:
        widget_creation_func: Function that creates and returns the widget
        output_path: Where to save the screenshot
        size: Tuple of (width, height)
    """
    import os
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'  # For Qt
    
    # Framework-specific implementations
    try:
        # Qt/PyQt
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtGui import QPixmap
        app = QApplication([])
        widget = widget_creation_func()
        widget.resize(*size)
        widget.show()
        app.processEvents()
        pixmap = QPixmap(widget.size())
        widget.render(pixmap)
        pixmap.save(output_path)
        app.quit()
    except ImportError:
        try:
            # Tkinter
            import tkinter as tk
            from PIL import ImageGrab
            root = tk.Tk()
            widget = widget_creation_func(root)
            root.update()
            # Note: This requires X server
            ImageGrab.grab().save(output_path)
            root.destroy()
        except ImportError:
            print("No supported GUI framework found")
```

### Detecting Available Display
```python
import os
import subprocess

def has_display():
    """Check if a display is available"""
    # Check for X11
    if os.environ.get('DISPLAY'):
        try:
            subprocess.run(['xset', 'q'], capture_output=True, check=True)
            return True
        except:
            pass
    
    # Check for Wayland
    if os.environ.get('WAYLAND_DISPLAY'):
        return True
    
    return False

# Use appropriate backend
if has_display():
    print("Display available - can show GUI")
else:
    print("No display - use headless mode")
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
```

## Python Development

### Virtual Environment Best Practices
```bash
# Create venv with system site packages (useful for system Qt)
python3 -m venv venv --system-site-packages

# Create isolated venv
python3 -m venv venv

# Activate
source venv/bin/activate

# Ensure pip is updated
python3 -m pip install --upgrade pip
```

### Installing Packages
```bash
# Some packages need system libraries in WSL
# For PyQt6
sudo apt-get update
sudo apt-get install python3-pyqt6

# For image processing
sudo apt-get install python3-pil

# For audio
sudo apt-get install portaudio19-dev
```

## Testing in WSL

### Running Tests with GUI Components
```bash
# PyTest with Qt
QT_QPA_PLATFORM=offscreen pytest

# With coverage
QT_QPA_PLATFORM=offscreen pytest --cov=. --cov-report=html

# Open coverage report in Windows browser
cmd.exe /c start htmlcov/index.html
```

### Mock Display for Testing
```python
import os
import sys

def setup_headless_display():
    """Setup virtual display for testing"""
    try:
        from xvfbwrapper import Xvfb
        vdisplay = Xvfb(width=1920, height=1080)
        vdisplay.start()
        return vdisplay
    except ImportError:
        # Fallback to offscreen
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
        return None
```

## File Operations

### Safe File Operations in WSL
```python
import os
import tempfile
import shutil

def safe_write_file(filepath, content):
    """Write file safely with atomic operations"""
    # Use temp file to avoid corruption
    fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(filepath))
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        # Atomic rename
        shutil.move(temp_path, filepath)
    except:
        os.unlink(temp_path)
        raise

def ensure_windows_compatible_filename(filename):
    """Ensure filename is valid for Windows"""
    # Remove invalid Windows characters
    invalid_chars = '<>:"|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    # Remove trailing dots and spaces (Windows limitation)
    filename = filename.rstrip('. ')
    return filename
```

### Permission Handling
```bash
# Check file permissions
ls -la file.txt

# Fix permission issues for Windows files
# Note: Windows files in /mnt/c often have 777 permissions
chmod 644 file.txt  # May not work on NTFS

# Better approach: copy to Linux filesystem
cp /mnt/c/path/to/file.txt ~/temp/file.txt
chmod 644 ~/temp/file.txt
```

## Process Management

### Running Windows Executables
```bash
# Run Windows executable
cmd.exe /c "program.exe"

# Run PowerShell command
powershell.exe -Command "Get-Process"

# Open URL in Windows browser
cmd.exe /c start https://example.com
```

### Background Processes
```bash
# Run GUI app in background
QT_QPA_PLATFORM=offscreen python3 app.py &

# Get process ID
echo $!

# Check if process is running
ps aux | grep python3

# Kill process
kill $PID
```

## Debugging in WSL

### Common Issues and Solutions

```bash
# Issue: "Command not found" but command exists
# Solution: Check PATH
echo $PATH
# Add to PATH if needed
export PATH=$PATH:/usr/local/bin

# Issue: Permission denied on Windows files
# Solution: Work in Linux filesystem
cd ~/projects  # Instead of /mnt/c/...

# Issue: Line ending problems (CRLF vs LF)
# Solution: Configure git
git config --global core.autocrlf input
# Convert file endings
dos2unix file.txt
```

### Debugging Python GUI Apps
```python
import logging
import sys

def setup_debug_logging():
    """Setup comprehensive debug logging"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('debug.log')
        ]
    )
    
    # Enable Qt debug messages
    if 'PyQt' in sys.modules:
        os.environ['QT_LOGGING_RULES'] = '*.debug=true'

def debug_environment():
    """Print environment debugging info"""
    import platform
    
    print(f"Python: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"WSL: {'Microsoft' in platform.uname().release}")
    print(f"Display: {os.environ.get('DISPLAY', 'Not set')}")
    print(f"Qt Platform: {os.environ.get('QT_QPA_PLATFORM', 'Not set')}")
    print(f"Working Directory: {os.getcwd()}")
    print(f"PATH: {os.environ.get('PATH', '')[:100]}...")
```

## Performance Optimization

### WSL2 Specific Optimizations
```bash
# Use Linux filesystem for better performance
# Avoid: /mnt/c/project
# Prefer: ~/project

# Exclude from Windows Defender (run in PowerShell as admin)
# Add-MpPreference -ExclusionPath "\\wsl$\Ubuntu\home\user\projects"

# Limit WSL2 memory usage (.wslconfig in Windows home)
# [wsl2]
# memory=4GB
# processors=2
```

### File Watching
```python
# File watching in WSL can be slow on Windows files
import os

def get_optimal_watch_location(preferred_path):
    """Get optimal location for file watching"""
    if preferred_path.startswith('/mnt/'):
        # Windows filesystem - consider copying to Linux
        linux_path = os.path.expanduser(f"~/temp/{os.path.basename(preferred_path)}")
        print(f"Note: Watching Windows files is slow. Consider using {linux_path}")
    return preferred_path
```

## Network Operations

### Accessing Services
```bash
# Access Windows host from WSL
# Use: $(cat /etc/resolv.conf | grep nameserver | awk '{print $2}')
WINDOWS_HOST=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}')

# Access service running on Windows
curl http://$WINDOWS_HOST:8080

# Access WSL service from Windows
# WSL2 IP changes on restart, use:
WSL_IP=$(ip addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
echo "Access from Windows at: http://$WSL_IP:8000"
```

## Quick Command Reference

### Essential WSL Commands
```bash
# System info
uname -a                    # Linux kernel info
lsb_release -a             # Distribution info
df -h /mnt/c              # Windows drive space

# File operations
wslpath -w $(pwd)          # Current dir in Windows format
explorer.exe .             # Open in Windows Explorer
cmd.exe /c start file.pdf  # Open with Windows app

# Process management
ps aux | grep python       # Find Python processes
jobs                       # List background jobs
fg %1                      # Bring job to foreground

# Network
ip addr show              # Network interfaces
ss -tuln                  # Listening ports
```

### Python/GUI Quick Fixes
```bash
# Qt issues
export QT_QPA_PLATFORM=offscreen
export QT_LOGGING_RULES="*.debug=true"

# Python path issues
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Pip issues
python3 -m pip install --user package_name
```

## Best Practices Summary

1. **File System**: Use Linux filesystem for development, Windows filesystem for final output
2. **GUI Apps**: Always set `QT_QPA_PLATFORM=offscreen` for headless operation
3. **Testing**: Run tests from Linux filesystem for better performance
4. **Paths**: Use `wslpath` for path conversion, avoid hardcoding paths
5. **Permissions**: Be aware that Windows files have different permission model
6. **Line Endings**: Configure git for LF endings, use dos2unix when needed
7. **Performance**: Exclude development directories from Windows Defender
8. **Debugging**: Always check environment variables when GUI apps fail

## Detecting Project Type

```python
import os
import json

def detect_project_type():
    """Detect project type based on files present"""
    if os.path.exists('package.json'):
        with open('package.json') as f:
            data = json.load(f)
            return f"Node.js project: {data.get('name', 'Unknown')}"
    elif os.path.exists('requirements.txt') or os.path.exists('setup.py'):
        return "Python project"
    elif os.path.exists('Cargo.toml'):
        return "Rust project"
    elif os.path.exists('go.mod'):
        return "Go project"
    else:
        return "Unknown project type"
```

This guide should help any LLM working in a WSL environment, regardless of the specific project.