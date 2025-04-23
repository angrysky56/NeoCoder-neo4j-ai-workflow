"""
MCP Server for NeoCoder Neo4j-Guided AI Coding Workflow

This server implements a system where an AI coding assistant uses a Neo4j graph database 
as its primary, dynamic "instruction manual" and project memory.
"""

import json
import logging
import uuid
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import mcp.types as types
from mcp.server.fastmcp import FastMCP
from neo4j import AsyncDriver, AsyncGraphDatabase, AsyncTransaction
from pydantic import Field

from .cypher_snippets import CypherSnippetMixin

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger("mcp_neocoder")


class Neo4jWorkflowServer(CypherSnippetMixin):
    """Server for Neo4j-guided AI coding workflow."""

    def __init__(self, driver: AsyncDriver, database: str = "neo4j"):
        self.driver = driver
        self.database = database
        self.mcp = FastMCP("mcp-neocoder", dependencies=["neo4j", "pydantic"])
        self._register_tools()

    def _register_tools(self):
        """Register all tools with the MCP server."""
        # Core navigation and retrieval tools
        self.mcp.add_tool(self.get_guidance_hub)
        self.mcp.add_tool(self.get_action_template)
        self.mcp.add_tool(self.list_action_templates)
        self.mcp.add_tool(self.get_best_practices)
        
        # Project tools
        self.mcp.add_tool(self.get_project)
        self.mcp.add_tool(self.list_projects)
        
        # Workflow execution tools
        self.mcp.add_tool(self.log_workflow_execution)
        self.mcp.add_tool(self.get_workflow_history)
        
        # Feedback tools
        self.mcp.add_tool(self.add_template_feedback)
        
        # Advanced query tools
        self.mcp.add_tool(self.run_custom_query)
        self.mcp.add_tool(self.write_neo4j_cypher)
        self.mcp.add_tool(self.check_connection)
        
        # Cypher snippet toolkit
        self.mcp.add_tool(self.list_cypher_snippets)
        self.mcp.add_tool(self.get_cypher_snippet)
        self.mcp.add_tool(self.search_cypher_snippets)
        self.mcp.add_tool(self.create_cypher_snippet)
        self.mcp.add_tool(self.update_cypher_snippet)
        self.mcp.add_tool(self.delete_cypher_snippet)
        self.mcp.add_tool(self.get_cypher_tags)
        
        # Tool guidance
        self.mcp.add_tool(self.suggest_tool)
        
    def get_tool_descriptions(self) -> dict:
        """Get descriptions of all available tools."""
        tools = {
            "get_guidance_hub": "Get the central entry point for navigation and guidance",
            "get_action_template": "Retrieve detailed steps for a specific action template by keyword (FIX, REFACTOR, etc.)",
            "list_action_templates": "List all available action templates",
            "get_best_practices": "Get the best practices guide for coding workflows",
            "get_project": "Get details about a specific project by ID",
            "list_projects": "List all available projects",
            "log_workflow_execution": "Record a successful workflow execution (ONLY after passing tests)",
            "get_workflow_history": "View history of workflow executions, optionally filtered",
            "add_template_feedback": "Provide feedback about a template to improve it",
            "run_custom_query": "Execute a custom READ Cypher query (for retrieving data)",
            "write_neo4j_cypher": "Execute a WRITE Cypher query (for creating/updating data)",
            "check_connection": "Check database connection status and permissions",
            # Cypher snippet toolkit
            "list_cypher_snippets": "List all available Cypher snippets with optional filtering",
            "get_cypher_snippet": "Get a specific Cypher snippet by ID",
            "search_cypher_snippets": "Search for Cypher snippets by keyword, tag, or pattern",
            "create_cypher_snippet": "Add a new Cypher snippet to the database",
            "update_cypher_snippet": "Update an existing Cypher snippet",
            "delete_cypher_snippet": "Delete a Cypher snippet from the database",
            "get_cypher_tags": "Get all tags used for Cypher snippets"
        }
        return tools
    
    async def suggest_tool(
        self,
        task_description: str = Field(..., description="Description of the task you're trying to accomplish"),
    ) -> list[types.TextContent]:
        """Suggest the appropriate tool based on a task description."""
        tools = self.get_tool_descriptions()
        
        # Define task patterns to match with tools
        task_patterns = {
            "get_guidance_hub": ["where to start", "what should i do", "guidance", "help me", "not sure", "initial instructions"],
            "get_action_template": ["how to fix", "steps to refactor", "deploy process", "template for", "get instructions"],
            "list_action_templates": ["what actions", "available workflows", "what can i do", "available templates", "list workflows"],
            "get_best_practices": ["best practices", "coding standards", "guidelines", "recommended approach"],
            "get_project": ["project details", "about project", "project readme", "project information"],
            "list_projects": ["what projects", "available projects", "list projects", "all projects"],
            "log_workflow_execution": ["completed work", "task completed", "record execution", "log completion", "finished task"],
            "get_workflow_history": ["past workflows", "execution history", "previous work", "task history"],
            "add_template_feedback": ["improve template", "feedback about", "suggestion for workflow", "template issue"],
            "run_custom_query": ["search for", "find", "query", "read data", "get data", "retrieve information"],
            "write_neo4j_cypher": ["create new", "update", "modify", "delete", "write data", "change data"],
            "check_connection": ["database connection", "connection issues", "connectivity", "database error"],
            # Cypher snippet toolkit patterns
            "list_cypher_snippets": ["list cypher", "show snippets", "available cypher", "cypher commands"],
            "get_cypher_snippet": ["get cypher", "show cypher snippet", "display cypher", "view snippet"],
            "search_cypher_snippets": ["search cypher", "find cypher", "lookup cypher", "cypher syntax"],
            "create_cypher_snippet": ["add cypher", "new cypher", "create snippet", "add snippet"],
            "update_cypher_snippet": ["update cypher", "modify cypher", "change snippet", "edit cypher"],
            "delete_cypher_snippet": ["delete cypher", "remove cypher", "drop snippet"],
            "get_cypher_tags": ["cypher tags", "snippet categories", "snippet tags"]
        }
        
        # Normalize task description
        task = task_description.lower()
        
        # Find matching tools
        matches = []
        for tool, patterns in task_patterns.items():
            for pattern in patterns:
                if pattern in task:
                    matches.append((tool, tools[tool]))
        
        # If no matches, suggest based on common actions
        if not matches:
            if "cypher" in task.lower() or "snippet" in task.lower():
                if "search" in task.lower() or "find" in task.lower():
                    matches.append(("search_cypher_snippets", tools["search_cypher_snippets"]))
                elif "list" in task.lower() or "show" in task.lower():
                    matches.append(("list_cypher_snippets", tools["list_cypher_snippets"]))
                else:
                    matches.append(("get_cypher_snippet", tools["get_cypher_snippet"]))
            elif "create" in task or "new" in task:
                matches.append(("write_neo4j_cypher", tools["write_neo4j_cypher"]))
            elif "find" in task or "search" in task or "get" in task:
                matches.append(("run_custom_query", tools["run_custom_query"]))
            else:
                # Default to guidance hub if no clear match
                matches.append(("get_guidance_hub", tools["get_guidance_hub"]))
        
        # Format response
        response = "Based on your task description, here are the recommended tools:\n\n"
        
        for tool, description in matches:
            response += f"- **{tool}**: {description}\n"
            
            # Add example usage for the top match
            if tool == matches[0][0]:
                if tool == "get_action_template":
                    response += "\n  Example usage: `get_action_template(keyword=\"FIX\")`\n"
                elif tool == "get_project":
                    response += "\n  Example usage: `get_project(project_id=\"your_project_id\")`\n"
                elif tool == "run_custom_query":
                    response += "\n  Example usage: `run_custom_query(query=\"MATCH (n:Project) RETURN n.name\")`\n"
                elif tool == "write_neo4j_cypher":
                    response += "\n  Example usage: `write_neo4j_cypher(query=\"CREATE (n:TestNode {name: 'Test'}) RETURN n\")`\n"
        
        response += "\nFor full navigation help, try `get_guidance_hub()` to see all available options."
        
        return [types.TextContent(type="text", text=response)]
        
    async def check_connection(self) -> List[types.TextContent]:
        """Check the Neo4j connection status and database access permissions."""
        try:
            # Check if we can connect and run a simple read query
            async with self.driver.session(database=self.database) as session:
                read_result = await session.execute_read(
                    self._read_query, "RETURN 'Read access is working' as status", {}
                )
                
                # Check if we have write access
                try:
                    # Try a harmless write operation
                    write_result = await session.execute_write(
                        self._write, 
                        "CREATE (n:ConnectionTest {id: randomUUID()}) WITH n DELETE n RETURN 'Write access is working' as status", 
                        {}
                    )
                    write_access = True
                    write_message = "Write access is working"
                except Exception as e:
                    write_access = False
                    write_message = f"Write access error: {str(e)}"
                
                # Get Neo4j version and database info
                info_result = await session.execute_read(
                    self._read_query, "CALL dbms.components() YIELD name, versions RETURN name, versions[0] as version", {}
                )
                
                result = {
                    "connection": "Connected to Neo4j database",
                    "database": self.database,
                    "read_access": True,
                    "write_access": write_access,
                    "write_message": write_message,
                    "server_info": json.loads(info_result) if info_result else "N/A"
                }
                
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        except Exception as e:
            logger.error(f"Error checking connection: {e}")
            return [types.TextContent(
                type="text", 
                text=f"Error connecting to Neo4j database: {e}\n\nCheck your connection settings in claude-app-config.json."
            )]


    async def _read_query(self, tx: AsyncTransaction, query: str, params: dict) -> str:
        """Execute a read query and return results as JSON string."""
        raw_results = await tx.run(query, params)
        eager_results = await raw_results.to_eager_result()
        return json.dumps([r.data() for r in eager_results.records], default=str)
    
    async def _write(self, tx: AsyncTransaction, query: str, params: dict):
        """Execute a write query and return results as JSON string."""
        result = await tx.run(query, params or {})
        summary = await result.consume()
        return summary
    
    def is_write_query(self, query: str) -> bool:
        """Check if a query is a write query.
        
        Neo4j write operations typically start with CREATE, DELETE, SET, REMOVE, MERGE, or DROP.
        This method checks if the query contains any of these keywords.
        """
        if not query:
            return False
            
        query = query.strip().upper()
        write_keywords = ["CREATE", "DELETE", "SET", "REMOVE", "MERGE", "DROP"]
        return any(keyword in query for keyword in write_keywords)
        
    def analyze_cypher_syntax(self, query: str) -> tuple[bool, str]:
        """
        Analyze Cypher query syntax and provide feedback on common errors.
        
        Args:
            query: The Cypher query to analyze
            
        Returns:
            tuple: (is_valid, message)
        """
        if not query or not query.strip():
            return False, "Empty query. Please provide a valid Cypher query."
            
        query = query.strip()
        
        # Check for missing parentheses in node patterns
        if '(' in query and ')' not in query:
            return False, "Syntax error: Missing closing parenthesis ')' in node pattern. Remember nodes should be defined with (node:Label)."
            
        # Check for missing brackets in property access
        if '[' in query and ']' not in query:
            return False, "Syntax error: Missing closing bracket ']' in property access or collection."
            
        # Check for missing curly braces in property maps
        if '{' in query and '}' not in query:
            return False, "Syntax error: Missing closing curly brace '}' in property map. Properties should be defined with {key: value}."
            
        # Check for missing quotes in property strings
        quote_chars = ['\'', '"', '`']
        for char in quote_chars:
            if query.count(char) % 2 != 0:
                return False, f"Syntax error: Unbalanced quotes ({char}). Make sure all string literals are properly enclosed."
                
        # Check for common cypher keywords
        cypher_keywords = ['MATCH', 'RETURN', 'WHERE', 'CREATE', 'MERGE', 'SET', 'REMOVE', 'DELETE', 'WITH', 'UNWIND', 'ORDER BY', 'LIMIT']
        if not any(keyword in query.upper() for keyword in cypher_keywords):
            return False, "Warning: Query doesn't contain common Cypher keywords (MATCH, RETURN, CREATE, etc.). Please check your syntax."
            
        # Check for RETURN in read queries or missing RETURN where needed
        if 'MATCH' in query.upper() and 'RETURN' not in query.upper() and not self.is_write_query(query):
            return False, "Syntax warning: MATCH queries typically need a RETURN clause to specify what to return from the matched patterns."
            
        return True, "Query syntax appears valid."
    
    async def write_neo4j_cypher(
        self,
        query: str = Field(..., description="The Cypher query to execute."),
        params: Optional[dict[str, Any]] = Field(
            None, description="The parameters to pass to the Cypher query."
        ),
    ) -> list[types.TextContent]:
        """Execute a write Cypher query on the neo4j database."""

        # Check if query is a write query
        if not self.is_write_query(query):
            suggested_tool = "run_custom_query"
            return [types.TextContent(type="text", text=f"Error: Only write queries are allowed for write_neo4j_cypher. Your query appears to be a read query.\n\nSuggestion: For read queries, use the '{suggested_tool}' tool instead. Example:\n\n```\nrun_custom_query(query=\"{query}\"" + (", params=" + str(params) if params else "") + ")\n```")]
        
        # Check query syntax
        is_valid, syntax_message = self.analyze_cypher_syntax(query)
        if not is_valid:
            return [types.TextContent(type="text", text=f"Error: {syntax_message}\n\nYour query: {query}")]

        try:
            async with self.driver.session(database=self.database) as session:
                # First check if we have write access
                try:
                    test_result = await session.execute_write(
                        self._write, 
                        "CREATE (n:WriteTest {id: randomUUID()}) WITH n DELETE n RETURN 'Success'", 
                        {}
                    )
                except Exception as e:
                    error_msg = str(e).lower()
                    if "access mode" in error_msg or "permission" in error_msg or "read only" in error_msg:
                        return [types.TextContent(
                            type="text", 
                            text="Error: Database is in read-only mode. Write operations are not allowed. Check your Neo4j configuration or connection parameters."
                        )]
                    else:
                        # Let it proceed and fail with the actual query if it's not a permissions issue
                        pass
                
                # Execute the actual query
                raw_results = await session.execute_write(self._write, query, params or {})
                
                # Create a counters dictionary with safer attribute access
                try:
                    # Try to access counters using more public APIs or properties
                    counters_dict = {}
                    
                    # Add known counter attributes if they exist
                    for attr in ["nodes_created", "nodes_deleted", "relationships_created", 
                                "relationships_deleted", "properties_set", "labels_added",
                                "labels_removed", "indexes_added", "indexes_removed",
                                "constraints_added", "constraints_removed"]:
                        if hasattr(raw_results.counters, attr):
                            counters_dict[attr] = getattr(raw_results.counters, attr)
                    
                    counters_json_str = json.dumps(counters_dict, default=str)
                except Exception as e:
                    # Fallback if counters are not accessible
                    logger.warning(f"Could not access counters: {e}")
                    counters_json_str = json.dumps({"success": True}, default=str)

                logger.debug(f"Write query affected {counters_json_str}")
                return [types.TextContent(type="text", text=f"Query executed successfully. Results: {counters_json_str}")]

        except Exception as e:
            logger.error(f"Database error executing query: {e}\n{query}\n{params}")
            
            error_msg = str(e).lower()
            
            # Check for specific error types and provide helpful messages
            if "access mode" in error_msg or "permission" in error_msg or "read only" in error_msg:
                return [types.TextContent(
                    type="text", 
                    text="Error: Database is in read-only mode. Write operations are not allowed. Check your Neo4j configuration or connection parameters."
                )]
            elif "connection" in error_msg or "unavailable" in error_msg or "refused" in error_msg:
                return [types.TextContent(
                    type="text", 
                    text="Error: Could not connect to the Neo4j database. Please check:\n"
                         "1. Is the Neo4j server running?\n"
                         "2. Are the connection details correct?\n"
                         "3. Is there a network issue preventing connection?\n\n"
                         "You can use the check_connection() tool to verify database connectivity."
                )]
            elif "constraint" in error_msg or "unique" in error_msg:
                return [types.TextContent(
                    type="text", 
                    text=f"Error: A constraint violation occurred. This typically happens when:\n"
                         "1. Trying to create a node with a label and property combination that must be unique\n"
                         "2. Violating a relationship constraint\n\n"
                         "Details: {e}\n\n"
                         "You might need to check if the entity already exists before creating it."
                )]
            elif "syntax" in error_msg:
                return [types.TextContent(
                    type="text", 
                    text=f"Syntax Error in Cypher query:\n{e}\n\n"
                         f"Your query: {query}\n\n"
                         "Common syntax issues include:\n"
                         "1. Missing or unbalanced parentheses/brackets/braces\n"
                         "2. Incorrect property access (node.property instead of node['property'])\n"
                         "3. Missing quotes around property values\n"
                         "4. Incorrect relationship direction (-->, <--, --)"
                )]
            else:
                return [types.TextContent(
                    type="text", 
                    text=f"Error executing query: {e}\n\n"
                         f"Query: {query}\n\n"
                         f"Parameters: {params}\n\n"
                         "If this is unexpected, try:\n"
                         "1. Breaking down the query into smaller parts\n"
                         "2. Using run_custom_query for testing before write operations\n"
                         "3. Checking Neo4j documentation for correct syntax"
                )]
    
    async def get_guidance_hub(self) -> List[types.TextContent]:
        """Get the AI Guidance Hub content, which serves as the central entry point for navigation."""
        query = """
        MATCH (hub:AiGuidanceHub {id: 'main_hub'})
        RETURN hub.description AS description
        """
        
        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_read(self._read_query, query, {})
                results = json.loads(results_json)
                
                if results and len(results) > 0:
                    return [types.TextContent(type="text", text=results[0]["description"])]
                else:
                    # If hub doesn't exist, create it with default content
                    return await self._create_default_hub()
        except Exception as e:
            logger.error(f"Error retrieving guidance hub: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def _create_default_hub(self) -> List[types.TextContent]:
        """Create a default guidance hub if none exists."""
        default_description = """
Welcome AI Assistant. This is your central hub for coding assistance using our Neo4j knowledge graph. Choose your path:
1.  **Execute Task:** If you know the action keyword (e.g., FIX, REFACTOR), directly query for the ActionTemplate: Use get_action_template tool with the keyword parameter.
2.  **List Workflows/Templates:** Use list_action_templates tool to see available actions.
3.  **View Core Practices:** Use get_best_practices tool to understand essential rules.
4.  **Project Information:** Use get_project tool to retrieve project details and README content.
5.  **Log Completion:** After successful testing, use log_workflow_execution to record successful completions.

Always follow template steps precisely, especially testing before logging.
        """
        
        query = """
        CREATE (hub:AiGuidanceHub {id: 'main_hub', description: $description})
        RETURN hub.description AS description
        """
        
        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_write(
                    self._read_query, query, {"description": default_description}
                )
                results = json.loads(results_json)
                
                if results and len(results) > 0:
                    return [types.TextContent(type="text", text=results[0]["description"])]
                else:
                    return [types.TextContent(type="text", text="Error creating default hub")]
        except Exception as e:
            logger.error(f"Error creating default hub: {e}")
            return [types.TextContent(type="text", text=f"Error creating default hub: {e}")]

    async def get_action_template(
        self, 
        keyword: str = Field(..., description="The template keyword (e.g., FIX, REFACTOR, DEPLOY)"),
        version: Optional[str] = Field(None, description="Specific version to retrieve (default: current)")
    ) -> List[types.TextContent]:
        """Get a specific action template by keyword and optional version."""
        query = """
        MATCH (t:ActionTemplate {keyword: $keyword})
        WHERE 1=1
        """
        
        params = {"keyword": keyword}
        
        if version:
            query += " AND t.version = $version"
            params["version"] = version
        else:
            query += " AND t.isCurrent = true"
            
        query += """
        RETURN t.keyword AS keyword, 
               t.version AS version, 
               t.description AS description,
               t.complexity AS complexity,
               t.estimatedEffort AS estimatedEffort,
               t.steps AS steps
        """
        
        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_read(self._read_query, query, params)
                results = json.loads(results_json)
                
                if results and len(results) > 0:
                    # Format the template for better readability
                    template = results[0]
                    text = f"# {template['keyword']} Template (v{template['version']})\n\n"
                    text += f"**Description:** {template['description']}\n"
                    text += f"**Complexity:** {template['complexity']}\n"
                    text += f"**Estimated Effort:** {template['estimatedEffort']} minutes\n\n"
                    text += "## Steps:\n\n"
                    text += template['steps']
                    
                    return [types.TextContent(type="text", text=text)]
                else:
                    return [types.TextContent(type="text", text=f"No template found with keyword '{keyword}'{' v' + version if version else ''}")]
        except Exception as e:
            logger.error(f"Error retrieving action template: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def list_action_templates(
        self,
        include_inactive: bool = Field(False, description="Include non-current template versions"),
        domain: Optional[str] = Field(None, description="Filter templates by domain (e.g., 'web', 'ml', 'backend')")
    ) -> List[types.TextContent]:
        """List all available action templates, optionally filtered by domain."""
        query = """
        MATCH (t:ActionTemplate)
        WHERE 1=1
        """
        
        params = {}
        
        if not include_inactive:
            query += " AND t.isCurrent = true"
            
        if domain:
            query += " AND t.domain = $domain"
            params["domain"] = domain
            
        query += """
        RETURN t.keyword AS keyword, 
               t.version AS version, 
               t.isCurrent AS current,
               t.description AS description,
               t.complexity AS complexity,
               t.estimatedEffort AS estimatedEffort,
               t.domain AS domain
        ORDER BY t.keyword, t.version DESC
        """
        
        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_read(self._read_query, query, params)
                results = json.loads(results_json)
                
                if results and len(results) > 0:
                    # Format the templates as a readable table
                    text = "# Available Action Templates\n\n"
                    text += "| Keyword | Version | Status | Complexity | Effort (min) | Description |\n"
                    text += "| ------- | ------- | ------ | ---------- | ------------ | ----------- |\n"
                    
                    for t in results:
                        current = "Current" if t.get("current") else "Inactive"
                        text += f"| {t.get('keyword', 'N/A')} | {t.get('version', 'N/A')} | {current} | {t.get('complexity', 'N/A')} | {t.get('estimatedEffort', 'N/A')} | {t.get('description', 'N/A')} |\n"
                    
                    return [types.TextContent(type="text", text=text)]
                else:
                    return [types.TextContent(type="text", text="No action templates found in the database.")]
        except Exception as e:
            logger.error(f"Error listing action templates: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def get_best_practices(self) -> List[types.TextContent]:
        """Get the best practices guide for coding workflows."""
        query = """
        MATCH (hub:AiGuidanceHub {id: 'main_hub'})-[:LINKS_TO]->(bp:BestPracticesGuide)
        RETURN bp.content AS content
        """
        
        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_read(self._read_query, query, {})
                results = json.loads(results_json)
                
                if results and len(results) > 0:
                    return [types.TextContent(type="text", text=results[0]["content"])]
                else:
                    # If best practices guide doesn't exist, create it with default content
                    return await self._create_default_best_practices()
        except Exception as e:
            logger.error(f"Error retrieving best practices: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def _create_default_best_practices(self) -> List[types.TextContent]:
        """Create a default best practices guide if none exists."""
        default_content = """
# Core Coding & System Practices

- **Efficiency First:** Prefer editing existing code over complete rewrites where feasible. Avoid temporary patch files.
- **Meaningful Naming:** Do not name functions, variables, or files 'temp', 'fixed', 'patch'. Use descriptive names reflecting purpose.
- **README is Key:** ALWAYS review the project's README before starting work. Find it via the :Project node.
- **Test Rigorously:** Before logging completion, ALL relevant tests must pass. If tests fail, revisit the code, do not log success.
- **Update After Success:** ONLY AFTER successful testing, update the Neo4j project tree AND the project's README with changes made.
- **Risk Assessment:** Always evaluate the potential impact of changes and document any areas that need monitoring.
- **Metrics Collection:** Track completion time and success rates to improve future estimation accuracy.
        """
        
        query_hub = """
        MERGE (hub:AiGuidanceHub {id: 'main_hub'})
        RETURN hub
        """
        
        query_bp = """
        MATCH (hub:AiGuidanceHub {id: 'main_hub'})
        MERGE (bp:BestPracticesGuide {id: 'core_practices'})
        ON CREATE SET bp.content = $content
        MERGE (hub)-[:LINKS_TO]->(bp)
        RETURN bp.content AS content
        """
        
        try:
            async with self.driver.session(database=self.database) as session:
                # Ensure hub exists
                await session.execute_write(self._read_query, query_hub, {})
                
                # Create best practices guide
                results_json = await session.execute_write(
                    self._read_query, query_bp, {"content": default_content}
                )
                results = json.loads(results_json)
                
                if results and len(results) > 0:
                    return [types.TextContent(type="text", text=results[0]["content"])]
                else:
                    return [types.TextContent(type="text", text="Error creating default best practices guide")]
        except Exception as e:
            logger.error(f"Error creating default best practices guide: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def get_project(
        self,
        project_id: str = Field(..., description="The unique project identifier")
    ) -> List[types.TextContent]:
        """Get a project by ID, including its README content."""
        query = """
        MATCH (p:Project {projectId: $projectId})
        RETURN p.projectId AS projectId,
               p.name AS name,
               p.readmeContent AS readmeContent,
               p.readmeUrl AS readmeUrl,
               p.currentVersion AS currentVersion,
               p.lastDeployment AS lastDeployment
        """
        
        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_read(
                    self._read_query, query, {"projectId": project_id}
                )
                results = json.loads(results_json)
                
                if results and len(results) > 0:
                    project = results[0]
                    text = f"# Project: {project.get('name', project_id)}\n\n"
                    
                    if project.get('currentVersion'):
                        text += f"**Current Version:** {project['currentVersion']}\n"
                    
                    if project.get('lastDeployment'):
                        text += f"**Last Deployment:** {project['lastDeployment']}\n"
                    
                    text += "\n## README Content:\n\n"
                    
                    if project.get('readmeContent'):
                        text += project['readmeContent']
                    elif project.get('readmeUrl'):
                        text += f"README available at: {project['readmeUrl']}"
                    else:
                        text += "No README content available."
                    
                    return [types.TextContent(type="text", text=text)]
                else:
                    return [types.TextContent(type="text", text=f"No project found with ID '{project_id}'")]
        except Exception as e:
            logger.error(f"Error retrieving project: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def list_projects(self) -> List[types.TextContent]:
        """List all projects in the database."""
        query = """
        MATCH (p:Project)
        RETURN p.projectId AS projectId,
               p.name AS name,
               p.currentVersion AS currentVersion
        ORDER BY p.name
        """
        
        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_read(self._read_query, query, {})
                results = json.loads(results_json)
                
                if results and len(results) > 0:
                    text = "# Available Projects\n\n"
                    text += "| Project ID | Name | Current Version |\n"
                    text += "| ---------- | ---- | --------------- |\n"
                    
                    for p in results:
                        text += f"| {p.get('projectId', 'N/A')} | {p.get('name', 'N/A')} | {p.get('currentVersion', 'N/A')} |\n"
                    
                    return [types.TextContent(type="text", text=text)]
                else:
                    return [types.TextContent(type="text", text="No projects found in the database.")]
        except Exception as e:
            logger.error(f"Error listing projects: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def log_workflow_execution(
        self,
        project_id: str = Field(..., description="The project identifier"),
        keyword: str = Field(..., description="The template keyword used (e.g., FIX, REFACTOR)"),
        description: str = Field(..., description="Brief description of the work performed"),
        modified_files: List[str] = Field(..., description="List of file paths that were modified"),
        execution_time_seconds: Optional[int] = Field(None, description="Time taken to complete the workflow in seconds"),
        test_results: Optional[str] = Field(None, description="Summary of test results"),
        environment: Optional[str] = Field(None, description="Target environment (for DEPLOY workflows)"),
        deployed_version: Optional[str] = Field(None, description="Deployed version (for DEPLOY workflows)")
    ) -> List[types.TextContent]:
        """Log a successful workflow execution after completing all steps and passing all tests."""
        # Generate a workflow ID
        workflow_id = str(uuid.uuid4())
        
        # Base query for creating the workflow execution node
        query = """
        CREATE (exec:WorkflowExecution {
          id: $workflowId,
          timestamp: datetime(),
          keywordUsed: $keyword,
          description: $description,
          status: "Completed"
        """
        
        # Add optional parameters
        params = {
            "workflowId": workflow_id,
            "keyword": keyword,
            "description": description,
            "projectId": project_id,
            "modifiedFiles": modified_files
        }
        
        if execution_time_seconds is not None:
            query += ", executionTime: $executionTime"
            params["executionTime"] = execution_time_seconds
            
        if test_results is not None:
            query += ", testResults: $testResults"
            params["testResults"] = test_results
            
        if environment is not None:
            query += ", environment: $environment"
            params["environment"] = environment
            
        if deployed_version is not None:
            query += ", deployedVersion: $deployedVersion"
            params["deployedVersion"] = deployed_version
        
        # Complete the node creation and add relationships
        query += """
        })
        WITH exec
        MATCH (p:Project {projectId: $projectId})
        MERGE (exec)-[:APPLIED_TO_PROJECT]->(p)
        WITH exec
        MATCH (t:ActionTemplate {keyword: $keyword, isCurrent: true})
        MERGE (exec)-[:USED_TEMPLATE]->(t)
        WITH exec
        FOREACH (filePath IN $modifiedFiles | 
          MERGE (f:File {path: filePath, project_id: $projectId})
          MERGE (exec)-[:MODIFIED]->(f)
        )
        RETURN exec.id AS id, exec.timestamp AS timestamp
        """
        
        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_write(self._read_query, query, params)
                results = json.loads(results_json)
                
                if results and len(results) > 0:
                    timestamp = results[0]["timestamp"]
                    text = f"Successfully logged workflow execution:\n\n"
                    text += f"- Workflow ID: {workflow_id}\n"
                    text += f"- Timestamp: {timestamp}\n"
                    text += f"- Action: {keyword}\n"
                    text += f"- Project: {project_id}\n"
                    text += f"- Description: {description}\n"
                    text += f"- Modified Files: {len(modified_files)} files\n"
                    
                    return [types.TextContent(type="text", text=text)]
                else:
                    return [types.TextContent(type="text", text="Error logging workflow execution")]
        except Exception as e:
            logger.error(f"Error logging workflow execution: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def get_workflow_history(
        self,
        project_id: Optional[str] = Field(None, description="Filter by project ID"),
        keyword: Optional[str] = Field(None, description="Filter by template keyword"),
        days: int = Field(30, description="Number of days to include in history"),
        limit: int = Field(20, description="Maximum number of executions to return")
    ) -> List[types.TextContent]:
        """Get workflow execution history, optionally filtered by project or keyword."""
        query = """
        MATCH (w:WorkflowExecution)
        WHERE w.timestamp > datetime() - duration({days: $days})
        """
        
        params = {"days": days, "limit": limit}
        
        if project_id:
            query += """
            AND (w)-[:APPLIED_TO_PROJECT]->(:Project {projectId: $projectId})
            """
            params["projectId"] = project_id
            
        if keyword:
            query += """
            AND w.keywordUsed = $keyword
            """
            params["keyword"] = keyword
            
        query += """
        OPTIONAL MATCH (w)-[:MODIFIED]->(f)
        WITH w, count(f) as modifiedFileCount
        RETURN w.id AS id,
               w.keywordUsed AS keyword,
               w.timestamp AS timestamp,
               w.description AS description,
               modifiedFileCount
        ORDER BY w.timestamp DESC
        LIMIT $limit
        """
        
        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_read(self._read_query, query, params)
                results = json.loads(results_json)
                
                if results and len(results) > 0:
                    text = "# Workflow Execution History\n\n"
                    
                    if project_id:
                        text += f"Project: {project_id}\n\n"
                    if keyword:
                        text += f"Action: {keyword}\n\n"
                        
                    text += "| Date | Action | Description | Files Modified |\n"
                    text += "| ---- | ------ | ----------- | -------------- |\n"
                    
                    for w in results:
                        timestamp = w.get("timestamp", "")[:19]  # Truncate to remove milliseconds
                        text += f"| {timestamp} | {w.get('keyword', 'N/A')} | {w.get('description', 'N/A')} | {w.get('modifiedFileCount', 0)} |\n"
                    
                    return [types.TextContent(type="text", text=text)]
                else:
                    return [types.TextContent(type="text", text="No workflow executions found matching the criteria.")]
        except Exception as e:
            logger.error(f"Error retrieving workflow history: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def add_template_feedback(
        self,
        keyword: str = Field(..., description="Template keyword to provide feedback on"),
        content: str = Field(..., description="Feedback content"),
        severity: str = Field("MEDIUM", description="Feedback severity (LOW, MEDIUM, HIGH)"),
        tags: Optional[List[str]] = Field(None, description="Tags for categorizing feedback")
    ) -> List[types.TextContent]:
        """Add feedback for a template to help improve it."""
        # Generate a feedback ID
        feedback_id = str(uuid.uuid4())
        feedback_tags = tags or []
        
        query = """
        MATCH (t:ActionTemplate {keyword: $keyword, isCurrent: true})
        CREATE (f:Feedback {
          id: $id,
          content: $content,
          timestamp: datetime(),
          source: 'AI',
          severity: $severity,
          tags: $tags
        })
        CREATE (f)-[:REGARDING]->(t)
        RETURN f.id AS id, t.keyword AS keyword
        """
        
        params = {
            "id": feedback_id,
            "keyword": keyword,
            "content": content,
            "severity": severity,
            "tags": feedback_tags
        }
        
        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_write(self._read_query, query, params)
                results = json.loads(results_json)
                
                if results and len(results) > 0:
                    return [types.TextContent(
                        type="text", 
                        text=f"Successfully added feedback for template '{keyword}' with ID: {feedback_id}"
                    )]
                else:
                    return [types.TextContent(
                        type="text", 
                        text=f"No current template found with keyword '{keyword}'"
                    )]
        except Exception as e:
            logger.error(f"Error adding template feedback: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def run_custom_query(
        self,
        query: str = Field(..., description="Custom Cypher query to execute"),
        params: Optional[Dict[str, Any]] = Field(None, description="Query parameters")
    ) -> List[types.TextContent]:
        """Run a custom Cypher query for advanced operations."""
        params = params or {}
        
        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_read(self._read_query, query, params)
                return [types.TextContent(type="text", text=results_json)]
        except Exception as e:
            logger.error(f"Error executing custom query: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    def run(self, transport: str = "stdio"):
        """Run the MCP server."""
        self.mcp.run(transport=transport)


def create_server(db_url: str, username: str, password: str, database: str = "neo4j") -> Neo4jWorkflowServer:
    """Create and return a Neo4jWorkflowServer instance."""
    driver = AsyncGraphDatabase.driver(db_url, auth=(username, password))
    return Neo4jWorkflowServer(driver, database)


def main():
    """Main entry point for the MCP server."""
    import os
    
    db_url = os.environ.get("NEO4J_URL", "bolt://localhost:7687")
    username = os.environ.get("NEO4J_USERNAME", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "password")
    database = os.environ.get("NEO4J_DATABASE", "neo4j")
    
    logger.info(f"Starting NeoCoder MCP Server, connecting to {db_url}")
    
    server = create_server(db_url, username, password, database)
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
