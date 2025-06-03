#!/usr/bin/env python3
"""
Test script to verify that incarnation tools are properly registered.

This script will create a Neo4j Workflow Server instance, and then check if the tools
from the data_analysis incarnation are registered with the MCP server.
"""

import os
import sys
import asyncio
import logging
from typing import Dict, List, Set

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_tool_fix")

# Set up Neo4j connection parameters
os.environ.setdefault("NEO4J_URL", "bolt://localhost:7687")
os.environ.setdefault("NEO4J_USERNAME", "neo4j")
os.environ.setdefault("NEO4J_PASSWORD", "password")
os.environ.setdefault("NEO4J_DATABASE", "neo4j")

async def init_server():
    """Initialize the server and check if tools are registered."""
    from neo4j import AsyncGraphDatabase
    from mcp.server.fastmcp import FastMCP
    from mcp_neocoder.incarnations.polymorphic_adapter import IncarnationType
    from mcp_neocoder.incarnation_registry import registry as incarnation_registry
    
    # Create Neo4j driver directly
    db_url = os.environ.get("NEO4J_URL")
    username = os.environ.get("NEO4J_USERNAME")
    password = os.environ.get("NEO4J_PASSWORD")
    database = os.environ.get("NEO4J_DATABASE")
    
    logger.info(f"Creating Neo4j driver with connection parameters:")
    logger.info(f"  URL: {db_url}")
    logger.info(f"  Username: {username}")
    logger.info(f"  Database: {database}")
    
    driver = AsyncGraphDatabase.driver(db_url, auth=(username, password))
    
    # Create MCP server for testing
    mcp = FastMCP("test-mcp", dependencies=["neo4j", "pydantic"])
    
    # Discover incarnations
    incarnation_registry.discover()
    
    # For each incarnation, get its tools and register them with MCP
    registered_tools = set()
    
    for inc_type, inc_class in incarnation_registry.incarnations.items():
        logger.info(f"Processing tools for incarnation: {inc_type.value}")
        
        # Create instance
        instance = inc_class(driver, database)
        
        # Get tool methods
        tool_methods = instance.list_tool_methods()
        logger.info(f"Found {len(tool_methods)} tools in {inc_type.value}: {tool_methods}")
        
        # Register each tool with MCP
        for method_name in tool_methods:
            method = getattr(instance, method_name)
            mcp.add_tool(method)
            registered_tools.add(method.__name__)
            logger.info(f"Registered tool: {method_name}")
    
    # Check if specific incarnation tools are registered
    data_analysis_tools = {"tool_one", "tool_two"}
    missing_tools = data_analysis_tools - registered_tools
    found_tools = data_analysis_tools & registered_tools
    
    logger.info(f"Looking for data_analysis tools: {data_analysis_tools}")
    logger.info(f"All registered tools: {registered_tools}")
    
    if missing_tools:
        logger.error(f"Missing tools: {missing_tools}")
        logger.error("Tool registration FAILED!")
    else:
        logger.info(f"Found all expected tools: {found_tools}")
        logger.info("Tool registration SUCCESS!")
    
    # Close all connections
    await driver.close()
    
    return {
        "total_tools": len(registered_tools),
        "all_tools": sorted(registered_tools),
        "registered_data_analysis_tools": sorted(found_tools),
        "missing_data_analysis_tools": sorted(missing_tools),
    }

if __name__ == "__main__":
    # Run the test
    result = asyncio.run(init_server())
    
    # Print results
    print("\n=== TOOL REGISTRATION TEST RESULTS ===")
    print(f"Total registered tools: {result['total_tools']}")
    print(f"Data analysis tools found: {', '.join(result['registered_data_analysis_tools'])}")
    
    if result['missing_data_analysis_tools']:
        print(f"MISSING TOOLS: {', '.join(result['missing_data_analysis_tools'])}")
        print("\nREGISTRATION TEST FAILED!")
        sys.exit(1)
    else:
        print("\nREGISTRATION TEST PASSED!")
        sys.exit(0)
