#!/usr/bin/env python3
"""
Template Addition Utility for NeoCoder

This script demonstrates how to properly add new templates to the Neo4j database,
handling Neo4j version-specific constraints and transaction management.
"""

import os
import logging
import time
from pathlib import Path
from neo4j import GraphDatabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("add_templates")

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

def add_template_from_cypher(driver, database, cypher_path):
    """
    Add a template from a Cypher file, breaking down complex operations into multiple transactions.
    
    This demonstrates how to properly handle Neo4j constraints for complex operations.
    """
    logger.info(f"Adding template from: {cypher_path}")
    
    # Read the Cypher file
    with open(cypher_path, 'r') as f:
        full_query = f.read()
    
    # Simple version: direct execution (might fail with complex operations)
    try:
        with driver.session(database=database) as session:
            result = session.run(full_query)
            logger.info(f"Template added successfully via direct execution: {result.single()[0]}")
            return True
    except Exception as e:
        logger.warning(f"Direct execution failed: {e}")
        logger.info("Trying operation breakdown approach...")
    
    # Advanced version: Break down into multiple operations
    # This pattern is useful for Neo4j versions with stricter transaction constraints
    try:
        # Extract template details (this is a simplified parser)
        import re
        
        # Extract keyword, version, and other metadata
        keyword_match = re.search(r"keyword: '([^']+)'", full_query)
        version_match = re.search(r"version: '([^']+)'", full_query)
        desc_match = re.search(r"description = '([^']+)'", full_query)
        
        if not keyword_match or not version_match:
            logger.error("Failed to parse template details from Cypher file")
            return False
        
        keyword = keyword_match.group(1)
        version = version_match.group(1)
        description = desc_match.group(1) if desc_match else "No description"
        
        # Split the operation into multiple transactions
        with driver.session(database=database) as session:
            # 1. First create or update the template node
            template_query = f"""
            MERGE (t:ActionTemplate {{keyword: '{keyword}', version: '{version}'}})
            ON CREATE SET 
                t.description = '{description}',
                t.isCurrent = true
            ON MATCH SET
                t.isCurrent = true
            RETURN t.keyword as keyword, t.version as version
            """
            template_result = session.run(template_query)
            template_record = template_result.single()
            
            # 2. Then find the content section and update it separately
            steps_match = re.search(r"t.steps = \"(.*?)\"", full_query, re.DOTALL)
            if steps_match:
                steps_content = steps_match.group(1)
                # Escape quotes for Cypher
                steps_content = steps_content.replace('"', '\\"')
                
                steps_query = f"""
                MATCH (t:ActionTemplate {{keyword: '{keyword}', version: '{version}'}})
                SET t.steps = "{steps_content}"
                RETURN t.keyword as keyword
                """
                session.run(steps_query)
            
            # 3. Finally create the relationship to the hub
            hub_query = f"""
            MATCH (t:ActionTemplate {{keyword: '{keyword}', version: '{version}'}})
            MATCH (hub:AiGuidanceHub {{id: 'main_hub'}})
            MERGE (hub)-[:PROVIDES_TEMPLATE]->(t)
            RETURN t.keyword as keyword
            """
            hub_result = session.run(hub_query)
            
            logger.info(f"Template {keyword} v{version} added successfully via multi-transaction approach")
            return True
            
    except Exception as e:
        logger.error(f"Advanced execution also failed: {e}")
        return False

def main():
    """Main function to add templates."""
    uri, username, password, database = get_neo4j_connection()
    
    logger.info(f"Connecting to Neo4j at {uri} as {username}...")
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    if not wait_for_neo4j(driver, database):
        driver.close()
        return
    
    try:
        # Get templates directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        templates_dir = os.path.abspath(os.path.join(script_dir, "..", "templates"))
        
        # List of template files to add
        template_files = [
            os.path.join(templates_dir, "feature_template.cypher"),
            os.path.join(templates_dir, "tool_add_template.cypher")
        ]
        
        # Add each template
        success_count = 0
        for template_file in template_files:
            if os.path.exists(template_file):
                if add_template_from_cypher(driver, database, template_file):
                    success_count += 1
            else:
                logger.warning(f"Template file not found: {template_file}")
        
        logger.info(f"Added {success_count} templates successfully")
        
    finally:
        driver.close()

if __name__ == "__main__":
    main()
