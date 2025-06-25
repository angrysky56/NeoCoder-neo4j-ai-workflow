#!/usr/bin/env python3
"""
Verify Tool Registration Script for NeoCoder Framework

This script checks that tools are being properly registered from incarnations.
It runs outside the MCP environment to directly examine the structure and registry.
"""

import inspect
import sys
import os
import logging
import importlib

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("verify_tools")

# Add the src directory to the Python path
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.path.insert(0, src_dir)

print(f"Starting verification script from: {os.path.abspath(__file__)}")
print(f"Adding to path: {src_dir}")
print(f"Path exists: {os.path.exists(src_dir)}")

def check_incarnation_registry():
    """Check the incarnation registry and discovered types."""
    try:
        # Import using direct module import
        from mcp_neocoder.incarnations.base_incarnation import BaseIncarnation
        from mcp_neocoder.incarnation_registry import registry

        logger.info("Discovered incarnations:")
        registry.discover()

        for inc_type, inc_class in registry.incarnations.items():
            logger.info(f"  {inc_type}: {inc_class.__name__} - {getattr(inc_class, 'description', 'No description')}")

        return registry, BaseIncarnation
    except Exception as e:
        logger.error(f"Error checking incarnation registry: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None, None

def find_incarnation_modules():
    """Find all incarnation modules in the codebase."""
    incarnation_modules = []

    # Check each incarnation file
    incarnations_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "incarnations")
    for entry in os.listdir(incarnations_dir):
        if not entry.endswith(".py") or entry.startswith("__"):
            continue

        if entry in ["base_incarnation.py"]:
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
                incarnation_name = getattr(obj, "name", None)
                logger.info(f"  Incarnation name: {incarnation_name}")

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

        return registry

    except Exception as e:
        logger.error(f"Error checking tool registry: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def test_tool_registration():
    """Test actual tool registration from incarnations."""
    logger.info("\n========== Testing Tool Registration ==========")

    try:
        from mcp_neocoder.incarnation_registry import registry as inc_registry
        from mcp_neocoder.tool_registry import registry as tool_registry

        # Mock Neo4j driver for testing
        class MockDriver:
            async def session(self, database=None):
                return MockSession()

        class MockSession:
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
            async def execute_read(self, func, query, params=None):
                return "[]"
            async def execute_write(self, func, query=None, params=None):
                return None

        # Create mock driver
        driver = MockDriver()

        # Test each incarnation's tool registration
        inc_registry.discover()
        total_tools_registered = 0
        incarnation_summary = []

        for inc_type, inc_class in inc_registry.incarnations.items():
            logger.info(f"\nTesting tool registration for {inc_type}")

            # Create instance
            instance = inc_registry.get_instance(inc_type, driver, "neo4j")
            if not instance:
                logger.warning(f"Could not create instance for {inc_type}")
                continue

            # Get tool methods for this incarnation
            if hasattr(instance, 'list_tool_methods'):
                tool_methods = instance.list_tool_methods()
            elif hasattr(instance.__class__, '_tool_methods'):
                tool_methods = instance.__class__._tool_methods
            else:
                tool_methods = []

            # Get initial tool count
            initial_count = len(tool_registry.tools)

            # Register tools from this incarnation
            registered_count = tool_registry.register_class_tools(instance, inc_type)

            # Verify tools were actually added
            final_count = len(tool_registry.tools)
            actual_added = final_count - initial_count

            logger.info(f"  {inc_type}: Expected {len(tool_methods)} tools, registered {registered_count}, actually added {actual_added}")

            # Show what tools were detected vs registered
            logger.info(f"  Detected tools: {tool_methods}")
            if inc_type in tool_registry.tool_categories:
                tools_in_category = list(tool_registry.tool_categories[inc_type])
                logger.info(f"  Registered tools: {tools_in_category}")

            incarnation_summary.append({
                'name': inc_type,
                'expected': len(tool_methods),
                'registered': registered_count,
                'added': actual_added
            })

            total_tools_registered += actual_added

        # Summary table
        logger.info(f"\n{'='*80}")
        logger.info("TOOL REGISTRATION SUMMARY")
        logger.info(f"{'='*80}")
        logger.info(f"{'Incarnation':<25} {'Expected':<10} {'Registered':<12} {'Added':<8}")
        logger.info(f"{'-'*80}")

        for summary in incarnation_summary:
            logger.info(f"{summary['name']:<25} {summary['expected']:<10} {summary['registered']:<12} {summary['added']:<8}")

        logger.info(f"{'-'*80}")
        logger.info(f"{'TOTAL':<25} {'':<10} {'':<12} {total_tools_registered:<8}")
        logger.info(f"{'='*80}")

        return total_tools_registered

    except Exception as e:
        logger.error(f"Error testing tool registration: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 0

def main():
    """Main verification function."""
    logger.info("Starting verification of NeoCoder tools and incarnations")

    # Check incarnation registry
    registry, base_class = check_incarnation_registry()
    if not registry:
        logger.error("Failed to load incarnation registry")
        return

    # Find all incarnation modules
    modules = find_incarnation_modules()

    # Examine each module
    all_incarnation_classes = []
    for module_name in modules:
        classes = examine_incarnation_module(module_name)
        all_incarnation_classes.extend(classes)

    logger.info(f"Found {len(all_incarnation_classes)} incarnation classes")

    # Check tool registry (before registration)
    logger.info("\n========== Initial Tool Registry State ==========")
    initial_tool_registry = check_tool_registry()
    initial_tool_count = len(initial_tool_registry.tools) if initial_tool_registry else 0

    # Test actual tool registration
    total_registered = test_tool_registration()

    # Check tool registry again (after registration)
    logger.info("\n========== Final Tool Registry State ==========")
    final_tool_registry = check_tool_registry()
    final_tool_count = len(final_tool_registry.tools) if final_tool_registry else 0

    logger.info("\nVerification Summary:")
    logger.info(f"  Initial tools in registry: {initial_tool_count}")
    logger.info(f"  Final tools in registry: {final_tool_count}")
    logger.info(f"  Tools added during test: {final_tool_count - initial_tool_count}")
    logger.info(f"  Total tools registered: {total_registered}")
    logger.info("\nVerification complete!")

if __name__ == "__main__":
    main()
