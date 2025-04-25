#!/usr/bin/env python3
"""
Test script for dynamic incarnation loading in NeoCoder framework.

This script verifies that incarnations can be dynamically discovered and loaded
without requiring hardcoding of incarnation types or imports.
"""

import sys
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("test_dynamic_loading")

# Add src to Python path
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, src_dir)

class MockDriver:
    """Mock Neo4j driver for testing."""
    async def session(self, database=None):
        class MockSession:
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
            async def execute_read(self, func, query, params=None):
                return "[]"
            async def execute_write(self, func, query=None, params=None):
                return None
        return MockSession()

class MockServer:
    """Mock server for testing."""
    def __init__(self):
        self.driver = MockDriver()
        self.database = "neo4j"
        
        class MockMCP:
            def __init__(self):
                self.tools = []
            
            def add_tool(self, tool):
                self.tools.append(tool)
                return True
        
        self.mcp = MockMCP()

def create_test_incarnation(name):
    """Create a test incarnation file."""
    from mcp_neocoder.incarnation_registry import registry
    return registry.create_template_incarnation(name)

def test_incarnation_discovery():
    """Test that incarnations can be automatically discovered."""
    logger.info("Testing incarnation discovery...")
    
    # Import incarnation registry
    from mcp_neocoder.incarnation_registry import registry
    
    # Discover dynamic types
    types = registry.discover_dynamic_types()
    logger.info(f"Discovered {len(types)} dynamic types: {types}")
    
    # Extend incarnation types
    registry.extend_incarnation_types()
    
    # Check IncarnationType enum
    from mcp_neocoder.incarnations.base_incarnation import IncarnationType
    logger.info("Updated IncarnationType values:")
    for t in IncarnationType:
        logger.info(f"  {t.name} = {t.value}")
    
    # Discover incarnations
    registry.discover()
    
    # List discovered incarnations
    incarnations = registry.list()
    logger.info(f"Registered {len(incarnations)} incarnations:")
    for inc in incarnations:
        logger.info(f"  {inc['type']} - {inc['name']} - {inc['description']}")
    
    return len(incarnations)

def test_tool_discovery():
    """Test that tools can be automatically discovered from incarnations."""
    logger.info("Testing tool discovery...")
    
    # Import incarnation registry
    from mcp_neocoder.incarnation_registry import registry
    
    # Create a mock server
    server = MockServer()
    
    # Get all incarnation instances
    instances = []
    for inc_type in registry.incarnations:
        instance = registry.get_instance(inc_type, server.driver, server.database)
        instances.append(instance)
    
    # Test tool registration for each incarnation
    total_tools = 0
    for instance in instances:
        logger.info(f"Checking tools for {instance.incarnation_type.value}...")
        
        # Get tool methods
        tool_methods = instance.list_tool_methods()
        logger.info(f"  Found {len(tool_methods)} tool methods: {tool_methods}")
        
        # Try registering tools
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_running():
                tools_registered = loop.run_until_complete(instance.register_tools(server))
                total_tools += tools_registered
                logger.info(f"  Registered {tools_registered} tools with server")
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            tools_registered = loop.run_until_complete(instance.register_tools(server))
            total_tools += tools_registered
            logger.info(f"  Registered {tools_registered} tools with server")
    
    logger.info(f"Total tools registered: {total_tools}")
    logger.info(f"Server tool count: {len(server.mcp.tools)}")
    
    return total_tools

def test_incarnation_generator():
    """Test the incarnation generator functionality."""
    logger.info("Testing incarnation generator...")
    
    # Create a new test incarnation
    test_name = "test_dynamic_incarnation"
    file_path = create_test_incarnation(test_name)
    logger.info(f"Created test incarnation: {file_path}")
    
    # Make sure it exists
    if os.path.exists(file_path):
        logger.info(f"Incarnation file created successfully: {file_path}")
        
        # Read the file to verify contents
        with open(file_path, 'r') as f:
            content = f.read()
        logger.info(f"Incarnation file size: {len(content)} bytes")
        
        # Check for key elements
        expected_elements = [
            "class TestDynamicIncarnation",
            "incarnation_type = IncarnationType.TEST_DYNAMIC",
            "_tool_methods",
            "example_tool_one",
            "example_tool_two"
        ]
        
        for element in expected_elements:
            if element in content:
                logger.info(f"  Found expected element: {element}")
            else:
                logger.error(f"  Missing expected element: {element}")
        
        # Clean up
        os.remove(file_path)
        logger.info(f"Cleaned up test incarnation file")
        
        return True
    else:
        logger.error(f"Failed to create incarnation file")
        return False

def main():
    """Main test function."""
    logger.info("NeoCoder Dynamic Loading Test")
    logger.info("===========================")
    
    # Run tests
    inc_count = test_incarnation_discovery()
    tool_count = test_tool_discovery()
    generator_success = test_incarnation_generator()
    
    # Print summary
    logger.info("===========================")
    logger.info("Test Results:")
    logger.info(f"Incarnations discovered: {inc_count}")
    logger.info(f"Tools registered: {tool_count}")
    logger.info(f"Generator test: {'Success' if generator_success else 'Failed'}")
    logger.info("===========================")

if __name__ == "__main__":
    main()
