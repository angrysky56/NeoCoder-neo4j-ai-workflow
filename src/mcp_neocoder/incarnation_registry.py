"""
Incarnation Registry System for NeoCoder Neo4j-Guided AI Workflow

This module provides a streamlined plugin system for registering and managing incarnations,
allowing new incarnations to be added without modifying the base code.
"""

import importlib
import inspect
import logging
import os
from typing import Dict, Type, List, Optional, Any

from .incarnations.base_incarnation import BaseIncarnation

logger = logging.getLogger("mcp_neocoder.incarnation_registry")

class IncarnationRegistry:
    """Registry for managing incarnation classes."""

    def __init__(self):
        """Initialize an empty incarnation registry."""
        self.incarnations: Dict[str, Type[BaseIncarnation]] = {}
        self.instances: Dict[str, BaseIncarnation] = {}
        self.loaded_modules = set()
        self.dynamic_types = {}  # Still needed for compatibility with existing code

    def register(self, incarnation_class: Type[BaseIncarnation]) -> None:
        """Register an incarnation class with the registry.

        Args:
            incarnation_class: The incarnation class to register.
        """
        # Check for name attribute
        if hasattr(incarnation_class, 'name'):
            incarnation_name = incarnation_class.name

            # Convert to string if it's an enum or other object with value attribute
            if not isinstance(incarnation_name, str) and hasattr(incarnation_name, 'value'):
                incarnation_name = incarnation_name.value
                incarnation_class.name = incarnation_name

            # Register using the name
            self.incarnations[incarnation_name] = incarnation_class
            logger.info(f"Registered incarnation: {incarnation_name} ({incarnation_class.__name__})")
        else:
            logger.warning(f"Cannot register {incarnation_class.__name__}: missing name attribute")

    def get(self, incarnation: str) -> Optional[Type[BaseIncarnation]]:
        """Get an incarnation class by its type identifier.

        Args:
            incarnation: The type identifier of incarnation to retrieve.

        Returns:
            The incarnation class, or None if not found.
        """
        return self.incarnations.get(incarnation)

    def get_instance(self, incarnation: str, driver: Any, database: str) -> Optional[BaseIncarnation]:
        """Get or create an incarnation instance.

        Args:
            incarnation: The type identifier of incarnation to retrieve.
            driver: The Neo4j driver to use.
            database: The Neo4j database name.

        Returns:
            An instance of the incarnation, or None if not found.
        """
        # Return existing instance if available
        if incarnation in self.instances:
            return self.instances[incarnation]

        # Get the class and create a new instance
        incarnation_class = self.get(incarnation)
        if not incarnation_class:
            return None

        # Create a new instance
        instance = incarnation_class(driver, database)
        self.instances[incarnation] = instance
        return instance

    def list(self) -> List[dict]:
        """List all registered incarnations.

        Returns:
            A list of dictionaries with incarnation metadata.
        """
        return [
            {
                "type": inc_type,
                "name": inc_class.__name__,
                "description": getattr(inc_class, 'description', "No description"),
                "version": getattr(inc_class, 'version', "Unknown")
            }
            for inc_type, inc_class in self.incarnations.items()
        ]

    def discover_dynamic_types(self) -> Dict[str, str]:
        """Discover incarnation types from actual implementations.

        This method scans all incarnation implementations and dynamically builds
        a set of types without any hardcoded references.

        Returns:
            Dict mapping uppercase identifiers to type values
        """
        dynamic_types = {}

        # Get the package directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        incarnations_dir = os.path.join(current_dir, "incarnations")

        if not os.path.exists(incarnations_dir):
            logger.warning(f"Incarnations directory not found: {incarnations_dir}")
            return dynamic_types

        # Simple discovery approach: scan for *_incarnation.py files
        for entry in os.listdir(incarnations_dir):
            if not entry.endswith('_incarnation.py') or entry.startswith('__'):
                continue

            # Skip base incarnation
            if entry == 'base_incarnation.py':
                continue

            # Extract type from filename (e.g., "data_analysis" from "data_analysis_incarnation.py")
            file_type = entry[:-14]  # Remove "_incarnation.py" (14 chars)
            if file_type:
                enum_name = file_type.upper()
                dynamic_types[enum_name] = file_type
                logger.info(f"Discovered incarnation type: {enum_name}={file_type}")

                # Also add simplified versions for easier reference
                if '_' in file_type:
                    parts = file_type.split('_')
                    simple_name = parts[0].upper()
                    if simple_name != enum_name and simple_name not in dynamic_types:
                        dynamic_types[simple_name] = file_type
                        logger.info(f"Added simplified alias: {simple_name}={file_type}")

        return dynamic_types

    def discover_incarnation_identifiers(self) -> Dict[str, str]:
        """Discover all incarnation identifiers from filenames.

        This method scans the incarnations directory for valid incarnation files
        and returns their identifiers.

        Returns:
            Dictionary of discovered incarnation identifiers
        """
        # Build on top of the existing dynamic types discovery
        discovered_types = self.discover_dynamic_types()

        # Just return the values (actual identifiers) rather than the enum mapping
        identifiers = {value: value for _, value in discovered_types.items()}

        if not identifiers:
            # Fallback to direct directory scan if no types were discovered
            current_dir = os.path.dirname(os.path.abspath(__file__))
            incarnations_dir = os.path.join(current_dir, "incarnations")

            if os.path.exists(incarnations_dir):
                for entry in os.listdir(incarnations_dir):
                    if entry.endswith('_incarnation.py') and not entry.startswith('__') and entry != 'base_incarnation.py':
                        # Extract identifier from filename
                        inc_type = entry[:-14]  # Remove "_incarnation.py"
                        identifiers[inc_type] = inc_type
                        logger.info(f"Direct scan found incarnation: {inc_type}")

        logger.info(f"Discovered incarnation identifiers: {list(identifiers.keys())}")
        return identifiers

    def discover(self) -> None:
        """Discover and register all incarnation classes in the package.

        This method scans the incarnations directory for classes that inherit from BaseIncarnation.
        """
        # Discover incarnation identifiers first
        self.discover_incarnation_identifiers()

        # Now discover incarnation classes
        current_dir = os.path.dirname(os.path.abspath(__file__))
        incarnations_dir = os.path.join(current_dir, "incarnations")

        logger.info(f"Searching for incarnations in: {incarnations_dir}")

        if not os.path.exists(incarnations_dir):
            logger.warning(f"Incarnations directory not found: {incarnations_dir}")
            return

        # Process each incarnation file
        for entry in os.listdir(incarnations_dir):
            # Only process *_incarnation.py files
            if not entry.endswith('_incarnation.py') or entry.startswith('__'):
                continue

            # Skip base incarnation
            if entry == 'base_incarnation.py':
                continue

            module_name = entry[:-3]  # Remove .py extension

            # Skip if already loaded
            if module_name in self.loaded_modules:
                logger.debug(f"Module {module_name} already loaded, skipping")
                continue

            # Import the module
            try:
                # Use importlib to load the module
                module = importlib.import_module(f"mcp_neocoder.incarnations.{module_name}")
                self.loaded_modules.add(module_name)

                # Find all incarnation classes in the module
                for name, obj in inspect.getmembers(module):
                    # Check if it's a class that inherits from BaseIncarnation
                    if (inspect.isclass(obj) and
                        issubclass(obj, BaseIncarnation) and
                        obj is not BaseIncarnation):

                        # Check if it has either 'incarnation' or 'name' attribute
                        if hasattr(obj, 'incarnation'):
                            # Get incarnation type as string (in case it's still an enum value)
                            inc_type = getattr(obj, 'incarnation')
                            if hasattr(inc_type, 'value'):  # Handle case where it might still be an enum
                                inc_type = inc_type.value

                            logger.info(f"Found incarnation class via 'incarnation' attribute: {name}, type: {inc_type}")

                            # Update the incarnation to be a string if it's not already
                            if hasattr(inc_type, 'value'):
                                setattr(obj, 'incarnation', inc_type)

                            # Add a name attribute if it doesn't exist
                            if not hasattr(obj, 'name'):
                                obj.name = inc_type

                            self.register(obj)
                        elif hasattr(obj, 'name'):
                            # Also register classes that have a 'name' but no 'incarnation' attribute
                            logger.info(f"Found incarnation class via 'name' attribute: {name}, name: {obj.name}")

                            # Add an incarnation attribute that matches the name for compatibility
                            if not hasattr(obj, 'incarnation'):
                                setattr(obj, 'incarnation', obj.name)

                            self.register(obj)
                        else:
                            logger.warning(f"Skipping class {name} in {module_name}: missing both 'incarnation' and 'name' attributes")
            except Exception as e:
                logger.error(f"Error importing incarnation module {module_name}: {e}")

    def discover_incarnations(self) -> List[str]:
        """Discover all incarnation types based on module filenames.

        This can be used even before classes are loaded to determine available incarnations.

        Returns:
            A list of incarnation type identifiers found in the directory.
        """
        incarnations = []

        # Get the package directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        incarnations_dir = os.path.join(current_dir, "incarnations")

        if not os.path.exists(incarnations_dir):
            logger.warning(f"Incarnations directory not found: {incarnations_dir}")
            return incarnations

        # Match module filenames to incarnation types
        for entry in os.listdir(incarnations_dir):
            if entry.startswith("__") or not entry.endswith(".py"):
                continue

            module_name = entry[:-3]  # Remove .py extension

            # Skip base modules and adapters
            if module_name in ("base_incarnation", "polymorphic_adapter"):
                continue

            # Try to match filename to incarnation type
            if module_name.endswith("_incarnation"):
                # Extract the type from the filename (e.g., research_incarnation.py -> research)
                incarnation_name = module_name.replace("_incarnation", "")
                incarnations.append(incarnation_name)

        return incarnations

    def create_template_incarnation(self, name: str, output_path: Optional[str] = None) -> str:
        """Create a template incarnation file with the given name.

        Args:
            name: The name of the incarnation (e.g., 'my_feature')
            output_path: Optional path to save the file (defaults to incarnations directory)

        Returns:
            The path to the created file
        """
        # Convert any format to snake_case
        name = name.lower().replace('-', '_').replace(' ', '_')
        if not name.endswith('_incarnation'):
            file_name = f"{name}_incarnation.py"
        else:
            file_name = f"{name}.py"
            name = name.replace('_incarnation', '')

        # Generate type value - ensure it's in snake_case
        type_value = name

        # Generate class name - class name should ALWAYS match the filename
        # without the .py suffix, e.g., DataAnalysisIncarnation for data_analysis_incarnation.py
        class_name = ''.join(word.capitalize() for word in name.split('_')) + 'Incarnation'

        # Determine output path
        if not output_path:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            output_path = os.path.join(current_dir, "incarnations", file_name)
        elif os.path.isdir(output_path):
            output_path = os.path.join(output_path, file_name)

        # Generate template content
        template = f'''"""
{class_name} for the NeoCoder framework.

This incarnation provides tools for {name.replace('_', ' ')} functionality.
"""

import json
import logging
import uuid
from typing import Dict, Any, List, Optional, Union

import mcp.types as types
from pydantic import Field
from neo4j import AsyncDriver, AsyncTransaction

from .base_incarnation import BaseIncarnation
from ..event_loop_manager import safe_neo4j_session

logger = logging.getLogger("mcp_neocoder.incarnations.{name}")


class {class_name}(BaseIncarnation):
    """
    {class_name} for the NeoCoder framework.

    Provides tools for {name.replace('_', ' ')} functionality.
    """

    # IMPORTANT: The class name above MUST match the filename pattern
    # e.g., {class_name} for {name}_incarnation.py

    # Define the incarnation type with a string identifier
    # This should match the filename without the '_incarnation.py' suffix
    incarnation_type = "{type_value}"

    # Metadata for display in the UI
    description = "{name.replace('_', ' ').title()} incarnation for the NeoCoder framework"
    version = "0.1.0"

    # Optional list of tool methods that should be registered
    _tool_methods = [
        "example_tool_one",
        "example_tool_two",
        "example_database_tool"
    ]

    # Schema creation queries - run when incarnation is initialized
    schema_queries = [
        f"CREATE CONSTRAINT {name}_entity_id IF NOT EXISTS FOR (e:{name.capitalize()}) REQUIRE e.id IS UNIQUE",
        f"CREATE INDEX {name}_entity_name IF NOT EXISTS FOR (e:{name.capitalize()}) ON (e.name)",
    ]

    # Hub content - what users see when they access this incarnation's guidance hub
    hub_content = """
# {name.replace('_', ' ').title()} Hub

Welcome to the {name.replace('_', ' ').title()} functionality powered by the NeoCoder framework.
This system provides the following capabilities:

## Key Features

1. **Feature One**
   - Capability one
   - Capability two
   - Capability three

2. **Feature Two**
   - Capability one
   - Capability two
   - Capability three

## Getting Started

- Use `example_tool_one()` to perform the first action
- Use `example_tool_two()` to perform the second action

Each entity in the system has full tracking and audit capabilities.
    """

    async def example_tool_one(
        self,
        param1: str = Field(..., description="Description of parameter 1"),
        param2: Optional[int] = Field(None, description="Description of parameter 2")
    ) -> List[types.TextContent]:
        """Example tool one for {name.replace('_', ' ')} incarnation."""
        try:
            # Implementation goes here
            response = f"Executed example_tool_one with param1={{param1}} and param2={{param2}}"
            return [types.TextContent(type="text", text=response)]
        except Exception as e:
            logger.error(f"Error in example_tool_one: {{e}}")
            return [types.TextContent(type="text", text=f"Error: {{e}}")]

    async def example_tool_two(
        self,
        param1: str = Field(..., description="Description of parameter 1")
    ) -> List[types.TextContent]:
        """Example tool two for {name.replace('_', ' ')} incarnation."""
        try:
            # Implementation goes here
            response = f"Executed example_tool_two with param1={{param1}}"
            return [types.TextContent(type="text", text=response)]
        except Exception as e:
            logger.error(f"Error in example_tool_two: {{e}}")
            return [types.TextContent(type="text", text=f"Error: {{e}}")]

    async def example_database_tool(
        self,
        query_param: str = Field(..., description="Parameter for database query")
    ) -> List[types.TextContent]:
        """Example database tool showing safe session usage."""
        try:
            # IMPORTANT: Always use safe_neo4j_session for database operations
            # This prevents "Future attached to a different loop" errors
            async with safe_neo4j_session(self.driver, self.database) as session:
                query = "MATCH (n) RETURN count(n) as node_count"
                result = await session.run(query)
                record = await result.single()
                node_count = record["node_count"] if record else 0

                response = f"Database query with param '{{query_param}}' returned {{node_count}} nodes"
                return [types.TextContent(type="text", text=response)]
        except Exception as e:
            logger.error(f"Error in example_database_tool: {{e}}")
            return [types.TextContent(type="text", text=f"Error: {{e}}")]'''

        # Create the file
        try:
            with open(output_path, 'w') as f:
                f.write(template)
            logger.info(f"Created template incarnation file: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error creating template incarnation file: {e}")
            raise

# Create a global registry instance
registry = IncarnationRegistry()
