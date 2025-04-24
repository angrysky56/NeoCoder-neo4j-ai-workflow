"""
Modified MCP Server for NeoCoder Neo4j-Guided AI Workflow with Polymorphic Support

This version adds support for multiple incarnations of the NeoCoder framework,
allowing it to function as a research orchestration platform, decision support system,
continuous learning environment, or complex system simulator.
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
from .tool_proposals import ToolProposalMixin
from .polymorphic_adapter import PolymorphicAdapterMixin, IncarnationType
from .action_templates import ActionTemplateMixin
from .research_incarnation import ResearchOrchestration
from .init_db import init_db, INCARNATION_TYPES
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger("mcp_neocoder")


class Neo4jWorkflowServer(PolymorphicAdapterMixin, CypherSnippetMixin, ToolProposalMixin, ActionTemplateMixin):
    """Server for Neo4j-guided AI workflow with polymorphic support."""

    def __init__(self, driver: AsyncDriver, database: str = "neo4j"):
        """Initialize the workflow server with Neo4j connection."""
        self.driver = driver
        self.database = database
        self.mcp = FastMCP("mcp-neocoder", dependencies=["neo4j", "pydantic"])
        
        # Auto-initialize the database if needed
        asyncio.get_event_loop().run_until_complete(self._ensure_db_initialized())
        
        # Initialize the polymorphic adapter
        PolymorphicAdapterMixin.__init__(self)
        
        # Register incarnations
        self.register_incarnation(ResearchOrchestration, IncarnationType.RESEARCH)
        
        # Register core tools
        self._register_tools()
        
    async def _ensure_db_initialized(self):
        """Check if the database is initialized and run initialization if needed."""
        logger.info("Checking if database needs initialization...")
        try:
            # Check if the main hub exists
            init_needed = False
            hub_exists = False
            
            async with self.driver.session(database=self.database) as session:
                # Check if main hub exists
                hub_query = "MATCH (hub:AiGuidanceHub {id: 'main_hub'}) RETURN count(hub) as count"
                hub_result = await session.execute_read(self._read_query, hub_query, {})
                hub_data = json.loads(hub_result)
                
                if not hub_data or hub_data[0].get("count", 0) == 0:
                    logger.info("Main hub not found, database needs initialization")
                    init_needed = True
                else:
                    hub_exists = True
                    
                # If hub exists, check if incarnation hubs exist
                if hub_exists:
                    incarnation_query = """
                    MATCH (hub:AiGuidanceHub {id: 'main_hub'})
                    OPTIONAL MATCH (hub)-[:HAS_INCARNATION]->(inc:AiGuidanceHub)
                    RETURN count(inc) as count
                    """
                    inc_result = await session.execute_read(self._read_query, incarnation_query, {})
                    inc_data = json.loads(inc_result)
                    
                    if not inc_data or inc_data[0].get("count", 0) < 3:  # At least research, decision, and coding
                        logger.info("Incarnation hubs not fully set up, database needs initialization")
                        init_needed = True
                
                # Check if action templates exist
                if not init_needed:
                    template_query = "MATCH (t:ActionTemplate) RETURN count(t) as count"
                    template_result = await session.execute_read(self._read_query, template_query, {})
                    template_data = json.loads(template_result)
                    
                    if not template_data or template_data[0].get("count", 0) == 0:
                        logger.info("No action templates found, database needs initialization")
                        init_needed = True
            
            if init_needed:
                logger.info("Initializing database...")
                await init_db(INCARNATION_TYPES)
                logger.info("Database initialization completed")
            else:
                logger.info("Database already initialized, skipping initialization")
                
        except Exception as e:
            logger.error(f"Error during database initialization check: {e}")
            logger.info("Will attempt database initialization due to error")
            try:
                await init_db(INCARNATION_TYPES)
                logger.info("Database initialization completed after error recovery")
            except Exception as init_err:
                logger.error(f"Database initialization failed: {init_err}")

    def _register_tools(self):
        """Register all tools with the MCP server."""
        # Core navigation and retrieval tools
        self.mcp.add_tool(self.get_guidance_hub)
        self.mcp.add_tool(self.list_action_templates)
        self.mcp.add_tool(self.get_action_template)
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

        # Tool proposal system
        self.mcp.add_tool(self.propose_tool)
        self.mcp.add_tool(self.request_tool)
        self.mcp.add_tool(self.get_tool_proposal)
        self.mcp.add_tool(self.get_tool_request)
        self.mcp.add_tool(self.list_tool_proposals)
        self.mcp.add_tool(self.list_tool_requests)

        # Tool guidance
        self.mcp.add_tool(self.suggest_tool)
        
        # Incarnation tools
        self.mcp.add_tool(self.get_current_incarnation)
        self.mcp.add_tool(self.list_incarnations)
        self.mcp.add_tool(self.switch_incarnation)

    async def get_current_incarnation(self) -> List[types.TextContent]:
        """Get the currently active incarnation type."""
        try:
            current = await self.get_current_incarnation_type()
            if current:
                return [types.TextContent(
                    type="text",
                    text=f"Currently using '{current.value}' incarnation"
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text="No incarnation is currently active. Use `switch_incarnation()` to set one."
                )]
        except Exception as e:
            logger.error(f"Error getting current incarnation: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def list_incarnations(self) -> List[types.TextContent]:
        """List all available incarnations."""
        try:
            incarnations = []
            for inc_type, inc_class in self.incarnation_registry.items():
                incarnations.append({
                    "type": inc_type.value,
                    "description": inc_class.description if hasattr(inc_class, 'description') else "No description available",
                })
            
            if incarnations:
                text = "# Available Incarnations\n\n"
                text += "| Type | Description |\n"
                text += "| ---- | ----------- |\n"
                
                for inc in incarnations:
                    text += f"| {inc['type']} | {inc['description']} |\n"
                
                current = await self.get_current_incarnation_type()
                if current:
                    text += f"\nCurrently using: **{current.value}**"
                else:
                    text += "\nNo incarnation is currently active. Use `switch_incarnation()` to activate one."
                
                return [types.TextContent(type="text", text=text)]
            else:
                return [types.TextContent(type="text", text="No incarnations are registered")]
        except Exception as e:
            logger.error(f"Error listing incarnations: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def switch_incarnation(
        self,
        incarnation_type: str = Field(..., description="Type of incarnation to switch to (coding, research_orchestration, decision_support, continuous_learning, complex_system)"),
    ) -> List[types.TextContent]:
        """Switch the server to a different incarnation."""
        try:
            # Convert string to enum
            inc_type = None
            for t in IncarnationType:
                if t.value == incarnation_type:
                    inc_type = t
                    break
            
            if not inc_type:
                available_types = ", ".join([t.value for t in IncarnationType])
                return [types.TextContent(
                    type="text",
                    text=f"Unknown incarnation type: '{incarnation_type}'. Available types: {available_types}"
                )]
            
            await self.set_incarnation(inc_type)
            return [types.TextContent(
                type="text",
                text=f"Successfully switched to '{inc_type.value}' incarnation"
            )]
        except Exception as e:
            logger.error(f"Error switching incarnation: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

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
            "get_cypher_tags": "Get all tags used for Cypher snippets",
            # Tool proposal system
            "propose_tool": "Propose a new tool for the NeoCoder system",
            "request_tool": "Request a new tool feature as a user",
            "get_tool_proposal": "Get details of a specific tool proposal",
            "get_tool_request": "Get details of a specific tool request",
            "list_tool_proposals": "List all tool proposals with optional filtering",
            "list_tool_requests": "List all tool requests with optional filtering",
            # Incarnation tools
            "get_current_incarnation": "Get the currently active incarnation type",
            "list_incarnations": "List all available incarnations",
            "switch_incarnation": "Switch the server to a different incarnation type"
        }
        return tools

    async def suggest_tool(
        self,
        task_description: str = Field(..., description="Description of the task you're trying to accomplish"),
    ) -> list[types.TextContent]:
        """Suggest the appropriate tool based on a task description."""
        tools = self.get_tool_descriptions()

        # Get the current incarnation type
        current_incarnation = await self.get_current_incarnation_type()
        
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
            "get_cypher_tags": ["cypher tags", "snippet categories", "snippet tags"],
            # Tool proposal patterns
            "propose_tool": ["suggest tool", "propose tool", "new tool idea", "tool proposal", "implement tool"],
            "request_tool": ["request tool", "need tool", "want tool", "tool feature request", "add functionality"],
            "get_tool_proposal": ["view proposal", "see tool proposal", "proposal details", "proposed tool info"],
            "get_tool_request": ["view request", "see tool request", "request details", "requested tool info"],
            "list_tool_proposals": ["all proposals", "tool ideas", "proposed tools", "tool suggestions"],
            "list_tool_requests": ["all requests", "requested tools", "tool requests", "feature requests"],
            # Incarnation tools
            "get_current_incarnation": ["what mode", "current incarnation", "what functionality", "active mode"],
            "list_incarnations": ["available modes", "list incarnations", "system modes", "what can it do"],
            "switch_incarnation": ["change mode", "switch to", "research mode", "coding mode", "decision mode"]
        }
        
        # Add research-specific patterns if in research mode
        if current_incarnation == IncarnationType.RESEARCH:
            research_patterns = {
                "register_hypothesis": ["new hypothesis", "create hypothesis", "register hypothesis", "add hypothesis"],
                "list_hypotheses": ["show hypotheses", "all hypotheses", "view hypotheses", "list hypotheses"],
                "get_hypothesis": ["hypothesis details", "view hypothesis", "show hypothesis"],
                "update_hypothesis": ["change hypothesis", "modify hypothesis", "update hypothesis"],
                "create_protocol": ["new protocol", "create protocol", "design experiment", "experiment protocol"],
                "list_protocols": ["show protocols", "all protocols", "view protocols", "list protocols"],
                "get_protocol": ["protocol details", "view protocol", "show protocol"],
                "create_experiment": ["new experiment", "create experiment", "set up experiment"],
                "list_experiments": ["show experiments", "all experiments", "view experiments", "list experiments"],
                "record_observation": ["add observation", "record data", "log result", "add result", "record observation"],
                "list_observations": ["show observations", "view data", "experiment data", "list observations"],
                "compute_statistics": ["analyze results", "compute statistics", "statistical analysis", "data analysis"],
                "create_publication_draft": ["draft paper", "publication draft", "create paper", "write up"]
            }
            task_patterns.update(research_patterns)

        # Normalize task description
        task = task_description.lower()

        # Find matching tools
        matches = []
        for tool, patterns in task_patterns.items():
            for pattern in patterns:
                if pattern in task:
                    matches.append((tool, tools.get(tool, "No description available")))

        # If no matches, suggest based on common actions
        if not matches:
            # Check if task involves switching incarnations
            if "switch" in task.lower() or "change" in task.lower() or "mode" in task.lower():
                matches.append(("switch_incarnation", tools.get("switch_incarnation", "No description available")))
                matches.append(("list_incarnations", tools.get("list_incarnations", "No description available")))
            
            # Check if in research mode and task is research-related
            elif current_incarnation == IncarnationType.RESEARCH and ("hypothesis" in task.lower() or "experiment" in task.lower() or "research" in task.lower()):
                if "create" in task.lower() or "new" in task.lower():
                    if "hypothesis" in task.lower():
                        matches.append(("register_hypothesis", "Register a new scientific hypothesis"))
                    elif "experiment" in task.lower():
                        matches.append(("create_experiment", "Create a new experiment to test a hypothesis"))
                    elif "protocol" in task.lower():
                        matches.append(("create_protocol", "Create an experimental protocol"))
                elif "list" in task.lower() or "show" in task.lower() or "view" in task.lower():
                    matches.append(("list_hypotheses", "List scientific hypotheses"))
                    matches.append(("list_experiments", "List experiments"))
            else:
                # Default to guidance hub if no clear match
                matches.append(("get_guidance_hub", tools.get("get_guidance_hub", "No description available")))
                matches.append(("get_current_incarnation", tools.get("get_current_incarnation", "No description available")))

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
                elif tool == "register_hypothesis":
                    response += "\n  Example usage: `register_hypothesis(text=\"Higher caffeine intake leads to improved cognitive performance\", prior_probability=0.6)`\n"
                elif tool == "switch_incarnation":
                    response += "\n  Example usage: `switch_incarnation(incarnation_type=\"research_orchestration\")`\n"

        response += "\nFor full navigation help, try `get_guidance_hub()` to see all available options."

        # Add incarnation-specific hint if active
        if current_incarnation:
            if current_incarnation == IncarnationType.RESEARCH:
                response += f"\n\nYou are currently in the **{current_incarnation.value}** incarnation, which provides tools for scientific workflow management."
            else:
                response += f"\n\nYou are currently in the **{current_incarnation.value}** incarnation."
        else:
            response += "\n\nNo incarnation is currently active. Use `switch_incarnation()` to activate one."

        return [types.TextContent(type="text", text=response)]

    async def get_guidance_hub(self) -> List[types.TextContent]:
        """Get the AI Guidance Hub content, which serves as the central entry point for navigation."""
        # Get the current incarnation
        current_incarnation = self.current_incarnation
        
        # If an incarnation is active, use its guidance hub
        if current_incarnation:
            return await current_incarnation.get_guidance_hub()
        
        # Otherwise, use the default guidance hub
        query = """
        MATCH (hub:AiGuidanceHub {id: 'main_hub'})
        RETURN hub.description AS description
        """

        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_read(self._read_query, query, {})
                results = json.loads(results_json)

                if results and len(results) > 0:
                    # Add incarnation information to the hub content
                    hub_content = results[0]["description"]
                    
                    # Add information about available incarnations
                    incarnation_info = "\n\n## Available Incarnations\n\n"
                    incarnation_info += "This system supports multiple incarnations with different functionalities:\n\n"
                    
                    incarnation_info += "1. **coding** - Original code workflow management\n"
                    incarnation_info += "2. **research_orchestration** - Scientific research management platform\n"
                    incarnation_info += "3. **decision_support** - Decision analysis and evidence tracking\n"
                    
                    incarnation_info += "\nUse `switch_incarnation(incarnation_type=\"...\")` to switch to a different incarnation."
                    
                    return [types.TextContent(type="text", text=hub_content + incarnation_info)]
                else:
                    # If hub doesn't exist, create it with default content
                    return await self._create_default_hub()
        except Exception as e:
            logger.error(f"Error retrieving guidance hub: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

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

                # Add current incarnation information
                current_incarnation = await self.get_current_incarnation_type()
                incarnation_info = "None" if current_incarnation is None else current_incarnation.value

                result = {
                    "connection": "Connected to Neo4j database",
                    "database": self.database,
                    "read_access": True,
                    "write_access": write_access,
                    "write_message": write_message,
                    "server_info": json.loads(info_result) if info_result else "N/A",
                    "current_incarnation": incarnation_info
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
            
    async def write_neo4j_cypher(
        self,
        query: str = Field(..., description="Cypher query to execute (CREATE, DELETE, MERGE, etc.)"),
        params: Optional[Dict[str, Any]] = Field(None, description="Query parameters")
    ) -> List[types.TextContent]:
        """Execute a WRITE Cypher query (for creating/updating data)."""
        params = params or {}
        
        # Check if this is actually a write query
        if not self.is_write_query(query):
            return [types.TextContent(
                type="text",
                text="This does not appear to be a write query. Use run_custom_query() for read operations."
            )]
            
        # Analyze query syntax for common errors
        is_valid, message = self.analyze_cypher_syntax(query)
        if not is_valid:
            return [types.TextContent(type="text", text=message)]
            
        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.execute_write(self._write, query, params)
                
                # Format a summary of what happened
                response = f"Query executed successfully.\n\n"
                response += f"Nodes created: {result.counters.nodes_created}\n"
                response += f"Relationships created: {result.counters.relationships_created}\n"
                response += f"Properties set: {result.counters.properties_set}\n"
                response += f"Nodes deleted: {result.counters.nodes_deleted}\n"
                response += f"Relationships deleted: {result.counters.relationships_deleted}\n"
                
                return [types.TextContent(type="text", text=response)]
        except Exception as e:
            logger.error(f"Error executing write query: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def _create_default_hub(self) -> List[types.TextContent]:
        """Create a default guidance hub if none exists."""
        default_description = """
# NeoCoder Neo4j-Guided AI Workflow

Welcome! This system uses a Neo4j knowledge graph to guide AI coding assistance and other workflows. The system supports multiple "incarnations" with different functionalities.

## Core Functionality

1. **Coding Workflow** (Original incarnation)
   - Follow structured templates for code modification
   - Access project information and history
   - Record successful workflow executions

2. **Research Orchestration** (Alternate incarnation)
   - Manage scientific hypotheses and experiments
   - Track experimental protocols and observations
   - Analyze results and generate publication drafts

3. **Decision Support** (Alternate incarnation)
   - Create and evaluate decision alternatives
   - Attach evidence to decisions
   - Track stakeholder inputs

## Getting Started

- To switch incarnations, use `switch_incarnation(incarnation_type="...")` 
- To list available incarnations, use `list_incarnations()`
- To get specific tool suggestions, use `suggest_tool(task_description="...")`
- To check database connection status, use `check_connection()`

Each incarnation has its own set of specialized tools alongside the core Neo4j interaction capabilities.
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

    def run(self, transport: str = "stdio"):
        """Run the MCP server."""
        self.mcp.run(transport=transport)


def create_server(db_url: str, username: str, password: str, database: str = "neo4j") -> Neo4jWorkflowServer:
    """Create and return a Neo4jWorkflowServer instance."""
    logger.info(f"Creating Neo4j driver with URL: {db_url}, username: {username}, database: {database}")
    driver = AsyncGraphDatabase.driver(db_url, auth=(username, password))
    
    # Set environment variables for init_db to use
    os.environ["NEO4J_URL"] = db_url
    os.environ["NEO4J_USERNAME"] = username
    os.environ["NEO4J_PASSWORD"] = password
    os.environ["NEO4J_DATABASE"] = database
    
    return Neo4jWorkflowServer(driver, database)


def main():
    """Main entry point for the MCP server."""
    db_url = os.environ.get("NEO4J_URL", "bolt://localhost:7687")
    username = os.environ.get("NEO4J_USERNAME", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "password")
    database = os.environ.get("NEO4J_DATABASE", "neo4j")

    logger.info(f"Starting NeoCoder MCP Server, connecting to {db_url}")

    server = create_server(db_url, username, password, database)
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
