"""
Neo4j-Guided AI Workflow Server with Polymorphic Incarnation Support

This server provides a bridge between AI assistants and a Neo4j knowledge graph,
supporting multiple incarnations (operational modes) such as:
- Coding workflows
- Research orchestration
- Decision support
- Data analysis
- Knowledge graph management

Each incarnation has specialized tools while sharing the core Neo4j infrastructure.
"""

import asyncio
import json
import logging
import os
import sys
import traceback
from typing import Any, Dict, List, Optional, TypeVar, Awaitable

import mcp.types as types
from mcp.server.fastmcp import FastMCP
from neo4j import AsyncDriver, AsyncGraphDatabase, AsyncTransaction, AsyncManagedTransaction
import neo4j
from pydantic import Field

# Import mixins and core functionality
from .action_templates import ActionTemplateMixin
from .cypher_snippets import CypherSnippetMixin
from .event_loop_manager import initialize_main_loop, safe_neo4j_session
from .init_db import init_db
from .polymorphic_adapter import PolymorphicAdapterMixin
from .tool_proposals import ToolProposalMixin

# Import process management for cleanup
from .process_manager import (
    register_cleanup_handlers,
    track_driver,
    untrack_driver,
    # track_session,
    # untrack_session, # handled by safe_neo4j_session
    track_background_task,
    cleanup_processes_sync,
    get_cleanup_status
)

# Configure logging to stderr for MCP servers
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("mcp_neocoder")

# Type definitions for function return handling
T = TypeVar('T')
def async_to_sync(func: Awaitable[T]) -> T:
    """Run an async function in a synchronous context."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(func)

class Neo4jWorkflowServer(PolymorphicAdapterMixin, CypherSnippetMixin, ToolProposalMixin, ActionTemplateMixin):
    # Qdrant client for vector search (optional, injected at startup)
    qdrant_client: Optional[Any] = None
    """Server for Neo4j-guided AI workflow with polymorphic incarnation support."""

    def __init__(self, driver: AsyncDriver, database: str = "neo4j", loop: Optional[asyncio.AbstractEventLoop] = None, *args: Any, **kwargs: Any):
        """Initialize the workflow server with Neo4j connection."""
        # CRITICAL: Register cleanup handlers first
        register_cleanup_handlers()
        logger.info("Cleanup handlers registered")

        # Track the driver for cleanup
        track_driver(driver)

        # Use the provided loop or initialize a new one
        self.loop: asyncio.AbstractEventLoop = loop if loop is not None else initialize_main_loop()

        # Store connection info
        self.driver: AsyncDriver = driver
        self.database = database if database is not None else "neo4j"

        # Initialize parent classes with required parameters
        # CypherSnippetMixin requires database and driver
        super().__init__(driver=driver, database=database, *args, **kwargs)

        # Initialize FastMCP server
        self.mcp: FastMCP = FastMCP("mcp-neocoder", dependencies=["neo4j", "pydantic"])

        # Initialize the base attributes
        self.incarnation_registry: Dict[str, Any] = {}
        self.current_incarnation: Optional[Any] = None

        # Add initialization event for synchronization
        self.initialized_event: asyncio.Event = asyncio.Event()

        # Register basic protocol handlers first to ensure responsiveness
        task = asyncio.create_task(self._register_basic_handlers())
        track_background_task(task)
        logger.info("Basic protocol handlers registered")

        # Start full initialization in a separate task to avoid blocking
        # This allows the server to respond to basic requests while
        # initialization is in progress
        init_task = asyncio.create_task(self._initialize_async())
        track_background_task(init_task)

    def __del__(self):
        """Destructor to ensure cleanup when server instance is destroyed."""
        try:
            if hasattr(self, 'driver'):
                untrack_driver(self.driver)
                logger.debug("Untracked driver in destructor")
        except Exception as e:
            logger.debug(f"Error in destructor: {e}")

    async def cleanup(self):
        """Explicit cleanup method for the server."""
        logger.info("Starting server cleanup...")
        try:
            # Stop any running background initialization
            if hasattr(self, 'initialized_event'):
                self.initialized_event.set()

            # Cleanup tracked driver
            if hasattr(self, 'driver'):
                untrack_driver(self.driver)

            logger.info("Server cleanup completed")
        except Exception as e:
            logger.error(f"Error during server cleanup: {e}")

    async def get_cleanup_status(self) -> List[types.TextContent]:
        """Get current cleanup and resource status for monitoring."""
        try:
            status = get_cleanup_status()

            response = "# Resource Management Status\n\n"
            response += f"- **Running Processes**: {status['running_processes']}\n"
            response += f"- **Background Tasks**: {status['background_tasks']}\n"
            response += f"- **Active Drivers**: {status['active_drivers']}\n"
            response += f"- **Active Sessions**: {status['active_sessions']}\n"
            response += f"- **Cleanup Registered**: {status['cleanup_registered']}\n"

            if status['process_ids']:
                response += f"\n**Tracked Process IDs**: {', '.join(status['process_ids'])}\n"

            # Add server-specific info
            response += "\n## Server Status\n"
            response += f"- **Initialized**: {self.initialized_event.is_set() if hasattr(self, 'initialized_event') else 'Unknown'}\n"
            response += f"- **Database**: {self.database}\n"

            if hasattr(self, 'incarnation_registry'):
                response += f"- **Incarnations Loaded**: {len(self.incarnation_registry)}\n"

            return [types.TextContent(type="text", text=response)]

        except Exception as e:
            logger.error(f"Error getting cleanup status: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def _initialize_async(self):
        """Execute the complete initialization sequence asynchronously."""
        try:
            # 1. Run async database initialization
            db_init_success = await self._initialize_database()
            if not db_init_success:
                logger.warning("Database initialization failed, some features may not work")
            else:
                logger.info("Database initialization completed successfully")

            # 3. Register core tools that don't depend on incarnations
            self._register_core_tools()
            logger.info("Core tools registered")

            # 4. Load incarnations (non-async component)
            self._load_incarnations()
            logger.info("Incarnations loaded")

            # 5. Register incarnation-specific tools (async)
            tool_count = await self._register_all_incarnation_tools()
            logger.info(f"Registered {tool_count} tools from all incarnations")

            # Set the initialized event to signal completion
            self.initialized_event.set()
            logger.info("Server initialization completed successfully")
        except Exception as e:
            logger.error(f"Error during initialization: {str(e)}")
            logger.debug(f"Initialization error details: {traceback.format_exc()}")
            logger.info("Server will continue with limited functionality")

    # _initialize method removed since we now use async initialization

    async def _initialize_database(self) -> bool:
        """Check database initialization status and initialize if needed.

        Returns:
            bool: True if initialization was successful
        """
        logger.info("Checking database initialization status")

        try:
            # Check three key indicators of proper initialization:
            # 1. Main guidance hub exists
            # 2. Incarnation hubs exist
            # 3. Action templates exist

            initialized = await self._check_database_initialized()

            if not initialized:
                logger.info("Database needs initialization, running setup")
                await init_db()
                logger.info("Database initialization completed")
                return True
            else:
                logger.info("Database already initialized")
                return True

        except Exception as e:
            logger.error(f"Database initialization check failed: {str(e)}")
            logger.debug(f"Database initialization error details: {traceback.format_exc()}")

            # Attempt recovery by running initialization anyway
            try:
                logger.info("Attempting database initialization after error")
                await init_db()
                logger.info("Database initialization successful after error recovery")
                return True
            except Exception as recovery_err:
                logger.error(f"Database initialization failed during recovery: {str(recovery_err)}")
                return False

    async def _check_database_initialized(self) -> bool:
        """Check if the database has been properly initialized.

        Returns:
            bool: True if all required components exist
        """

        try:
            async with safe_neo4j_session(self.driver, self.database or "neo4j") as session:
                # 1. Check if main hub exists
                hub_exists = await self._check_component_exists(
                    session,
                    "MATCH (hub:AiGuidanceHub {id: 'main_hub'}) RETURN count(hub) > 0 as exists"
                )

                if not hub_exists:
                    return False

                # 2. Check if incarnation hubs exist
                inc_hubs_exist = await self._check_component_exists(
                    session,
                    """
                    MATCH (hub:AiGuidanceHub {id: 'main_hub'})
                    OPTIONAL MATCH (hub)-[:HAS_INCARNATION]->(inc:AiGuidanceHub)
                    RETURN count(inc) >= 3 as exists
                    """
                )

                if not inc_hubs_exist:
                    return False

                # 3. Check if action templates exist
                templates_exist = await self._check_component_exists(
                    session,
                    "MATCH (t:ActionTemplate) RETURN count(t) > 0 as exists"
                )

                return templates_exist

        except Exception as e:
            logger.error(f"Error checking database initialization: {str(e)}")
            return False

    async def _check_component_exists(self, session, query: str) -> bool:
        """Execute a boolean check query and return the result.

        Args:
            session: Neo4j session
            query: Cypher query that returns a single boolean 'exists' value

        Returns:
            bool: Whether the component exists
        """
        try:
            result = await session.execute_read(
                lambda tx: self._execute_boolean_query(tx, query, {})
            )
            return result
        except Exception as e:
            logger.debug(f"Component check failed: {str(e)}")
            return False

    async def _execute_boolean_query(self, tx: AsyncTransaction, query: str, params: dict) -> bool:
        """Execute a query that returns a boolean result.

        Args:
            tx: Neo4j transaction
            query: Cypher query
            params: Query parameters

        Returns:
            bool: Query result
        """
        from typing import cast, LiteralString

        result = await tx.run(cast(LiteralString, query), params)
        records = await result.values()

        if not records or not records[0]:
            return False

        return bool(records[0][0])

    def _register_core_tools(self):
        """Register all core tools with the ToolRegistry.

        Core tools are those that don't depend on specific incarnations.
        """
        from .tool_registry import registry as tool_registry

        # Register tools with the ToolRegistry instead of directly with MCP
        # This prevents duplicate registration

        # Navigation tools
        navigation_tools = [
            self.get_guidance_hub,
            self.list_action_templates,
            self.get_action_template,
            self.get_best_practices,
            self.suggest_tool
        ]
        for tool in navigation_tools:
            tool_registry.register_tool(tool, "navigation")

        # Project tools
        project_tools = [
            self.get_project,
            self.list_projects
        ]
        for tool in project_tools:
            tool_registry.register_tool(tool, "project")

        # Workflow tools
        workflow_tools = [
            self.log_workflow_execution,
            self.get_workflow_history,
            self.add_template_feedback
        ]
        for tool in workflow_tools:
            tool_registry.register_tool(tool, "workflow")

        # Query tools
        query_tools = [
            self.run_custom_query,
            self.write_neo4j_cypher,
            self.check_connection
        ]
        for tool in query_tools:
            tool_registry.register_tool(tool, "query")

        # Cypher toolkit tools
        cypher_tools = [
            self.list_cypher_snippets,
            self.get_cypher_snippet,
            self.search_cypher_snippets,
            self.create_cypher_snippet,
            self.update_cypher_snippet,
            self.delete_cypher_snippet,
            self.get_cypher_tags
        ]
        for tool in cypher_tools:
            tool_registry.register_tool(tool, "cypher")

        # Tool proposal tools
        proposal_tools = [
            self.propose_tool,
            self.request_tool,
            self.get_tool_proposal,
            self.get_tool_request,
            self.list_tool_proposals,
            self.list_tool_requests
        ]
        for tool in proposal_tools:
            tool_registry.register_tool(tool, "proposal")

        # Incarnation management tools
        incarnation_tools = [
            self.get_current_incarnation,
            self.list_incarnations,
            self.switch_incarnation
        ]
        for tool in incarnation_tools:
            tool_registry.register_tool(tool, "incarnation")

        # System monitoring tools
        monitoring_tools = [
            self.get_cleanup_status
        ]
        for tool in monitoring_tools:
            tool_registry.register_tool(tool, "monitoring")

        logger.info("Registered all core tools with ToolRegistry")

    def _load_incarnations(self):
        """Discover and load all available incarnations."""
        # Import the registry (deferred to avoid circular imports)
        from .incarnation_registry import registry as global_registry
        import importlib
        import inspect

        # Force a re-discovery to ensure we get all classes
        logger.info("Discovering available incarnation classes")
        global_registry.discover()

        # If incarnations is empty, try alternative discovery methods
        if not global_registry.incarnations:
            logger.warning("No incarnations found via standard discovery. Trying alternative discovery methods.")

            # Try to find incarnations directly from files
            direct_incarnations = global_registry.discover_incarnations()
            if direct_incarnations:
                logger.info(f"Found {len(direct_incarnations)} incarnations through filesystem scan")

                # Manually load each incarnation file
                for inc_type in direct_incarnations:
                    try:
                        logger.info(f"Manually loading incarnation module: {inc_type}")
                        module_name = f"{inc_type}_incarnation"
                        full_module_path = f"mcp_neocoder.incarnations.{module_name}"

                        # Force import of the module
                        try:
                            module = importlib.import_module(full_module_path)

                            # Find incarnation class in the module
                            for name, obj in inspect.getmembers(module):
                                if (inspect.isclass(obj) and
                                    obj.__module__ == full_module_path and
                                    name.endswith('Incarnation')):

                                    # Set the name attribute if not present
                                    if not hasattr(obj, 'name'):
                                        logger.info(f"Setting name attribute for {name} to {inc_type}")
                                        obj.name = inc_type

                                    # Register the class
                                    global_registry.register(obj)
                                    logger.info(f"Manually registered incarnation: {inc_type} ({name})")
                        except ImportError as ie:
                            logger.error(f"Could not import module {full_module_path}: {ie}")
                    except Exception as e:
                        logger.error(f"Error manually loading {inc_type} incarnation: {e}")
                        logger.error(traceback.format_exc())

        # Register discovered incarnations with this server
        incarnation_count = 0
        logger.info(f"Registering {len(global_registry.incarnations)} incarnations with server")

        for name, inc_class in list(global_registry.incarnations.items()):
            try:
                # Handle both string and enum names
                name_str = name.value if hasattr(name, 'value') and not isinstance(name, str) else str(name)

                logger.info(f"Attempting to register incarnation: {name_str} ({inc_class.__name__})")
                self.register_incarnation(name_str, inc_class)
                logger.info(f"Registered incarnation: {name_str} ({inc_class.__name__})")
                incarnation_count += 1

                # Create and store an instance for later use
                try:
                    # Ensure database is never None by providing a default value
                    instance = inc_class(self.driver, self.database or "neo4j")
                    logger.info(f"Created instance of {inc_class.__name__}")

                    # Store in the registry for later use
                    global_registry.instances[name_str] = instance

                    # Don't register tools here - they will be registered via ToolRegistry
                    # in _register_all_incarnation_tools to avoid duplicates
                    tool_methods = instance.list_tool_methods() if hasattr(instance, 'list_tool_methods') else []
                    logger.info(f"Found {len(tool_methods)} tool methods in {name_str} (will register later)")

                except Exception as inst_err:
                    logger.error(f"Failed to create instance of {inc_class.__name__}: {inst_err}")
            except Exception as e:
                logger.error(f"Failed to register incarnation {name}: {str(e)}")
                logger.error(traceback.format_exc())

        logger.info(f"Loaded {incarnation_count} incarnations successfully")

        # If no incarnations were loaded, log a clear error
        if incarnation_count == 0:
            logger.error("NO INCARNATIONS WERE LOADED. This is a critical failure.")
            logger.error("Check the incarnations directory and make sure incarnation classes are properly defined.")
    async def _register_basic_handlers(self):
        """Register handlers for basic MCP protocol requests to prevent timeouts."""
        # Define the basic handlers
        async def empty_list_handler():
            """Return empty list for protocol handlers."""
            return []

        async def default_guidance_hub_handler():
            """Return basic guidance hub content in case database is not available."""
            content = """
# NeoCoder Neo4j-Guided AI Workflow

Welcome! This system is still initializing. Basic commands available:

- `check_connection()` - Verify database connection
- `list_incarnations()` - List available operational modes
- `switch_incarnation(incarnation_type="...")` - Change operational mode

Please wait a moment for full initialization to complete or check connection status.
"""
            return [types.TextContent(type="text", text=content)]

        # Try to set the handlers with several fallback mechanisms
        try:
            # First try to set handlers with attribute assignment
            try:
                # Set basic handlers for list endpoints
                if hasattr(self.mcp, 'list_prompts'):
                    async def list_prompts_handler():
                        return []
                    self.mcp.add_tool(list_prompts_handler, "list_prompts")

                if hasattr(self.mcp, 'list_resources'):
                    async def list_resources_handler():
                        return []
                    self.mcp.add_tool(list_resources_handler, "list_resources")

                # Also register a default guidance hub handler as a fallback
                if hasattr(self.mcp, 'add_tool'):
                    # Create a wrapper function that matches the tool signature
                    async def guidance_hub_wrapper():
                        return await default_guidance_hub_handler()

                    # Only add this if get_guidance_hub isn't working yet
                    self.mcp.add_tool(guidance_hub_wrapper, "get_guidance_hub_initializing")

                logger.info("Registered basic protocol handlers via direct attribute assignment")
            except Exception as attr_err:
                logger.warning(f"Could not set handlers via attributes: {attr_err}")

                # Try alternative method - using the decorator interface if available
                if hasattr(self.mcp, 'list_prompts'):
                    async def list_prompts_handler():
                        return []
                    self.mcp.add_tool(list_prompts_handler, "list_prompts")

                    async def list_resources_handler():
                        return []
                    self.mcp.add_tool(list_resources_handler, "list_resources")

                    logger.info("Registered basic protocol handlers via add_tool")
                else:
                    logger.warning("Could not register basic handlers via add_tool")

            # Error suppression handler has been removed as part of refactoring
            # We now handle Neo4j transaction scope issues properly in query methods

        except Exception as e:
            # Last resort error handling
            logger.error(f"Failed to register basic handlers: {e}")
            logger.info("Server will continue but may have reduced functionality")



    async def _register_all_incarnation_tools(self):
        """Register tools from all incarnations through the ToolRegistry."""
        logger.info("Registering tools from all incarnations...")

        if not self.incarnation_registry:
            logger.warning("No incarnations registered, skipping tool registration")
            return 0

        # Import the registries
        from .incarnation_registry import registry as global_registry
        from .tool_registry import registry as tool_registry

        # Ensure incarnations are discovered
        if not self.incarnation_registry:
            logger.warning("incarnation_registry is empty, trying to discover incarnations automatically")
            global_registry.discover()

        # Clear any previously registered MCP tools to start fresh
        tool_registry._mcp_registered_tools.clear()

        # First register core tools with MCP
        logger.info("Registering core tools with MCP server...")
        core_count = tool_registry.register_tools_with_server(self)
        logger.info(f"Registered {core_count} core tools with MCP server")

        # Process each incarnation
        total_incarnation_tools = 0
        logger.info(f"Processing {len(self.incarnation_registry)} incarnation types")

        for incarnation_type, incarnation_class in list(self.incarnation_registry.items()):
            try:
                logger.info(f"Processing incarnation: {incarnation_type}")

                # Get or create an instance
                instance = global_registry.get_instance(incarnation_type, self.driver, self.database or "neo4j")

                if not instance:
                    logger.info(f"Creating new instance of {incarnation_type} incarnation")
                    try:
                        instance = incarnation_class(self.driver, self.database)
                        # Store the instance for future use
                        global_registry.instances[incarnation_type] = instance
                    except Exception as instance_err:
                        logger.error(f"Failed to create instance of {incarnation_class.__name__}: {instance_err}")
                        continue

                # Register incarnation tools through the ToolRegistry
                if instance:
                    # Use the ToolRegistry's method to register incarnation tools
                    count = tool_registry.register_incarnation_tools(instance, self)
                    total_incarnation_tools += count
                    logger.info(f"Registered {count} tools from {incarnation_type} incarnation")
                else:
                    logger.error(f"No instance available for {incarnation_type}")

            except Exception as e:
                logger.error(f"Error processing incarnation {incarnation_type}: {e}")
                logger.error(traceback.format_exc())

        # Log final summary
        total_registered = core_count + total_incarnation_tools
        logger.info(f"Tool registration complete. Total tools registered: {total_registered}")
        logger.info(f"  - Core tools: {core_count}")
        logger.info(f"  - Incarnation tools: {total_incarnation_tools}")

        return total_registered

    async def get_current_incarnation(self) -> List[types.TextContent]:
        """Get the currently active incarnation type."""
        try:
            current = await self.get_current_incarnation_type()
            if current:
                return [types.TextContent(
                    type="text",
                    text=f"Currently using '{current}' incarnation"
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
                # Get the type value - handle both string and enum cases
                type_value = inc_type
                if hasattr(inc_type, 'value') and not isinstance(inc_type, str):
                    type_value = inc_type.value

                incarnations.append({
                    "type": type_value,
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
                    text += f"\nCurrently using: **{current}**"
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
        incarnation_type: str = Field(..., description="Type of incarnation to switch to (coding, research, decision, data_analysis, knowledge_graph)"),
    ) -> List[types.TextContent]:
        """Switch the server to a different incarnation."""
        try:
            # Check if the incarnation type exists in the registry
            available_types = list(self.incarnation_registry.keys())

            if incarnation_type not in available_types:
                available_types_str = ", ".join(available_types)
                return [types.TextContent(
                    type="text",
                    text=f"Unknown incarnation type: '{incarnation_type}'. Available types: {available_types_str}"
                )]

            # Set the incarnation using the string directly
            await self.set_incarnation(incarnation_type)
            return [types.TextContent(
                type="text",
                text=f"Successfully switched to '{incarnation_type}' incarnation"
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

        # Add research-specific patterns if in research mode- I think this may be redundant and should come from the incarnation itself.
        if current_incarnation == "research":
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
            elif current_incarnation == "research" and ("hypothesis" in task.lower() or "experiment" in task.lower() or "research" in task.lower()):
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
            if current_incarnation == "research":
                response += f"\n\nYou are currently in the **{current_incarnation}** incarnation, which provides tools for scientific workflow management."
            else:
                response += f"\n\nYou are currently in the **{current_incarnation}** incarnation."
        else:
            response += "\n\nNo incarnation is currently active. Use `switch_incarnation()` to activate one."

        return [types.TextContent(type="text", text=response)]

    async def get_guidance_hub(self) -> List[types.TextContent]:
        """Get the AI Guidance Hub content, which serves as the central entry point for navigation.

        The guidance hub provides the main entry point for AI assistants to understand
        what capabilities are available and how to navigate the system.

        If an incarnation is active, its specialized hub will be returned instead.

        Returns:
            MCP response containing the hub content
        """
        # Import the safe session manager
        from .event_loop_manager import safe_neo4j_session

        # Fallback description in case of any database issues
        fallback_hub_description = """
# NeoCoder Neo4j-Guided AI Workflow

Welcome! This system uses a Neo4j knowledge graph to guide AI coding assistance and other workflows.

## Key Commands
- `check_connection()` - Verify database connection
- `list_incarnations()` - View available operational modes
- `switch_incarnation(incarnation_type="...")` - Change operational mode
- `get_action_template(keyword="...")` - Get workflow instructions

This is the default guidance hub. Use the commands above to explore the system's capabilities.
"""

        # 1. Try to get incarnation-specific hub if an incarnation is active
        if hasattr(self, 'current_incarnation') and self.current_incarnation:
            try:
                logger.info(f"Getting guidance hub from active incarnation: {self.current_incarnation.name}")
                result = await self.current_incarnation.get_guidance_hub()
                if result and isinstance(result, list) and len(result) > 0:
                    return result
                logger.warning("Empty result from incarnation hub, falling back to main hub")
            except Exception as e:
                logger.error(f"Error getting hub from incarnation {self.current_incarnation.name}: {str(e)}")
                logger.info("Falling back to main hub")

        # 2. Get the main hub with event loop safe session handling
        logger.info("Getting main guidance hub")

        try:
            # Use the safe session manager to avoid event loop issues
            async with safe_neo4j_session(self.driver, self.database or "neo4j") as session:
                query = """
                MATCH (hub:AiGuidanceHub {id: 'main_hub'})
                RETURN hub.description AS description
                """

                # Use a direct transaction to avoid scope issues
                async def read_hub_description(tx):
                    result = await tx.run(query)
                    values = await result.values()
                    return values

                values = await session.execute_read(read_hub_description)

                if values and len(values) > 0 and values[0][0]:
                    # Hub exists, get its content
                    hub_content = values[0][0]

                    # Enhance with incarnation information
                    try:
                        hub_content = await self._enhance_hub_with_incarnation_info(hub_content)
                    except Exception as e:
                        logger.error(f"Error enhancing hub content: {str(e)}")
                        # Continue with unenhanced content

                    return [types.TextContent(type="text", text=hub_content)]
                else:
                    # Hub doesn't exist or no description, create it
                    logger.info("Main hub not found or has no description, creating default hub")
                    return await self._create_default_hub()

        except Exception as e:
            # Handle database errors gracefully
            logger.error(f"Error getting main guidance hub: {str(e)}")
            logger.error(f"Error details: {traceback.format_exc()}")

            # Return fallback content instead of failing
            logger.info("Returning fallback guidance hub due to database error")
            return [types.TextContent(type="text", text=fallback_hub_description)]

    async def _enhance_hub_with_incarnation_info(self, hub_content: str) -> str:
        """Enhance hub content with up-to-date incarnation information.

        Args:
            hub_content: Original hub content

        Returns:
            Enhanced hub content with incarnation information
        """
        # Get incarnation information
        incarnation_types = []
        incarnation_descriptions = {}

        # Get incarnation types from registry if available
        if hasattr(self, 'incarnation_registry') and self.incarnation_registry:
            try:
                # Extract information from registry
                for inc_type, inc_class in self.incarnation_registry.items():
                    # Convert to string if it's an enum
                    inc_name = inc_type
                    if hasattr(inc_type, 'value') and not isinstance(inc_type, str):
                        inc_name = inc_type.value

                    incarnation_types.append(inc_name)

                    # Get description if available
                    if hasattr(inc_class, 'description'):
                        incarnation_descriptions[inc_name] = inc_class.description
                    else:
                        incarnation_descriptions[inc_name] = "Custom incarnation"
            except Exception as e:
                logger.error(f"Error getting incarnation info: {str(e)}")

        # Add incarnation info to hub content if we have any
        if incarnation_types:
            # Check if hub already has an incarnation section
            if "## Available Incarnations" in hub_content:
                # Find where the incarnation section starts and ends
                start = hub_content.find("## Available Incarnations")

                # Find the next section if any, or use the end of the content
                next_section = hub_content.find("##", start + 1)
                if next_section == -1:
                    next_section = len(hub_content)

                # Replace the existing incarnation section
                before = hub_content[:start]
                after = hub_content[next_section:]

                incarnation_info = "## Available Incarnations\n\n"
                incarnation_info += "| Type | Description |\n"
                incarnation_info += "| ---- | ----------- |\n"

                for inc_type in sorted(incarnation_types):
                    desc = incarnation_descriptions.get(inc_type, "Custom incarnation")
                    incarnation_info += f"| {inc_type} | {desc} |\n"

                # Include current incarnation information if available
                current = await self.get_current_incarnation_type()
                if current:
                    incarnation_info += f"\nCurrently using: **{current}**\n"
                else:
                    incarnation_info += "\nNo incarnation is currently active. Use `switch_incarnation()` to activate one.\n"

                # Add usage hint
                incarnation_info += "\nUse `switch_incarnation(incarnation_type=\"...\")` to switch incarnations.\n\n"

                hub_content = before + incarnation_info + after
            else:
                # Add a new incarnation section at the end
                incarnation_info = "\n\n## Available Incarnations\n\n"
                incarnation_info += "| Type | Description |\n"
                incarnation_info += "| ---- | ----------- |\n"

                for inc_type in sorted(incarnation_types):
                    desc = incarnation_descriptions.get(inc_type, "Custom incarnation")
                    incarnation_info += f"| {inc_type} | {desc} |\n"

                # Include current incarnation information if available
                current = await self.get_current_incarnation_type()
                if current:
                    incarnation_info += f"\nCurrently using: **{current}**\n"
                else:
                    incarnation_info += "\nNo incarnation is currently active. Use `switch_incarnation()` to activate one.\n"

                # Add usage hint
                incarnation_info += "\nUse `switch_incarnation(incarnation_type=\"...\")` to switch incarnations."

                hub_content += incarnation_info

        return hub_content

    async def check_connection(self) -> List[types.TextContent]:
        """Check the Neo4j connection status and database access permissions."""
        from .event_loop_manager import safe_neo4j_session

        result = {
            "connection": "Not Connected",
            "database": self.database,
            "read_access": False,
            "write_access": False,
            "neo4j_url": os.environ.get("NEO4J_URL", "bolt://localhost:7687"),
            "neo4j_username": os.environ.get("NEO4J_USERNAME", "neo4j"),
            "neo4j_password": os.environ.get("NEO4J_PASSWORD", "********"),
            "neo4j_database": os.environ.get("NEO4J_DATABASE", "neo4j"),
            "server_info": "Unknown",
            "current_incarnation": "Unknown",
            "error": None,
            "tools_registered": []
        }

        # Test connection by running basic queries with robust error handling
        try:
            # First test if driver is valid
            if not self.driver:
                raise RuntimeError("Driver is not initialized")

            # Test read access with a simple query using safe session manager
            async with safe_neo4j_session(self.driver, self.database or "neo4j") as session:
                try:
                    # Test read access
                    read_result = await session.run("RETURN 'Connection works' as status")
                    read_data = await read_result.data()
                    if read_data and read_data[0]["status"] == "Connection works":
                        result["read_access"] = True
                        logger.info("Read access verified")
                    else:
                        logger.warning("Read query returned unexpected result")
                except Exception as read_err:
                    logger.error(f"Read access test failed: {read_err}")
                    result["error"] = f"Read access test failed: {str(read_err)}"

                try:
                    # Test write access with a harmless write operation
                    write_result = await session.run(
                        "CREATE (t:TestNode {id: 'temp_test'}) "
                        "WITH t "
                        "DETACH DELETE t "
                        "RETURN count(t) as deleted"
                    )
                    write_data = await write_result.data()
                    if write_data and write_data[0]["deleted"] == 1:
                        result["write_access"] = True
                        logger.info("Write access verified")
                    else:
                        logger.warning("Write query returned unexpected result")
                except Exception as write_err:
                    logger.error(f"Write access test failed: {write_err}")
                    if not result["error"]:
                        result["error"] = f"Write access test failed: {str(write_err)}"

                # Get server info
                try:
                    info_result = await session.run(
                        "CALL dbms.components() YIELD name, versions RETURN name, versions[0] as version"
                    )
                    info_data = await info_result.data()
                    if info_data:
                        result["server_info"] = info_data
                        logger.info(f"Server info retrieved: {len(info_data)} components")
                except Exception as info_err:
                    logger.warning(f"Couldn't get server info: {info_err}")
                    # Don't set as primary error

            # If we got this far with at least read access, we're connected
            if result["read_access"]:
                result["connection"] = "Connected to Neo4j database"
                logger.info("Database connection verified")

            # Get current incarnation
            try:
                current_incarnation = await self.get_current_incarnation_type()
                if current_incarnation:
                    result["current_incarnation"] = current_incarnation
                    logger.info(f"Current incarnation: {current_incarnation}")

                # Get registered tool count for each incarnation
                if hasattr(self, 'incarnation_registry') and self.incarnation_registry:
                    # Collect tool status information
                    for inc_type, inc_class in self.incarnation_registry.items():
                        try:
                            # Get instance
                            from .incarnation_registry import registry as global_registry
                            instance = global_registry.get_instance(inc_type, self.driver, self.database or "neo4j")
                            if not instance:
                                continue

                            # Get tool methods
                            tools = instance.list_tool_methods()
                            if tools:
                                result["tools_registered"].append({
                                    "incarnation": inc_type,
                                    "tool_count": len(tools),
                                    "tools": tools[:5] + ["..."] if len(tools) > 5 else tools
                                })
                        except Exception as tool_err:
                            logger.warning(f"Error getting tool info for {inc_type}: {tool_err}")
            except Exception as inc_err:
                logger.warning(f"Error getting incarnation info: {inc_err}")

        except Exception as e:
            # Record the actual error for debugging
            logger.error(f"Connection check error: {e}")
            logger.error(f"Error details: {traceback.format_exc()}")
            result["error"] = str(e)

        # Format the response with enhanced detailed diagnostics
        response = "# Neo4j Connection Status\n\n"

        if result["read_access"] and result["write_access"]:
            response += "✅ **Connection Functioning**\n\n"
        elif result["read_access"]:
            response += "⚠️ **Partial Connection**\n\n"
            response += "Read operations work but write operations may fail.\n\n"
        else:
            response += "❌ **Connection Failed**\n\n"
            response += "Unable to connect to Neo4j database.\n\n"

        response += f"- **Connection:** {result['connection']}\n"
        response += f"- **Database:** {result['database']}\n"
        response += f"- **Read Access:** {result['read_access']}\n"
        response += f"- **Write Access:** {result['write_access']}\n"

        if isinstance(result["server_info"], list):
            server_info = ", ".join([f"{item['name']} {item['version']}" for item in result["server_info"]])
            response += f"- **Neo4j Server:** [{server_info}]\n"

        if result["current_incarnation"] != "Unknown":
            response += f"- **Current Incarnation:** {result['current_incarnation']}\n"

        # Add tools registered info
        if result["tools_registered"]:
            response += "\n## Registered Tools\n\n"
            for inc in result["tools_registered"]:
                response += f"- **{inc['incarnation']}**: {inc['tool_count']} tools\n"
                if inc['tool_count'] > 0:
                    sample_tools = ', '.join(inc['tools'])
                    response += f"  Sample tools: `{sample_tools}`\n"

        if result["error"]:
            response += f"\n## Error Details\n\n```\n{result['error']}\n```\n"
            response += "This error may help with troubleshooting database connection issues.\n"

        response += "\n## Connection Settings\n\n"
        response += f"- **URL:** {result['neo4j_url']}\n"
        response += f"- **Username:** {result['neo4j_username']}\n"
        response += f"- **Password:** {result['neo4j_password']}\n"
        response += f"- **Database:** {result['neo4j_database']}\n"

        # Add troubleshooting tips
        response += "\n## Troubleshooting Tips\n\n"

        if not result["read_access"]:
            response += "1. Verify Neo4j is running: `sudo systemctl status neo4j`\n"
            response += "2. Check connection settings in environment variables\n"
            response += "3. Try restarting Neo4j: `sudo systemctl restart neo4j`\n"
            response += "4. Check Neo4j logs: `sudo journalctl -u neo4j`\n"
        elif not result["write_access"]:
            response += "1. Check user permissions in Neo4j\n"
            response += "2. Verify database name is correct\n"
            response += "3. Check if the database is in read-only mode\n"
        else:
            response += "Everything looks good! If you're still experiencing issues:\n"
            response += "1. Try switching incarnation: `switch_incarnation(incarnation_type=\"...\")`\n"
            response += "2. Check available incarnations: `list_incarnations()`\n"
            response += "3. Restart the server to reload all components\n"

        return [types.TextContent(type="text", text=response)]


    async def _read_query(self, tx: AsyncManagedTransaction, query: str, params: dict) -> str:
        """Execute a read query and return results as JSON string.

        Args:
            tx: Neo4j transaction
            query: Cypher query to execute
            params: Query parameters

        Returns:
            JSON string representing the query results
        """
        try:
            from typing import cast, LiteralString
            raw_results = await tx.run(cast(LiteralString, query), params or {})
            eager_results = await raw_results.to_eager_result()
            return json.dumps([r.data() for r in eager_results.records], default=str)
        except Exception as e:
            logger.error(f"Error executing read query: {str(e)}")
            logger.debug(f"Failed query: {query}")
            logger.debug(f"Parameters: {params}")
            raise

    async def _write(self, tx: AsyncManagedTransaction, query: str, params: dict):
        """Execute a write query and return result summary.

        Args:
            tx: Neo4j transaction
            query: Cypher query to execute
            params: Query parameters

        Returns:
            Neo4j result summary
        """
        try:
            from typing import cast, LiteralString
            result = await tx.run(cast(LiteralString, query), params or {})
            return await result.consume()
        except Exception as e:
            logger.error(f"Error executing write query: {str(e)}")
            logger.debug(f"Failed query: {query}")
            logger.debug(f"Parameters: {params}")
            raise

    async def _safe_execute_read(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a read query with proper error handling and transaction management.

        This is a higher-level method that handles session creation and error handling.

        Args:
            query: Cypher query to execute
            params: Query parameters

        Returns:
            Query results as a list of dictionaries
        """
        from .event_loop_manager import safe_neo4j_session

        params = params or {}

        try:
            async with safe_neo4j_session(self.driver, self.database or "neo4j") as session:
                # Execute inside a read transaction
                result_json = await session.execute_read(
                    lambda tx: self._read_query(tx, query, params)  # type: ignore
                )

                # Parse the result safely
                try:
                    return json.loads(result_json)
                except json.JSONDecodeError:
                    logger.error("Failed to decode JSON result")
                    return []
        except Exception as e:
            logger.error(f"Error in safe read execution: {str(e)}")
            return []

    async def _safe_execute_write(self, query: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """Execute a write query with proper error handling and transaction management.

        This is a higher-level method that handles session creation and error handling.

        Args:
            query: Cypher query to execute
            params: Query parameters

        Returns:
            True if the operation succeeded, False otherwise
        """
        from .event_loop_manager import safe_neo4j_session

        params = params or {}

        try:
            async with safe_neo4j_session(self.driver, self.database or "neo4j") as session:
                # Execute inside a write transaction
                from typing import Callable
                await session.execute_write(
                    Callable[[neo4j.AsyncManagedTransaction], Awaitable[Any]](lambda tx: self._write(tx, query, params)) # type: ignore
                )
                return True
        except Exception as e:
            logger.error(f"Error in safe write execution: {str(e)}")
            return False

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
        from .event_loop_manager import safe_neo4j_session

        params = params or {}

        try:
            async with safe_neo4j_session(self.driver, self.database or "neo4j") as session:
                # Fixed: Use lambda directly without wrapping in Callable
                results_json = await session.execute_read(
                    lambda tx: self._read_query(tx, query, params)
                )
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
        from .event_loop_manager import safe_neo4j_session

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
            async with safe_neo4j_session(self.driver, self.database or "neo4j") as session:
                # Fixed: Use lambda directly without wrapping in Callable
                result = await session.execute_write(
                    lambda tx: self._write(tx, query, params)
                )

                # Format a summary of what happened
                response = "Query executed successfully.\n\n"
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
        """Create a default guidance hub if none exists.

        This creates the main hub node in Neo4j with default content that
        explains the system capabilities and provides navigation guidance.

        Returns:
            MCP response containing the hub content
        """
        from .event_loop_manager import safe_neo4j_session

        # Define the default hub content
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

4. **Knowledge Graph Management** (Specialized incarnation)
   - Create and manage entities with observations
   - Connect entities with typed relationships
   - Search and visualize knowledge structures

5. **Code Analysis** (Specialized incarnation)
   - Parse and analyze code structure
   - Track code complexity and quality metrics
   - Generate documentation from code analysis

## Getting Started

- To switch incarnations, use `switch_incarnation(incarnation_type="...")`
- To list available incarnations, use `list_incarnations()`
- To get specific tool suggestions, use `suggest_tool(task_description="...")`
- To check database connection status, use `check_connection()`

Each incarnation has its own set of specialized tools alongside the core Neo4j interaction capabilities.
"""

        try:
            # Try to create the hub node using safe session manager
            async with safe_neo4j_session(self.driver, self.database or "neo4j") as session:
                query = """
                CREATE (hub:AiGuidanceHub {id: 'main_hub', description: $description, created: datetime()})
                RETURN hub.description AS description
                """
                # Use a direct transaction to avoid scope issues
                async def create_hub(tx):
                    result = await tx.run(query, {"description": default_description})
                    values = await result.values()
                    return values

                values = await session.execute_write(create_hub)

                if values and len(values) > 0:
                    logger.info("Successfully created default guidance hub")
                    return [types.TextContent(type="text", text=default_description)]
                else:
                    error_message = "Created hub but couldn't verify result"
                    logger.warning(error_message)
                    return [types.TextContent(type="text", text=default_description)]

        except Exception as e:
            # If there was an error, try to return a helpful message
            error_message = f"Failed to create default guidance hub: {str(e)}"
            logger.error(error_message)
            logger.error(f"Error details: {traceback.format_exc()}")

            # Still try to return the content anyway to improve user experience
            return [types.TextContent(type="text", text=default_description)]

    def initialize_server(self):
        """Initialize the server properly without causing event loop issues.

        This is an alternative initialization method that can be used in scenarios
        where the standard initialization in __init__ is causing event loop problems.
        """
        try:
            # Initialize the polymorphic adapter
            from .polymorphic_adapter import PolymorphicAdapterMixin
            PolymorphicAdapterMixin.__init__(self)

            # Use the incarnation registry to discover and register all incarnations
            from .incarnation_registry import registry as global_registry

            # Discover all incarnations and ensure they're properly registered
            logger.info("Running discovery to find all incarnation classes")
            global_registry.discover()

            # Register discovered incarnations with this server
            for inc_type, inc_class in global_registry.incarnations.items():
                logger.info(f"Auto-registering incarnation {inc_type} ({inc_class.__name__})")
                self.register_incarnation(inc_type, inc_class)

            # Register core tools
            self._register_core_tools()

            # For async initialization, create a new event loop if needed
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # If no event loop in thread, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Run async initialization steps properly in the loop
            async def run_async_init_wrapper():
                """Wrap database initialization and tool registration in a single async function."""
                # Auto-initialize the database if needed
                await self._initialize_database()

                # Register tools from all incarnations
                tool_count = await self._register_all_incarnation_tools()
                logger.info(f"Registered {tool_count} tools from all incarnations")

                return tool_count

            # Run the async initialization in the event loop
            loop.run_until_complete(run_async_init_wrapper())

            return True
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            import traceback
            logger.error(traceback.format_exc())
            logger.info("Basic MCP handlers are still registered, so the server will respond to protocol requests")
            return False

    def run(self, transport: str = "stdio"):
        """Run the MCP server."""
        from typing import cast, Literal
        self.mcp.run(transport=cast(Literal["stdio", "sse"], transport))


def create_server(db_url: str, username: str, password: str, database: str = "neo4j") -> Neo4jWorkflowServer:
    """Create and initialize a Neo4jWorkflowServer instance.

    This factory function handles proper initialization of the event loop,
    Neo4j driver, and server components to ensure consistent behavior.

    Args:
        db_url: Neo4j connection URL
        username: Neo4j username
        password: Neo4j password
        database: Neo4j database name

    Returns:
        Initialized Neo4jWorkflowServer instance
    """
    try:
        # 1. Make sure we have a running event loop
        try:
            # Get existing event loop or create a new one
            loop = asyncio.get_event_loop()
            if not loop.is_running():
                logger.info("Using existing event loop")
        except RuntimeError:
            # No event loop exists in this thread, create a new one
            logger.info("Creating new event loop")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # 2. Initialize the event loop manager to ensure it's in sync
        from .event_loop_manager import initialize_main_loop
        loop = initialize_main_loop()
        logger.info("Initialized main event loop for Neo4j operations")

        # 3. Store connection parameters in environment variables for init_db
        os.environ["NEO4J_URL"] = db_url
        os.environ["NEO4J_USERNAME"] = username
        os.environ["NEO4J_PASSWORD"] = password
        os.environ["NEO4J_DATABASE"] = database

        # 4. Create the Neo4j driver
        logger.info(f"Creating Neo4j driver (URL: {db_url}, database: {database})")
        driver_config = {
            # Default to a more conservative connection pool size
            "max_connection_pool_size": int(os.environ.get("NEO4J_MAX_CONNECTIONS", "50")),
            # Allow driver to handle more request types concurrently
            "max_transaction_retry_time": 30.0,
            # More aggressive connection acquisition timeout
            "connection_acquisition_timeout": 60.0
        }

        # Only pass supported arguments to the driver
        driver = AsyncGraphDatabase.driver(
            db_url,
            auth=(username, password),
            max_connection_pool_size=driver_config["max_connection_pool_size"],
            max_transaction_retry_time=driver_config["max_transaction_retry_time"],
            connection_acquisition_timeout=driver_config["connection_acquisition_timeout"]
        )

        # Track the driver for cleanup (this will be done again in the server constructor)
        track_driver(driver)

        # 4.5. Qdrant integration: ensure Qdrant is available and get client
        try:
            from .qdrant_utils import get_qdrant_client
            qdrant_client = get_qdrant_client()
            logger.info("Qdrant client initialized successfully")
        except Exception as qdrant_err:
            logger.warning(f"Qdrant not available or failed to initialize: {qdrant_err}")
            qdrant_client = None

        # 5. Define an async function for all async operations
        async def async_server_setup():
            # 5.1 Verify the driver connection works
            try:
                async with safe_neo4j_session(driver, database) as session:
                    result = await session.run("RETURN 1 as n")
                    data = await result.data()
                    if not data or data[0]["n"] != 1:
                        raise RuntimeError("Driver verification failed: unexpected response")

                    logger.info("Neo4j driver connection verified successfully")
            except Exception as e:
                logger.error(f"Driver verification failed: {str(e)}")
                raise RuntimeError(f"Could not connect to Neo4j: {str(e)}")

            # 5.2 Create the server instance, passing qdrant_client if needed
            server = Neo4jWorkflowServer(driver, database, loop)
            # If your server or vector-enabled classes need the client, set it here:
            if qdrant_client is not None:
                try:
                    server.qdrant_client = qdrant_client
                except Exception as e:
                    logger.warning(f"Failed to set qdrant_client on server: {e}")
            logger.info("Neo4jWorkflowServer created successfully")

            # Wait for server to complete initialization
            logger.info("Waiting for server initialization to complete...")
            try:
                await asyncio.wait_for(server.initialized_event.wait(), timeout=60.0)
                logger.info("Server initialization complete")
            except asyncio.TimeoutError:
                logger.error("Server initialization timed out after 60 seconds")
                logger.warning("Continuing with potentially incomplete initialization")

            return server

        # 6. Run the async setup with proper error handling
        # SIMPLIFIED APPROACH: Always create server directly in current context
        # This avoids the complex event loop juggling that was causing Future conflicts
        try:
            current_loop = asyncio.get_running_loop()
            logger.info("Current event loop detected - creating server directly")
        except RuntimeError:
            # No running loop
            current_loop = None
            logger.info("No running event loop - will create server with async setup")

        if current_loop:
            # We're in a running event loop - create server directly
            # Let the server initialize itself asynchronously to avoid deadlocks
            logger.info("Creating server with direct initialization")
            
            # Note: Skip driver verification here since we're in a sync context
            # The server will verify the connection during its async initialization
            logger.info("Skipping sync driver verification - will be done during async init")

            # Create the server instance
            server = Neo4jWorkflowServer(driver, database, loop)
            if qdrant_client is not None:
                try:
                    server.qdrant_client = qdrant_client
                except Exception as e:
                    logger.warning(f"Failed to set qdrant_client on server: {e}")
            logger.info("Neo4jWorkflowServer created successfully")

            # Don't wait for initialization to complete here - let it happen asynchronously
            logger.info("Server created with async initialization in progress")
        else:
            # No running loop - safe to use run_until_complete
            logger.info("No running loop - using run_until_complete for setup")
            server = loop.run_until_complete(async_server_setup())

        return server

    except Exception as e:
        logger.error(f"Failed to create server: {str(e)}")
        logger.debug(f"Server creation error details: {traceback.format_exc()}")
        raise RuntimeError(f"Failed to create Neo4jWorkflowServer: {str(e)}")


def cleanup_zombie_instances():
    """Clean up any orphaned server processes.

    This function identifies and terminates any zombie server instances
    that might be left running from previous executions. This prevents
    port conflicts and resource leaks.

    Returns:
        int: Number of processes cleaned up
    """
    # Use the new process manager cleanup
    from .process_manager import cleanup_zombie_instances as cleanup_zombies
    return cleanup_zombies()

def main():
    """Main entry point for the MCP server.

    This function handles the complete server startup sequence:
    1. Environment setup and configuration loading
    2. Connection to Neo4j database
    3. Server initialization
    4. Server execution

    It includes proper error handling and logging at each stage.
    """
    server = None
    try:
        # 1. Initial setup - clean up zombie instances and load config
        logger.info("Starting NeoCoder Neo4j Workflow Server")
        cleanup_zombie_instances()

        # 2. Load configuration from .env file if available
        try:
            from dotenv import load_dotenv
            env_loaded = load_dotenv()
            if env_loaded:
                logger.info("Loaded environment variables from .env file")
        except ImportError:
            logger.info("dotenv package not installed, using environment variables directly")

        # 3. Set up logging based on environment configuration
        log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
        if hasattr(logging, log_level):
            logging.getLogger("mcp_neocoder").setLevel(getattr(logging, log_level))
            logger.info(f"Set log level to {log_level}")

        # 4. Get Neo4j connection parameters
        db_url = os.environ.get("NEO4J_URL", "bolt://localhost:7687")
        username = os.environ.get("NEO4J_USERNAME", "neo4j")
        password = os.environ.get("NEO4J_PASSWORD", "password")
        database = os.environ.get("NEO4J_DATABASE", "neo4j")

        logger.info(f"Neo4j connection: {db_url}, database: {database}")

        # 5. Create and start the server with correct event loop handling
        try:
            # Set up the event loop properly
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # No event loop exists in this thread, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Create the server, which automatically handles async initialization
            server = create_server(db_url, username, password, database)
            logger.info("Server created successfully, starting MCP transport")

            # 6. Run the server with the configured transport
            transport = os.environ.get("MCP_TRANSPORT", "stdio")

            # Run the server - this should block until termination
            server.run(transport=transport)

        except Exception as server_err:
            logger.error(f"Server creation or execution failed: {str(server_err)}")
            logger.debug(f"Error details: {traceback.format_exc()}")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Unhandled exception in main: {str(e)}")
        logger.debug(f"Error details: {traceback.format_exc()}")
        sys.exit(1)
    finally:
        # CRITICAL: Always cleanup resources
        logger.info("Performing final cleanup...")
        try:
            if server:
                # Cleanup the server instance
                loop = asyncio.get_event_loop()
                if not loop.is_closed():
                    loop.run_until_complete(server.cleanup())
        except Exception as cleanup_err:
            logger.error(f"Error during server cleanup: {cleanup_err}")

        # Final process cleanup
        cleanup_processes_sync()
        logger.info("Final cleanup completed")


# Test functions to verify server operation
async def test_server_initialization(db_url: str, username: str, password: str, database: str = "neo4j"):
    """Test function to verify server initialization.

    This function creates a server instance and verifies:
    1. Connection to the database works
    2. Hub initialization succeeds
    3. Tool registration works
    4. Basic queries function

    Args:
        db_url: Neo4j connection URL
        username: Neo4j username
        password: Neo4j password
        database: Neo4j database name

    Returns:
        bool: True if all tests pass
    """
    logger.info("Running server initialization test")

    try:
        # Create a temporary event loop for testing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Create the driver with minimal connection pool
        driver_config = {
            "max_connection_pool_size": 5,
        }

        driver = AsyncGraphDatabase.driver(
            db_url,
            auth=(username, password),
            max_connection_pool_size=driver_config["max_connection_pool_size"]
        )

        # Test connection
        logger.info("Testing Neo4j connection")
        async with safe_neo4j_session(driver, database) as session:
            result = await session.run("RETURN 1 as success")
            data = await result.data()
            if not data or data[0]["success"] != 1:
                logger.error("Basic Neo4j connectivity test failed")
                return False

        logger.info("Basic Neo4j connectivity verified")

        # Create server instance
        logger.info("Creating test server instance")
        server = Neo4jWorkflowServer(driver, database, loop)

        # Test hub access
        logger.info("Testing guidance hub access")
        hub_response = await server.get_guidance_hub()
        if not hub_response or not isinstance(hub_response[0], types.TextContent):
            logger.error("Guidance hub test failed")
            return False

        # Test incarnation functions
        logger.info("Testing incarnation listing")
        inc_response = await server.list_incarnations()
        if not inc_response or not isinstance(inc_response[0], types.TextContent):
            logger.error("Incarnation listing test failed")
            return False

        # Close the driver
        await driver.close()

        logger.info("All server initialization tests passed")
        return True

    except Exception as e:
        logger.error(f"Server initialization test failed: {str(e)}")
        logger.debug(f"Test error details: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    # Add missing imports only needed in main
    import sys

    # Run initialization test in debug mode
    if "--test" in sys.argv:
        import asyncio

        # Get connection info from environment
        db_url = os.environ.get("NEO4J_URL", "bolt://localhost:7687")
        username = os.environ.get("NEO4J_USERNAME", "neo4j")
        password = os.environ.get("NEO4J_PASSWORD", "password")
        database = os.environ.get("NEO4J_DATABASE", "neo4j")

        # Run the test
        test_result = asyncio.run(test_server_initialization(db_url, username, password, database))

        if test_result:
            logger.info("Server test successful, exiting...")
            sys.exit(0)
        else:
            logger.error("Server test failed, exiting...")
            sys.exit(1)
    else:
        # Start the server normally
        main()
