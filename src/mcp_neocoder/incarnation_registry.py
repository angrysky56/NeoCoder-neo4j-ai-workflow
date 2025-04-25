"""
Incarnation Registry System for NeoCoder Neo4j-Guided AI Workflow

This module provides a streamlined plugin system for registering and managing incarnations,
allowing new incarnations to be added without modifying the base code.
"""

import importlib
import inspect
import logging
import os
import pkgutil
import sys
import re
from pathlib import Path
from typing import Dict, Type, List, Optional, Any, Tuple, Set

from .incarnations.base_incarnation import BaseIncarnation, IncarnationType, get_incarnation_type_from_filename

logger = logging.getLogger("mcp_neocoder.incarnation_registry")

class IncarnationRegistry:
    """Registry for managing incarnation classes."""

    def __init__(self):
        """Initialize an empty incarnation registry."""
        self.incarnations: Dict[IncarnationType, Type[BaseIncarnation]] = {}
        self.instances: Dict[IncarnationType, BaseIncarnation] = {}
        self.loaded_modules = set()
        self.dynamic_types = {}

    def register(self, incarnation_class: Type[BaseIncarnation]) -> None:
        """Register an incarnation class with the registry.

        Args:
            incarnation_class: The incarnation class to register.
        """
        # Check if the class has the required incarnation_type attribute
        if not hasattr(incarnation_class, 'incarnation_type'):
            logger.warning(f"Cannot register {incarnation_class.__name__}: missing incarnation_type attribute")
            return

        incarnation_type = incarnation_class.incarnation_type

        # Log registration
        logger.info(f"Registering incarnation: {incarnation_type.value} ({incarnation_class.__name__})")

        # Add to registry
        self.incarnations[incarnation_type] = incarnation_class

    def get(self, incarnation_type: IncarnationType) -> Optional[Type[BaseIncarnation]]:
        """Get an incarnation class by its type.

        Args:
            incarnation_type: The type of incarnation to retrieve.

        Returns:
            The incarnation class, or None if not found.
        """
        return self.incarnations.get(incarnation_type)

    def get_instance(self, incarnation_type: IncarnationType, driver: Any, database: str) -> Optional[BaseIncarnation]:
        """Get or create an incarnation instance.

        Args:
            incarnation_type: The type of incarnation to retrieve.
            driver: The Neo4j driver to use.
            database: The Neo4j database name.

        Returns:
            An instance of the incarnation, or None if not found.
        """
        # Return existing instance if available
        if incarnation_type in self.instances:
            return self.instances[incarnation_type]

        # Get the class and create a new instance
        incarnation_class = self.get(incarnation_type)
        if not incarnation_class:
            return None

        # Create a new instance
        instance = incarnation_class(driver, database)
        self.instances[incarnation_type] = instance
        return instance

    def list(self) -> List[dict]:
        """List all registered incarnations.

        Returns:
            A list of dictionaries with incarnation metadata.
        """
        return [
            {
                "type": inc_type.value,
                "name": inc_class.__name__,
                "description": getattr(inc_class, 'description', "No description"),
                "version": getattr(inc_class, 'version', "Unknown")
            }
            for inc_type, inc_class in self.incarnations.items()
        ]

    def discover_dynamic_types(self) -> Dict[str, str]:
        """Discover potential new incarnation types from filenames.
        
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
            
        # Check all Python files in the directory
        for entry in os.listdir(incarnations_dir):
            if not entry.endswith('.py') or entry.startswith('__'):
                continue
                
            # Skip base modules
            if entry in ['base_incarnation.py', 'polymorphic_adapter.py']:
                continue
                
            # Extract potential type from filename
            type_value = get_incarnation_type_from_filename(entry)
            if type_value:
                # Convert snake_case to UPPER_SNAKE_CASE for enum name
                enum_name = type_value.upper()
                
                # Check if this type is already in IncarnationType
                if not any(member.value == type_value for member in IncarnationType):
                    dynamic_types[enum_name] = type_value
                    logger.info(f"Discovered potential new incarnation type: {enum_name}={type_value}")
        
        return dynamic_types

    def extend_incarnation_types(self) -> Type[IncarnationType]:
        """Extend the IncarnationType enum with dynamically discovered types.
        
        Returns:
            The updated IncarnationType enum class
        """
        # Discover dynamic types
        self.dynamic_types = self.discover_dynamic_types()
        
        if not self.dynamic_types:
            logger.info("No new incarnation types discovered")
            return IncarnationType
            
        # Extend the enum with new types
        extended_enum = IncarnationType.extend(self.dynamic_types)
        logger.info(f"Extended IncarnationType with {len(self.dynamic_types)} new types: {list(self.dynamic_types.keys())}")
        
        # Update global reference
        sys.modules[IncarnationType.__module__].IncarnationType = extended_enum
        
        return extended_enum

    def discover(self) -> None:
        """Discover and register all incarnation classes in the package.

        This method scans the incarnations directory for classes that inherit from BaseIncarnation.
        """
        # First extend the IncarnationType enum with dynamic types
        self.extend_incarnation_types()
        
        # Now discover incarnation classes
        current_dir = os.path.dirname(os.path.abspath(__file__))
        incarnations_dir = os.path.join(current_dir, "incarnations")

        logger.info(f"Searching for incarnations in: {incarnations_dir}")

        if not os.path.exists(incarnations_dir):
            logger.warning(f"Incarnations directory not found: {incarnations_dir}")
            return

        # Load all Python files in the incarnations directory
        for entry in os.listdir(incarnations_dir):
            # Skip __init__.py, __pycache__, and other non-Python files
            if entry.startswith("__") or not entry.endswith(".py"):
                continue
                
            # Skip base modules
            if entry in ["base_incarnation.py", "polymorphic_adapter.py"]:
                continue

            module_name = entry[:-3]  # Remove .py extension
            module_path = os.path.join(incarnations_dir, entry)

            try:
                if module_name in self.loaded_modules:
                    logger.debug(f"Module {module_name} already loaded, skipping")
                    continue

                # Dynamically import the module
                spec = importlib.util.spec_from_file_location(
                    f"mcp_neocoder.incarnations.{module_name}",
                    module_path
                )
                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module
                spec.loader.exec_module(module)
                self.loaded_modules.add(module_name)

                logger.info(f"Loaded incarnation module: {module_name}")

                # Find all classes that inherit from BaseIncarnation
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and
                        issubclass(obj, BaseIncarnation) and
                        obj is not BaseIncarnation):
                        # Log details of found incarnation for debugging
                        logger.info(f"Found incarnation class: {name}, type: {getattr(obj, 'incarnation_type', 'Unknown')}")
                        self.register(obj)

            except Exception as e:
                logger.error(f"Error discovering incarnation in module {module_name}: {e}")
                import traceback
                logger.error(traceback.format_exc())

    def discover_incarnation_types(self) -> List[IncarnationType]:
        """Discover all incarnation types based on module filenames.

        This can be used even before classes are loaded to determine available incarnations.

        Returns:
            A list of incarnation types found in the directory.
        """
        incarnation_types = []

        # Get the package directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        incarnations_dir = os.path.join(current_dir, "incarnations")

        if not os.path.exists(incarnations_dir):
            logger.warning(f"Incarnations directory not found: {incarnations_dir}")
            return incarnation_types

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

                # Find matching IncarnationType
                for inc_type in IncarnationType:
                    if inc_type.value.startswith(incarnation_name):
                        incarnation_types.append(inc_type)
                        break

        return incarnation_types

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
        
        # Generate class name - convert to CamelCase
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
from neo4j import AsyncTransaction

from .base_incarnation import BaseIncarnation, IncarnationType

logger = logging.getLogger("mcp_neocoder.incarnations.{name}")


class {class_name}(BaseIncarnation):
    """
    {class_name} for the NeoCoder framework.
    
    Provides tools for {name.replace('_', ' ')} functionality.
    """
    
    # Define the incarnation type - must match an entry in IncarnationType enum
    # This will be auto-discovered based on the filename
    incarnation_type = IncarnationType.{name.upper()}
    
    # Metadata for display in the UI
    description = "{name.replace('_', ' ').title()} incarnation for the NeoCoder framework"
    version = "0.1.0"
    
    # Optional list of tool methods that should be registered
    _tool_methods = [
        "example_tool_one",
        "example_tool_two"
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
'''

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
