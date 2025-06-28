"""
Polymorphic Adapter for NeoCoder Neo4j AI Workflow

This module provides mixin capabilities to the Neo4jWorkflowServer for managing
multiple incarnations using string-based identifiers.

Enhanced with async context preservation for robust operation across incarnation transitions.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Type, TYPE_CHECKING

import mcp.types as types

if TYPE_CHECKING:
    from neo4j import AsyncDriver

logger = logging.getLogger("mcp_neocoder.polymorphic_adapter")


class PolymorphicAdapterMixin:
    """Mixin to add polymorphic incarnation capabilities to the Neo4jWorkflowServer.

    This mixin enables dynamic switching between different AI incarnations (knowledge_graph,
    data_analysis, research, etc.) while preserving async context and tool registration.

    Expected attributes from the host class:
        driver (AsyncDriver): Neo4j database driver for persistent operations
        database (str): Database name for Neo4j operations

    Provides methods:
        set_incarnation: Switch to a different incarnation type
        get_current_incarnation_type: Get the currently active incarnation
        list_available_incarnations: List all registered incarnation types
        register_incarnation: Register a new incarnation class
    """

    # Type hints for IDE compatibility - these attributes are provided by the host class
    driver: 'AsyncDriver'
    database: str

    def __init__(self, *args, **kwargs) -> None:
        """Initialize the polymorphic adapter with event loop tracking.

        Sets up incarnation registry and async context management for robust
        operation across different event loop contexts.
        """
        # Initialize incarnation registry if not present
        if not hasattr(self, 'incarnation_registry'):
            self.incarnation_registry: Dict[str, Type] = {}
        if not hasattr(self, 'current_incarnation'):
            self.current_incarnation: Optional[Any] = None

        self._event_loop_context: Optional[asyncio.AbstractEventLoop] = None
        super().__init__(*args, **kwargs)

    async def set_incarnation(self, incarnation_type: str) -> Any:
        """Set the current incarnation type with enhanced async context handling.

        Switches the system to use the specified incarnation, handling schema
        initialization and tool registration with proper async context preservation.

        Args:
            incarnation_type: String identifier for the incarnation type
                            (e.g., 'knowledge_graph', 'data_analysis', 'research')

        Returns:
            The incarnation instance that was activated

        Raises:
            ValueError: If the incarnation type is not registered
            RuntimeError: If async context conflicts cannot be resolved
        """
        if incarnation_type not in self.incarnation_registry:
            available = list(self.incarnation_registry.keys())
            raise ValueError(f"Unknown incarnation type: '{incarnation_type}'. Available: {available}")

        # Preserve event loop context for consistency across async operations
        try:
            current_loop = asyncio.get_running_loop()
            if self._event_loop_context is None:
                self._event_loop_context = current_loop
            elif self._event_loop_context != current_loop:
                logger.warning("Event loop context changed, updating reference")
                self._event_loop_context = current_loop
        except RuntimeError:
            # No running loop - acceptable for some initialization contexts
            pass

        # Get instance from global registry or create new one
        from mcp_neocoder.incarnation_registry import registry as global_registry

        database = getattr(self, 'database', 'neo4j') or "neo4j"
        driver = getattr(self, 'driver')

        incarnation_instance = global_registry.get_instance(incarnation_type, driver, database)

        if not incarnation_instance:
            incarnation_class = self.incarnation_registry[incarnation_type]
            incarnation_instance = incarnation_class(driver, database)

        self.current_incarnation = incarnation_instance

        # Initialize schema with async context error recovery
        if self.current_incarnation is None:
            raise RuntimeError("No current incarnation is set; cannot initialize schema.")
        try:
            await self.current_incarnation.initialize_schema()
        except RuntimeError as e:
            if "different loop" in str(e).lower():
                logger.warning("Async loop conflict during schema initialization, attempting recovery")
                try:
                    await asyncio.create_task(self.current_incarnation.initialize_schema())
                except Exception as recovery_err:
                    logger.error(f"Failed to recover from async loop conflict: {recovery_err}")
                    raise RuntimeError(f"Schema initialization failed: {recovery_err}") from recovery_err
            else:
                raise

        # Register incarnation-specific tools with async error recovery
        logger.info(f"Registering tools for incarnation: {incarnation_type}")
        try:
            tool_count = await self.current_incarnation.register_tools(self)
            logger.info(f"Registered {tool_count} tools for {incarnation_type}")
        except RuntimeError as e:
            if "different loop" in str(e).lower():
                logger.warning("Tool registration async loop conflict, attempting recovery")
                try:
                    tool_count = await asyncio.create_task(self.current_incarnation.register_tools(self))
                    logger.info(f"Registered {tool_count} tools for {incarnation_type} (recovered)")
                except Exception as recovery_err:
                    logger.error(f"Failed to recover from tool registration conflict: {recovery_err}")
                    raise RuntimeError(f"Tool registration failed: {recovery_err}") from recovery_err
            else:
                raise

        logger.info(f"Successfully switched to incarnation: {incarnation_type}")
        return self.current_incarnation

    async def get_current_incarnation_type(self) -> Optional[str]:
        """Get the currently active incarnation identifier.

        Returns:
            String identifier of the active incarnation, or None if no incarnation is active
        """
        if not self.current_incarnation:
            return None
        return getattr(self.current_incarnation, 'name', None) or \
               getattr(self.current_incarnation, 'incarnation_type', None)

    async def list_available_incarnations(self) -> List[Dict[str, Any]]:
        """List all available incarnations with their metadata.

        Returns:
            List of dictionaries containing incarnation type and description information
        """
        incarnations = []
        for inc_type, inc_class in self.incarnation_registry.items():
            # Handle both string and enum-like type values
            type_value = inc_type
            if hasattr(inc_type, 'value') and not isinstance(inc_type, str):
                type_value = inc_type.value

            incarnations.append({
                "type": type_value,
                "description": getattr(inc_class, 'description', None) or
                              getattr(inc_class, '__doc__', None) or
                              "No description available",
            })
        return incarnations

    def register_incarnation(self, incarnation_type: str, incarnation_class: Type) -> None:
        """Register a new incarnation type with its implementation class.

        Args:
            incarnation_type: String identifier for the incarnation (e.g., 'knowledge_graph')
            incarnation_class: Class that implements the incarnation functionality
        """
        self.incarnation_registry[incarnation_type] = incarnation_class
        logger.info(f"Registered incarnation: {incarnation_type} -> {incarnation_class.__name__}")
