#!/usr/bin/env python3
"""
Verify Export Module Consolidation
Checks that all imports in the reorganized export module are correct.
"""

import os
import re
import sys
from pathlib import Path

def find_relative_imports(file_path):
    """Find all relative imports in a Python file."""
    imports = []
    with open(file_path, 'r') as f:
        content = f.read()
        
    # Match relative imports like: from .module import ...
    pattern = r'from\s+(\.[^\s]+)\s+import'
    matches = re.findall(pattern, content)
    
    for match in matches:
        imports.append((file_path, match))
        
    return imports

def check_import_exists(base_path, from_file, import_path):
    """Check if a relative import path exists."""
    # Get directory of the importing file
    from_dir = os.path.dirname(from_file)
    
    # Convert relative import to actual path
    # .module → same directory
    # ..module → parent directory
    # ...module → grandparent directory
    parts = import_path.split('.')
    up_levels = len(parts) - 1
    module_name = parts[-1]
    
    # Navigate up directories
    target_dir = from_dir
    for _ in range(up_levels):
        target_dir = os.path.dirname(target_dir)
        
    # Check if module exists
    module_path = os.path.join(target_dir, module_name + '.py')
    package_path = os.path.join(target_dir, module_name, '__init__.py')
    
    return os.path.exists(module_path) or os.path.exists(package_path)

def main():
    """Main verification function."""
    export_dir = Path('export')
    if not export_dir.exists():
        print("Error: export directory not found")
        sys.exit(1)
        
    print("Verifying export module imports...")
    print("=" * 60)
    
    errors = []
    checked = 0
    
    # Find all Python files
    for py_file in export_dir.rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue
            
        # Find relative imports
        imports = find_relative_imports(py_file)
        
        for file_path, import_path in imports:
            checked += 1
            if not check_import_exists(export_dir, file_path, import_path):
                errors.append(f"{file_path}: Cannot resolve import '{import_path}'")
                
    # Report results
    print(f"Files checked: {len(list(export_dir.rglob('*.py')))}")
    print(f"Imports checked: {checked}")
    print(f"Errors found: {len(errors)}")
    
    if errors:
        print("\nImport errors:")
        for error in errors:
            print(f"  ❌ {error}")
        sys.exit(1)
    else:
        print("\n✅ All imports are valid!")
        
    # Test basic import
    print("\nTesting basic module import...")
    try:
        from export import ExportDialog, get_frame_exporter
        print("✅ Basic imports successful!")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()