"""
Base Incarnation Module for NeoCoder Framework

This module defines the base class for all incarnations, with common functionality
and required interface methods that must be implemented by each incarnation.
"""

import json
import logging
import uuid
import os
from typing import Dict, Any, List, Optional, Type, Union
from enum import Enum, auto

import mcp.types as types
from pydantic import Field
from neo4j import AsyncDriver, AsyncTransaction

logger = logging.getLogger("mcp_neocoder.incarnations.base")

# Default incarnation types
class IncarnationType(str, Enum):
    """Supported incarnation types for the NeoCoder framework.
    
    This enum will be extended dynamically based on discovered incarnation modules.
    """
    DATA_ANALYSIS = "data_analysis"        # Data analysis incarnation
    CODING = "coding"                      # Original coding workflow
    RESEARCH = "research_orchestration"    # Research lab notebook
    DECISION = "decision_support"          # Decision-making system
    LEARNING = "continuous_learning"       # Learning environment
    SIMULATION = "complex_system"          # Complex system simulator
    KNOWLEDGE_GRAPH = "knowledge_graph"    # Knowledge graph management
    
    @classmethod
    def extend(cls, new_types: Dict[str, str]):
        """Extend the enum with new incarnation types.
        
        Args:
            new_types: Dictionary mapping identifiers to string values
        
        Returns:
            The updated enum class
        """
        # Create a new enum class with the original values plus new ones
        extended_items = {name: member.value for name, member in cls.__members__.items()}
        extended_items.update(new_types)
        
        # Create a new Enum class with the extended values
        return Enum(cls.__name__, extended_items, type=str)


class BaseIncarnation:
    """Base class for all incarnation implementations."""

    # These should be overridden by each incarnation
    incarnation_type: IncarnationType
    description: str
    version: str

    # Optional schema creation scripts, format: List of Cypher queries to execute
    schema_queries: List[str] = []

    # Hub content - default guidance hub text for this incarnation
    hub_content: str = """
# Default Incarnation Hub

Welcome to this incarnation of the NeoCoder framework.
This is a default hub that should be overridden by each incarnation.
    """
    
    # Optional list of tool method names - can be defined by subclasses
    # to explicitly declare which methods should be registered as tools
    # Format: list[str] with method names to be registered as tools
    _tool_methods: List[str] = []

    def __init__(self, driver: AsyncDriver, database: str = "neo4j"):
        """Initialize the incarnation with database connection."""
        self.driver = driver
        self.database = database

    async def initialize_schema(self):
        """Initialize the Neo4j schema for this incarnation."""
        # Execute schema queries if defined
        if self.schema_queries:
            try:
                async with self.driver.session(database=self.database) as session:
                    # Execute each constraint/index query individually
                    for query in self.schema_queries:
                        await session.execute_write(lambda tx: tx.run(query))

                # Create guidance hub if needed
                await self.ensure_hub_exists()

                logger.info(f"{self.incarnation_type} incarnation schema initialized")
            except Exception as e:
                logger.error(f"Error initializing schema for {self.incarnation_type}: {e}")
                raise
        else:
            # No schema queries defined
            logger.warning(f"No schema queries defined for {self.incarnation_type}")

            # Still create the hub
            await self.ensure_hub_exists()

    async def ensure_hub_exists(self):
        """Create the guidance hub for this incarnation if it doesn't exist."""
        hub_id = f"{self.incarnation_type.value}_hub"

        query = """
        MERGE (hub:AiGuidanceHub {id: $hub_id})
        ON CREATE SET hub.description = $description
        RETURN hub
        """

        params = {
            "hub_id": hub_id,
            "description": self.hub_content
        }

        try:
            async with self.driver.session(database=self.database) as session:
                await session.execute_write(lambda tx: tx.run(query, params))
                logger.info(f"Ensured hub exists for {self.incarnation_type}")
        except Exception as e:
            logger.error(f"Error creating hub for {self.incarnation_type}: {e}")
            raise

    async def get_guidance_hub(self) -> List[types.TextContent]:
        """Get the guidance hub content for this incarnation."""
        hub_id = f"{self.incarnation_type.value}_hub"

        query = f"""
        MATCH (hub:AiGuidanceHub {{id: $hub_id}})
        RETURN hub.description AS description
        """

        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_read(self._read_query, query, {"hub_id": hub_id})
                results = json.loads(results_json)

                if results and len(results) > 0:
                    return [types.TextContent(type="text", text=results[0]["description"])]
                else:
                    # If hub doesn't exist, create it
                    await self.ensure_hub_exists()
                    # Try again
                    return await self.get_guidance_hub()
        except Exception as e:
            logger.error(f"Error retrieving guidance hub for {self.incarnation_type}: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    def list_tool_methods(self):
        """List all methods in this class that appear to be tools.

        Returns:
            list: List of method names that appear to be tools
        """
        import inspect
        import mcp.types as types

        tool_methods = []

        logger.debug(f"Checking methods in {self.__class__.__name__}")

        # First, check if there's a hardcoded list of tools
        if hasattr(self, '_tool_methods') and isinstance(self._tool_methods, list):
            logger.info(f"Using predefined tool list for {self.__class__.__name__}: {self._tool_methods}")
            for name in self._tool_methods:
                if hasattr(self, name) and callable(getattr(self, name)):
                    tool_methods.append(name)
                else:
                    logger.warning(f"Predefined tool method {name} does not exist in {self.__class__.__name__}")
            return tool_methods

        # If no predefined list, use inspection to find tools
        class_dict = {}

        # Collect methods from all parent classes
        for cls in self.__class__.__mro__:
            if cls is object:
                continue
            class_dict.update(cls.__dict__)

        # Skip these common non-tool methods
        excluded_methods = {
            'initialize_schema', 'get_guidance_hub', 'register_tools',
            'list_tool_methods', 'ensure_hub_exists', '_read_query', '_write'
        }

        for name, method_obj in class_dict.items():
            # Skip private methods and excluded methods
            if name.startswith('_') or name in excluded_methods:
                continue

            # Check if it's an async method
            if inspect.iscoroutinefunction(method_obj):
                # Get the actual bound method
                method = getattr(self, name)

                # Check return type annotation if available
                is_tool = False

                if hasattr(method, '__annotations__'):
                    return_type = method.__annotations__.get('return')
                    # Check for List[types.TextContent] return type
                    if return_type and (
                        return_type == List[types.TextContent] or
                        getattr(return_type, '__origin__', None) == list and
                        getattr(return_type, '__args__', [None])[0] == types.TextContent
                    ):
                        is_tool = True
                        logger.debug(f"Identified tool method via return type annotation: {name}")

                # Fallback: if it's an async method defined in the class itself (not inherited),
                # and it has parameters, assume it's a tool
                if not is_tool and hasattr(method, '__code__'):
                    # Check if it has at least one parameter beyond 'self'
                    if method.__code__.co_argcount > 1:
                        is_tool = True
                        logger.debug(f"Identified tool method via parameter count: {name}")

                if is_tool:
                    tool_methods.append(name)

        logger.info(f"Found {len(tool_methods)} tool methods in {self.__class__.__name__} via inspection: {tool_methods}")
        return tool_methods

    async def register_tools(self, server):
        """Register incarnation-specific tools with the server.
        Uses direct registration to ensure tools are properly connected.
        """
        # Get all tool methods from this incarnation
        tool_methods = self.list_tool_methods()
        logger.info(f"Tool methods in {self.incarnation_type.value}: {tool_methods}")

        # Register each tool directly with the MCP server
        registered_count = 0
        for method_name in tool_methods:
            try:
                # Get the method
                method = getattr(self, method_name)

                # Check if it's already registered
                if not hasattr(method, '_registered_to_mcp'):
                    # Register directly with MCP
                    server.mcp.add_tool(method)
                    setattr(method, '_registered_to_mcp', True)
                    registered_count += 1
                    logger.info(f"Directly registered tool {method_name} from {self.incarnation_type.value}")
            except Exception as e:
                logger.error(f"Error registering tool {method_name}: {e}")

        # Also register with tool registry for tracking/listing
        from ..tool_registry import registry
        registry.register_class_tools(self, self.incarnation_type.value)

        logger.info(f"{self.incarnation_type} incarnation: {registered_count} tools registered directly with server")
        return registered_count

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
