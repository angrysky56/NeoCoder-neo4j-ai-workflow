#!/usr/bin/env python3
"""
Test script to verify Neo4j transaction scope fixes in NeoCoder
"""

import asyncio
import logging
from neo4j import AsyncGraphDatabase
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_neocoder.incarnations.knowledge_graph_incarnation import KnowledgeGraphIncarnation
from mcp_neocoder.event_loop_manager import initialize_main_loop

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_delete_entities():
    """Test the fixed delete_entities method"""
    # Initialize the main event loop
    initialize_main_loop()
    
    # Connection details from environment variables
    uri = os.environ.get("NEO4J_URL", "bolt://localhost:7687")
    username = os.environ.get("NEO4J_USERNAME", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD")
    database = os.environ.get("NEO4J_DATABASE", "neo4j")
    
    if not password:
        logger.error("NEO4J_PASSWORD environment variable not set!")
        logger.info("Please set NEO4J_PASSWORD and try again:")
        logger.info("export NEO4J_PASSWORD='your_password_here'")
        return
    
    driver = None
    try:
        # Create driver
        logger.info("Creating Neo4j driver...")
        driver = AsyncGraphDatabase.driver(uri, auth=(username, password))
        
        # Create incarnation instance
        incarnation = KnowledgeGraphIncarnation(driver, database)
        
        # Test 1: Create test entities
        logger.info("Creating test entities...")
        test_entities = [
            {
                "name": "TestEntity1",
                "entityType": "TestType",
                "observations": ["Test observation 1", "Test observation 2"]
            },
            {
                "name": "TestEntity2", 
                "entityType": "TestType",
                "observations": ["Test observation 3"]
            }
        ]
        
        result = await incarnation.create_entities(entities=test_entities)
        logger.info(f"Create result: {result[0].text}")
        
        # Test 2: Delete entities
        logger.info("Testing delete_entities...")
        delete_result = await incarnation.delete_entities(entityNames=["TestEntity1", "TestEntity2"])
        logger.info(f"Delete result: {delete_result[0].text}")
        
        # Test 3: Verify deletion by trying to read
        logger.info("Verifying deletion...")
        read_result = await incarnation.open_nodes(names=["TestEntity1", "TestEntity2"])
        logger.info(f"Read result: {read_result[0].text}")
        
        logger.info("All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            await driver.close()
            logger.info("Driver closed")

if __name__ == "__main__":
    asyncio.run(test_delete_entities())
