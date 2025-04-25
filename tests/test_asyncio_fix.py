"""
Test file to verify the asyncio event loop fix in the NeoCoder server.

This test ensures that the Neo4jWorkflowServer properly handles event loops
and doesn't encounter the "Future attached to a different loop" error.
"""

import os
import asyncio
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

# Import the server
from mcp_neocoder.server import Neo4jWorkflowServer, logger

# Mock environment variables for the test
os.environ["NEO4J_URL"] = "bolt://localhost:7687"
os.environ["NEO4J_USERNAME"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "password"
os.environ["NEO4J_DATABASE"] = "neo4j"

@pytest.mark.asyncio
async def test_server_initialization():
    """Test that server initialization handles the event loop correctly."""
    # Create mocks
    mock_driver = AsyncMock()
    mock_session = AsyncMock()
    mock_driver.session.return_value.__aenter__.return_value = mock_session
    
    # Make _read_query return empty results (simple case)
    read_response = '[]'
    mock_session.execute_read.return_value = read_response
    
    # Testing the initialization of the server
    with patch('asyncio.get_event_loop', return_value=asyncio.get_event_loop()):
        server = Neo4jWorkflowServer(mock_driver, "neo4j")
        
        # Test should reach this point without raising event loop errors
        assert hasattr(server, 'mcp'), "Server should have an MCP instance"

@pytest.mark.asyncio
async def test_get_guidance_hub():
    """Test that get_guidance_hub doesn't cause event loop errors."""
    # Create mocks
    mock_driver = AsyncMock()
    mock_session = AsyncMock()
    mock_driver.session.return_value.__aenter__.return_value = mock_session
    
    # Make _read_query return dummy results 
    read_response = '[{"description": "Test Hub Content"}]'
    mock_session.execute_read.return_value = read_response
    
    # Create server with minimum configuration for testing
    server = Neo4jWorkflowServer(mock_driver, "neo4j")
    
    # Create a minimal incarnation registry for testing
    server.incarnation_registry = {}  # Empty but not None
    
    # Test the guidance hub function
    result = await server.get_guidance_hub()
    
    # Verify the function returns expected content format
    assert isinstance(result, list), "Result should be a list"
    assert len(result) > 0, "Result should not be empty"
    assert hasattr(result[0], 'type'), "Result should have a type attribute"
    assert hasattr(result[0], 'text'), "Result should have a text attribute"
    assert result[0].type == "text", "Result type should be text"
    assert "Test Hub Content" in result[0].text, "Result should contain the hub content"

if __name__ == "__main__":
    # Run these tests with pytest
    pytest.main(["-xvs", __file__])
