# NeoCoder Tests

This directory contains test scripts for the NeoCoder Neo4j AI Workflow.

## Available Tests

- `test_knowledge_graph.py` - Tests the Knowledge Graph API functions to ensure proper Neo4j node labeling integration

## Running Tests

To run a specific test:

```bash
python tests/test_knowledge_graph.py
```

Make sure your Neo4j database is running and accessible, and that your environment variables are set correctly:

- `NEO4J_URL` - The URL for your Neo4j database (default: "bolt://localhost:7687")
- `NEO4J_USERNAME` - Your Neo4j username (default: "neo4j")
- `NEO4J_PASSWORD` - Your Neo4j password (default: "password")
- `NEO4J_DATABASE` - The Neo4j database to use (default: "neo4j")

## Adding New Tests

When adding new tests:

1. Create a new Python file in the tests directory
2. Import the relevant modules from the src directory
3. Implement async test functions
4. Add logging to show test progress and results
5. Update this README to include your new test

## Test Guidelines

- Tests should clean up after themselves
- Tests should include proper error handling
- Tests should verify both functionality and data structure
- Tests should be independent of each other
