#!/usr/bin/env python3
"""Simple test to check imports."""

import sys
import os

# Add src to path
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, src_dir)

print(f"Python path: {sys.path[:3]}")
print(f"Current directory: {os.getcwd()}")
print(f"Source directory: {src_dir}")
print(f"Source directory exists: {os.path.exists(src_dir)}")

try:
    print("Attempting to import mcp_neocoder...")
    import mcp_neocoder
    print("✓ mcp_neocoder imported successfully")

    print("Attempting to import BaseIncarnation...")
    from mcp_neocoder.incarnations.base_incarnation import BaseIncarnation
    print("✓ BaseIncarnation imported successfully")

    print("Attempting to import registry...")
    from mcp_neocoder.incarnation_registry import registry
    print("✓ Registry imported successfully")

    print("Discovering incarnations...")
    registry.discover()
    print(f"✓ Found {len(registry.incarnations)} incarnations:")
    for name, cls in registry.incarnations.items():
        print(f"  - {name}: {cls.__name__}")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
