#!/usr/bin/env python3
"""
Simplified test for incarnation discovery in NeoCoder framework.

This script directly tests the dynamic incarnation type discovery
without requiring the neo4j package.
"""

import os
import sys
import logging
import re
import importlib.util

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("test_incarnation_discovery")

# Add src to Python path
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, src_dir)

def get_incarnation_files():
    """Get all incarnation files in the project."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    incarnations_dir = os.path.join(current_dir, "src", "mcp_neocoder", "incarnations")
    
    if not os.path.exists(incarnations_dir):
        logger.error(f"Incarnations directory not found: {incarnations_dir}")
        return []
    
    files = []
    for entry in os.listdir(incarnations_dir):
        if entry.endswith("_incarnation.py") and not entry.startswith("__"):
            files.append(os.path.join(incarnations_dir, entry))
    
    return files

def extract_incarnation_info(file_path):
    """Extract incarnation information from a file."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Extract class name
        class_match = re.search(r'class\s+(\w+)\s*\(', content)
        class_name = class_match.group(1) if class_match else "Unknown"
        
        # Extract incarnation type
        type_match = re.search(r'incarnation_type\s*=\s*IncarnationType\.(\w+)', content)
        inc_type = type_match.group(1) if type_match else "Unknown"
        
        # Extract description
        desc_match = re.search(r'description\s*=\s*[\'"](.+?)[\'"]', content)
        description = desc_match.group(1) if desc_match else "No description"
        
        # Extract tool methods
        tool_methods = []
        tool_methods_match = re.search(r'_tool_methods\s*=\s*\[(.*?)\]', content, re.DOTALL)
        if tool_methods_match:
            tools_str = tool_methods_match.group(1)
            # Extract quoted strings
            tool_methods = re.findall(r'[\'"](.+?)[\'"]', tools_str)
        
        # Also find async methods that might be tools
        async_methods = re.findall(r'async\s+def\s+(\w+)\s*\(', content)
        
        return {
            "file": os.path.basename(file_path),
            "class": class_name,
            "type": inc_type,
            "description": description,
            "explicit_tools": tool_methods,
            "async_methods": async_methods
        }
    except Exception as e:
        logger.error(f"Error extracting info from {file_path}: {e}")
        return None

def create_test_incarnation():
    """Create a temporary test incarnation file."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_file = os.path.join(current_dir, "src", "mcp_neocoder", "incarnations", "test_dynamic_incarnation.py")
    
    content = """
from .base_incarnation import BaseIncarnation, IncarnationType

class TestDynamicIncarnation(BaseIncarnation):
    \"\"\"Test incarnation for dynamic discovery\"\"\"
    
    # This incarnation type should be automatically discovered
    incarnation_type = IncarnationType.TEST_DYNAMIC
    
    description = "Test incarnation for dynamic discovery"
    version = "0.1.0"
    
    _tool_methods = [
        "test_tool_one",
        "test_tool_two"
    ]
    
    async def test_tool_one(self, param1: str):
        \"\"\"Test tool one\"\"\"
        return []
        
    async def test_tool_two(self, param1: str):
        \"\"\"Test tool two\"\"\"
        return []
"""
    
    try:
        with open(test_file, 'w') as f:
            f.write(content)
        logger.info(f"Created test incarnation file: {test_file}")
        return test_file
    except Exception as e:
        logger.error(f"Error creating test incarnation: {e}")
        return None

def get_base_incarnation_types():
    """Get the base incarnation types defined in the enum."""
    base_inc_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "mcp_neocoder", "incarnations", "base_incarnation.py")
    
    try:
        with open(base_inc_file, 'r') as f:
            content = f.read()
            
        enum_section = None
        enum_match = re.search(r'class IncarnationType.*?:.*?""".*?"""(.*?)class', content, re.DOTALL)
        if enum_match:
            enum_section = enum_match.group(1)
            
        types = []
        if enum_section:
            # Extract name = value pairs
            types_matches = re.findall(r'(\w+)\s*=\s*[\'"](.+?)[\'"]', enum_section)
            types = [t for t in types_matches]
            
        return types
    except Exception as e:
        logger.error(f"Error getting base incarnation types: {e}")
        return []

def get_incarnation_type_from_filename(filename):
    """Extract an incarnation type value from a filename."""
    if not filename.endswith('_incarnation.py'):
        return None
        
    # Remove '.py' extension and '_incarnation' suffix
    name = filename.replace('_incarnation.py', '')
    
    return name

def main():
    """Main test function."""
    logger.info("NeoCoder Incarnation Discovery Test")
    logger.info("=================================")
    
    # Check the base incarnation types
    base_types = get_base_incarnation_types()
    logger.info(f"Base incarnation types: {base_types}")
    
    # Test filename-based discovery
    filenames = os.listdir(os.path.join(src_dir, "mcp_neocoder", "incarnations"))
    for filename in filenames:
        if filename.endswith('_incarnation.py') and not filename.startswith('__'):
            type_value = get_incarnation_type_from_filename(filename)
            logger.info(f"File: {filename} -> Type: {type_value}")
    
    # Create a test incarnation file
    test_file = create_test_incarnation()
    
    # Get all incarnation files
    files = get_incarnation_files()
    logger.info(f"Found {len(files)} incarnation files")
    
    # Extract information from each file
    incarnations = []
    for file in files:
        info = extract_incarnation_info(file)
        if info:
            incarnations.append(info)
            logger.info(f"Incarnation: {info['class']} - Type: {info['type'