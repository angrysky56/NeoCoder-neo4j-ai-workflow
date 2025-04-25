#!/usr/bin/env python3
"""
Extract incarnation types directly from source file.
"""

import re
import os

# Path to base_incarnation.py
base_incarnation_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "src", "mcp_neocoder", "incarnations", "base_incarnation.py"
)

def extract_incarnation_types():
    """Extract incarnation types from the base_incarnation.py file."""
    if not os.path.exists(base_incarnation_path):
        print(f"Error: File not found: {base_incarnation_path}")
        return
    
    print(f"Reading file: {base_incarnation_path}")
    with open(base_incarnation_path, 'r') as f:
        content = f.read()
    
    # Find the IncarnationType enum
    enum_pattern = r"class IncarnationType\(str, Enum\):\s*\"\"\".*?\"\"\"\s*(.*?)class"
    enum_match = re.search(enum_pattern, content, re.DOTALL)
    
    if not enum_match:
        print("Error: IncarnationType enum not found in file")
        return
    
    enum_content = enum_match.group(1)
    
    # Extract types and values
    type_pattern = r"(\w+)\s*=\s*\"(\w+)\"\s*#\s*(.*)"
    types = re.findall(type_pattern, enum_content)
    
    print("\nIncarnation Types Found:")
    print("------------------------")
    for name, value, comment in types:
        print(f"{name} = \"{value}\"  # {comment}")
    
    print(f"\nTotal types found: {len(types)}")
    
    # Check tool method extraction
    tool_pattern = r"def list_tool_methods.*?return tool_methods"
    tool_match = re.search(tool_pattern, content, re.DOTALL)
    
    if tool_match:
        print("\nTool method extraction looks good.")
    else:
        print("\nWarning: Tool method detection code not found as expected.")

def main():
    extract_incarnation_types()

if __name__ == "__main__":
    main()
