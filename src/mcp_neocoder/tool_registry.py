"""
Tool Registry System for NeoCoder Neo4j-Guided AI Workflow

This module provides a centralized system for registering and managing tools across
different incarnations, making it easy to add, discover, and manage tools dynamically.
"""

import inspect
import logging
from typing import Any, Callable, Dict, List, Set

import mcp.types as types

logger = logging.getLogger("mcp_neocoder.tool_registry")

class ToolRegistry:
    """Registry for managing and discovering tools."""

    def __init__(self):
        """Initialize an empty tool registry."""
        self.tools: Dict[str, Callable] = {}
        self.tool_categories: Dict[str, Set[str]] = {}
        self.tool_descriptions: Dict[str, str] = {}
        self.tool_full_docs: Dict[str, str] = {}
        self.registered_classes: Set[str] = set()

    def register_tool(self, tool_func: Callable, category: str = "general") -> None:
        """Register a tool function with the registry.

        Args:
            tool_func: The tool function to register.
            category: The category to assign to the tool (e.g., 'research', 'decision').
        """
        tool_name = tool_func.__name__

        # Skip if already registered
        if tool_name in self.tools:
            logger.debug(f"Tool '{tool_name}' already registered, skipping.")
            return

        # Add tool to registry
        self.tools[tool_name] = tool_func

        # Add to category
        if category not in self.tool_categories:
            self.tool_categories[category] = set()
        self.tool_categories[category].add(tool_name)

        # Extract description from docstring
        if tool_func.__doc__:
            self.tool_descriptions[tool_name] = tool_func.__doc__.split('\n')[0].strip()
            self.tool_full_docs[tool_name] = tool_func.__doc__.strip()
        else:
            self.tool_descriptions[tool_name] = f"{tool_name} tool"
            self.tool_full_docs[tool_name] = f"{tool_name} tool"

        logger.info(f"Registered tool '{tool_name}' in category '{category}'")

    def register_class_tools(self, obj: Any, category: str = "general") -> int:
        """Register all tool methods from a class instance.

        Args:
            obj: The class instance containing tool methods.
            category: The category to assign to the tools.

        Returns:
            int: Number of tools registered
        """
        # Skip if class already registered
        class_id = f"{obj.__class__.__name__}@{id(obj)}"
        if class_id in self.registered_classes:
            logger.debug(f"Class {obj.__class__.__name__} already registered, skipping.")
            return 0

        # Find all methods that return List[types.TextContent]
        count = 0

        # If the object has a list_tool_methods method, use that
        if hasattr(obj, 'list_tool_methods') and callable(getattr(obj, 'list_tool_methods')):
            try:
                tool_method_names = obj.list_tool_methods()
                logger.info(f"Found {len(tool_method_names)} tools via list_tool_methods: {tool_method_names}")

                for name in tool_method_names:
                    if not hasattr(obj, name):
                        logger.warning(f"Method {name} listed in list_tool_methods not found in {obj.__class__.__name__}")
                        continue

                    method = getattr(obj, name)
                    if callable(method):
                        self.register_tool(method, category)
                        count += 1
                    else:
                        logger.warning(f"Attribute {name} in {obj.__class__.__name__} is not callable")
            except Exception as e:
                logger.error(f"Error using list_tool_methods for {obj.__class__.__name__}: {e}")
                # Fall back to inspection
                count += self._register_tools_by_inspection(obj, category)
        else:
            # Use inspection to find tool methods if no list_tool_methods
            logger.info(f"No list_tool_methods found in {obj.__class__.__name__}, using inspection")
            count = self._register_tools_by_inspection(obj, category)

        # Mark class as registered only if we found tools
        if count > 0:
            self.registered_classes.add(class_id)

        logger.info(f"Registered {count} tools from class {obj.__class__.__name__}")
        return count

    def _register_tools_by_inspection(self, obj: Any, category: str) -> int:
        """Register tool methods by inspecting a class.

        Args:
            obj: The class instance to inspect
            category: The category to assign tools to

        Returns:
            int: Number of tools registered
        """
        count = 0
        for name, method in inspect.getmembers(obj, inspect.ismethod):
            # Skip private methods and common base methods
            if name.startswith('_') or name in ('initialize_schema', 'get_guidance_hub',
                                              'register_tools', 'list_tool_methods',
                                              '_read_query', '_write'):
                continue

            # Check return type annotation if available
            tool_method = False
            if hasattr(method, '__annotations__'):
                return_type = method.__annotations__.get('return')
                if return_type and (
                    return_type == List[types.TextContent] or
                    getattr(return_type, '__origin__', None) is list and
                    getattr(return_type, '__args__', [None])[0] == types.TextContent
                ):
                    tool_method = True

            # If the method is directly in the incarnation class (not base class)
            # and it's an async function, treat it as a potential tool
            if not tool_method and name in obj.__class__.__dict__:
                method_obj = obj.__class__.__dict__[name]
                if inspect.iscoroutinefunction(method_obj):
                    logger.info(f"Found potential async tool method: {name}")
                    tool_method = True

            if tool_method:
                logger.info(f"Registering tool method via inspection: {name}")
                self.register_tool(method, category)
                count += 1

        return count

    # Track registered tools at the class level using a set
    _mcp_registered_tools = set()

    def register_tools_with_server(self, server) -> int:
        """Register all tools with an MCP server.

        Args:
            server: The MCP server to register tools with.

        Returns:
            The number of tools registered.
        """
        count = 0
        # Log the tool names for debugging
        logger.debug(f"Tools available for registration: {list(self.tools.keys())}")

        for tool_name, tool_func in self.tools.items():
            try:
                # Generate a unique key for this tool function
                registration_key = f"{tool_func.__module__}.{tool_func.__qualname__}"

                # Check if tool has already been registered to avoid duplicates
                if registration_key not in self._mcp_registered_tools:
                    server.mcp.add_tool(tool_func)
                    # Add to our registry's class-level set instead of trying to set attribute on method
                    self._mcp_registered_tools.add(registration_key)
                    logger.info(f"Added tool '{tool_name}' to MCP server")
                    count += 1
                else:
                    logger.info(f"Tool '{tool_name}' already registered, skipping")
            except Exception as e:
                logger.error(f"Error adding tool '{tool_name}' to MCP server: {e}")

        return count

    def register_incarnation_tools(self, incarnation_instance, server) -> int:
        """Register all tools from a specific incarnation with the MCP server.

        Args:
            incarnation_instance: The incarnation instance containing tool methods
            server: The MCP server to register tools with

        Returns:
            The number of tools registered
        """
        if not incarnation_instance:
            logger.warning("No incarnation instance provided, skipping tool registration")
            return 0

        # Get the incarnation category
        category = incarnation_instance.name
        logger.info(f"Registering tools from {category} incarnation")

        # Register tools from the incarnation
        tool_count = self.register_class_tools(incarnation_instance, category)
        logger.info(f"Found {tool_count} tools in {category} incarnation")

        if tool_count == 0:
            # Try to introspect methods directly as a fallback
            logger.info(f"Attempting direct method inspection for {category}")
            import inspect

            # Check for methods with MCP tool signature
            for name, method in inspect.getmembers(incarnation_instance, inspect.ismethod):
                # Skip private methods and inherited methods from BaseIncarnation
                if (name.startswith('_') or
                    name in ('initialize_schema', 'get_guidance_hub', 'register_tools', 'list_tool_methods')):
                    continue

                # Check method signature
                try:
                    inspect.signature(method)
                    # Check if this looks like a tool method (has type annotations)
                    if hasattr(method, '__annotations__') and 'return' in method.__annotations__:
                        logger.info(f"Found potential tool method: {name}")
                        self.register_tool(method, category)
                        tool_count += 1
                except Exception as e:
                    logger.error(f"Error inspecting method {name}: {e}")

        # Add each new tool to the MCP server
        added_count = 0
        tools_in_category = self.tool_categories.get(category, set())
        logger.info(f"Tools in category {category}: {tools_in_category}")

        for tool_name in tools_in_category:
            if tool_name in self.tools:
                tool_func = self.tools[tool_name]
                # Generate a unique key for this tool function
                registration_key = f"{tool_func.__module__}.{tool_func.__qualname__}"

                # Only add tools that haven't been registered yet
                if registration_key not in self._mcp_registered_tools:
                    try:
                        server.mcp.add_tool(tool_func)
                        # Add to our registry's set
                        self._mcp_registered_tools.add(registration_key)
                        logger.info(f"Added tool '{tool_name}' from {category} to MCP server")
                        added_count += 1
                    except Exception as e:
                        logger.error(f"Error adding tool '{tool_name}' to MCP server: {e}")

        logger.info(f"Successfully registered {added_count} tools from {category} incarnation")
        return added_count

    def get_tools_by_category(self, category: str) -> List[Callable]:
        """Get all tools in a category.

        Args:
            category: The category to get tools for.

        Returns:
            A list of tool functions.
        """
        tool_names = self.tool_categories.get(category, set())
        return [self.tools[name] for name in tool_names if name in self.tools]

    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get descriptions for all registered tools.

        Returns:
            A dictionary mapping tool names to descriptions.
        """
        return self.tool_descriptions

    def get_full_tool_description(self, tool_name: str) -> str:
        """Get the full docstring for a tool."""
        return self.tool_full_docs.get(tool_name, "No description available.")

    def clear_category(self, category: str) -> None:
        """Remove all tools in a category.

        Args:
            category: The category to clear.
        """
        if category not in self.tool_categories:
            return

        for tool_name in self.tool_categories[category]:
            if tool_name in self.tools:
                del self.tools[tool_name]
                if tool_name in self.tool_descriptions:
                    del self.tool_descriptions[tool_name]
                if tool_name in self.tool_full_docs:
                    del self.tool_full_docs[tool_name]

        del self.tool_categories[category]
        logger.info(f"Cleared tools in category '{category}'")


# Create a global registry instance
registry = ToolRegistry()
