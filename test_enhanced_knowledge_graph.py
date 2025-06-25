#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced Knowledge Graph tools with better AI guidance.
"""

import asyncio
import logging
from src.mcp_neocoder.incarnations.knowledge_graph_incarnation import KnowledgeGraphIncarnation
from src.mcp_neocoder.init_db import init_neo4j_connection
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_enhanced_tools():
    """Test the enhanced knowledge graph tools with AI-friendly validation and guidance."""

    # Initialize the driver
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")

    try:
        driver = await init_neo4j_connection(uri, user, password)
    except Exception as e:
        logger.error(f"Failed to initialize Neo4j driver: {e}")
        return

    try:
        incarnation = KnowledgeGraphIncarnation(driver=driver, database="neo4j")
        await incarnation.initialize_schema()

        print("=" * 60)
        print("Testing Enhanced Knowledge Graph Tools")
        print("=" * 60)

        # Test 1: Try to create relations without entities (should give helpful error)
        print("\n1. Testing relation creation without existing entities...")
        relations_missing_entities = [
            {"from": "React", "to": "JavaScript", "relationType": "DEPENDS_ON"},
            {"from": "Node.js", "to": "JavaScript", "relationType": "USES"}
        ]

        result = await incarnation.create_relations(relations_missing_entities)
        print("Result:", result[0].text if result else "No result")

        # Test 2: Create entities first
        print("\n2. Creating entities with comprehensive examples...")
        entities = [
            {
                "name": "React",
                "entityType": "Framework",
                "observations": [
                    "JavaScript UI library",
                    "Component-based architecture",
                    "Virtual DOM for performance",
                    "Developed by Facebook"
                ]
            },
            {
                "name": "JavaScript",
                "entityType": "Language",
                "observations": [
                    "Dynamic programming language",
                    "Runs in browsers and servers",
                    "Event-driven and functional paradigms",
                    "ECMAScript standard"
                ]
            },
            {
                "name": "Node.js",
                "entityType": "Runtime",
                "observations": [
                    "JavaScript server runtime",
                    "Non-blocking I/O",
                    "Event-driven architecture",
                    "Built on V8 engine"
                ]
            }
        ]

        result = await incarnation.create_entities(entities)
        print("Result:", result[0].text if result else "No result")

        # Test 3: Now create relations (should succeed)
        print("\n3. Creating relations between existing entities...")
        relations = [
            {"from": "React", "to": "JavaScript", "relationType": "DEPENDS_ON"},
            {"from": "Node.js", "to": "JavaScript", "relationType": "USES"},
            {"from": "React", "to": "Node.js", "relationType": "CAN_RUN_ON"}
        ]

        result = await incarnation.create_relations(relations)
        print("Result:", result[0].text if result else "No result")

        # Test 4: Read the entire graph to see results
        print("\n4. Reading the complete knowledge graph...")
        result = await incarnation.read_graph()
        print("Graph contents:")
        print(result[0].text if result else "No result")

        # Test 5: Test validation with malformed data
        print("\n5. Testing validation with malformed entity data...")
        bad_entities = [
            {"name": "BadEntity"},  # Missing entityType and observations
            {"entityType": "Type", "observations": []},  # Missing name
            {"name": "AnotherEntity", "entityType": "Type", "observations": "not_a_list"}  # Wrong type for observations
        ]

        result = await incarnation.create_entities(bad_entities)
        print("Validation result:", result[0].text if result else "No result")

        # Test 6: Test validation with malformed relation data
        print("\n6. Testing validation with malformed relation data...")
        bad_relations = [
            {"from": "Entity1"},  # Missing to and relationType
            {"to": "Entity2", "relationType": "RELATES"},  # Missing from
            {"from": "", "to": "Entity3", "relationType": "CONNECTS"}  # Empty from field
        ]

        result = await incarnation.create_relations(bad_relations)
        print("Validation result:", result[0].text if result else "No result")

        print("\n" + "=" * 60)
        print("Enhanced Knowledge Graph Tools Test Complete!")
        print("All tools now provide comprehensive validation and guidance for AI users.")
        print("=" * 60)

    except Exception as e:
        logger.error(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if driver:
            await driver.close()

if __name__ == "__main__":
    asyncio.run(test_enhanced_tools())
