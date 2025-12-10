#!/usr/bin/env python3
"""
Fix relative imports in backend module
Converts all relative imports to absolute imports with 'backend.' prefix
"""
import re
from pathlib import Path

BACKEND_DIR = Path("backend")
MODULES_TO_FIX = [
    "config", "schemas", "services", "clients", "utils", "routers"
]

def fix_imports_in_file(file_path: Path):
    """Fix imports in a single Python file"""
    if not file_path.exists():
        return False
    
    content = file_path.read_text(encoding="utf-8")
    original = content
    
    # Fix imports like "from schemas import..."
    for module in MODULES_TO_FIX:
        # Pattern: from module import ...
        pattern = rf"^from {module}(\.|\ import)"
        replacement = rf"from backend.{module}\1"
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    if content != original:
        file_path.write_text(content, encoding="utf-8")
        print(f"✅ Fixed: {file_path}")
        return True
    return False

def main():
    """Fix all Python files in backend directory"""
    print("=== Fixing Backend Imports ===\n")
    
    fixed_count = 0
    for py_file in BACKEND_DIR.rglob("*.py"):
        if fix_imports_in_file(py_file):
            fixed_count += 1
    
    print(f"\n✅ Fixed {fixed_count} files")

if __name__ == "__main__":
    main()
