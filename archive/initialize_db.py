#!/usr/bin/env python3
"""
Initialize the Neo4j database for NeoCoder with the required data structure and templates.
This script bypasses the MCP server to directly write to the Neo4j database.
"""

import os
import sys
import time
import logging
from pathlib import Path
from neo4j import GraphDatabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Get Neo4j connection details from environment or use defaults
    neo4j_uri = os.environ.get("NEO4J_URL", "bolt://localhost:7687")
    neo4j_user = os.environ.get("NEO4J_USERNAME", "neo4j")
    neo4j_pass = os.environ.get("NEO4J_PASSWORD", "password")
    neo4j_db = os.environ.get("NEO4J_DATABASE", "neo4j")

    # Debug output
    logger.info(f"Using Neo4j connection: {neo4j_uri}")
    logger.info(f"Using Neo4j username: {neo4j_user}")
    logger.info(f"Using Neo4j database: {neo4j_db}")

    # Connect to Neo4j
    driver = None
    try:
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_pass))
        # Verify connection
        with driver.session(database=neo4j_db) as session:
            session.run("RETURN 1 as result")
        logger.info("Connected to Neo4j successfully")

        # Create constraints and indexes
        with driver.session(database=neo4j_db) as session:
            session.run(
                """CREATE CONSTRAINT unique_action_template_current IF NOT EXISTS
                FOR (t:ActionTemplate)
                REQUIRE (t.keyword, t.isCurrent) IS UNIQUE"""
            )

            session.run(
                """CREATE CONSTRAINT unique_project_id IF NOT EXISTS
                FOR (p:Project)
                REQUIRE p.projectId IS UNIQUE"""
            )

            session.run(
                """CREATE CONSTRAINT unique_workflow_execution_id IF NOT EXISTS
                FOR (w:WorkflowExecution)
                REQUIRE w.id IS UNIQUE"""
            )

            # Indexes
            session.run(
                """CREATE INDEX action_template_keyword IF NOT EXISTS
                FOR (t:ActionTemplate)
                ON (t.keyword)"""
            )

            session.run(
                """CREATE INDEX file_path IF NOT EXISTS
                FOR (f:File)
                ON (f.path)"""
            )

            logger.info("Created constraints and indexes")

        # Create guide nodes
        with driver.session(database=neo4j_db) as session:
            # Create AiGuidanceHub node
            session.run(
                """MERGE (hub:AiGuidanceHub {id: 'main_hub'})
                ON CREATE SET hub.description =
                'Welcome AI Assistant. This is your central hub for coding assistance using our Neo4j knowledge graph. Choose your path:\n
                1.  **Execute Task:** If you know the action keyword (e.g., FIX, REFACTOR), directly query for the ActionTemplate: Use get_action_template tool with the keyword parameter.\n
                2.  **List Workflows/Templates:** Use list_action_templates tool to see available actions.\n
                3.  **View Core Practices:** Use get_best_practices tool to understand essential rules.\n
                4.  **Project Information:** Use get_project tool to retrieve project details and README content.\n
                5.  **Log Completion:** After successful testing, use log_workflow_execution to record successful completions.'"""
            )
            logger.info("Created AiGuidanceHub node")

            # Create Best Practices Guide
            session.run(
                """MERGE (hub:AiGuidanceHub {id: 'main_hub'})
                MERGE (bp:BestPracticesGuide {id: 'core_practices'})
                ON CREATE SET bp.content =
                'Core Coding & System Practices:\n
                - **Efficiency First:** Prefer editing existing code over complete rewrites where feasible. Avoid temporary patch files.\n
                - **Meaningful Naming:** Do not name functions, variables, or files "temp", "fixed", "patch". Use descriptive names reflecting purpose.\n
                - **README is Key:** ALWAYS review the project's README before starting work. Find it via the :Project node.\n
                - **Test Rigorously:** Before logging completion, ALL relevant tests must pass. If tests fail, revisit the code, do not log success.\n
                - **Update After Success:** ONLY AFTER successful testing, update the Neo4j project tree AND the project's README with changes made.\n
                - **Risk Assessment:** Always evaluate the potential impact of changes and document any areas that need monitoring.\n
                - **Metrics Collection:** Track completion time and success rates to improve future estimation accuracy.'
                MERGE (hub)-[:LINKS_TO]->(bp)"""
            )
            logger.info("Created BestPracticesGuide node")

            # Create Templating Guide
            session.run(
                """MERGE (hub:AiGuidanceHub {id: 'main_hub'})
                MERGE (tg:TemplatingGuide {id: 'template_guide'})
                ON CREATE SET tg.content =
                'How to Create/Edit ActionTemplates:\n
                -   Nodes are `:ActionTemplate {keyword: STRING, version: STRING, isCurrent: BOOLEAN, description: STRING, steps: STRING}`.\n
                -   `keyword`: Short, unique verb (e.g., "DEPLOY", "TEST_COMPONENT"). Used for lookup.\n
                -   `version`: Semantic version (e.g., "1.0", "1.1").\n
                -   `isCurrent`: Only one template per keyword should be `true`. Use transactions to update.\n
                -   `description`: Brief explanation of the template's purpose.\n
                -   `complexity`: Estimation of task complexity (e.g., "LOW", "MEDIUM", "HIGH").\n
                -   `estimatedEffort`: Estimated time in minutes to complete the task.\n
                -   `steps`: Detailed, multi-line string with numbered steps. Use Markdown for formatting. MUST include critical checkpoints like "Test Verification" and "Log Successful Execution".\n\n
                When updating a template:\n
                1. Create new version with incremented version number\n
                2. Set isCurrent = true on new version\n
                3. Set isCurrent = false on old version\n
                4. Document changes in a :Feedback node'
                MERGE (hub)-[:LINKS_TO]->(tg)"""
            )
            logger.info("Created TemplatingGuide node")

            # Create System Usage Guide
            session.run(
                """MERGE (hub:AiGuidanceHub {id: 'main_hub'})
                MERGE (sg:SystemUsageGuide {id: 'system_guide'})
                ON CREATE SET sg.content =
                'Neo4j System Overview:\n
                -   `:AiGuidanceHub`: Your starting point.\n
                -   `:Project`: Represents a codebase. Has `projectId`, `name`, `readmeContent`/`readmeUrl`.\n
                -   `:ActionTemplate`: Contains steps for a keyword task. Query by `{keyword: $kw, isCurrent: true}`.\n
                -   `:File`, `:Directory`: Represent code structure within a project. Linked via `CONTAINS`, have `path`, `project_id`.\n
                -   `:WorkflowExecution`: Logs a completed action. Links via `APPLIED_TO_PROJECT` to `:Project`, `MODIFIED` to `:File`/`:Directory`, `USED_TEMPLATE` to `:ActionTemplate`.\n
                -   `:Feedback`: Stores feedback on template effectiveness. Links to templates via `REGARDING`.\n
                -   `:BestPracticesGuide`, `:TemplatingGuide`, `:SystemUsageGuide`: Linked from `:AiGuidanceHub` for help.\n
                -   Always use parameters ($projectId, $keyword) in queries for safety and efficiency.\n\n
                Common Metrics to Track:\n
                -   Success rate per template\n
                -   Average execution time per template\n
                -   Number of test failures before success\n
                -   Frequency of template usage\n
                -   Most commonly modified files'
                MERGE (hub)-[:LINKS_TO]->(sg)"""
            )
            logger.info("Created SystemUsageGuide node")

        # Load template files from directory
        template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
        if os.path.exists(template_dir) and os.path.isdir(template_dir):
            logger.info(f"Loading templates from {template_dir}")
            template_files = [f for f in os.listdir(template_dir) if f.endswith('.cypher')]

            if template_files:
                logger.info(f"Found {len(template_files)} template files")
                for template_file in template_files:
                    template_path = os.path.join(template_dir, template_file)
                    try:
                        with open(template_path, 'r') as f:
                            template_query = f.read()

                        with driver.session(database=neo4j_db) as session:
                            session.run(template_query)

                        logger.info(f"Loaded template from {template_file}")
                    except Exception as e:
                        logger.error(f"Error loading template {template_file}: {e}")
            else:
                logger.warning(f"No template files found in {template_dir}")
        else:
            logger.warning(f"Template directory not found: {template_dir}")

        # Check for sample project
        with driver.session(database=neo4j_db) as session:
            check_project_query = """
                MATCH (p:Project {projectId: 'sample-project'})
                RETURN count(p) AS project_count
            """
            result = session.run(check_project_query)
            record = result.single()

            if record and record["project_count"] > 0:
                logger.info("Sample project already exists, skipping creation")
            else:
                session.run(
                    """MERGE (p:Project {
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
                    MERGE (p)-[:CONTAINS]->(readme)"""
                )
                logger.info("Created sample project")

            # Check for neocoder project
            check_neocoder_query = """
                MATCH (p:Project {projectId: 'neocoder'})
                RETURN count(p) AS project_count
            """
            result = session.run(check_neocoder_query)
            record = result.single()

            if record and record["project_count"] > 0:
                logger.info("NeoCoder project already exists, skipping creation")
            else:
                session.run(
                    """MERGE (p:Project {
                    projectId: 'neocoder',
                    name: 'NeoCoder',
                    readmeContent: '# NeoCoder: Neo4j-Guided AI Coding Workflow\n\nAn MCP server implementation that enables AI assistants like Claude to use a Neo4j knowledge graph as their primary, dynamic "instruction manual" and project memory for standardized coding workflows.\n\n## Overview\n\nNeoCoder implements a system where:\n\n1. AI assistants query a Neo4j database for standardized workflows (`ActionTemplates`) triggered by keywords (e.g., `FIX`, `REFACTOR`)\n2. The AI follows specific steps in these templates when performing coding tasks\n3. Critical steps like testing are enforced before logging success\n4. A complete audit trail of changes is maintained in the graph itself',
                    currentVersion: '1.0.0'
                    })
                    // Create basic directory structure
                    MERGE (src:Directory {path: 'src', project_id: 'neocoder'})
                    MERGE (templates:Directory {path: 'templates', project_id: 'neocoder'})
                    MERGE (docs:Directory {path: 'docs', project_id: 'neocoder'})
                    MERGE (p)-[:CONTAINS]->(src)
                    MERGE (p)-[:CONTAINS]->(templates)
                    MERGE (p)-[:CONTAINS]->(docs)
                    // Add some files
                    MERGE (server:File {path: 'src/server.py', project_id: 'neocoder'})
                    MERGE (initdb:File {path: 'src/init_db.py', project_id: 'neocoder'})
                    MERGE (fixTemplate:File {path: 'templates/fix_template.cypher', project_id: 'neocoder'})
                    MERGE (refactorTemplate:File {path: 'templates/refactor_template.cypher', project_id: 'neocoder'})
                    MERGE (deployTemplate:File {path: 'templates/deploy_template.cypher', project_id: 'neocoder'})
                    MERGE (readme:File {path: 'README.md', project_id: 'neocoder'})
                    MERGE (src)-[:CONTAINS]->(server)
                    MERGE (src)-[:CONTAINS]->(initdb)
                    MERGE (templates)-[:CONTAINS]->(fixTemplate)
                    MERGE (templates)-[:CONTAINS]->(refactorTemplate)
                    MERGE (templates)-[:CONTAINS]->(deployTemplate)
                    MERGE (p)-[:CONTAINS]->(readme)"""
                )
                logger.info("Created NeoCoder project")

        logger.if __name__ == "__main__": main()
