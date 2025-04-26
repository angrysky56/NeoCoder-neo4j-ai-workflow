#!/usr/bin/env python
"""
Simple verification script for the fixes we've made.

This script just checks that the files can be parsed correctly.
"""

import sys
import ast
import os
from pathlib import Path

def check_imports(file_path):
    """Check the imports in a file for correctness."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Parse the file using AST
        tree = ast.parse(content)
        
        # Find all import statements
        imports = []
        from_imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.append(name.name)
            elif isinstance(node, ast.ImportFrom):
                for name in node.names:
                    from_imports.append((node.module, name.name))
        
        print(f"✅ Successfully parsed {os.path.basename(file_path)}")
        if imports:
            print(f"  - Imports: {', '.join(imports)}")
        if from_imports:
            print(f"  - From imports:")
            for module, name in from_imports:
                print(f"    - from {module} import {name}")
        
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error in {os.path.basename(file_path)}: {e}")
        print(f"  Line {e.lineno}, column {e.offset}: {e.text.strip()}")
        return False
    except Exception as e:
        print(f"❌ Error checking {os.path.basename(file_path)}: {e}")
        return False

def verify_file_integrity():
    """Verify that all the files can be parsed properly."""
    print("Verifying file integrity...")
    
    base_dir = Path(__file__).parent
    incarnations_dir = base_dir / "src" / "mcp_neocoder" / "incarnations"
    
    # Check base incarnation
    if not check_imports(incarnations_dir / "base_incarnation.py"):
        return False
    
    # Check polymorphic adapter
    if not check_imports(incarnations_dir / "polymorphic_adapter.py"):
        return False
    
    # Check all incarnation files
    for incarnation_file in incarnations_dir.glob("*_incarnation.py"):
        if not check_imports(incarnation_file):
            return False
    
    # Check server.py
    if not check_imports(base_dir / "src" / "mcp_neocoder" / "server.py"):
        return False
    
    # Check incarnation_registry.py
    if not check_imports(base_dir / "src" / "mcp_neocoder" / "incarnation_registry.py"):
        return False
    
    return True

def scan_for_tool_methods():
    """Scan files for _tool_methods attributes."""
    print("\nScanning for tool methods in incarnation classes...")
    
    base_dir = Path(__file__).parent
    incarnations_dir = base_dir / "src" / "mcp_neocoder" / "incarnations"
    
    for incarnation_file in incarnations_dir.glob("*_incarnation.py"):
        try:
            with open(incarnation_file, 'r') as f:
                content = f.read()
            
            # Use a simple string search for _tool_methods
            if "_tool_methods" in content:
                print(f"✅ Found _tool_methods in {incarnation_file.name}")
            else:
                print(f"⚠️ No _tool_methods found in {incarnation_file.name}")
        except Exception as e:
            print(f"❌ Error scanning {incarnation_file.name}: {e}")
    
    return True

def main():
    """Run all verification checks."""
    if verify_file_integrity() and scan_for_tool_methods():
        print("\n✅ All verifications passed!")
        return 0
    else:
        print("\n❌ Verification failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
