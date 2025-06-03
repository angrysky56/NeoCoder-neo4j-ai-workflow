"""
Decorator utilities for NeoCoder Neo4j-Guided AI Workflow

This module provides decorators that simplify the creation and registration
of incarnation-specific tools and functionality.
"""

import functools
import logging
from typing import Any, Optional

import mcp.types as types
from pydantic import Field

from .tool_registry import registry

logger = logging.getLogger("mcp_neocoder.decorators")

def incarnation_tool(category: Optional[str] = None):
    """Decorator for marking methods as incarnation tools.

    This decorator marks a method as an incarnation tool and ensures it
    conforms to the expected signature and return type. It also automatically
    registers the tool with the global tool registry.

    Args:
        category: Optional category name. If not provided, uses the incarnation type.

    Returns:
        The decorated method.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Call the original function
            result = await func(self, *args, **kwargs)

            # Ensure the result is a list of TextContent
            if not isinstance(result, list) or not all(isinstance(item, types.TextContent) for item in result):
                logger.warning(f"Tool {func.__name__} returned invalid result: {result}")
                # Convert to proper return type
                if isinstance(result, str):
                    result = [types.TextContent(type="text", text=result)]
                elif not isinstance(result, list):
                    result = [types.TextContent(type="text", text=str(result))]

            # Register the tool
            tool_category = category or getattr(self, 'incarnation_type', 'general')
            registry.register_tool(wrapper, str(tool_category))

            return result

        # Update the wrapper's metadata to match the original function
        functools.update_wrapper(wrapper, func)

        return wrapper

    # Handle both @incarnation_tool and @incarnation_tool()
    if callable(category):
        func = category
        category = None
        return decorator(func)

    return decorator


def create_field(*args, **kwargs):
    """Helper function to create a Field with proper typing.

    This function makes it easier to create Pydantic Fields with
    the correct typing information.

    Args:
        *args: Positional arguments to pass to Field.
        **kwargs: Keyword arguments to pass to Field.

    Returns:
        A properly typed Field.
    """
    return Field(*args, **kwargs)


def create_incarnation_class(name: str,
                            description: str,
                            base_class,
                            incarnation_type: Any,
                            version: str = "0.1.0"):
    """Factory function to create new incarnation classes.

    This function makes it easier to create new incarnation classes
    with the proper structure and inheritance.

    Args:
        name: Name of the incarnation class.
        description: Description of the incarnation.
        base_class: Base class to inherit from.
        incarnation_type: The incarnation type enum value.
        version: Version string.

    Returns:
        A new incarnation class.
    """
    return type(name, (base_class,), {
        "incarnation_type": incarnation_type,
        "description": description,
        "version": version,
        "__doc__": description
    })
