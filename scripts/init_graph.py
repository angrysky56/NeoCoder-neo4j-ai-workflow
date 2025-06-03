#!/usr/bin/env python3
"""
Initialize Neo4j Graph Structure for AI-Guided Coding Workflow

This script creates the core components of the Neo4j graph structure:
- AiGuidanceHub node (central entry point)
- Guide nodes for documentation
- Constraints and indexes for data integrity and performance
"""

import os
import sys
from neo4j import GraphDatabase
import logging
import argparse
from pathlib import Path
import neo4j
from typing import cast, LiteralString
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Neo4jGraphInitializer:
    def __init__(self, uri, username, password):
        """Initialize the Neo4j connection"""
        try:
            self.driver = GraphDatabase.driver(uri, auth=(username, password))
            # Verify connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("Connected to Neo4j database")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            sys.exit(1)

    def close(self):
        """Close the Neo4j driver connection"""
        self.driver.close()
        logger.info("Disconnected from Neo4j database")

    def create_constraints_and_indexes(self):
        """Create constraints and indexes for optimal performance"""
        with self.driver.session() as session:
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

    def create_guidance_hub(self):
        """Create the central AI Guidance Hub node"""
        with self.driver.session() as session:
            session.run("""
            MERGE (hub:AiGuidanceHub {id: "main_hub"})
            ON CREATE SET hub.description =
            "Welcome AI Assistant. This is your central hub for coding assistance using our Neo4j knowledge graph. Choose your path:
            1.  **Execute Task:** If you know the action keyword (e.g., FIX, REFACTOR), directly query for the ActionTemplate: `MATCH (t:ActionTemplate {keyword: $keyword, isCurrent: true}) RETURN t.steps`. Always follow the template steps precisely, especially testing before logging.
            2.  **List Workflows/Templates:** Query available actions: `MATCH (t:ActionTemplate {isCurrent: true}) RETURN t.keyword, t.description ORDER BY t.keyword`.
            3.  **View Core Practices:** Understand essential rules: `MATCH (hub:AiGuidanceHub)-[:LINKS_TO]->(bp:BestPracticesGuide) RETURN bp.content`. Review this before starting complex tasks.
            4.  **Learn Templating:** Create or modify templates: `MATCH (hub:AiGuidanceHub)-[:LINKS_TO]->(tg:TemplatingGuide) RETURN tg.content`.
            5.  **Understand System:** Learn graph structure & queries: `MATCH (hub:AiGuidanceHub)-[:LINKS_TO]->(sg:SystemUsageGuide) RETURN sg.content`."
            """)
            logger.info("Created AiGuidanceHub node")

    def create_guide_nodes(self):
        """Create the guide nodes and link them to the hub"""
        with self.driver.session() as session:
            # Create Best Practices Guide
            session.run("""
            MERGE (hub:AiGuidanceHub {id: "main_hub"})
            MERGE (bp:BestPracticesGuide {id: "core_practices"})
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
            MERGE (hub:AiGuidanceHub {id: "main_hub"})
            MERGE (tg:TemplatingGuide {id: "template_guide"})
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
            MERGE (hub:AiGuidanceHub {id: "main_hub"})
            MERGE (sg:SystemUsageGuide {id: "system_guide"})
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

    def load_templates_from_directory(self, template_dir):
        """Load template files from directory and execute them"""
        template_path = Path(template_dir)
        if not template_path.exists() or not template_path.is_dir():
            logger.error(f"Template directory not found: {template_dir}")
            return False

        template_files = list(template_path.glob("*.cypher"))
        if not template_files:
            logger.warning(f"No template files found in {template_dir}")
            return False

        logger.info(f"Found {len(template_files)} template files")

        with self.driver.session() as session:
            for template_file in template_files:
                try:
                    with open(template_file) as f:
                        template_query = f.read()
                        session.run(neo4j.Query(cast(LiteralString, template_query)))
                        logger.info(f"Executed template file: {template_file.name}")
                except Exception as e:
                    logger.error(f"Error executing template file {template_file.name}: {e}")

        return True
def main():
    parser = argparse.ArgumentParser(description='Initialize Neo4j Graph for AI-Guided Coding')
    parser.add_argument('--uri', default='bolt://localhost:7687', help='Neo4j connection URI')
    parser.add_argument('--username', default='neo4j', help='Neo4j username')
    parser.add_argument('--password', required=True, help='Neo4j password')
    parser.add_argument('--template-dir', default='../templates', help='Directory containing template files')

    args = parser.parse_args()

    # Resolve template directory path relative to script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.abspath(os.path.join(script_dir, args.template_dir))

    # Initialize graph
    initializer = Neo4jGraphInitializer(args.uri, args.username, args.password)

    try:
        # Create structure
        initializer.create_constraints_and_indexes()
        initializer.create_guidance_hub()
        initializer.create_guide_nodes()

        # Load templates
        success = initializer.load_templates_from_directory(template_dir)
        if success:
            logger.info("Templates loaded successfully")
        else:
            logger.warning("Failed to load templates or no templates found")

        logger.info("Graph initialization complete")
    finally:
        initializer.close()

if __name__ == "__main__":
    main()
