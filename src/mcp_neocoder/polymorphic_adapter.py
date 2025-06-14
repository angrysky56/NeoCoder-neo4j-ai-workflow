"""
Polymorphic Adapter for NeoCoder Neo4j AI Workflow

This module extends the NeoCoder framework to support multiple incarnations beyond code workflows,
including research orchestration, decision support, continuous learning, and complex systems simulation.

The adapter follows a plugin architecture where different incarnations can be registered and
dynamically loaded based on configuration.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Type

import mcp.types as types

# Import the BaseIncarnation from incarnations.base_incarnation
from .incarnations.base_incarnation import BaseIncarnation

logger = logging.getLogger("mcp_neocoder.polymorphic_adapter")


def get_incarnation_type_from_filename(filename: str) -> Optional[str]:
    """Extract an incarnation type value from a filename.

    Args:
        filename: The filename to extract from (e.g., 'data_analysis_incarnation.py')

    Returns:
        The extracted value or None if no match
    """
    if not filename.endswith('_incarnation.py'):
        return None

    # Remove '.py' extension and '_incarnation' suffix
    name = filename[:-3].replace('_incarnation', '')

    return name


class PolymorphicAdapterMixin:
    """Mixin to add polymorphic capabilities to the Neo4jWorkflowServer."""

    def __init__(self, driver=None, database=None, *args, **kwargs):
        """Initialize the polymorphic adapter."""
        self.driver = driver
        self.database = database
        self.incarnation_registry = {}
        self.current_incarnation = None
        super().__init__(*args, **kwargs)

    def register_incarnation(self, incarnation_class: Type[BaseIncarnation], incarnation_id: Optional[str] = None):
        """Register a new incarnation.

        Args:
            incarnation_class: The incarnation class to register
            incarnation_id: Optional identifier override (uses class.name by default)
        """
        # Use provided id or get it from the class
        incarnation_id = incarnation_id if incarnation_id is not None else incarnation_class.name
        self.incarnation_registry[incarnation_id] = incarnation_class

    async def set_incarnation(self, incarnation_type_id: str):
        """Set the current incarnation type using its string identifier.

        Args:
            incarnation_type_id: String identifier for the incarnation type
        """
        if incarnation_type_id not in self.incarnation_registry:
            raise ValueError(f"Unknown incarnation type: {incarnation_type_id}")

        # Get instance from incarnation registry if available
        from mcp_neocoder.incarnation_registry import registry as global_registry

        database = self.database or "neo4j"  # Provide default database name if None
        incarnation_instance = global_registry.get_instance(incarnation_type_id, self.driver, database)

        # If not available in global registry, create it directly
        if not incarnation_instance:
            incarnation_class = self.incarnation_registry[incarnation_type_id]
            incarnation_instance = incarnation_class(self.driver, self.database)

        self.current_incarnation = incarnation_instance

        # Initialize schema for this incarnation
        await self.current_incarnation.initialize_schema()

        # Register incarnation-specific tools with explicit logging
        logger.info(f"Registering tools for incarnation: {incarnation_type_id}")
        tool_count = await self.current_incarnation.register_tools(self)
        logger.info(f"Registered {tool_count} tools for {incarnation_type_id}")

        logger.info(f"Switched to incarnation: {incarnation_type_id}")
        return self.current_incarnation
    async def get_current_incarnation_type(self) -> Optional[str]:
        """Get the currently active incarnation identifier."""
        if not self.current_incarnation:
            return None
        return self.current_incarnation.name

    async def list_available_incarnations(self) -> List[Dict[str, Any]]:
        """List all available incarnations with metadata."""
        return [
            {
                "type": inc_type_id,
                "description": getattr(inc_class, 'description', inc_class.__doc__ or "No description available"),
            }
            for inc_type_id, inc_class in self.incarnation_registry.items()
        ]


# Module functions for switching between incarnations
def switch_incarnation(
    server,
    incarnation_type: str
) -> List[types.TextContent]:
    """Switch the server to a different incarnation."""
    # Handle async operation with proper event loop methodology
    try:
        # Get the current running loop or create a new one
        try:
            loop = asyncio.get_running_loop()
            # METHODOLOGICAL CORRECTION: If we got here, loop IS running
            # Must use run_coroutine_threadsafe, not run_until_complete
            logger.debug("Using existing running loop for switch_incarnation")
            future = asyncio.run_coroutine_threadsafe(_switch_incarnation_async(server, incarnation_type), loop)
            return future.result(timeout=30)  # Add timeout to prevent hanging
        except RuntimeError:
            # No loop is running in current thread, create a new one
            logger.debug("Creating new event loop for switch_incarnation")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(_switch_incarnation_async(server, incarnation_type))
            finally:
                # Clean up the loop we created
                loop.close()
    except Exception as e:
        logger.error(f"Error in switch_incarnation: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return [types.TextContent(type="text", text=f"Error switching incarnation: {e}")]

async def _switch_incarnation_async(
    server,
    incarnation_type: str
) -> List[types.TextContent]:
    """Async implementation of switch_incarnation using simple string matching.

    Uses direct string matching - no enums.
    """
    # Simple approach: just use the string directly
    try:
        logger.info(f"Switching to incarnation type: {incarnation_type}")

        # Look first for exact match
        if incarnation_type in server.incarnation_registry:
            target_type = incarnation_type
        else:
            # Try case-insensitive match
            lower_type = incarnation_type.lower()
            available_types = list(server.incarnation_registry.keys())

            matches = []
            for type_id in available_types:
                # Try both exact match and first-segment match for multi-part names
                if type_id.lower() == lower_type:
                    matches.append((type_id, 100))  # Perfect match, highest score
                elif type_id.lower().startswith(lower_type):
                    matches.append((type_id, 80))   # Prefix match, high score
                elif lower_type.startswith(type_id.lower()):
                    matches.append((type_id, 70))   # Substring match, lower score
                # Check for first segment match in multi-part names
                elif '_' in type_id and type_id.split('_')[0].lower() == lower_type:
                    matches.append((type_id, 90))   # First segment match, very high score
                # Match on class name (remove 'Incarnation' suffix if present)
                else:
                    inc_class = server.incarnation_registry[type_id]
                    if hasattr(inc_class, '__name__'):
                        class_name = inc_class.__name__.lower()
                        if class_name.endswith('incarnation'):
                            class_name = class_name[:-11]  # Remove 'incarnation'
                        if class_name == lower_type:
                            matches.append((type_id, 85))  # Class name match, high score

            # No matches found
            if not matches:
                available_types_str = ", ".join(available_types)
                return [types.TextContent(
                    type="text",
                    text=f"Unknown incarnation type: '{incarnation_type}'. Available types: {available_types_str}"
                )]

            # Sort by score (highest first) and use the best match
            matches.sort(key=lambda x: x[1], reverse=True)
            target_type = matches[0][0]
            logger.info(f"Found matching incarnation: {target_type}")

        # Switch to the matched incarnation
        try:
            await server.set_incarnation(target_type)
            return [types.TextContent(
                type="text",
                text=f"Successfully switched to '{target_type}' incarnation"
            )]
        except Exception as e:
            logger.error(f"Error setting incarnation: {e}")
            return [types.TextContent(type="text", text=f"Error setting incarnation: {e}")]

    except Exception as e:
        logger.error(f"Error switching incarnation: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return [types.TextContent(type="text", text=f"Error: {e}")]


def get_current_incarnation(server) -> List[types.TextContent]:
    """Get the currently active incarnation type."""
    import asyncio

    # Handle async operation with proper event loop methodology
    try:
        # Get the current running loop or create a new one
        try:
            loop = asyncio.get_running_loop()
            # METHODOLOGICAL CORRECTION: If we got here, loop IS running
            logger.debug("Using existing running loop for get_current_incarnation")
            future = asyncio.run_coroutine_threadsafe(_get_current_incarnation_async(server), loop)
            return future.result(timeout=30)
        except RuntimeError:
            # No loop is running in current thread, create a new one
            logger.debug("Creating new event loop for get_current_incarnation")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(_get_current_incarnation_async(server))
            finally:
                # Clean up the loop we created
                loop.close()
    except Exception as e:
        logger.error(f"Error in get_current_incarnation: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return [types.TextContent(type="text", text=f"Error getting current incarnation: {e}")]

async def _get_current_incarnation_async(server) -> List[types.TextContent]:
    """Get the currently active incarnation type using string identifiers."""
    try:
        current = await server.get_current_incarnation_type()
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


def list_incarnations(server) -> List[types.TextContent]:
    """List all available incarnations."""
    import asyncio

    # Handle async operation with proper event loop methodology
    try:
        # Get the current running loop or create a new one
        try:
            loop = asyncio.get_running_loop()
            # METHODOLOGICAL CORRECTION: If we got here, loop IS running
            logger.debug("Using existing running loop for list_incarnations")
            future = asyncio.run_coroutine_threadsafe(_list_incarnations_async(server), loop)
            return future.result(timeout=30)
        except RuntimeError:
            # No loop is running in current thread, create a new one
            logger.debug("Creating new event loop for list_incarnations")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(_list_incarnations_async(server))
            finally:
                # Clean up the loop we created
                loop.close()
    except Exception as e:
        logger.error(f"Error in list_incarnations: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return [types.TextContent(type="text", text=f"Error listing incarnations: {e}")]

async def _list_incarnations_async(server) -> List[types.TextContent]:
    """List all available incarnations with simple string identifiers."""
    try:
        # Just get the direct list with no enum translations
        incarnations = []

        for type_id, inc_class in server.incarnation_registry.items():
            # Get description from class if available or use docstring
            description = getattr(inc_class, 'description', None)
            if not description and inc_class.__doc__:
                description = inc_class.__doc__.strip().split('\n')[0]
            if not description:
                description = "No description available"

            # Get a nice display name
            display_name = type_id
            if '_' in type_id:
                display_name = type_id.split('_')[0]

            incarnations.append({
                "id": type_id,
                "display_name": display_name,
                "description": description
            })

        # Format the output
        if incarnations:
            # Sort by display name
            incarnations.sort(key=lambda x: x["display_name"])

            text = "# Available Incarnations\n\n"
            text += "| Type | Description |\n"
            text += "| ---- | ----------- |\n"

            for inc in incarnations:
                text += f"| {inc['display_name']} | {inc['description']} |\n"

            # Show current incarnation
            current = await server.get_current_incarnation_type()
            if current:
                text += f"\nCurrently using: **{current}** incarnation"
            else:
                text += "\nNo incarnation is currently active. Use `switch_incarnation()` to activate one."

            return [types.TextContent(type="text", text=text)]
        else:
            return [types.TextContent(type="text", text="No incarnations are registered")]
    except Exception as e:
        logger.error(f"Error listing incarnations: {e}")
        return [types.TextContent(type="text", text=f"Error: {e}")]
