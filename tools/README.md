# Tools Directory

This directory contains utility scripts for verifying specific functionality in the Sprite Viewer application. These are standalone scripts, not pytest tests.

## Available Tools

### verify_animation_imports.py
Verifies that animation splitting components can be imported without PySide6 dependencies.

### verify_segment_fixes.py  
Tests animation segment functionality and validates segment management fixes.

### verify_export_consolidation.py
Verifies that export presets work correctly with both all frames and selected frames.

### verify_export_dialog_fix.py
Tests export dialog functionality to ensure crash fixes are working.

### verify_export_fixes.py
Comprehensive export system verification including threading and error handling.

### verify_segment_naming.py
Validates animation segment naming functionality and fixes.

## Usage

These scripts can be run directly:
```bash
python tools/verify_animation_imports.py
```

They are designed to be run independently of the main test suite for quick verification of specific functionality.