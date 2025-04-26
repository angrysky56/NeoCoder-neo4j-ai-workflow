#!/usr/bin/env python3
"""
Verify Tool Registration Script for NeoCoder Framework

This script checks that tools are being properly registered from incarnations.
It runs outside the MCP environment to directly examine the structure and registry.
"""

import importlib.util
import inspect
import sys
import os
import logging
from typing import Dict, Any, Type

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("verify_tools")

# Add the src directory to the Python path
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, src_dir)

def check_incarnation_types():
    """Check that IncarnationType enum is defined correctly."""
    try:
        # Import using direct module import
        from mcp_neocoder.incarnations.base_incarnation import IncarnationType, BaseIncarnation
        
        logger.info("IncarnationType values:")
        for t in IncarnationType:
            logger.info(f"  {t.name} = {t.value}")
            
        return IncarnationType, BaseIncarnation
    except Exception as e:
        logger.error(f"Error importing IncarnationType: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None, None

def find_incarnation_modules():
    """Find all incarnation modules in the codebase."""
    incarnation_modules = []
    
    # Check each incarnation file
    incarnations_dir = os.path.join(src_dir, "mcp_neocoder", "incarnations")
    for entry in os.listdir(incarnations_dir):
        if not entry.endswith(".py") or entry.startswith("__"):
            continue
            
        if entry in ["base_incarnation.py", "polymorphic_adapter.py"]:
            continue
            
        module_name = entry[:-3]  # Remove .py extension
        incarnation_modules.append(module_name)
    
    logger.info(f"Found incarnation modules: {incarnation_modules}")
    return incarnation_modules

def examine_incarnation_module(module_name):
    """Examine a single incarnation module."""
    logger.info(f"Examining module: {module_name}")
    
    try:
        # Import the module
        module = importlib.import_module(f"mcp_neocoder.incarnations.{module_name}")
        
        # Get BaseIncarnation for comparison
        from mcp_neocoder.incarnations.base_incarnation import BaseIncarnation
        
        # Find all classes that inherit from BaseIncarnation
        incarnation_classes = []
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, BaseIncarnation) and obj is not BaseIncarnation:
                logger.info(f"Found incarnation class: {name}")
                incarnation_classes.append((name, obj))
                
                # Check incarnation type
                incarnation_type = getattr(obj, "incarnation_type", None)
                logger.info(f"  Incarnation type: {incarnation_type}")
                
                # Check for tool methods
                tool_methods = []
                
                # Check for _tool_methods attribute
                if hasattr(obj, "_tool_methods") and isinstance(obj._tool_methods, list):
                    logger.info(f"  Found explicit tool methods: {obj._tool_methods}")
                    tool_methods.extend(obj._tool_methods)
                
                # Check for async methods with appropriate return type
                for method_name, method in inspect.getmembers(obj, predicate=inspect.isfunction):
                    if inspect.iscoroutinefunction(method) and method_name not in tool_methods:
                        # Check if it's not a private or special method
                        if not method_name.startswith("_") and method_name not in [
                            "initialize_schema", "get_guidance_hub", "ensure_hub_exists",
                            "register_tools", "list_tool_methods"
                        ]:
                            tool_methods.append(method_name)
                
                logger.info(f"  All potential tool methods: {tool_methods}")
                
        return incarnation_classes
    except Exception as e:
        logger.error(f"Error examining module {module_name}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def check_tool_registry():
    """Check the tool registry module."""
    try:
        # Import directly
        from mcp_neocoder.tool_registry import registry
        
        logger.info("Tool Registry Contents:")
        logger.info(f"  Tool categories: {list(registry.tool_categories.keys())}")
        logger.info(f"  Number of registered tools: {len(registry.tools)}")
        
        # Show registered tool names
        if registry.tools:
            logger.info("Registered tools:")
            for tool_name in registry.tools:
                logger.info(f"  - {tool_name}")
        else:
            logger.info("No tools are currently registered in the registry")
            
    except Exception as e:
        logger.error(f"Error checking tool registry: {e}")
        import traceback
        logger.error(traceback.format_exc())

def main():
    """Main verification function."""
    logger.info("Starting verification of NeoCoder tools and incarnations")
    
    # Check incarnation types
    check_incarnation_types()
    
    # Find all incarnation modules
    modules = find_incarnation_modules()
    
    # Examine each module
    all_incarnation_classes = []
    for module_name in modules:
        classes = examine_incarnation_module(module_name)
        all_incarnation_classes.extend(classes)
    
    logger.info(f"Found {len(all_incarnation_classes)} incarnation classes")
    
    # Check tool registry
    check_tool_registry()
    
    logger.info("Verification complete")

if __name__ == "__main__":
    main()
