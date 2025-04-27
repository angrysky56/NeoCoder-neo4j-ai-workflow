"""
Initialization Script for NeoCoder Polymorphic Framework

This script initializes the Neo4j database with the necessary schemas for each incarnation.
It creates the base nodes and relationships needed for the system to function properly.
"""

import asyncio
import json
import logging
import os
import sys
from typing import List, Optional
from neo4j import AsyncGraphDatabase, AsyncDriver

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mcp_neocoder_init")

from enum import Enum

# Import and use the IncarnationType enum from the polymorphic adapter
from .incarnations.polymorphic_adapter import IncarnationType

# List of incarnation type values for validation
INCARNATION_TYPES = [t.value for t in IncarnationType]

# Dynamically discover available incarnation types
def discover_incarnation_types():
    """Discover available incarnation types from the filesystem."""
    import os
    import importlib.util

    incarnation_types = []
    current_dir = os.path.dirname(os.path.abspath(__file__))
    incarnations_dir = os.path.join(current_dir, "incarnations")

    if not os.path.exists(incarnations_dir):
        logger.warning(f"Incarnations directory not found: {incarnations_dir}")
        return INCARNATION_TYPES  # Fall back to the predefined list

    # Match module filenames to incarnation types
    for entry in os.listdir(incarnations_dir):
        if entry.startswith("__") or not entry.endswith(".py"):
            continue

        module_name = entry[:-3]  # Remove .py extension

        # Skip base modules and adapters
        if module_name in ("base_incarnation", "polymorphic_adapter"):
            continue

        # Try to match filename to incarnation type
        if module_name.endswith("_incarnation"):
            # Extract the type from the filename (e.g., research_incarnation.py -> research)
            incarnation_name = module_name.replace("_incarnation", "")

            # Add to discovered types
            for inc_type in IncarnationType:
                if inc_type.value.startswith(incarnation_name):
                    incarnation_types.append(inc_type.value)
                    logger.info(f"Discovered incarnation type: {inc_type.value} from {module_name}")
                    break

    return incarnation_types if incarnation_types else INCARNATION_TYPES


async def init_neo4j_connection(uri: str, user: str, password: str) -> AsyncDriver:
    """Initialize Neo4j connection."""
    try:
        driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        # Test the connection
        async with driver.session() as session:
            await session.run("RETURN 1")
        logger.info("Successfully connected to Neo4j")
        return driver
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        sys.exit(1)


async def init_base_schema(driver: AsyncDriver, database: str = "neo4j"):
    """Initialize the base schema that is common to all incarnations."""
    logger.info("Initializing base schema...")

    # Base constraints and indexes
    base_schema_queries = [
        # Guidance Hub
        "CREATE CONSTRAINT hub_id IF NOT EXISTS FOR (hub:AiGuidanceHub) REQUIRE hub.id IS UNIQUE",

        # Tool proposals
        "CREATE CONSTRAINT proposal_id IF NOT EXISTS FOR (p:ToolProposal) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT request_id IF NOT EXISTS FOR (r:ToolRequest) REQUIRE r.id IS UNIQUE",

        # Cypher snippets
        "CREATE CONSTRAINT snippet_id IF NOT EXISTS FOR (s:CypherSnippet) REQUIRE s.id IS UNIQUE",
        "CREATE CONSTRAINT tag_name IF NOT EXISTS FOR (t:Tag) REQUIRE t.name IS UNIQUE",

        # Indexes
        "CREATE INDEX hub_type IF NOT EXISTS FOR (hub:AiGuidanceHub) ON (hub.type)",
        "CREATE INDEX proposal_status IF NOT EXISTS FOR (p:ToolProposal) ON (p.status)",
        "CREATE INDEX request_status IF NOT EXISTS FOR (r:ToolRequest) ON (r.status)",
        "CREATE INDEX snippet_name IF NOT EXISTS FOR (s:CypherSnippet) ON (s.name)"
    ]

    try:
        async with driver.session(database=database) as session:
            for query in base_schema_queries:
                await session.run(query)
        logger.info("Base schema initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing base schema: {e}")
        raise


async def init_research_schema(driver: AsyncDriver, database: str = "neo4j"):
    """Initialize the schema for the Research Orchestration Platform incarnation."""
    logger.info("Initializing research schema...")

    research_schema_queries = [
        # Constraints
        "CREATE CONSTRAINT research_hypothesis_id IF NOT EXISTS FOR (h:Hypothesis) REQUIRE h.id IS UNIQUE",
        "CREATE CONSTRAINT research_experiment_id IF NOT EXISTS FOR (e:Experiment) REQUIRE e.id IS UNIQUE",
        "CREATE CONSTRAINT research_protocol_id IF NOT EXISTS FOR (p:Protocol) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT research_observation_id IF NOT EXISTS FOR (o:Observation) REQUIRE o.id IS UNIQUE",
        "CREATE CONSTRAINT research_run_id IF NOT EXISTS FOR (r:Run) REQUIRE r.id IS UNIQUE",

        # Indexes
        "CREATE INDEX research_hypothesis_status IF NOT EXISTS FOR (h:Hypothesis) ON (h.status)",
        "CREATE INDEX research_experiment_status IF NOT EXISTS FOR (e:Experiment) ON (e.status)",
        "CREATE INDEX research_protocol_name IF NOT EXISTS FOR (p:Protocol) ON (p.name)",

        # Create research hub
        """
        MERGE (hub:AiGuidanceHub {id: 'research_hub'})
        ON CREATE SET
            hub.description = 'Research Orchestration Platform - A system for managing scientific workflows, hypotheses, experiments, and observations.'
        RETURN hub
        """
    ]

    try:
        async with driver.session(database=database) as session:
            for query in research_schema_queries:
                await session.run(query)
        logger.info("Research schema initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing research schema: {e}")
        raise


async def init_decision_schema(driver: AsyncDriver, database: str = "neo4j"):
    """Initialize the schema for the Decision Support System incarnation."""
    logger.info("Initializing decision support schema...")

    decision_schema_queries = [
        # Constraints
        "CREATE CONSTRAINT decision_id IF NOT EXISTS FOR (d:Decision) REQUIRE d.id IS UNIQUE",
        "CREATE CONSTRAINT alternative_id IF NOT EXISTS FOR (a:Alternative) REQUIRE a.id IS UNIQUE",
        "CREATE CONSTRAINT metric_id IF NOT EXISTS FOR (m:Metric) REQUIRE m.id IS UNIQUE",
        "CREATE CONSTRAINT evidence_id IF NOT EXISTS FOR (e:Evidence) REQUIRE e.id IS UNIQUE",

        # Indexes
        "CREATE INDEX decision_status IF NOT EXISTS FOR (d:Decision) ON (d.status)",
        "CREATE INDEX alternative_name IF NOT EXISTS FOR (a:Alternative) ON (a.name)",

        # Create decision hub
        """
        MERGE (hub:AiGuidanceHub {id: 'decision_hub'})
        ON CREATE SET
            hub.description = 'Decision Support System - A system for tracking decisions, alternatives, metrics, and evidence to support transparent, data-driven decision-making.'
        RETURN hub
        """
    ]

    try:
        async with driver.session(database=database) as session:
            for query in decision_schema_queries:
                await session.run(query)
        logger.info("Decision schema initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing decision schema: {e}")
        raise


async def init_learning_schema(driver: AsyncDriver, database: str = "neo4j"):
    """Initialize the schema for the Continuous Learning Environment incarnation."""
    logger.info("Initializing learning schema...")

    learning_schema_queries = [
        # Constraints
        "CREATE CONSTRAINT learning_user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
        "CREATE CONSTRAINT learning_concept_id IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE",
        "CREATE CONSTRAINT learning_problem_id IF NOT EXISTS FOR (p:Problem) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT learning_attempt_id IF NOT EXISTS FOR (a:Attempt) REQUIRE a.id IS UNIQUE",

        # Indexes
        "CREATE INDEX learning_user_name IF NOT EXISTS FOR (u:User) ON (u.name)",
        "CREATE INDEX learning_concept_name IF NOT EXISTS FOR (c:Concept) ON (c.name)",
        "CREATE INDEX learning_problem_difficulty IF NOT EXISTS FOR (p:Problem) ON (p.difficulty)",

        # Create learning hub
        """
        MERGE (hub:AiGuidanceHub {id: 'learning_hub'})
        ON CREATE SET
            hub.description = 'Continuous Learning Environment - A system for adaptive learning and personalized content delivery based on knowledge spaces and mastery tracking.'
        RETURN hub
        """
    ]

    try:
        async with driver.session(database=database) as session:
            for query in learning_schema_queries:
                await session.run(query)
        logger.info("Learning schema initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing learning schema: {e}")
        raise


async def init_simulation_schema(driver: AsyncDriver, database: str = "neo4j"):
    """Initialize the schema for the Complex System Simulation incarnation."""
    logger.info("Initializing simulation schema...")

    simulation_schema_queries = [
        # Constraints
        "CREATE CONSTRAINT simulation_entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
        "CREATE CONSTRAINT simulation_model_id IF NOT EXISTS FOR (m:Model) REQUIRE m.id IS UNIQUE",
        "CREATE CONSTRAINT simulation_run_id IF NOT EXISTS FOR (r:SimulationRun) REQUIRE r.id IS UNIQUE",
        "CREATE CONSTRAINT simulation_state_id IF NOT EXISTS FOR (s:State) REQUIRE s.id IS UNIQUE",

        # Indexes
        "CREATE INDEX simulation_entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)",
        "CREATE INDEX simulation_model_name IF NOT EXISTS FOR (m:Model) ON (m.name)",
        "CREATE INDEX simulation_run_timestamp IF NOT EXISTS FOR (r:SimulationRun) ON (r.timestamp)",

        # Create simulation hub
        """
        MERGE (hub:AiGuidanceHub {id: 'simulation_hub'})
        ON CREATE SET
            hub.description = 'Complex System Simulation - A system for modeling and simulating complex systems with multiple interacting components and emergent behavior.'
        RETURN hub
        """
    ]

    try:
        async with driver.session(database=database) as session:
            for query in simulation_schema_queries:
                await session.run(query)
        logger.info("Simulation schema initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing simulation schema: {e}")
        raise


async def create_main_guidance_hub(driver: AsyncDriver, database: str = "neo4j"):
    """Create the main guidance hub that lists all available incarnations."""
    logger.info("Creating main guidance hub...")

    main_hub_description = """
# NeoCoder Polymorphic Framework

Welcome to the NeoCoder Polymorphic Framework. This system can transform between multiple incarnations to support different use cases:

## Default Available Incarnation Templates
- **base_incarnation**: The original NeoCoder for AI-assisted coding
- **data_analysis_incarnation**: Data Analysis Incarnation
- **decision_incarnation**: Decision Support System
- **knowledge_graph_incarnation**: Knowledge Graph Incarnation
- **research_incarnation**: Research Orchestration Platform

## Getting Started

- Use `list_incarnations()` to see all available incarnations
- Use `switch_incarnation(incarnation_type="research")` to activate a specific incarnation
- Once activated, use `get_guidance_hub()` again to see incarnation-specific guidance

Each incarnation provides its own set of specialized tools while maintaining core Neo4j integration.
    """

    query = """
    MERGE (hub:AiGuidanceHub {id: 'main_hub'})
    ON CREATE SET hub.description = $description
    RETURN hub
    """

    try:
        async with driver.session(database=database) as session:
            await session.run(query, {"description": main_hub_description})
        logger.info("Main guidance hub created successfully")
    except Exception as e:
        logger.error(f"Error creating main guidance hub: {e}")
        raise


async def create_dynamic_links_between_hubs(driver: AsyncDriver, database: str = "neo4j", incarnations: List[str] = None):
    """Create relationships between the main hub and all incarnation-specific hubs."""
    logger.info("Creating dynamic links between hubs...")

    # Get all AiGuidanceHub nodes
    query = """
    MATCH (hub:AiGuidanceHub)
    WHERE hub.id <> 'main_hub' AND hub.id ENDS WITH '_hub'
    RETURN hub.id AS id
    """

    try:
        async with driver.session(database=database) as session:
            # Get all hub IDs using to_eager_result() instead
            result = await session.run(query)
            eager_result = await result.to_eager_result()

            # Create links for each hub
            main_hub_query = """
            MATCH (main:AiGuidanceHub {id: 'main_hub'})
            MATCH (inc:AiGuidanceHub {id: $hub_id})
            MERGE (main)-[:HAS_INCARNATION {type: $inc_type}]->(inc)
            """

            for record in eager_result.records:
                hub_id = record.get("id")
                if hub_id:
                    # Extract incarnation type from hub ID (e.g., research_hub -> research)
                    inc_type = hub_id.replace("_hub", "")

                    # Create link
                    await session.run(main_hub_query, {"hub_id": hub_id, "inc_type": inc_type})
                    logger.info(f"Created link for incarnation: {inc_type}")

        logger.info("Hub links created successfully")
    except Exception as e:
        logger.error(f"Error creating hub links: {e}")
        raise


async def create_links_between_hubs(driver: AsyncDriver, database: str = "neo4j"):
    """Create relationships between the main hub and incarnation-specific hubs (legacy version).
    This is kept for backward compatibility but we should prefer create_dynamic_links_between_hubs.
    """
    logger.info("Creating links between predefined hubs...")

    # Links to incarnation hubs
    query = """
    MATCH (main:AiGuidanceHub {id: 'main_hub'})

    OPTIONAL MATCH (research:AiGuidanceHub {id: 'research_hub'})
    OPTIONAL MATCH (decision:AiGuidanceHub {id: 'decision_hub'})
    OPTIONAL MATCH (learning:AiGuidanceHub {id: 'learning_hub'})
    OPTIONAL MATCH (simulation:AiGuidanceHub {id: 'simulation_hub'})

    FOREACH(x IN CASE WHEN research IS NOT NULL THEN [1] ELSE [] END |
        MERGE (main)-[:HAS_INCARNATION {type: 'research_orchestration'}]->(research))

    FOREACH(x IN CASE WHEN decision IS NOT NULL THEN [1] ELSE [] END |
        MERGE (main)-[:HAS_INCARNATION {type: 'decision_support'}]->(decision))

    FOREACH(x IN CASE WHEN learning IS NOT NULL THEN [1] ELSE [] END |
        MERGE (main)-[:HAS_INCARNATION {type: 'continuous_learning'}]->(learning))

    FOREACH(x IN CASE WHEN simulation IS NOT NULL THEN [1] ELSE [] END |
        MERGE (main)-[:HAS_INCARNATION {type: 'complex_system'}]->(simulation))

    RETURN main
    """

    try:
        async with driver.session(database=database) as session:
            await session.run(query)
        logger.info("Hub links created successfully")
    except Exception as e:
        logger.error(f"Error creating hub links: {e}")
        raise


async def init_db(incarnations: Optional[List[str]] = None):
    """Initialize the database with the schemas for the specified incarnations."""
    # Get Neo4j connection info from environment variables
    neo4j_uri = os.environ.get("NEO4J_URL", "bolt://localhost:7687")
    neo4j_user = os.environ.get("NEO4J_USERNAME", "neo4j")
    neo4j_password = os.environ.get("NEO4J_PASSWORD", "password")
    neo4j_database = os.environ.get("NEO4J_DATABASE", "neo4j")

    # Discover available incarnation types
    available_incarnations = discover_incarnation_types()
    logger.info(f"Discovered incarnation types: {available_incarnations}")

    # If no incarnations specified, initialize all discovered
    incarnations = incarnations or available_incarnations

    # Connect to Neo4j
    driver = await init_neo4j_connection(neo4j_uri, neo4j_user, neo4j_password)

    try:
        # Initialize base schema
        await init_base_schema(driver, neo4j_database)

        # Initialize incarnation-specific schemas
        if "research_orchestration" in incarnations:
            await init_research_schema(driver, neo4j_database)

        if "decision_support" in incarnations:
            await init_decision_schema(driver, neo4j_database)

        if "continuous_learning" in incarnations:
            await init_learning_schema(driver, neo4j_database)

        if "complex_system" in incarnations:
            await init_simulation_schema(driver, neo4j_database)

        # Create incarnation-specific schemas for other discovered incarnations
        # This is just a placeholder and should be implemented properly
        for inc_type in incarnations:
            if inc_type not in ["research_orchestration", "decision_support", "continuous_learning", "complex_system"]:
                logger.info(f"Creating basic schema for incarnation: {inc_type}")
                hub_id = f"{inc_type}_hub"
                hub_description = f"This is the {inc_type} incarnation of the NeoCoder framework."

                try:
                    # Create a basic hub for this incarnation
                    hub_query = f"""
                    MERGE (hub:AiGuidanceHub {{id: '{hub_id}'}})
                    ON CREATE SET hub.description = '{hub_description}'
                    RETURN hub
                    """

                    async with driver.session(database=neo4j_database) as session:
                        await session.run(hub_query)

                except Exception as e:
                    logger.error(f"Error creating hub for {inc_type}: {e}")

        # Create main guidance hub
        await create_main_guidance_hub(driver, neo4j_database)

        # Create links between hubs for all discovered incarnations
        await create_dynamic_links_between_hubs(driver, neo4j_database, incarnations)

        logger.info("Database initialization complete!")
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        sys.exit(1)
    finally:
        await driver.close()


def main():
    """Main entry point for the database initialization."""
    # Get incarnations to initialize from command line arguments
    incarnations_to_init = sys.argv[1:] if len(sys.argv) > 1 else None

    if incarnations_to_init:
        # Validate incarnation types
        for inc in incarnations_to_init:
            if inc not in INCARNATION_TYPES:
                logger.error(f"Invalid incarnation type: {inc}")
                logger.error(f"Valid types are: {', '.join(INCARNATION_TYPES)}")
                sys.exit(1)

    # Run the initialization
    asyncio.run(init_db(incarnations_to_init))


if __name__ == "__main__":
    main()
