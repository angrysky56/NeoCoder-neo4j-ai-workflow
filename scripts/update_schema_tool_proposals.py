#!/usr/bin/env python3
"""
Schema Update for Tool Proposal System

This script initializes the Neo4j database with the necessary structure for the tool proposal system,
including creating the ToolProposal and ToolRequest nodes and relationships.
"""

import os
import logging
import time
from neo4j import GraphDatabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("update_schema")


def get_neo4j_connection():
    """Get Neo4j connection details from environment variables or defaults."""
    uri = os.environ.get("NEO4J_URL", "bolt://localhost:7687")
    username = os.environ.get("NEO4J_USERNAME", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "password")  # Replace with actual password in production
    database = os.environ.get("NEO4J_DATABASE", "neo4j")

    return uri, username, password, database


def wait_for_neo4j(driver, database, max_attempts=5):
    """Wait for Neo4j to become available."""
    attempts = 0
    success = False

    logger.info("Checking Neo4j connection...")

    while not success and attempts < max_attempts:
        try:
            with driver.session(database=database) as session:
                session.run("RETURN 1")
            success = True
            logger.info("Connected to Neo4j successfully")
        except Exception as e:
            attempts += 1
            wait_time = (1 + attempts) * 2
            logger.warning(f"Failed to connect (attempt {attempts}/{max_attempts}). Waiting {wait_time} seconds...")
            logger.debug(f"Error: {e}")
            time.sleep(wait_time)

    if not success:
        logger.error("Failed to connect to Neo4j after multiple attempts. Exiting.")
        return False

    return True


def update_schema(driver, database):
    """Update Neo4j schema for the tool proposal system."""
    with driver.session(database=database) as session:
        # Create constraints for ToolProposal and ToolRequest
        try:
            session.run("""
            CREATE CONSTRAINT tool_proposal_id IF NOT EXISTS
            FOR (p:ToolProposal)
            REQUIRE p.id IS UNIQUE
            """)
            logger.info("Created constraint for ToolProposal.id")
        except Exception as e:
            logger.error(f"Error creating ToolProposal constraint: {e}")

        try:
            session.run("""
            CREATE CONSTRAINT tool_request_id IF NOT EXISTS
            FOR (r:ToolRequest)
            REQUIRE r.id IS UNIQUE
            """)
            logger.info("Created constraint for ToolRequest.id")
        except Exception as e:
            logger.error(f"Error creating ToolRequest constraint: {e}")

        # Create indexes for efficient searching
        try:
            session.run("""
            CREATE INDEX tool_proposal_status IF NOT EXISTS
            FOR (p:ToolProposal)
            ON (p.status)
            """)
            logger.info("Created index for ToolProposal.status")
        except Exception as e:
            logger.error(f"Error creating ToolProposal.status index: {e}")

        try:
            session.run("""
            CREATE INDEX tool_request_status IF NOT EXISTS
            FOR (r:ToolRequest)
            ON (r.status)
            """)
            logger.info("Created index for ToolRequest.status")
        except Exception as e:
            logger.error(f"Error creating ToolRequest.status index: {e}")

        try:
            session.run("""
            CREATE INDEX tool_request_priority IF NOT EXISTS
            FOR (r:ToolRequest)
            ON (r.priority)
            """)
            logger.info("Created index for ToolRequest.priority")
        except Exception as e:
            logger.error(f"Error creating ToolRequest.priority index: {e}")

        # Update AiGuidanceHub to include Tool Proposal system
        try:
            session.run("""
            MATCH (hub:AiGuidanceHub {id: 'main_hub'})
            MERGE (tps:ToolProposalSystem {id: 'tool_proposals'})
            ON CREATE SET tps.description = 'The Tool Proposal System allows AI assistants to propose new tools and users to request new functionality.'
            MERGE (hub)-[:HAS_SYSTEM]->(tps)
            """)
            logger.info("Created ToolProposalSystem node and linked to AiGuidanceHub")
        except Exception as e:
            logger.error(f"Error creating ToolProposalSystem: {e}")

        # Create sample proposals and requests for testing
        try:
            session.run("""
            // Sample Tool Proposal
            MERGE (p:ToolProposal {id: 'sample-proposal-1'})
            ON CREATE SET
                p.name = 'Schema Visualization Tool',
                p.description = 'A tool to visualize the Neo4j database schema with nodes and relationships',
                p.parameters = '[{"name": "include_properties", "type": "boolean", "description": "Whether to include properties in the visualization", "required": false}, {"name": "format", "type": "string", "description": "Output format (SVG, PNG, or DOT)", "required": false}]',
                p.rationale = 'Visualizing the database schema would make it easier to understand the structure of the knowledge graph.',
                p.timestamp = datetime(),
                p.status = 'Proposed',
                p.exampleUsage = 'visualize_schema(include_properties=true, format="SVG")'

            // Sample Tool Request
            MERGE (r:ToolRequest {id: 'sample-request-1'})
            ON CREATE SET
                r.description = 'Add a tool to export project data',
                r.useCase = 'I need to be able to export project data for backup and sharing purposes.',
                r.priority = 'MEDIUM',
                r.timestamp = datetime(),
                r.status = 'Submitted',
                r.requestedBy = 'User'

            // Link to hub
            WITH p, r
            MATCH (hub:AiGuidanceHub {id: 'main_hub'})
            MERGE (hub)-[:HAS_PROPOSAL]->(p)
            MERGE (hub)-[:HAS_REQUEST]->(r)

            RETURN p.id, r.id
            """)
            logger.info("Created sample tool proposals and requests")
        except Exception as e:
            logger.error(f"Error creating sample data: {e}")

        logger.info("Schema update complete")


def main():
    """Main function to update the schema."""
    uri, username, password, database = get_neo4j_connection()

    logger.info(f"Connecting to Neo4j at {uri} as {username}...")
    driver = GraphDatabase.driver(uri, auth=(username, password))

    if not wait_for_neo4j(driver, database):
        driver.close()
        return

    try:
        update_schema(driver, database)
    finally:
        driver.close()


if __name__ == "__main__":
    main()
