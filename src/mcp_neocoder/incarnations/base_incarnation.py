"""
Base Incarnation Module for NeoCoder Framework

This module defines the base class for all incarnations, with common functionality
and required interface methods that must be implemented by each incarnation.

The design follows a plugin architecture where different incarnations can be dynamically
discovered and loaded without requiring central registration of types.
"""

import json
import logging
from typing import List, cast
try:
    from typing import LiteralString
except ImportError:
    # Fallback for Python < 3.11
    LiteralString = str

import mcp.types as types
from neo4j import AsyncDriver, AsyncManagedTransaction

from ..action_templates import ActionTemplateMixin

logger = logging.getLogger("mcp_neocoder.incarnations.base")


class BaseIncarnation(ActionTemplateMixin):
    """Base class for all incarnation implementations."""

    # This should be overridden by each incarnation
    name = "base"  # String identifier, should be unique
    description = "Base incarnation class"

    # Optional schema creation scripts, format: List of Cypher queries to execute
    # Use ActionTemplateMixin's schema_queries for ActionTemplate constraints/indexes
    from typing import Tuple

    schema_queries: Tuple[str, ...] = tuple(ActionTemplateMixin.schema_queries)

    # Hub content - comprehensive guidance hub for universal access
    hub_content: str = """
# NeoCoder Universal Base Guidance Hub

Welcome to the NeoCoder Neo4j-Guided AI Workflow System. This guidance is universally available across all incarnations.

## 🎯 Core System Architecture

### Universal Base Capabilities (Inherited by All Incarnations)
- **Action Templates**: `list_action_templates()`, `get_action_template(keyword)`
- **Project Management**: `get_project()`, `list_projects()`
- **Workflow Tracking**: `log_workflow_execution()`, `get_workflow_history()`
- **Best Practices**: `get_best_practices()`
- **Template Feedback**: `add_template_feedback()`

## 🔧 Adding Tools to NeoCoder (Simple Process)

### Method 1: Direct Addition to Incarnation Class
Add async methods with proper signatures to incarnation files:

```python
async def your_tool_name(
    self,
    param1: str = Field(..., description="Parameter description"),
    param2: Optional[int] = Field(None, description="Optional parameter")
) -> List[types.TextContent]:
    \"\"\"Tool description for automatic registration\"\"\"
    try:
        # Tool implementation here
        result = "Your tool result"
        return [types.TextContent(type="text", text=result)]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {e}")]
```

**Key Requirements:**
- Must be `async def` method
- Must return `List[types.TextContent]`
- Use `Field(...)` for parameter descriptions
- Include docstring for automatic discovery

### Method 2: Using ToolProposalMixin
All incarnations include `propose_tool()` for systematic requests:
```python
await propose_tool(
    name="tool_name",
    description="What the tool does",
    parameters=[{"name": "param1", "type": "str", "description": "param desc"}],
    rationale="Why this tool is needed"
)
```

## 🔍 Available Incarnations
Each provides specialized tools while inheriting base functionality:
- **coding**: Original NeoCoder workflows and development tools
- **knowledge_graph**: Entity/relationship management, graph operations
- **research_orchestration**: Scientific workflows, hypothesis testing
- **data_analysis**: Data exploration, visualization, statistical analysis
- **decision_support**: Structured decision-making, alternatives analysis
- **code_analysis**: AST/ASG analysis, code metrics, documentation

## 🧬 LV Framework (Lotka-Volterra Ecosystem Intelligence)
Available templates for diversity preservation:
- `KNOWLEDGE_EXTRACT_LV`: Multi-strategy knowledge extraction
- `KNOWLEDGE_QUERY_LV`: Multi-perspective information synthesis
- `LV_SELECT`: Generic LV enhancement for any workflow

## 📊 System Usage
- Switch incarnations: `switch_incarnation(incarnation_type="...")`
- List available incarnations: `list_incarnations()`
- Check system health: `check_connection()`
- Get incarnation guidance: `get_guidance_hub()`

**Remember**: The system is designed for simplicity. Tool addition should be straightforward through inheritance patterns and automatic discovery.
"""

    # Register all general-purpose tools in the base incarnation
    _tool_methods: List[str] = [
        # Action templates
        "list_action_templates",
        "get_action_template",
        "add_template_feedback",
        # Project management
        "get_project",
        "list_projects",
        # Workflow tracking
        "log_workflow_execution",
        "get_workflow_history",
        # Best practices
        "get_best_practices",
        # Universal guidance access
        "get_base_guidance",
    ]

    def __init__(self, driver: AsyncDriver, database: str = "neo4j"):
        """Initialize the incarnation with database connection."""
        self.driver = driver
        self.database = database

    async def initialize_schema(self):
        """Initialize the Neo4j schema for this incarnation."""
        from ..event_loop_manager import safe_neo4j_session

        # Execute schema queries if defined
        if self.schema_queries:
            try:
                async with safe_neo4j_session(self.driver, self.database) as session:
                    # Execute each constraint/index query individually
                    for query in self.schema_queries:
                        await session.execute_write(lambda tx: tx.run(query).consume())  # type: ignore

                # Create guidance hub if needed
                await self.ensure_hub_exists()

                logger.info(f"{self.name} incarnation schema initialized")
            except Exception as e:
                logger.error(f"Error initializing schema for {self.name}: {e}")
                raise
        else:
            # No schema queries defined
            logger.warning(f"No schema queries defined for {self.name}")

            # Still create the hub
            await self.ensure_hub_exists()

    async def ensure_hub_exists(self):
        """Create the guidance hub for this incarnation if it doesn't exist."""
        from ..event_loop_manager import safe_neo4j_session

        hub_id = f"{self.name}_hub"

        # Also ensure universal base_hub exists for cross-incarnation access
        base_hub_query = """
        MERGE (hub:AiGuidanceHub {id: 'base_hub'})
        ON CREATE SET hub.description = $description,
                      hub.created_at = datetime(),
                      hub.updated_at = datetime()
        ON MATCH SET hub.updated_at = datetime()
        RETURN hub
        """

        incarnation_hub_query = """
        MERGE (hub:AiGuidanceHub {id: $hub_id})
        ON CREATE SET hub.description = $description,
                      hub.created_at = datetime(),
                      hub.updated_at = datetime()
        ON MATCH SET hub.updated_at = datetime()
        RETURN hub
        """

        try:
            async with safe_neo4j_session(self.driver, self.database) as session:
                # Create universal base hub
                await session.execute_write(lambda tx: tx.run(base_hub_query, {"description": self.hub_content}))

                # Create incarnation-specific hub
                await session.execute_write(lambda tx: tx.run(incarnation_hub_query, {
                    "hub_id": hub_id,
                    "description": self.hub_content
                }))

                logger.info(f"Ensured base_hub and {self.name}_hub exist")
        except Exception as e:
            logger.error(f"Error creating hubs for {self.name}: {e}")
            raise

    async def get_guidance_hub(self) -> List[types.TextContent]:
        """Get the guidance hub content for this incarnation."""
        from ..event_loop_manager import safe_neo4j_session

        hub_id = f"{self.name}_hub"

        query = """
        MATCH (hub:AiGuidanceHub {id: $hub_id})
        RETURN hub.description AS description
        """

        try:
            async with safe_neo4j_session(self.driver, self.database) as session:
                results = await session.execute_read(
                    lambda tx: self._read_query(tx, query, {"hub_id": hub_id})
                )
                results = json.loads(results)

                if results and len(results) > 0:
                    return [types.TextContent(type="text", text=results[0]["description"])]
                else:
                    # If hub doesn't exist, create it
                    await self.ensure_hub_exists()
                    # Try again
                    return await self.get_guidance_hub()
        except Exception as e:
            logger.error(f"Error retrieving guidance hub for {self.name}: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def get_base_guidance(self) -> List[types.TextContent]:
        """Get the universal base guidance hub content available to all incarnations."""
        from ..event_loop_manager import safe_neo4j_session

        query = """
        MATCH (hub:AiGuidanceHub {id: 'base_hub'})
        RETURN hub.description AS description
        """

        try:
            async with safe_neo4j_session(self.driver, self.database) as session:
                results = await session.execute_read(lambda tx: self._read_query(tx, query, {}))
                results = json.loads(results)

                if results and len(results) > 0:
                    return [types.TextContent(type="text", text=results[0]["description"])]
                else:
                    # If base hub doesn't exist, create it
                    await self.ensure_hub_exists()
                    # Try again
                    return await self.get_base_guidance()
        except Exception as e:
            logger.error(f"Error retrieving base guidance hub: {e}")
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

        # First, check if there's a hardcoded base list of tools
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
                        getattr(return_type, '__origin__', None) is list and
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

    # Track registered tools at the class level - using a class variable
    _registered_tool_methods = set()

    async def register_tools(self, server):
        """Identify tool methods and register them with the central ToolRegistry."""
        # Get all tool methods from this incarnation
        tool_methods = self.list_tool_methods()
        logger.info(f"Identified tool methods in {self.name}: {tool_methods}")

        # Register these tools with the central tool registry for tracking/listing
        from ..tool_registry import registry as tool_registry

        # Let register_class_tools handle adding to the registry's internal structures
        tools_added_to_registry_count = tool_registry.register_class_tools(self, self.name)

        # Log based on tools found and added to the registry
        logger.info(f"{self.name} incarnation: {tools_added_to_registry_count} tools added to ToolRegistry")

        # Return the count of tools identified/added to registry
        return len(tool_methods)

    async def _read_query(self, tx: AsyncManagedTransaction, query: str, params: dict) -> str:
        """Execute a read query and return results as JSON string."""
        # Ensure params is a dict, even if None is passed
        if params is None:
            params = {}
        result = await tx.run(cast(LiteralString, query), params)  # type: ignore
        records = await result.data()
        return json.dumps(records)

    async def _write(self, tx: AsyncManagedTransaction, query: str, params: dict):
        """Execute a write query and return the summary object."""
        # Ensure params is a dict, even if None is passed
        if params is None:
            params = {}
        result = await tx.run(cast(LiteralString, query), params)  # type: ignore
        summary = await result.consume()
        return summary

    async def safe_session(self):
        """
        Return a context manager for an async Neo4j session that handles event loop issues.

        This is a convenience method that incarnations can use to get a session
        that properly handles asyncio event loop management.

        Returns:
            An async context manager yielding a Neo4j session.

        Usage:
            async with self.safe_session() as session:
                # Use session here
        """
        from ..event_loop_manager import safe_neo4j_session
        return safe_neo4j_session(self.driver, self.database)


# End of base incarnation module
