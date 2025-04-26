#!/usr/bin/env python3
"""
Test script to check if incarnation tools are properly registered.

This script initializes the Neo4j Workflow Server and then checks if tools from each
incarnation are successfully registered with the MCP server.
"""

import asyncio
import logging
import os
import sys
from typing import Dict, List

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("test_tool_registration")

# Import required modules
from mcp_neocoder.server import Neo4jWorkflowServer, create_server
from mcp_neocoder.incarnations.polymorphic_adapter import IncarnationType
from mcp_neocoder.tool_registry import registry

async def test_incarnation_tools():
    """Test if tools from each incarnation are properly registered."""
    # Get database connection parameters
    db_url = os.environ.get("NEO4J_URL", "bolt://localhost:7687")
    username = os.environ.get("NEO4J_USERNAME", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "password")
    database = os.environ.get("NEO4J_DATABASE", "neo4j")
    
    # Create server
    server = create_server(db_url, username, password, database)
    
    # Get registered tools
    tool_names = [tool.__name__ for tool in server.mcp.tools]
    logger.info(f"Registered tools: {tool_names}")
    
    # Check if incarnation tools are registered
    for inc_type in IncarnationType:
        tools_in_category = registry.tool_categories.get(inc_type.value, set())
        logger.info(f"Tools in {inc_type.value} category: {tools_in_category}")
        
        # Check if tools from this incarnation are in the MCP tools list
        missing_tools = []
        for tool_name in tools_in_category:
            if tool_name not in tool_names:
                missing_tools.append(tool_name)
        
        if missing_tools:
            logger.error(f"Missing tools from {inc_type.value} incarnation: {missing_tools}")
        else:
            logger.info(f"All tools from {inc_type.value} incarnation are registered")
    
    # Check specific tools we know should exist
    for tool_name in ["tool_one", "tool_two"]:
        if tool_name in tool_names:
            logger.info(f"Tool {tool_name} is registered")
        else:
            logger.error(f"Tool {tool_name} is NOT registered")
    
    return tool_names

if __name__ == "__main__":
    # Run the test
    loop = asyncio.get_event_loop()
    tools = loop.run_until_complete(test_incarnation_tools())
    print(f"Total tools registered: {len(tools)}")
    print("Registered tools:")
    for tool in sorted(tools):
        print(f"  - {tool}")
