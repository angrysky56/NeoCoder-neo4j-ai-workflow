import asyncio
import logging
from typing import Optional, Dict, Any, Type

from mcp import types
from neo4j import AsyncGraphDatabase, AsyncDriver

logger = logging.getLogger(__name__)


class PolymorphicAdapter:
    """Manages dynamic incarnation switching and tool registration."""

    def __init__(self, driver: AsyncDriver, database: str = "neo4j"):
        self.driver = driver
        self.database = database
        self.current_incarnation = None
        self.incarnation_registry: Dict[str, Type] = {}
        self._current_loop = None  # Track the event loop for consistency

    def register_incarnation(self, incarnation_id: str, incarnation_class: Type):
        """Register an incarnation type with its class."""
        self.incarnation_registry[incarnation_id] = incarnation_class

    async def set_incarnation(self, incarnation_type_id: str):
        """Set the current incarnation type using its string identifier.

        Args:
            incarnation_type_id: String identifier for the incarnation type
        """
        if incarnation_type_id not in self.incarnation_registry:
            raise ValueError(f"Unknown incarnation type: {incarnation_type_id}")

        # Ensure we're operating in the correct event loop context
        current_loop = asyncio.get_running_loop()
        if self._current_loop is None:
            self._current_loop = current_loop
        elif self._current_loop != current_loop:
            logger.warning("Event loop context changed, updating reference")
            self._current_loop = current_loop

        # Get instance from incarnation registry if available
        from mcp_neocoder.incarnation_registry import registry as global_registry

        database = self.database or "neo4j"  # Provide default database name if None
        incarnation_instance = global_registry.get_instance(incarnation_type_id, self.driver, database)

        # If not available in global registry, create it directly
        if not incarnation_instance:
            incarnation_class = self.incarnation_registry[incarnation_type_id]
            incarnation_instance = incarnation_class(self.driver, self.database)

        self.current_incarnation = incarnation_instance

        # Initialize schema for this incarnation with proper async context handling
        try:
            await self.current_incarnation.initialize_schema()
        except RuntimeError as e:
            if "different loop" in str(e).lower():
                logger.warning("Async loop conflict detected, attempting recovery")
                # Create a new task in the current loop
                await asyncio.create_task(self.current_incarnation.initialize_schema())
            else:
                raise

        # Register incarnation-specific tools with explicit logging and proper async context
        logger.info(f"Registering tools for incarnation: {incarnation_type_id}")
        try:
            tool_count = await self.current_incarnation.register_tools(self)
            logger.info(f"Registered {tool_count} tools for {incarnation_type_id}")
        except RuntimeError as e:
            if "different loop" in str(e).lower():
                logger.warning("Tool registration async loop conflict, attempting recovery")
                tool_count = await asyncio.create_task(self.current_incarnation.register_tools(self))
                logger.info(f"Registered {tool_count} tools for {incarnation_type_id} (recovered)")
            else:
                raise

        logger.info(f"Switched to incarnation: {incarnation_type_id}")
        return self.current_incarnation

    async def get_current_incarnation_type(self) -> Optional[str]:
        """Get the currently active incarnation identifier."""
        if not self.current_incarnation:
            return None
        return self.current_incarnation.name

    def has_tool(self, tool_name: str) -> bool:
        """Check if the current incarnation has a specific tool."""
        if not self.current_incarnation:
            return False
        return hasattr(self.current_incarnation, tool_name)

    async def call_tool(self, tool_name: str, **kwargs) -> Any:
        """Call a tool on the current incarnation."""
        if not self.current_incarnation:
            raise RuntimeError("No incarnation is currently active")

        if not hasattr(self.current_incarnation, tool_name):
            raise AttributeError(f"Current incarnation does not have tool: {tool_name}")

        method = getattr(self.current_incarnation, tool_name)
        return await method(**kwargs)

    async def switch_incarnation(self, incarnation_type: str) -> str:
        """Switch to a different incarnation type.
        
        Args:
            incarnation_type: The type of incarnation to switch to
            
        Returns:
            Confirmation message
        """
        available_types = list(self.incarnation_registry.keys())
        
        if incarnation_type not in available_types:
            available_types_str = ", ".join(available_types)
            raise ValueError(f"Unknown incarnation type: '{incarnation_type}'. Available types: {available_types_str}")
        
        # Use the existing set_incarnation method with enhanced async handling
        await self.set_incarnation(incarnation_type)
        return f"Successfully switched to '{incarnation_type}' incarnation"

    def get_available_incarnations(self) -> Dict[str, str]:
        """Get a mapping of available incarnation types to their descriptions."""
        incarnations = {}
        for inc_type, inc_class in self.incarnation_registry.items():
            incarnations[inc_type] = getattr(inc_class, 'description', 'No description available')
        return incarnations
