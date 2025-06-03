"""
Polymorphic Adapter for NeoCoder Neo4j AI Workflow

This module extends the NeoCoder framework to support multiple incarnations beyond code workflows,
including research orchestration, decision support, continuous learning, and complex systems simulation.

The adapter follows a plugin architecture where different incarnations can be registered and
dynamically loaded based on configuration.
"""

import json
import logging
import uuid
import asyncio
from typing import Dict, Any, List, Optional, Type, Union

import mcp.types as types
from pydantic import Field
from neo4j import AsyncTransaction

# Import the BaseIncarnation from base_incarnation to avoid duplication
from .base_incarnation import BaseIncarnation, IncarnationType, get_incarnation_type_from_filename

logger = logging.getLogger("mcp_neocoder.polymorphic_adapter")


class PolymorphicAdapterMixin:
    """Mixin to add polymorphic capabilities to the Neo4jWorkflowServer."""

    def __init__(self, *args, **kwargs):
        """Initialize the polymorphic adapter."""
        self.incarnation_registry = {}
        self.current_incarnation = None
        super().__init__(*args, **kwargs)

    def register_incarnation(self, incarnation_class: Type[BaseIncarnation], incarnation_type: IncarnationType):
        """Register a new incarnation type."""
        self.incarnation_registry[incarnation_type] = incarnation_class

    async def set_incarnation(self, incarnation_type: IncarnationType):
        """Set the current incarnation type."""
        if incarnation_type not in self.incarnation_registry:
            raise ValueError(f"Unknown incarnation type: {incarnation_type}")

        # Get instance from incarnation registry if available
        from mcp_neocoder.incarnation_registry import registry as global_registry

        incarnation_instance = global_registry.get_instance(incarnation_type, self.driver, self.database)

        # If not available in global registry, create it directly
        if not incarnation_instance:
            incarnation_class = self.incarnation_registry[incarnation_type]
            incarnation_instance = incarnation_class(self.driver, self.database)

        self.current_incarnation = incarnation_instance

        # Initialize schema for this incarnation
        await self.current_incarnation.initialize_schema()

        # Register incarnation-specific tools with explicit logging
        logger.info(f"Registering tools for incarnation: {incarnation_type.value}")
        tool_count = await self.current_incarnation.register_tools(self)
        logger.info(f"Registered {tool_count} tools for {incarnation_type.value}")

        logger.info(f"Switched to incarnation: {incarnation_type.value}")
        return self.current_incarnation

    async def get_current_incarnation_type(self) -> Optional[IncarnationType]:
        """Get the currently active incarnation type."""
        if not self.current_incarnation:
            return None
        return self.current_incarnation.incarnation_type

    async def list_available_incarnations(self) -> List[Dict[str, Any]]:
        """List all available incarnations with metadata."""
        return [
            {
                "type": inc_type.value,
                "description": inc_class.__doc__ or "No description available",
            }
            for inc_type, inc_class in self.incarnation_registry.items()
        ]


# Module functions for switching between incarnations
def switch_incarnation(
    server,
    incarnation_type: str
) -> List[types.TextContent]:
    """Switch the server to a different incarnation."""
    import asyncio
    
    # Handle async operation in a way that respects the current event loop
    try:
        # Get the current running loop or create a new one
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # If no loop is running, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(_switch_incarnation_async(server, incarnation_type))
        
        # If we already have a running loop
        if loop.is_running():
            # Create a future and schedule the coroutine
            future = asyncio.run_coroutine_threadsafe(_switch_incarnation_async(server, incarnation_type), loop)
            return future.result(timeout=30)  # Add timeout to prevent hanging
        else:
            # Use the existing loop
            return loop.run_until_complete(_switch_incarnation_async(server, incarnation_type))
    except Exception as e:
        logger.error(f"Error in switch_incarnation: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return [types.TextContent(type="text", text=f"Error switching incarnation: {e}")]

async def _switch_incarnation_async(
    server,
    incarnation_type: str
) -> List[types.TextContent]:
    """Async implementation of switch_incarnation."""
    try:
        # First, ensure that incarnation types are up to date by extending with any new types
        from ..incarnation_registry import registry
        registry.extend_incarnation_types()
        
        # Import the updated enum
        from .base_incarnation import IncarnationType
        
        logger.info(f"Trying to switch to incarnation type: {incarnation_type}")
        
        # Log available types for debugging
        available_types = [t.value for t in IncarnationType]
        logger.info(f"Available incarnation types: {available_types}")
        
        # First try exact match
        target_type = None
        for inc_type in IncarnationType:
            if inc_type.value.lower() == incarnation_type.lower() or inc_type.name.lower() == incarnation_type.lower():
                target_type = inc_type
                logger.info(f"Exact match found for incarnation type: {inc_type.value}")
                break
                
        # If no exact match, try a fuzzy match
        if not target_type:
            for inc_type in IncarnationType:
                if (incarnation_type.lower() in inc_type.value.lower() or 
                    incarnation_type.lower() in inc_type.name.lower()):
                    target_type = inc_type
                    logger.info(f"Fuzzy match found for incarnation type: {incarnation_type} -> {inc_type.value}")
                    break
        
        # If still no match, check common aliases
        if not target_type:
            aliases = {
                "research": IncarnationType.RESEARCH,
                "decision": IncarnationType.DECISION,
                "learning": IncarnationType.LEARNING,
                "complex": IncarnationType.SIMULATION,
                "simulation": IncarnationType.SIMULATION,
                "knowledge": IncarnationType.KNOWLEDGE_GRAPH,
                "graph": IncarnationType.KNOWLEDGE_GRAPH,
                "data": IncarnationType.DATA_ANALYSIS,
                "analysis": IncarnationType.DATA_ANALYSIS,
                "coding": IncarnationType.CODING,
                "code": IncarnationType.CODING
            }
            
            for alias, inc_type in aliases.items():
                if alias.lower() in incarnation_type.lower():
                    target_type = inc_type
                    logger.info(f"Alias match found: {alias} -> {inc_type.value}")
                    break
        
        if not target_type:
            available_types_str = ", ".join(available_types)
            return [types.TextContent(
                type="text",
                text=f"Unknown incarnation type: '{incarnation_type}'. Available types: {available_types_str}"
            )]
        
        try:
            logger.info(f"Setting incarnation to: {target_type.value}")
            await server.set_incarnation(target_type)
            logger.info(f"Successfully switched to incarnation: {target_type.value}")
            return [types.TextContent(
                type="text",
                text=f"Successfully switched to '{target_type.value}' incarnation"
            )]
        except Exception as set_err:
            logger.error(f"Error in set_incarnation: {set_err}")
            return [types.TextContent(type="text", text=f"Error setting incarnation: {set_err}")]
            
    except Exception as e:
        logger.error(f"Error switching incarnation: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return [types.TextContent(type="text", text=f"Error: {e}")]


def get_current_incarnation(server) -> List[types.TextContent]:
    """Get the currently active incarnation type."""
    import asyncio
    
    # Handle async operation in a way that respects the current event loop
    try:
        # Get the current running loop or create a new one
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # If no loop is running, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(_get_current_incarnation_async(server))
        
        # If we already have a running loop
        if loop.is_running():
            # Create a future and schedule the coroutine
            future = asyncio.run_coroutine_threadsafe(_get_current_incarnation_async(server), loop)
            return future.result()
        else:
            # Use the existing loop
            return loop.run_until_complete(_get_current_incarnation_async(server))
    except Exception as e:
        logger.error(f"Error in get_current_incarnation: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return [types.TextContent(type="text", text=f"Error getting current incarnation: {e}")]

async def _get_current_incarnation_async(server) -> List[types.TextContent]:
    """Async implementation of get_current_incarnation."""
    try:
        current = await server.get_current_incarnation_type()
        if current:
            return [types.TextContent(
                type="text",
                text=f"Currently using '{current.value}' incarnation"
            )]
        else:
            return [types.TextContent(
                type="text",
                text="No incarnation is currently active"
            )]
    except Exception as e:
        logger.error(f"Error getting current incarnation: {e}")
        return [types.TextContent(type="text", text=f"Error: {e}")]


def list_incarnations(server) -> List[types.TextContent]:
    """List all available incarnations."""
    import asyncio
    
    # Handle async operation in a way that respects the current event loop
    try:
        # Get the current running loop or create a new one
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # If no loop is running, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(_list_incarnations_async(server))
        
        # If we already have a running loop
        if loop.is_running():
            # Create a future and schedule the coroutine
            future = asyncio.run_coroutine_threadsafe(_list_incarnations_async(server), loop)
            return future.result()
        else:
            # Use the existing loop
            return loop.run_until_complete(_list_incarnations_async(server))
    except Exception as e:
        logger.error(f"Error in list_incarnations: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return [types.TextContent(type="text", text=f"Error listing incarnations: {e}")]

async def _list_incarnations_async(server) -> List[types.TextContent]:
    """Async implementation of list_incarnations."""
    try:
        # First, ensure that incarnation types are up to date by extending with any new types
        from ..incarnation_registry import registry
        registry.extend_incarnation_types()
        
        # Get incarnations from server
        incarnations = await server.list_available_incarnations()

        if incarnations:
            text = "# Available Incarnations\n\n"
            text += "| Type | Description |\n"
            text += "| ---- | ----------- |\n"

            for inc in incarnations:
                text += f"| {inc['type']} | {inc['description']} |\n"

            current = await server.get_current_incarnation_type()
            if current:
                text += f"\nCurrently using: **{current.value}**"

            return [types.TextContent(type="text", text=text)]
        else:
            return [types.TextContent(type="text", text="No incarnations are registered")]
    except Exception as e:
        logger.error(f"Error listing incarnations: {e}")
        return [types.TextContent(type="text", text=f"Error: {e}")]
