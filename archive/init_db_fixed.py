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

# Incarnation types
class IncarnationType(str, Enum):
    """Supported incarnation types for the NeoCoder framework."""
    CODING = "coding"                       # Original coding workflow
    RESEARCH = "research_orchestration"     # Research lab notebook
    DECISION = "decision_support"           # Decision-making system
    LEARNING = "continuous_learning"        # Learning environment
    SIMULATION = "complex_system"           # Complex system simulator

# List of incarnation type values for validation
INCARNATION_TYPES = [t.value for t in IncarnationType]


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

    # Separate constraints and indexes queries (single-statement each)
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
        "CREATE INDEX research_protocol_name IF NOT EXISTS FOR (p:Protocol) ON (p.name)"
    ]

    # Hub creation query - separate as it has parameters
    research_hub_query = """
    MERGE (hub:AiGuidanceHub {id: 'research_hub'})
    ON CREATE SET hub.description = $description
    RETURN hub
    """
    
    research_hub_description = 'Research Orchestration Platform - A system for managing scientific workflows, hypotheses, experiments, and observations.'

    try:
        async with driver.session(database=database) as session:
            # Run each constraint/index query
            for query in research_schema_queries:
                await session.run(query)
                
            # Create the research hub with parameters
            await session.run(research_hub_query, {"description": research_hub_description})
            
        logger.info("Research schema initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing research schema: {e}")
        raise


async def init_decision_schema(driver: AsyncDriver, database: str = "neo4j"):
    """Initialize the schema for the Decision Support System incarnation."""
    logger.info("Initializing decision support schema...")

    # Separate constraints and indexes queries
    decision_schema_queries = [
        # Constraints
        "CREATE CONSTRAINT decision_id IF NOT EXISTS FOR (d:Decision) REQUIRE d.id IS UNIQUE",
        "CREATE CONSTRAINT alternative_id IF NOT EXISTS FOR (a:Alternative) REQUIRE a.id IS UNIQUE",
        "CREATE CONSTRAINT metric_id IF NOT EXISTS FOR (m:Metric) REQUIRE m.id IS UNIQUE",
        "CREATE CONSTRAINT evidence_id IF NOT EXISTS FOR (e:Evidence) REQUIRE e.id IS UNIQUE",

        # Indexes
        "CREATE INDEX decision_status IF NOT EXISTS FOR (d:Decision) ON (d.status)",
        "CREATE INDEX alternative_name IF NOT EXISTS FOR (a:Alternative) ON (a.name)"
    ]

    # Hub creation query - separate with parameters
    decision_hub_query = """
    MERGE (hub:AiGuidanceHub {id: 'decision_hub'})
    ON CREATE SET hub.description = $description
    RETURN hub
    """
    
    decision_hub_description = 'Decision Support System - A system for tracking decisions, alternatives, metrics, and evidence to support transparent, data-driven decision-making.'

    try:
        async with driver.session(database=database) as session:
            # Run each constraint/index query
            for query in decision_schema_queries:
                await session.run(query)
                
            # Create the decision hub with parameters
            await session.run(decision_hub_query, {"description": decision_hub_description})
            
        logger.info("Decision schema initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing decision schema: {e}")
        raise


async def init_learning_schema(driver: AsyncDriver, database: str = "neo4j"):
    """Initialize the schema for the Continuous Learning Environment incarnation."""
    logger.info("Initializing learning schema...")

    # Separate constraints and indexes queries
    learning_schema_queries = [
        # Constraints
        "CREATE CONSTRAINT learning_user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
        "CREATE CONSTRAINT learning_concept_id IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE",
        "CREATE CONSTRAINT learning_problem_id IF NOT EXISTS FOR (p:Problem) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT learning_attempt_id IF NOT EXISTS FOR (a:Attempt) REQUIRE a.id IS UNIQUE",

        # Indexes
        "CREATE INDEX learning_user_name IF NOT EXISTS FOR (u:User) ON (u.name)",
        "CREATE INDEX learning_concept_name IF NOT EXISTS FOR (c:Concept) ON (c.name)",
        "CREATE INDEX learning_problem_difficulty IF NOT EXISTS FOR (p:Problem) ON (p.difficulty)"
    ]

    # Hub creation query - separate with parameters
    learning_hub_query = """
    MERGE (hub:AiGuidanceHub {id: 'learning_hub'})
    ON CREATE SET hub.description = $description
    RETURN hub
    """
    
    learning_hub_description = 'Continuous Learning Environment - A system for adaptive learning and personalized content delivery based on knowledge spaces and mastery tracking.'

    try:
        async with driver.session(database=database) as session:
            # Run each constraint/index query
            for query in learning_schema_queries:
                await session.run(query)
                
            # Create the learning hub with parameters
            await session.run(learning_hub_query, {"description": learning_hub_description})
            
        logger.info("Learning schema initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing learning schema: {e}")
        raise


async def init_simulation_schema(driver: AsyncDriver, database: str = "neo4j"):
    """Initialize the schema for the Complex System Simulation incarnation."""
    logger.info("Initializing simulation schema...")

    # Separate constraints and indexes queries
    simulation_schema_queries = [
        # Constraints
        "CREATE CONSTRAINT simulation_entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
        "CREATE CONSTRAINT simulation_model_id IF NOT EXISTS FOR (m:Model) REQUIRE m.id IS UNIQUE",
        "CREATE CONSTRAINT simulation_run_id IF NOT EXISTS FOR (r:SimulationRun) REQUIRE r.id IS UNIQUE",
        "CREATE CONSTRAINT simulation_state_id IF NOT EXISTS FOR (s:State) REQUIRE s.id IS UNIQUE",

        # Indexes
        "CREATE INDEX simulation_entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)",
        "CREATE INDEX simulation_model_name IF NOT EXISTS FOR (m:Model) ON (m.name)",
        "CREATE INDEX simulation_run_timestamp IF NOT EXISTS FOR (r:SimulationRun) ON (r.timestamp)"
    ]

    # Hub creation query - separate with parameters
    simulation_hub_query = """
    MERGE (hub:AiGuidanceHub {id: 'simulation_hub'})
    ON CREATE SET hub.description = $description
    RETURN hub
    """
    
    simulation_hub_description = 'Complex System Simulation - A system for modeling and simulating complex systems with multiple interacting components and emergent behavior.'

    try:
        async with driver.session(database=database) as session:
            # Run each constraint/index query
            for query in simulation_schema_queries:
                await session.run(query)
                
            # Create the simulation hub with parameters
            await session.run(simulation_hub_query, {"description": simulation_hub_description})
            
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

## Available Incarnations

1. **Coding Workflow** - The original NeoCoder for AI-assisted coding
2. **Research Orchestration** - Scientific workflow management & hypothesis tracking
3. **Decision Support** - Transparent, data-driven decision making
4. **Continuous Learning** - Adaptive learning environment
5. **Complex System Simulation** - Model and simulate complex systems

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


async def create_links_between_hubs(driver: AsyncDriver, database: str = "neo4j"):
    """Create relationships between the main hub and incarnation-specific hubs."""
    logger.info("Creating links between hubs...")

    # Split the multi-statement query into individual queries
    link_queries = [
        # First check if hubs exist
        """
        MATCH (main:AiGuidanceHub {id: 'main_hub'})
        RETURN count(main) > 0 AS main_exists
        """,
        """
        MATCH (research:AiGuidanceHub {id: 'research_hub'})
        RETURN count(research) > 0 AS research_exists
        """,
        """
        MATCH (decision:AiGuidanceHub {id: 'decision_hub'})
        RETURN count(decision) > 0 AS decision_exists
        """,
        """
        MATCH (learning:AiGuidanceHub {id: 'learning_hub'})
        RETURN count(learning) > 0 AS learning_exists
        """,
        """
        MATCH (simulation:AiGuidanceHub {id: 'simulation_hub'})
        RETURN count(simulation) > 0 AS simulation_exists
        """
    ]
    
    # Individual link creation queries
    research_link_query = """
    MATCH (main:AiGuidanceHub {id: 'main_hub'})
    MATCH (research:AiGuidanceHub {id: 'research_hub'})
    MERGE (main)-[:HAS_INCARNATION {type: 'research'}]->(research)
    RETURN main.id, research.id
    """
    
    decision_link_query = """
    MATCH (main:AiGuidanceHub {id: 'main_hub'})
    MATCH (decision:AiGuidanceHub {id: 'decision_hub'})
    MERGE (main)-[:HAS_INCARNATION {type: 'decision'}]->(decision)
    RETURN main.id, decision.id
    """
    
    learning_link_query = """
    MATCH (main:AiGuidanceHub {id: 'main_hub'})
    MATCH (learning:AiGuidanceHub {id: 'learning_hub'})
    MERGE (main)-[:HAS_INCARNATION {type: 'learning'}]->(learning)
    RETURN main.id, learning.id
    """
    
    simulation_link_query = """
    MATCH (main:AiGuidanceHub {id: 'main_hub'})
    MATCH (simulation:AiGuidanceHub {id: 'simulation_hub'})
    MERGE (main)-[:HAS_INCARNATION {type: 'simulation'}]->(simulation)
    RETURN main.id, simulation.id
    """

    try:
        async with driver.session(database=database) as session:
            # First check which hubs exist
            exists_results = {}
            for query in link_queries:
                result = await session.run(query)
                records = await result.records()
                if records and len(records) > 0:
                    for key, value in records[0].items():
                        exists_results[key] = value
            
            # Only create links for hubs that exist
            if exists_results.get('main_exists', False):
                # Research link
                if exists_results.get('research_exists', False):
                    try:
                        await session.run(research_link_query)
                        logger.info("Created link to research hub")
                    except Exception as e:
                        logger.error(f"Error creating research link: {e}")
                
                # Decision link
                if exists_results.get('decision_exists', False):
                    try:
                        await session.run(decision_link_query)
                        logger.info("Created link to decision hub")
                    except Exception as e:
                        logger.error(f"Error creating decision link: {e}")
                
                # Learning link
                if exists_results.get('learning_exists', False):
                    try:
                        await session.run(learning_link_query)
                        logger.info("Created link to learning hub")
                    except Exception as e:
                        logger.error(f"Error creating learning link: {e}")
                
                # Simulation link
                if exists_results.get('simulation_exists', False):
                    try:
                        await session.run(simulation_link_query)
                        logger.info("Created link to simulation hub")
                    except Exception as e:
                        logger.error(f"Error creating simulation link: {e}")
            
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

    # If no incarnations specified, initialize all
    incarnations = incarnations or INCARNATION_TYPES

    # Connect to Neo4j
    driver = await init_neo4j_connection(neo4j_uri, neo4j_user, neo4j_password)

    try:
        # Initialize base schema
        await init_base_schema(driver, neo4j_database)

        # Create main guidance hub (needed for links)
        await create_main_guidance_hub(driver, neo4j_database)

        # Initialize incarnation-specific schemas
        incarnation_tasks = []
        
        if "research_orchestration" in incarnations:
            incarnation_tasks.append(init_research_schema(driver, neo4j_database))

        if "decision_support" in incarnations:
            incarnation_tasks.append(init_decision_schema(driver, neo4j_database))

        if "continuous_learning" in incarnations:
            incarnation_tasks.append(init_learning_schema(driver, neo4j_database))

        if "complex_system" in incarnations:
            incarnation_tasks.append(init_simulation_schema(driver, neo4j_database))

        # Execute all incarnation initialization tasks concurrently
        if incarnation_tasks:
            await asyncio.gather(*incarnation_tasks)

        # Create links between hubs
        await create_links_between_hubs(driver, neo4j_database)

        logger.info("Database initialization complete!")
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        raise
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
