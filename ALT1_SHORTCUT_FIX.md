# Alt+1 Shortcut Fix

## Issue
Alt+1 shortcut was not loading the previously loaded sprite.

## Root Cause
The `FileController` was trying to call `set_file_open_handler()` on the `RecentFilesManager`, but the actual method name is `set_file_open_callback()`. This method name mismatch prevented the callback connection from being established.

## Fix Applied
Changed line 45 in `core/file_controller.py`:
```python
# Before:
if hasattr(self._recent_files_manager, 'set_file_open_handler'):
    self._recent_files_manager.set_file_open_handler(self._on_recent_file_selected)

# After:
if hasattr(self._recent_files_manager, 'set_file_open_callback'):
    self._recent_files_manager.set_file_open_callback(self._on_recent_file_selected)
```

## How It Works
1. **Alt+1 is pressed** → QAction with Alt+1 shortcut triggers
2. **Recent files manager** → `_open_recent_file()` is called
3. **Signal emitted** → `fileRequested` signal is emitted
4. **Callback executed** → `_file_open_callback()` is called (now properly connected)
5. **File controller** → `_on_recent_file_selected()` validates and loads the file
6. **Sprite loaded** → The previously loaded sprite appears in the viewer

## Verification
- Alt+1 through Alt+9 shortcuts are properly mapped to recent files
- The most recent file (index 1) is loaded when Alt+1 is pressed
- File validation ensures non-existent files are removed from recent files list

The shortcut should now work as expected!