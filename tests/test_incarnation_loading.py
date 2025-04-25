#!/usr/bin/env python
"""
Script to test the dynamic loading of incarnations and their tools.

This script loads all incarnations and their tools, and displays them
to verify that they're being registered correctly.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
script_dir = Path(__file__).resolve().parent
src_dir = script_dir.parent / "src"
sys.path.append(str(src_dir))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_incarnation_loading")

# Import the required modules
from mcp_neocoder.incarnation_registry import registry as incarnation_registry
from mcp_neocoder.tool_registry import registry as tool_registry
from mcp_neocoder.incarnations.polymorphic_adapter import IncarnationType
from neo4j import AsyncGraphDatabase

# Neo4j connection parameters (can be overridden by environment variables)
NEO4J_URL = os.environ.get("NEO4J_URL", "bolt://localhost:7687")
NEO4J_USERNAME = os.environ.get("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")
NEO4J_DATABASE = os.environ.get("NEO4J_DATABASE", "neo4j")

async def test_incarnation_loading():
    """Test the loading of incarnations and their tools."""
    logger.info("Testing incarnation loading...")
    
    # Create a Neo4j driver
    driver = AsyncGraphDatabase.driver(NEO4J_URL, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    try:
        # Test connection to Neo4j
        async with driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run("RETURN 'Connection successful' as message")
            record = await result.single()
            logger.info(f"Neo4j connection: {record['message']}")
        
        # Discover incarnations
        incarnation_registry.discover()
        
        # Print discovered incarnations
        logger.info(f"Discovered {len(incarnation_registry.incarnations)} incarnations:")
        for inc_type, inc_class in incarnation_registry.incarnations.items():
            logger.info(f"  - {inc_type.value}: {inc_class.__name__}")
        
        # Create instances of each incarnation
        for inc_type, inc_class in incarnation_registry.incarnations.items():
            # Get or create an instance
            instance = incarnation_registry.get_instance(inc_type, driver, NEO4J_DATABASE)
            
            if instance:
                # Register tools
                tool_registry.register_class_tools(instance, inc_type.value)
                
                # List tools for this incarnation
                tools_for_incarnation = tool_registry.tool_categories.get(inc_type.value, set())
                logger.info(f"Tools for {inc_type.value} incarnation ({len(tools_for_incarnation)}):")
                
                for tool_name in tools_for_incarnation:
                    if tool_name in tool_registry.tools:
                        tool_func = tool_registry.tools[tool_name]
                        description = "No description"
                        if tool_func.__doc__:
                            description = tool_func.__doc__.split('\n')[0].strip()
                        logger.info(f"  - {tool_name}: {description}")
        
        # Print total tools registered
        logger.info(f"Total tools registered: {len(tool_registry.tools)}")
        
        # Print tool categories
        logger.info("Tool categories:")
        for category, tools in tool_registry.tool_categories.items():
            logger.info(f"  {category}: {len(tools)} tools")
    
    except Exception as e:
        logger.error(f"Error during incarnation loading test: {e}")
    finally:
        await driver.close()

if __name__ == "__main__":
    # Run the async test function
    asyncio.run(test_incarnation_loading())
