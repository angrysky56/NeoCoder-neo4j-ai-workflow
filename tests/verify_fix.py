#!/usr/bin/env python
"""
Simple verification script for the fixes we've made.

This script just checks that the imports in each file are correct and 
that there are no circular dependencies.
"""

import importlib.util
import sys
import os
from pathlib import Path

def import_module_from_path(path, module_name):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def verify_imports():
    """Verify that all the files can be imported properly."""
    print("Verifying imports...")
    
    base_dir = Path(__file__).parent
    incarnations_dir = base_dir / "src" / "mcp_neocoder" / "incarnations"
    
    # Try importing the base_incarnation module
    try:
        base_path = incarnations_dir / "base_incarnation.py"
        base_module = import_module_from_path(base_path, "base_incarnation")
        print(f"✅ Successfully imported base_incarnation.py")
        print(f"  - IncarnationType members: {[m.value for m in base_module.IncarnationType]}")
    except Exception as e:
        print(f"❌ Failed to import base_incarnation.py: {e}")
        return False
    
    # Try importing polymorphic_adapter module
    try:
        adapter_path = incarnations_dir / "polymorphic_adapter.py"
        adapter_module = import_module_from_path(adapter_path, "polymorphic_adapter")
        print(f"✅ Successfully imported polymorphic_adapter.py")
    except Exception as e:
        print(f"❌ Failed to import polymorphic_adapter.py: {e}")
        return False
    
    # Try importing each incarnation module
    for incarnation_file in incarnations_dir.glob("*_incarnation.py"):
        try:
            module_name = incarnation_file.stem
            module = import_module_from_path(incarnation_file, module_name)
            print(f"✅ Successfully imported {incarnation_file.name}")
            
            # Check for _tool_methods attribute
            for name, obj in module.__dict__.items():
                if isinstance(obj, type) and issubclass(obj, base_module.BaseIncarnation):
                    if hasattr(obj, '_tool_methods'):
                        print(f"  - Found {len(obj._tool_methods)} tool methods in {name}: {obj._tool_methods}")
            
        except Exception as e:
            print(f"❌ Failed to import {incarnation_file.name}: {e}")
            return False
    
    return True

def main():
    """Run all verification checks."""
    if verify_imports():
        print("\n✅ All verifications passed!")
        return 0
    else:
        print("\n❌ Verification failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
