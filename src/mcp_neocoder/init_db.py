#!/usr/bin/env python3
"""
Initialize Neo4j Database for AI Workflow System

This script sets up the Neo4j database with the core structure and templates
for the Neo4j-guided AI coding workflow system.
"""

import json
import logging
import os
import sys
import time
from pathlib import Path

from neo4j import GraphDatabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("init_workflow_db")

def wait_for_neo4j(uri, username, password, max_attempts=5):
    """Wait for Neo4j to become available."""
    logger.info(f"Attempting to connect to Neo4j at {uri} with username {username}")
    driver = GraphDatabase.driver(uri, auth=(username, password))
    attempts = 0
    success = False
    
    logger.info("Waiting for Neo4j to start...")
    
    while not success and attempts < max_attempts:
        try:
            with driver.session() as session:
                session.run("RETURN 1")
            success = True
            logger.info("Connected to Neo4j successfully")
            
            # Test write access
            try:
                with driver.session() as session:
                    session.run("""
                    CREATE (n:WriteAccessTest {id: "test"})
                    WITH n
                    DELETE n
                    RETURN "Write access confirmed" as status
                    """)
                logger.info("Write access to database confirmed")
            except Exception as e:
                logger.error(f"No write access to database: {e}")
                logger.error("Database initialization requires write access. Please check your Neo4j settings.")
                driver.close()
                sys.exit(1)
                
        except Exception as e:
            attempts += 1
            wait_time = (1 + attempts) * 2
            logger.warning(f"Failed to connect (attempt {attempts}/{max_attempts}). Waiting {wait_time} seconds...")
            logger.debug(f"Error: {e}")
            time.sleep(wait_time)
    
    if not success:
        driver.close()
        logger.error("Failed to connect to Neo4j after multiple attempts. Exiting.")
        logger.error("Please check your Neo4j connection settings:")
        logger.error(f"  URI: {uri}")
        logger.error(f"  Username: {username}")
        logger.error(f"  Password: {'Set (not shown)' if password else 'Not set'}")
        logger.error("Make sure Neo4j is running and accessible, and the credentials are correct.")
        sys.exit(1)
    
    return driver

def create_constraints_and_indexes(driver):
    """Create necessary constraints and indexes for the graph."""
    with driver.session() as session:
        # Constraints
        session.run("""
        CREATE CONSTRAINT unique_action_template_current IF NOT EXISTS
        FOR (t:ActionTemplate)
        REQUIRE (t.keyword, t.isCurrent) IS UNIQUE
        """)
        
        session.run("""
        CREATE CONSTRAINT unique_project_id IF NOT EXISTS
        FOR (p:Project)
        REQUIRE p.projectId IS UNIQUE
        """)
        
        session.run("""
        CREATE CONSTRAINT unique_workflow_execution_id IF NOT EXISTS
        FOR (w:WorkflowExecution)
        REQUIRE w.id IS UNIQUE
        """)
        
        # Indexes
        session.run("""
        CREATE INDEX action_template_keyword IF NOT EXISTS
        FOR (t:ActionTemplate)
        ON (t.keyword)
        """)
        
        session.run("""
        CREATE INDEX file_path IF NOT EXISTS
        FOR (f:File)
        ON (f.path)
        """)
        
        logger.info("Created constraints and indexes")

def create_guidance_hub(driver):
    """Create the AI Guidance Hub node."""
    with driver.session() as session:
        session.run("""
        MERGE (hub:AiGuidanceHub {id: 'main_hub'})
        ON CREATE SET hub.description = 
        "Welcome AI Assistant. This is your central hub for coding assistance using our Neo4j knowledge graph. Choose your path:
        1.  **Execute Task:** If you know the action keyword (e.g., FIX, REFACTOR), directly query for the ActionTemplate: `MATCH (t:ActionTemplate {keyword: $keyword, isCurrent: true}) RETURN t.steps`. Always follow the template steps precisely, especially testing before logging.
        2.  **List Workflows/Templates:** Query available actions: `MATCH (t:ActionTemplate {isCurrent: true}) RETURN t.keyword, t.description ORDER BY t.keyword`.
        3.  **View Core Practices:** Understand essential rules: `MATCH (hub:AiGuidanceHub)-[:LINKS_TO]->(bp:BestPracticesGuide) RETURN bp.content`. Review this before starting complex tasks.
        4.  **Learn Templating:** Create or modify templates: `MATCH (hub:AiGuidanceHub)-[:LINKS_TO]->(tg:TemplatingGuide) RETURN tg.content`.
        5.  **Understand System:** Learn graph structure & queries: `MATCH (hub:AiGuidanceHub)-[:LINKS_TO]->(sg:SystemUsageGuide) RETURN sg.content`."
        """)
        logger.info("Created AiGuidanceHub node")

def create_guide_nodes(driver):
    """Create the guide nodes and link them to the hub."""
    with driver.session() as session:
        # Create Best Practices Guide
        session.run("""
        MERGE (hub:AiGuidanceHub {id: 'main_hub'})
        MERGE (bp:BestPracticesGuide {id: 'core_practices'})
        ON CREATE SET bp.content = 
        "Core Coding & System Practices:
        - **Efficiency First:** Prefer editing existing code over complete rewrites where feasible. Avoid temporary patch files.
        - **Meaningful Naming:** Do not name functions, variables, or files 'temp', 'fixed', 'patch'. Use descriptive names reflecting purpose.
        - **README is Key:** ALWAYS review the project's README before starting work. Find it via the :Project node.
        - **Test Rigorously:** Before logging completion, ALL relevant tests must pass. If tests fail, revisit the code, do not log success.
        - **Update After Success:** ONLY AFTER successful testing, update the Neo4j project tree AND the project's README with changes made.
        - **Risk Assessment:** Always evaluate the potential impact of changes and document any areas that need monitoring.
        - **Metrics Collection:** Track completion time and success rates to improve future estimation accuracy."
        MERGE (hub)-[:LINKS_TO]->(bp)
        """)
        
        # Create Templating Guide
        session.run("""
        MERGE (hub:AiGuidanceHub {id: 'main_hub'})
        MERGE (tg:TemplatingGuide {id: 'template_guide'})
        ON CREATE SET tg.content = 
        "How to Create/Edit ActionTemplates:
        -   Nodes are `:ActionTemplate {keyword: STRING, version: STRING, isCurrent: BOOLEAN, description: STRING, steps: STRING}`.
        -   `keyword`: Short, unique verb (e.g., 'DEPLOY', 'TEST_COMPONENT'). Used for lookup.
        -   `version`: Semantic version (e.g., '1.0', '1.1').
        -   `isCurrent`: Only one template per keyword should be `true`. Use transactions to update.
        -   `description`: Brief explanation of the template's purpose.
        -   `complexity`: Estimation of task complexity (e.g., 'LOW', 'MEDIUM', 'HIGH').
        -   `estimatedEffort`: Estimated time in minutes to complete the task.
        -   `steps`: Detailed, multi-line string with numbered steps. Use Markdown for formatting. MUST include critical checkpoints like 'Test Verification' and 'Log Successful Execution'.
        
        When updating a template:
        1. Create new version with incremented version number
        2. Set isCurrent = true on new version
        3. Set isCurrent = false on old version
        4. Document changes in a :Feedback node"
        MERGE (hub)-[:LINKS_TO]->(tg)
        """)
        
        # Create System Usage Guide
        session.run("""
        MERGE (hub:AiGuidanceHub {id: 'main_hub'})
        MERGE (sg:SystemUsageGuide {id: 'system_guide'})
        ON CREATE SET sg.content = 
        "Neo4j System Overview:
        -   `:AiGuidanceHub`: Your starting point.
        -   `:Project`: Represents a codebase. Has `projectId`, `name`, `readmeContent`/`readmeUrl`.
        -   `:ActionTemplate`: Contains steps for a keyword task. Query by `{keyword: $kw, isCurrent: true}`.
        -   `:File`, `:Directory`: Represent code structure within a project. Linked via `CONTAINS`, have `path`, `project_id`.
        -   `:WorkflowExecution`: Logs a completed action. Links via `APPLIED_TO_PROJECT` to `:Project`, `MODIFIED` to `:File`/`:Directory`, `USED_TEMPLATE` to `:ActionTemplate`.
        -   `:Feedback`: Stores feedback on template effectiveness. Links to templates via `REGARDING`.
        -   `:BestPracticesGuide`, `:TemplatingGuide`, `:SystemUsageGuide`: Linked from `:AiGuidanceHub` for help.
        -   Always use parameters ($projectId, $keyword) in queries for safety and efficiency.
        
        Common Metrics to Track:
        -   Success rate per template
        -   Average execution time per template
        -   Number of test failures before success
        -   Frequency of template usage
        -   Most commonly modified files"
        MERGE (hub)-[:LINKS_TO]->(sg)
        """)
        
        logger.info("Created guide nodes and linked to hub")

def load_templates_from_directory(driver, templates_dir):
    """Load template files from directory and execute them."""
    template_path = Path(templates_dir)
    if not template_path.exists() or not template_path.is_dir():
        logger.error(f"Template directory not found: {templates_dir}")
        return False
        
    template_files = list(template_path.glob("*.cypher"))
    if not template_files:
        logger.warning(f"No template files found in {templates_dir}")
        return False
        
    logger.info(f"Found {len(template_files)} template files")
    
    with driver.session() as session:
        for template_file in template_files:
            try:
                with open(template_file, 'r') as f:
                    template_query = f.read()
                    session.run(template_query)
                logger.info(f"Executed template file: {template_file.name}")
            except Exception as e:
                logger.error(f"Error executing template file {template_file.name}: {e}")
                
    return True

def create_sample_project(driver):
    """Create a sample project in the database."""
    with driver.session() as session:
        session.run("""
        MERGE (p:Project {
          projectId: 'sample-project',
          name: 'Sample Project',
          readmeContent: '# Sample Project\n\nThis is a sample project for demonstrating the Neo4j-guided AI coding workflow system.\n\n## Features\n\n- Feature 1\n- Feature 2\n- Feature 3\n\n## Structure\n\n- `/src`: Source code\n- `/tests`: Test cases\n- `/docs`: Documentation\n',
          currentVersion: '1.0.0'
        })
        
        // Create basic directory structure
        MERGE (src:Directory {path: 'src', project_id: 'sample-project'})
        MERGE (tests:Directory {path: 'tests', project_id: 'sample-project'})
        MERGE (docs:Directory {path: 'docs', project_id: 'sample-project'})
        
        MERGE (p)-[:CONTAINS]->(src)
        MERGE (p)-[:CONTAINS]->(tests)
        MERGE (p)-[:CONTAINS]->(docs)
        
        // Add some files
        MERGE (main:File {path: 'src/main.py', project_id: 'sample-project'})
        MERGE (utils:File {path: 'src/utils.py', project_id: 'sample-project'})
        MERGE (test_main:File {path: 'tests/test_main.py', project_id: 'sample-project'})
        MERGE (readme:File {path: 'README.md', project_id: 'sample-project'})
        
        MERGE (src)-[:CONTAINS]->(main)
        MERGE (src)-[:CONTAINS]->(utils)
        MERGE (tests)-[:CONTAINS]->(test_main)
        MERGE (p)-[:CONTAINS]->(readme)
        """)
        
        logger.info("Created sample project")

def main():
    """Main function to initialize the database."""
    # Get Neo4j connection details from environment
    neo4j_uri = os.environ.get("NEO4J_URL", "bolt://localhost:7687")
    neo4j_user = os.environ.get("NEO4J_USERNAME", "neo4j")
    neo4j_pass = os.environ.get("NEO4J_PASSWORD", "00000000")
    
    # Debug output
    logger.info(f"Using Neo4j connection: {neo4j_uri}")
    logger.info(f"Using Neo4j username: {neo4j_user}")
    logger.info(f"Using Neo4j password: {'Set (not shown)' if neo4j_pass else 'Not set'}")
    
    # Get templates directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.abspath(os.path.join(script_dir, "..", "..", "templates"))
    
    # Wait for Neo4j to be available
    driver = wait_for_neo4j(neo4j_uri, neo4j_user, neo4j_pass)
    
    try:
        # Initialize the graph structure
        create_constraints_and_indexes(driver)
        create_guidance_hub(driver)
        create_guide_nodes(driver)
        
        # Load templates
        load_templates_from_directory(driver, templates_dir)
        
        # Create sample project
        create_sample_project(driver)
        
        logger.info("Database initialization complete")
    finally:
        driver.close()

if __name__ == "__main__":
    main()
