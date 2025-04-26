#!/usr/bin/env python3
"""
Test script for Knowledge Graph API functions.

This script tests the newly implemented knowledge graph API functions
to ensure they properly integrate with Neo4j's node labeling system.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from mcp_neocoder.incarnations.knowledge_graph_incarnation import KnowledgeGraphIncarnation
from neo4j import AsyncGraphDatabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_knowledge_graph")

# Neo4j connection parameters - update these as needed
NEO4J_URL = os.environ.get("NEO4J_URL", "bolt://localhost:7687")
NEO4J_USERNAME = os.environ.get("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")
NEO4J_DATABASE = os.environ.get("NEO4J_DATABASE", "neo4j")

async def run_test():
    """Run the knowledge graph API tests."""
    try:
        logger.info(f"Connecting to Neo4j at {NEO4J_URL}")
        driver = AsyncGraphDatabase.driver(NEO4J_URL, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        
        # Initialize the knowledge graph incarnation
        kg = KnowledgeGraphIncarnation(driver, NEO4J_DATABASE)
        
        # Initialize the schema
        logger.info("Initializing schema...")
        await kg.initialize_schema()
        
        # Clear any existing data
        logger.info("Clearing existing test data...")
        async with driver.session(database=NEO4J_DATABASE) as session:
            await session.execute_write(lambda tx: tx.run(
                "MATCH (e:Entity) WHERE e.name STARTS WITH 'Test' DETACH DELETE e"
            ))
            await session.execute_write(lambda tx: tx.run(
                "MATCH (o:Observation) WHERE NOT (o)<-[:HAS_OBSERVATION]-() DETACH DELETE o"
            ))
        
        # Test create_entities
        logger.info("Testing create_entities...")
        test_entities = [
            {
                "name": "TestEntity1",
                "entityType": "Person",
                "observations": ["This is a test entity", "It has multiple observations"]
            },
            {
                "name": "TestEntity2",
                "entityType": "Organization",
                "observations": ["Another test entity"]
            }
        ]
        
        result = await kg.create_entities(test_entities)
        logger.info(f"Create entities result: {result[0].text}")
        
        # Test create_relations
        logger.info("Testing create_relations...")
        test_relations = [
            {
                "from": "TestEntity1",
                "to": "TestEntity2",
                "relationType": "WORKS_FOR"
            }
        ]
        
        result = await kg.create_relations(test_relations)
        logger.info(f"Create relations result: {result[0].text}")
        
        # Test add_observations
        logger.info("Testing add_observations...")
        test_observations = [
            {
                "entityName": "TestEntity1",
                "contents": ["A new observation added later"]
            }
        ]
        
        result = await kg.add_observations(test_observations)
        logger.info(f"Add observations result: {result[0].text}")
        
        # Test read_graph
        logger.info("Testing read_graph...")
        result = await kg.read_graph()
        logger.info("Read graph returned data successfully")
        
        # Test search_nodes
        logger.info("Testing search_nodes...")
        result = await kg.search_nodes("test")
        logger.info(f"Search nodes found entities: {'TestEntity' in result[0].text}")
        
        # Test open_nodes
        logger.info("Testing open_nodes...")
        result = await kg.open_nodes(["TestEntity1", "TestEntity2"])
        logger.info(f"Open nodes returned data: {'TestEntity1' in result[0].text and 'TestEntity2' in result[0].text}")
        
        # Verify correct labeling in Neo4j
        logger.info("Verifying correct Neo4j labeling...")
        async with driver.session(database=NEO4J_DATABASE) as session:
            result = await session.execute_read(lambda tx: tx.run(
                "MATCH (e:Entity) WHERE e.name STARTS WITH 'Test' RETURN e.name, labels(e)"
            ))
            records = await result.values()
            
            for record in records:
                logger.info(f"Entity: {record[0]}, Labels: {record[1]}")
                assert "Entity" in record[1], f"Entity {record[0]} is missing the 'Entity' label"
            
            # Check observations
            result = await session.execute_read(lambda tx: tx.run(
                """
                MATCH (e:Entity)-[:HAS_OBSERVATION]->(o:Observation)
                WHERE e.name STARTS WITH 'Test'
                RETURN e.name, o.content, labels(o)
                """
            ))
            records = await result.values()
            
            for record in records:
                logger.info(f"Entity: {record[0]}, Observation: {record[1]}, Labels: {record[2]}")
                assert "Observation" in record[2], f"Observation for {record[0]} is missing the 'Observation' label"
        
        # Test delete functions
        logger.info("Testing delete_observations...")
        delete_observations = [
            {
                "entityName": "TestEntity1",
                "observations": ["This is a test entity"]
            }
        ]
        
        result = await kg.delete_observations(delete_observations)
        logger.info(f"Delete observations result: {result[0].text}")
        
        logger.info("Testing delete_relations...")
        delete_relations = [
            {
                "from": "TestEntity1",
                "to": "TestEntity2",
                "relationType": "WORKS_FOR"
            }
        ]
        
        result = await kg.delete_relations(delete_relations)
        logger.info(f"Delete relations result: {result[0].text}")
        
        logger.info("Testing delete_entities...")
        result = await kg.delete_entities(["TestEntity1", "TestEntity2"])
        logger.info(f"Delete entities result: {result[0].text}")
        
        logger.info("All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in test: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        if driver:
            await driver.close()

if __name__ == "__main__":
    # Run the test
    asyncio.run(run_test())
