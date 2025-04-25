"""
Fixed version of the Neo4jWorkflowServer initialization to properly handle asyncio event loops

This addresses the error:
"Error retrieving guidance hub: Task cb=[TaskGroup._spawn..task_done() at .../anyio/_backends/_asyncio.py:794]> got Future attached to a different loop"
"""

import logging
import asyncio

logger = logging.getLogger("mcp_neocoder")

def _register_basic_handlers(self):
    """Register handlers for basic MCP protocol requests to prevent timeouts."""
    
    # Simply set the handlers directly to avoid decorator issues
    # This approach doesn't rely on decorators which were causing the problems
    async def empty_list_handler():
        """Return empty list for protocol handlers."""
        return []
        
    # Set the handlers directly on the MCP instance
    self.mcp.prompts_list_handler = empty_list_handler
    self.mcp.resources_list_handler = empty_list_handler
    
    # Log the registration
    logger.info("Registered basic protocol handlers for prompts and resources")

async def run_async_init(self):
    """Run all async initialization steps properly in the current event loop."""
    # Auto-initialize the database if needed
    await self._ensure_db_initialized()
    
    # Register tools from all incarnations
    tool_count = await self._register_all_incarnation_tools()
    logger.info(f"Registered {tool_count} tools from all incarnations")
    
    return tool_count

def initialize_server(self):
    """Initialize the server properly without causing event loop issues."""
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
            logger.info(f"Auto-registering incarnation {inc_type.value} ({inc_class.__name__})")
            self.register_incarnation(inc_class, inc_type)
    
        # Register core tools
        self._register_tools()
        
        # For async initialization, create a new event loop if needed
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # If no event loop in thread, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run async initialization steps properly in the loop
        tool_count = loop.run_until_complete(self.run_async_init())
        
        return True
    except Exception as e:
        logger.error(f"Error during initialization: {e}")
        import traceback
        logger.error(traceback.format_exc())
        logger.info("Basic MCP handlers are still registered, so the server will respond to protocol requests")
        return False
