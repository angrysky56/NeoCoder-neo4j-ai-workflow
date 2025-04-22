"""
Tests for the NeoCoder MCP server.
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from mcp.types import TextContent
from mcp_neocoder.server import Neo4jWorkflowServer, create_server

@pytest.fixture
def mock_driver():
    """Create a mock Neo4j driver."""
    driver = AsyncMock()
    session = AsyncMock()
    tx = AsyncMock()
    
    # Set up the mock session to return a transaction that can be used in a context manager
    session.execute_read = AsyncMock(return_value='[]')
    session.execute_write = AsyncMock(return_value='[]')
    
    driver.session.return_value.__aenter__.return_value = session
    
    return driver

def test_create_server():
    """Test that create_server returns a Neo4jWorkflowServer instance."""
    with patch('mcp_neocoder.server.AsyncGraphDatabase.driver') as mock_driver_constructor:
        mock_driver_constructor.return_value = MagicMock()
        server = create_server("bolt://localhost:7687", "neo4j", "password")
        assert isinstance(server, Neo4jWorkflowServer)
        assert server.database == "neo4j"

@pytest.mark.asyncio
async def test_get_guidance_hub_empty_result(mock_driver):
    """Test the get_guidance_hub method with empty results."""
    # Mock the _read_query method to return an empty list
    server = Neo4jWorkflowServer(mock_driver)
    server._read_query = AsyncMock(return_value='[]')
    
    # Mock _create_default_hub to return a specific result
    mock_result = [TextContent(type="text", text="Default hub content")]
    server._create_default_hub = AsyncMock(return_value=mock_result)
    
    # Call the method
    result = await server.get_guidance_hub()
    
    # Verify that _create_default_hub was called since no hub was found
    server._create_default_hub.assert_called_once()
    assert result == mock_result

@pytest.mark.asyncio
async def test_get_guidance_hub_with_result(mock_driver):
    """Test the get_guidance_hub method with a result."""
    # Mock the _read_query method to return a result
    server = Neo4jWorkflowServer(mock_driver)
    server._read_query = AsyncMock(return_value='[{"description": "Hub content"}]')
    
    # Mock _create_default_hub (should not be called)
    server._create_default_hub = AsyncMock()
    
    # Call the method
    result = await server.get_guidance_hub()
    
    # Verify that _create_default_hub was not called since a hub was found
    server._create_default_hub.assert_not_called()
    assert len(result) == 1
    assert result[0].type == "text"
    assert result[0].text == "Hub content"
