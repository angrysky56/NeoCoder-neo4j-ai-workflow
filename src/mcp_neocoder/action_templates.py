"""
Action Templates Mixin for NeoCoder Neo4j-Guided AI Workflow

This module provides functionality to manage and access action templates for guiding AI coding workflows.
"""

import json
import logging
from typing import List, Optional, Dict, Any

import mcp.types as types
from pydantic import Field
from neo4j import AsyncManagedTransaction
from .event_loop_manager import safe_neo4j_session

logger = logging.getLogger("mcp_neocoder.action_templates")


class ActionTemplateMixin:
    """Mixin class providing action template functionality for the Neo4jWorkflowServer."""

    # Schema queries for Neo4j setup
    # Patch: Drop any conflicting index on ActionTemplate.keyword before creating uniqueness constraint
    schema_queries = [
        # Drop index if it exists (Neo4j 5+ syntax)
        "CALL db.indexes() YIELD name, entityType, labelsOrTypes, properties WHERE entityType = 'NODE' AND 'ActionTemplate' IN labelsOrTypes AND 'keyword' IN properties AND name CONTAINS 'index' WITH name CALL { WITH name CALL db.index.drop(name) YIELD name AS dropped RETURN dropped } RETURN *",
        # Action template uniqueness constraint
        "CREATE CONSTRAINT IF NOT EXISTS FOR (t:ActionTemplate) REQUIRE t.keyword IS UNIQUE",
        # Indexes for efficient querying
        "CREATE INDEX IF NOT EXISTS FOR (t:ActionTemplate) ON (t.isCurrent)",
    ]

    # These should be set by the parent class or during initialization
    driver: Any = None
    database: str = "neo4j"

    async def _read_query(self, tx: AsyncManagedTransaction, query: str, params: dict) -> str:
        """Execute a read query and return results as JSON string."""
        raise NotImplementedError("_read_query must be implemented by the parent class")

    async def _write(self, tx: AsyncManagedTransaction, query: str, params: dict):
        """Execute a write query and return results as JSON string."""
        raise NotImplementedError("_write must be implemented by the parent class")

    async def list_action_templates(
        self,
        current_only: bool = Field(True, description="Only return current templates"),
        keyword: Optional[str] = Field(None, description="Filter by specific keyword")
    ) -> List[types.TextContent]:
        """List all available action templates."""
        query = """
        MATCH (t:ActionTemplate)
        WHERE 1=1
        """

        params = {}

        if current_only:
            query += " AND t.isCurrent = true"

        if keyword:
            query += " AND t.keyword = $keyword"
            params["keyword"] = keyword

        query += """
        RETURN t.id AS id,
               t.keyword AS keyword,
               t.name AS name,
               t.description AS description,
               t.isCurrent AS isCurrent,
               t.version AS version
        ORDER BY t.keyword, t.version DESC
        """

        try:
            async with safe_neo4j_session(self.driver, self.database) as session:
                results_json = await session.execute_read(self._read_query, query, params)
                results = json.loads(results_json)

                if results and len(results) > 0:
                    text = "# Action Templates\n\n"

                    if keyword:
                        text += f"Filtered by keyword: `{keyword}`\n\n"

                    if current_only:
                        text += "Showing current versions only\n\n"

                    text += "| Keyword | Name | Description | Version |\n"
                    text += "| ------- | ---- | ----------- | ------- |\n"

                    for template in results:
                        version = template.get('version', '1.0')
                        current = " (current)" if template.get('isCurrent', False) else ""
                        text += f"| {template.get('keyword', 'N/A')} | {template.get('name', 'N/A')} | {template.get('description', 'N/A')} | {version}{current} |\n"

                    text += "\nTo view detailed steps for a template, use `get_action_template(keyword=\"KEYWORD\")`"

                    return [types.TextContent(type="text", text=text)]
                else:
                    filter_text = ""
                    if keyword:
                        filter_text = f" with keyword '{keyword}'"

                    if current_only:
                        if filter_text:
                            filter_text += " and"
                        filter_text += " that are current"

                    return [types.TextContent(type="text",
                                              text=f"No action templates found{filter_text}. Use `get_guidance_hub()` for general guidance.")]
        except Exception as e:
            logger.error(f"Error listing action templates: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def get_action_template(
        self,
        keyword: str = Field(..., description="Keyword for the template (e.g., FIX, REFACTOR)"),
        version: Optional[str] = Field(None, description="Specific version to retrieve (if not specified, gets current version)")
    ) -> List[types.TextContent]:
        """Retrieve detailed steps for a specific action template by keyword."""
        query = """
        MATCH (t:ActionTemplate {keyword: $keyword})
        """

        params = {"keyword": keyword}

        if version:
            query += " WHERE t.version = $version"
            params["version"] = version
        else:
            query += " WHERE t.isCurrent = true"

        query += """
        RETURN t.id AS id,
               t.keyword AS keyword,
               t.name AS name,
               t.description AS description,
               t.steps AS steps,
               t.verificationSteps AS verificationSteps,
               t.recordQuery AS recordQuery,
               t.version AS version
        LIMIT 1
        """

        try:
            async with safe_neo4j_session(self.driver, self.database) as session:
                results_json = await session.execute_read(self._read_query, query, params)
                results = json.loads(results_json)

                if results and len(results) > 0:
                    template = results[0]

                    text = f"# {template.get('name', 'Action Template')}\n\n"
                    text += f"**Keyword:** `{template.get('keyword', keyword)}`\n"
                    text += f"**Version:** {template.get('version', '1.0')}\n\n"

                    if template.get('description'):
                        text += f"## Description\n\n{template.get('description')}\n\n"

                    if template.get('steps'):
                        steps = template.get('steps')
                        if isinstance(steps, list):
                            text += "## Steps\n\n"
                            for i, step in enumerate(steps, 1):
                                text += f"{i}. {step}\n"
                            text += "\n"
                        else:
                            text += f"## Steps\n\n{steps}\n\n"

                    if template.get('verificationSteps'):
                        verification = template.get('verificationSteps')
                        if isinstance(verification, list):
                            text += "## Verification\n\n"
                            for i, step in enumerate(verification, 1):
                                text += f"{i}. {step}\n"
                            text += "\n"
                        else:
                            text += f"## Verification\n\n{verification}\n\n"

                    if template.get('recordQuery'):
                        text += "## Recording Completion\n\n"
                        text += "When the task is successfully completed and all verification steps pass, use this query to record the workflow execution:\n\n"
                        text += f"```cypher\n{template.get('recordQuery')}\n```\n"

                    return [types.TextContent(type="text", text=text)]
                else:
                    version_text = f" version {version}" if version else ""
                    return [types.TextContent(type="text",
                                             text=f"No action template found with keyword '{keyword}'{version_text}. Use `list_action_templates()` to see available templates.")]
        except Exception as e:
            logger.error(f"Error retrieving action template: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def get_best_practices(
        self,
        category: Optional[str] = Field(None, description="Specific best practice category")
    ) -> List[types.TextContent]:
        """Get the best practices guide for coding workflows."""
        query = """
        MATCH (bp:BestPractices)
        WHERE 1=1
        """

        params = {}

        if category:
            query += " AND bp.category = $category"
            params["category"] = category

        query += """
        RETURN bp.id AS id,
               bp.title AS title,
               bp.category AS category,
               bp.content AS content
        ORDER BY bp.category, bp.title
        """

        try:
            async with safe_neo4j_session(self.driver, self.database) as session:
                results_json = await session.execute_read(self._read_query, query, params)
                results = json.loads(results_json)

                if results and len(results) > 0:
                    text = "# Best Practices Guide\n\n"

                    if category:
                        text += f"Category: {category}\n\n"

                    # Group by category
                    categories = {}
                    for practice in results:
                        cat = practice.get('category', 'General')
                        if cat not in categories:
                            categories[cat] = []
                        categories[cat].append(practice)

                    # Output practices by category
                    for cat, practices in categories.items():
                        text += f"## {cat}\n\n"

                        for practice in practices:
                            text += f"### {practice.get('title', 'Best Practice')}\n\n"
                            text += f"{practice.get('content', 'No content available.')}\n\n"

                    return [types.TextContent(type="text", text=text)]
                else:
                    filter_text = f" for category '{category}'" if category else ""
                    return [types.TextContent(type="text",
                                             text=f"No best practices found{filter_text}. Contact the system administrator to add best practices guides.")]
        except Exception as e:
            logger.error(f"Error retrieving best practices: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def add_template_feedback(
        self,
        keyword: str = Field(..., description="Keyword of the template (e.g., FIX, REFACTOR)"),
        feedback: str = Field(..., description="The feedback to provide about the template"),
        rating: Optional[int] = Field(None, description="Optional rating (1-5)"),
        suggestions: Optional[str] = Field(None, description="Specific suggestions for improvements")
    ) -> List[types.TextContent]:
        """Provide feedback about an action template to improve it."""
        query = """
        MATCH (t:ActionTemplate {keyword: $keyword, isCurrent: true})
        CREATE (f:TemplateFeedback {
            id: randomUUID(),
            timestamp: datetime(),
            feedback: $feedback
        })
        CREATE (f)-[:ABOUT]->(t)
        """

        params = {
            "keyword": keyword,
            "feedback": feedback
        }

        if rating is not None:
            query = query.replace("feedback: $feedback", "feedback: $feedback, rating: $rating")
            params["rating"] = str(rating)

        if suggestions:
            query = query.replace("feedback: $feedback", "feedback: $feedback, suggestions: $suggestions")
            params["suggestions"] = suggestions

        try:
            async with safe_neo4j_session(self.driver, self.database) as session:
                # First check if the template exists
                check_query = """
                MATCH (t:ActionTemplate {keyword: $keyword, isCurrent: true})
                RETURN count(t) AS template_count
                """

                check_result = await session.execute_read(self._read_query, check_query, {"keyword": keyword})
                check_data = json.loads(check_result)

                if not check_data or check_data[0].get("template_count", 0) == 0:
                    return [types.TextContent(type="text",
                                             text=f"No current template found with keyword '{keyword}'. Use `list_action_templates()` to see available templates.")]

                # Submit the feedback
                await session.execute_write(self._write, query, params)

                return [types.TextContent(
                    type="text",
                    text=f"Thank you for your feedback on the {keyword} template. Your input helps improve the system."
                )]
        except Exception as e:
            logger.error(f"Error adding template feedback: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def get_project(
        self,
        project_id: str = Field(..., description="ID of the project to retrieve")
    ) -> List[types.TextContent]:
        """Get details about a specific project."""
        # Define default project information
        default_projects = {
            "neocoder": {
                "id": "neocoder",
                "name": "NeoCoder Neo4j AI Workflow",
                "description": "Neo4j-guided AI coding workflow system with multiple incarnations",
                "repository": "/home/ty/Repositories/NeoCoder-neo4j-ai-workflow",
                "language": "Python",
                "created_at": "2025-04-01",
                "updated_at": "2025-04-27",
                "workflow_count": 5,
                "readme": """
# NeoCoder: Neo4j-Guided AI Coding Workflow

An MCP server implementation that enables AI assistants like Claude to use a Neo4j knowledge graph as their primary, dynamic "instruction manual" and project memory for standardized coding workflows.

## Overview

NeoCoder implements a system where:

1. AI assistants query a Neo4j database for standardized workflows (`ActionTemplates`) triggered by keywords (e.g., `FIX`, `REFACTOR`)
2. The AI follows specific steps in these templates when performing coding tasks
3. Critical steps like testing are enforced before logging success
4. A complete audit trail of changes is maintained in the graph itself

## Multiple Incarnations

NeoCoder supports multiple "incarnations" - different operational modes that adapt the system for specialized use cases while preserving the core Neo4j graph structure. In a graph-native stack, the same Neo4j core can manifest as very different "brains" simply by swapping templates and execution policies.

Currently supported incarnations:
- **coding** (default) - Original code workflow management
- **research_orchestration** - Scientific research platform for hypothesis tracking and experiments
- **decision_support** - Decision analysis and evidence tracking system
- **knowledge_graph** - Knowledge graph management system
- **data_analysis** - Data analysis and visualization tools

## Recent Updates

### 2025-04-27: Eliminated Knowledge Graph Transaction Error Messages (v1.3.2)
- Completely eliminated error messages related to transaction scope issues
- Fixed server startup issues with improved error handling
- Enhanced transaction processing for Neo4j operations
                """
            }
        }

        query = """
        MATCH (p:Project {id: $project_id})
        OPTIONAL MATCH (p)-[:HAS_README]->(r:ReadmeContent)
        OPTIONAL MATCH (p)<-[:FOR_PROJECT]-(w:WorkflowExecution)
        WITH p, r, count(w) as workflow_count
        RETURN p.id AS id,
               p.name AS name,
               p.description AS description,
               p.repository AS repository,
               p.language AS language,
               p.created_at AS created_at,
               p.updated_at AS updated_at,
               r.content AS readme,
               workflow_count
        """

        params = {"project_id": project_id}

        try:
            async with safe_neo4j_session(self.driver, self.database) as session:
                try:
                    results_json = await session.execute_read(self._read_query, query, params)
                    results = json.loads(results_json)
                except Exception as query_error:
                    logger.warning(f"Error querying project, checking defaults: {query_error}")
                    results = []

                # If project not found in database but exists in default projects
                if (not results or len(results) == 0) and project_id in default_projects:
                    results = [default_projects[project_id]]

                if results and len(results) > 0:
                    project = results[0]

                    text = f"# {project.get('name', 'Project')}\n\n"

                    if project.get('description'):
                        text += f"{project.get('description')}\n\n"

                    text += f"**Project ID:** {project.get('id', project_id)}\n"

                    if project.get('language'):
                        text += f"**Language:** {project.get('language')}\n"

                    if project.get('repository'):
                        text += f"**Repository:** {project.get('repository')}\n"

                    text += f"**Created:** {project.get('created_at', 'Unknown')}\n"
                    text += f"**Last Updated:** {project.get('updated_at', 'Unknown')}\n"
                    text += f"**Workflow Executions:** {project.get('workflow_count', 0)}\n\n"

                    if project.get('readme'):
                        text += "## README\n\n"
                        text += f"{project.get('readme')}\n"

                    text += "\nYou can view the project's workflow history with `get_workflow_history(project_id=\"" + project_id + "\")`"

                    return [types.TextContent(type="text", text=text)]
                else:
                    return [types.TextContent(type="text",
                                            text=f"No project found with ID '{project_id}'. Use `list_projects()` to see available projects.")]
        except Exception as e:
            logger.error(f"Error retrieving project: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def list_projects(
        self,
        language: Optional[str] = Field(None, description="Filter by programming language"),
        limit: int = Field(10, description="Maximum number of projects to return")
    ) -> List[types.TextContent]:
        """List all available projects."""
        # Initialize projects list with a default project if none are found in the database
        default_projects = [
            {
                "id": "neocoder",
                "name": "NeoCoder Neo4j AI Workflow",
                "description": "Neo4j-guided AI coding workflow system with multiple incarnations",
                "language": "Python",
                "updated_at": "2025-04-27",
                "workflow_count": 5
            }
        ]

        query = """
        MATCH (p:Project)
        WHERE 1=1
        """

        params: Dict[str, Any] = {"limit": limit}

        if language:
            query += " AND p.language = $language"
            params["language"] = language

        query += """
        OPTIONAL MATCH (p)<-[:FOR_PROJECT]-(w:WorkflowExecution)
        WITH p, count(w) as workflow_count
        RETURN p.id AS id,
               p.name AS name,
               p.description AS description,
               p.language AS language,
               p.updated_at AS updated_at,
               workflow_count
        ORDER BY p.updated_at DESC
        LIMIT $limit
        """

        try:
            async with safe_neo4j_session(self.driver, self.database) as session:
                try:
                    results_json = await session.execute_read(self._read_query, query, params)
                    results = json.loads(results_json)
                except Exception as query_error:
                    logger.warning(f"Error querying projects, using default: {query_error}")
                    results = []

                # If no projects found in the database, use the default project
                if not results or len(results) == 0:
                    results = default_projects
                    # If language filter doesn't match default project, return empty
                    if language and language.lower() != "python":
                        results = []

                if results and len(results) > 0:
                    text = "# Projects\n\n"

                    if language:
                        text += f"Filtered by language: {language}\n\n"

                    text += "| Name | Description | Language | Last Updated | Workflows |\n"
                    text += "| ---- | ----------- | -------- | ------------ | --------- |\n"

                    for project in results:
                        description = project.get('description', '')
                        if len(description) > 30:
                            description = description[:30] + "..."

                        text += f"| [{project.get('name', 'Unnamed')}](get_project?project_id={project.get('id')}) | {description} | {project.get('language', 'Unknown')} | {project.get('updated_at', 'Unknown')} | {project.get('workflow_count', 0)} |\n"

                    text += "\nTo view details of a project, use `get_project(project_id=\"PROJECT_ID\")`"

                    return [types.TextContent(type="text", text=text)]
                else:
                    filter_text = f" for language '{language}'" if language else ""
                    return [types.TextContent(type="text",
                                             text=f"No projects found{filter_text}.")]
        except Exception as e:
            logger.error(f"Error listing projects: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def log_workflow_execution(
        self,
        project_id: str = Field(..., description="ID of the project"),
        action_keyword: str = Field(..., description="Keyword of the action template used (e.g., FIX, REFACTOR)"),
        summary: str = Field(..., description="Summary of what was done"),
        files_changed: List[str] = Field(..., description="List of files that were modified"),
        tests_passed: bool = Field(True, description="Whether all required tests passed"),
        notes: Optional[str] = Field(None, description="Additional notes about the workflow execution")
    ) -> List[types.TextContent]:
        """Record a successful workflow execution (ONLY after passing tests)."""
        if not tests_passed:
            return [types.TextContent(
                type="text",
                text="Cannot log workflow execution because tests did not pass. Please fix the issues and ensure all tests pass before recording."
            )]

        query = """
        MATCH (p:Project {id: $project_id})
        MATCH (t:ActionTemplate {keyword: $action_keyword, isCurrent: true})
        CREATE (w:WorkflowExecution {
            id: randomUUID(),
            timestamp: datetime(),
            summary: $summary,
            files_changed: $files_changed,
            tests_passed: $tests_passed
        })
        CREATE (w)-[:FOLLOWED]->(t)
        CREATE (w)-[:FOR_PROJECT]->(p)
        SET p.updated_at = datetime()
        """

        params = {
            "project_id": project_id,
            "action_keyword": action_keyword,
            "summary": summary,
            "files_changed": files_changed,
            "tests_passed": tests_passed
        }

        if notes:
            query = query.replace("tests_passed: $tests_passed", "tests_passed: $tests_passed, notes: $notes")
            params["notes"] = notes

        try:
            async with safe_neo4j_session(self.driver, self.database) as session:
                # Check if project exists
                check_project_query = """
                MATCH (p:Project {id: $project_id})
                RETURN count(p) AS project_count
                """

                project_result = await session.execute_read(self._read_query, check_project_query, {"project_id": project_id})
                project_data = json.loads(project_result)

                if not project_data or project_data[0].get("project_count", 0) == 0:
                    return [types.TextContent(type="text",
                                             text=f"No project found with ID '{project_id}'. Use `list_projects()` to see available projects.")]

                # Check if template exists
                check_template_query = """
                MATCH (t:ActionTemplate {keyword: $action_keyword, isCurrent: true})
                RETURN count(t) AS template_count
                """

                template_result = await session.execute_read(self._read_query, check_template_query, {"action_keyword": action_keyword})
                template_data = json.loads(template_result)

                if not template_data or template_data[0].get("template_count", 0) == 0:
                    return [types.TextContent(type="text",
                                             text=f"No current template found with keyword '{action_keyword}'. Use `list_action_templates()` to see available templates.")]

                # Record the workflow execution
                await session.execute_write(self._write, query, params)

                return [types.TextContent(
                    type="text",
                    text=f"Workflow execution successfully logged for project '{project_id}' using the '{action_keyword}' template.\n\n"
                         f"**Summary:** {summary}\n\n"
                         f"**Files Changed:** {', '.join(files_changed)}\n\n"
                         "The project's updated_at timestamp has been refreshed."
                )]
        except Exception as e:
            logger.error(f"Error logging workflow execution: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def get_workflow_history(
        self,
        project_id: Optional[str] = Field(None, description="Filter by project ID"),
        action_keyword: Optional[str] = Field(None, description="Filter by action template keyword"),
        limit: int = Field(10, description="Maximum number of workflow executions to return")
    ) -> List[types.TextContent]:
        """View history of workflow executions, optionally filtered."""
        query = """
        MATCH (w:WorkflowExecution)
        WHERE 1=1
        """

        params: Dict[str, Any] = {"limit": int(limit)}

        if project_id:
            query += " AND (w)-[:FOR_PROJECT]->(:Project {id: $project_id})"
            params["project_id"] = project_id

        if action_keyword:
            query += " AND (w)-[:FOLLOWED]->(:ActionTemplate {keyword: $action_keyword})"
            params["action_keyword"] = action_keyword

        query += """
        OPTIONAL MATCH (w)-[:FOR_PROJECT]->(p:Project)
        OPTIONAL MATCH (w)-[:FOLLOWED]->(t:ActionTemplate)
        RETURN w.id AS id,
               w.timestamp AS timestamp,
               w.summary AS summary,
               w.files_changed AS files_changed,
               w.tests_passed AS tests_passed,
               w.notes AS notes,
               p.id AS project_id,
               p.name AS project_name,
               t.keyword AS template_keyword
        ORDER BY w.timestamp DESC
        LIMIT $limit
        """

        try:
            async with safe_neo4j_session(self.driver, self.database) as session:
                results_json = await session.execute_read(self._read_query, query, params)
                results = json.loads(results_json)

                if results and len(results) > 0:
                    text = "# Workflow Execution History\n\n"

                    filters = []
                    if project_id:
                        project_name = results[0].get('project_name', 'Unknown')
                        filters.append(f"Project: {project_name} ({project_id})")
                    if action_keyword:
                        filters.append(f"Action: {action_keyword}")

                    if filters:
                        text += f"Filtered by: {', '.join(filters)}\n\n"

                    for i, w in enumerate(results, 1):
                        text += f"## {i}. {w.get('timestamp', 'Unknown')}\n\n"

                        if not project_id:
                            text += f"**Project:** {w.get('project_name', 'Unknown')}\n"

                        if not action_keyword:
                            text += f"**Template:** {w.get('template_keyword', 'Unknown')}\n"

                        text += f"**Summary:** {w.get('summary', 'No summary')}\n"

                        files = w.get('files_changed', [])
                        if files:
                            text += "**Files Changed:**\n"
                            for file in files:
                                text += f"- {file}\n"

                        text += f"**Tests Passed:** {'Yes' if w.get('tests_passed', False) else 'No'}\n"

                        if w.get('notes'):
                            text += f"**Notes:** {w.get('notes')}\n"

                        text += "\n"

                    return [types.TextContent(type="text", text=text)]
                else:
                    filter_text = []
                    if project_id:
                        filter_text.append(f"project '{project_id}'")
                    if action_keyword:
                        filter_text.append(f"action '{action_keyword}'")

                    filter_str = f" for {' and '.join(filter_text)}" if filter_text else ""
                    return [types.TextContent(type="text",
                                             text=f"No workflow executions found{filter_str}.")]
        except Exception as e:
            logger.error(f"Error retrieving workflow history: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]
