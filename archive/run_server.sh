#!/bin/bash
# Run the NeoCoder MCP server

set -e  # Exit on any error

# Check if Neo4j is running
if command -v docker &> /dev/null; then
    NEO4J_CONTAINER=$(docker ps | grep neo4j || true)
    if [ -z "$NEO4J_CONTAINER" ]; then
        echo "Warning: Neo4j container not detected. Make sure Neo4j is running."
    else
        echo "Neo4j container detected."
    fi
else
    echo "Docker not detected. Skipping container checks."
    echo "Make sure your Neo4j instance is running and accessible."
fi

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Set environment variables for Neo4j connection
export NEO4J_URL="bolt://localhost:7687"
export NEO4J_USERNAME="neo4j"
export NEO4J_PASSWORD="password"

# Run the MCP server
echo "Starting NeoCoder MCP Server..."
python -m mcp_neocoder server

# This line won't be reached if the server is still running
echo "Server stopped."
