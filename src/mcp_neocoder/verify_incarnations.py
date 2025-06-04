#!/usr/bin/env python
"""
Verify incarnation loading and tool registration.

This script verifies that incarnations can be loaded correctly and
tool methods can be discovered and registered properly.
"""

import asyncio
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("incarnation_verifier")

try:
    # Import the necessary modules
    from mcp_neocoder.incarnation_registry import registry

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

    async def verify_incarnations():
        """Verify that incarnations can be loaded properly."""
        logger.info("========== Verifying Incarnations ==========")

        # Discover incarnations
        registry.discover()

        # Log discovered incarnations
        logger.info(f"Discovered {len(registry.incarnations)} incarnations:")
        for inc_type, inc_class in registry.incarnations.items():
            logger.info(f"- {inc_type}: {inc_class.__name__}")

        return True

    async def verify_tool_discovery():
        """Verify that tools can be discovered from incarnations."""
        logger.info("\n========== Verifying Tool Discovery ==========")

        # Create mock driver
        driver = MockDriver()

        # Create instances and check tool detection
        all_tools = {}

        for inc_type, inc_class in registry.incarnations.items():
            # Create instance
            instance = registry.get_instance(inc_type, driver, "neo4j")
            if not instance:
                logger.warning(f"Could not create instance for {inc_type}")
                continue

            # Get tools via _tool_methods if available
            if hasattr(instance.__class__, '_tool_methods'):
                logger.info(f"Using _tool_methods for {inc_type}")
                tools = instance.__class__._tool_methods
            else:
                # Otherwise use dynamic detection
                logger.info(f"Using dynamic tool detection for {inc_type}")
                tools = instance.list_tool_methods()

            logger.info(f"- {inc_type}: {len(tools)} tools detected: {tools}")

            # Store in results
            all_tools[inc_type] = tools

        return all_tools

    async def main():
        """Run all verification tests."""
        try:
            await verify_incarnations()
            tool_results = await verify_tool_discovery()

            logger.info("\n========== Verification Results ==========")
            for inc_name, tools in tool_results.items():
                logger.info(f"{inc_name}: {len(tools)} tools")
                for tool in tools:
                    logger.info(f"  - {tool}")

            logger.info("\nAll verifications completed successfully!")
            return 0
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return 1

    # Run the async main function
    if __name__ == "__main__":
        exit_code = asyncio.run(main())
        sys.exit(exit_code)

except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.error("Make sure you're running this script from the correct directory")
    sys.exit(1)
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    import traceback
    logger.error(traceback.format_exc())
    sys.exit(1)
