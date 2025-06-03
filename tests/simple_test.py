#!/usr/bin/env python3
"""
Simplified test script to examine registered tools in the MCP server.
"""

import os
import sys
import asyncio
import logging
from neo4j import AsyncGraphDatabase

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("simple_test")

# Import required modules (but avoid creating the server for now)
from mcp_neocoder.incarnations.polymorphic_adapter import IncarnationType
from mcp_neocoder.tool_registry import registry
from mcp_neocoder.incarnation_registry import registry as incarnation_registry

# Manually initialize the registry
def init_registries():
    # Discover incarnations
    logger.info("Discovering incarnations...")
    incarnation_registry.discover()
    for inc_type, inc_class in incarnation_registry.incarnations.items():
        logger.info(f"Found incarnation: {inc_type.value} ({inc_class.__name__})")

async def test_registration():
    # Get connection parameters
    db_url = os.environ.get("NEO4J_URL", "bolt://localhost:7687")
    username = os.environ.get("NEO4J_USERNAME", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "password")
    database = os.environ.get("NEO4J_DATABASE", "neo4j")
    
    # Create a Neo4j driver
    driver = AsyncGraphDatabase.driver(db_url, auth=(username, password))
    
    # Create instances for each incarnation and check their tools
    for inc_type, inc_class in incarnation_registry.incarnations.items():
        logger.info(f"Testing {inc_type.value} incarnation...")
        
        # Create instance
        instance = inc_class(driver, database)
        
        # Get tool methods
        try:
            tool_methods = instance.list_tool_methods()
            logger.info(f"Tools in {inc_type.value}: {tool_methods}")
            
            # Verify tool methods exist
            for method_name in tool_methods:
                if hasattr(instance, method_name) and callable(getattr(instance, method_name)):
                    logger.info(f"Tool method exists: {method_name}")
                else:
                    logger.error(f"Tool method does not exist: {method_name}")
        except Exception as e:
            logger.error(f"Error listing tool methods: {e}")
    
    # Close the driver
    await driver.close()

async def main():
    try:
        # Initialize registries
        init_registries()
        
        # Test registration
        await test_registration()
    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    # Run the test
    asyncio.run(main())
