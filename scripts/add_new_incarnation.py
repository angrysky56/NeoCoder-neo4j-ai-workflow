#!/usr/bin/env python
"""
Script to create a new incarnation for the NeoCoder framework.

This script creates a new incarnation file with the necessary boilerplate code.
Just modify the parameters below and run the script to generate a new incarnation.
"""

import sys
import argparse
from pathlib import Path

# Template for a new incarnation file
INCARNATION_TEMPLATE = '''"""
{name_title} incarnation of the NeoCoder framework.

{description}
"""

import json
import logging
import uuid
from typing import Dict, Any, List, Optional, Union

import mcp.types as types
from pydantic import Field
from neo4j import AsyncTransaction

from .polymorphic_adapter import BaseIncarnation, IncarnationType

logger = logging.getLogger("mcp_neocoder.incarnations.{name_lower}")


class {class_name}(BaseIncarnation):
    """
    {name_title} incarnation of the NeoCoder framework.

    {description}
    """

    # Define the incarnation type - must match an entry in IncarnationType enum
    incarnation_type = IncarnationType.{incarnation_type}

    # Metadata for display in the UI
    description = "{description}"
    version = "0.1.0"

    async def initialize_schema(self):
        """Initialize the Neo4j schema for {name_title}."""
        # Define constraints and indexes for the schema
        schema_queries = [
            # Example constraints
            "CREATE CONSTRAINT {name_lower}_entity_id IF NOT EXISTS FOR (e:{entity_type}) REQUIRE e.id IS UNIQUE",

            # Example indexes
            "CREATE INDEX {name_lower}_entity_name IF NOT EXISTS FOR (e:{entity_type}) ON (e.name)",
        ]

        try:
            async with self.driver.session(database=self.database) as session:
                # Execute each constraint/index query individually
                for query in schema_queries:
                    await session.execute_write(lambda tx: tx.run(query))

                # Create base guidance hub for this incarnation if it doesn't exist
                await self.ensure_guidance_hub_exists()

            logger.info("{name_title} incarnation schema initialized")
        except Exception as e:
            logger.error(f"Error initializing {name_lower} schema: {{e}}")
            raise

    async def ensure_guidance_hub_exists(self):
        """Create the guidance hub for this incarnation if it doesn't exist."""
        query = """
        MERGE (hub:AiGuidanceHub {{id: '{name_lower}_hub'}})
        ON CREATE SET hub.description = $description
        RETURN hub
        """

        description = """
# {name_title}

Welcome to the {name_title} powered by the NeoCoder framework.
This system helps you {description_lowercase} with the following capabilities:

## Key Features

1. **Feature One**
   - Capability one
   - Capability two
   - Capability three

2. **Feature Two**
   - Capability one
   - Capability two
   - Capability three

3. **Feature Three**
   - Capability one
   - Capability two
   - Capability three

## Getting Started

- Use `tool_one()` to get started
- Use `tool_two()` for the next step
- Use `tool_three()` to complete the process

Each entity in the system has full tracking and audit capabilities.
        """

        params = {{"description": description}}

        async with self.driver.session(database=self.database) as session:
            await session.execute_write(lambda tx: tx.run(query, params))

    async def get_guidance_hub(self):
        """Get the guidance hub for this incarnation."""
        query = """
        MATCH (hub:AiGuidanceHub {{id: '{name_lower}_hub'}})
        RETURN hub.description AS description
        """

        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_read(self._read_query, query, {{}})
                results = json.loads(results_json)

                if results and len(results) > 0:
                    return [types.TextContent(type="text", text=results[0]["description"])]
                else:
                    # If hub doesn't exist, create it
                    await self.ensure_guidance_hub_exists()
                    # Try again
                    return await self.get_guidance_hub()
        except Exception as e:
            logger.error(f"Error retrieving {name_lower} guidance hub: {{e}}")
            return [types.TextContent(type="text", text=f"Error: {{e}}")]

    # Example tool methods for this incarnation

    async def tool_one(
        self,
        param1: str = Field(..., description="Description of parameter 1"),
        param2: Optional[int] = Field(None, description="Description of parameter 2")
    ) -> List[types.TextContent]:
        """Tool one for {name_title} incarnation."""
        try:
            # Implementation goes here
            response = f"Executed tool_one with param1={{param1}} and param2={{param2}}"
            return [types.TextContent(type="text", text=response)]
        except Exception as e:
            logger.error(f"Error in tool_one: {{e}}")
            return [types.TextContent(type="text", text=f"Error: {{e}}")]

    async def tool_two(
        self,
        param1: str = Field(..., description="Description of parameter 1")
    ) -> List[types.TextContent]:
        """Tool two for {name_title} incarnation."""
        try:
            # Implementation goes here
            response = f"Executed tool_two with param1={{param1}}"
            return [types.TextContent(type="text", text=response)]
        except Exception as e:
            logger.error(f"Error in tool_two: {{e}}")
            return [types.TextContent(type="text", text=f"Error: {{e}}")]
'''


def add_incarnation_type_to_enum(incarnation_type, enum_file_path):
    """Add the new incarnation type to the IncarnationType enum."""
    with open(enum_file_path, 'r') as f:
        content = f.read()

    # Find the IncarnationType class
    enum_start = content.find("class IncarnationType(str, Enum):")
    if enum_start == -1:
        print("Error: Could not find IncarnationType class in polymorphic_adapter.py")
        return False

    # Find the end of the enum definition
    lines = content[enum_start:].split('\n')
    enum_end = 0
    i = 0
    for i, line in enumerate(lines):
        if i > 0 and (not line.strip() or not line.strip().startswith("SIMULATION")):
            enum_end = enum_start + sum(len(line_content) + 1 for line_content in lines[:i])
            break

    if enum_end == 0:
        print("Error: Could not find the end of the IncarnationType enum")
        return False

    # Get the last enum entry to determine the format
    last_enum_line = lines[i-1].strip()
    indent = ' ' * (len(last_enum_line) - len(last_enum_line.lstrip()))

    # Add the new enum entry
    new_content = content[:enum_end]
    new_content += f"\n{indent}{incarnation_type.upper()} = \"{incarnation_type.lower()}\"{' ' * 5}# {incarnation_type} incarnation"
    new_content += content[enum_end:]

    # Write the updated file
    with open(enum_file_path, 'w') as f:
        f.write(new_content)

    print(f"Added {incarnation_type.upper()} to IncarnationType enum")
    return True
def main():
    parser = argparse.ArgumentParser(description="Create a new incarnation for the NeoCoder framework")
    parser.add_argument("--name", required=True, help="Name of the incarnation (e.g., 'Knowledge Graph')")
    parser.add_argument("--type", required=True, help="Type identifier (e.g., 'knowledge_graph')")
    parser.add_argument("--description", required=True, help="Description of the incarnation")
    parser.add_argument("--entity", default="Entity", help="Main entity type for this incarnation")
    parser.add_argument("--dir", help="Directory containing the incarnations package")

    args = parser.parse_args()

    # Process arguments
    name = args.name
    incarnation_type = args.type
    description = args.description
    entity_type = args.entity

    # Convert name to different formats
    name_title = name.title()
    name_lower = name.lower().replace(" ", "_")
    description_lowercase = description[0].lower() + description[1:]

    # Generate class name
    class_name = "".join(word.title() for word in name.split())
    if not class_name.endswith("Incarnation"):
        class_name += "Incarnation"

    # Get incarnations directory
    if args.dir:
        inc_dir = Path(args.dir)
    else:
        # Try to find the directory relative to this script
        script_dir = Path(__file__).parent
        inc_dir = script_dir.parent / "src" / "mcp_neocoder" / "incarnations"

        if not inc_dir.exists():
            print(f"Error: Could not find incarnations directory at {inc_dir}")
            print("Please provide the directory with --dir")
            sys.exit(1)

    # Generate the incarnation file
    file_content = INCARNATION_TEMPLATE.format(
        name_title=name_title,
        name_lower=name_lower,
        class_name=class_name,
        incarnation_type=incarnation_type.upper(),
        description=description,
        description_lowercase=description_lowercase,
        entity_type=entity_type
    )

    # Create the file
    file_path = inc_dir / f"{name_lower}_incarnation.py"

    # Check if file already exists
    if file_path.exists():
        overwrite = input(f"File {file_path} already exists. Overwrite? (y/n): ").lower()
        if overwrite != 'y':
            print("Aborted.")
            sys.exit(0)

    # Write the file
    with open(file_path, 'w') as f:
        f.write(file_content)

    print(f"Created new incarnation file: {file_path}")

    # Add the incarnation type to the IncarnationType enum if it doesn't exist
    enum_file = inc_dir / "polymorphic_adapter.py"
    if enum_file.exists():
        # Check if the type already exists
        with open(enum_file, 'r') as f:
            enum_content = f.read()

        if incarnation_type.upper() not in enum_content:
            add_incarnation_type_to_enum(incarnation_type, enum_file)

    print(f"\nSuccessfully created {name_title} incarnation!")
    print(f"Class: {class_name}")
    print(f"Type: {incarnation_type.upper()}")
    print("\nNext steps:")
    print("1. Customize the schema initialization in initialize_schema()")
    print("2. Add more tools specific to this incarnation")
    print("3. Restart the server to load the new incarnation")


if __name__ == "__main__":
    main()
