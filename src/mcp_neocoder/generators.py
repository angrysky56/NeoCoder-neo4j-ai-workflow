"""
Generator tools for NeoCoder Neo4j AI Workflow

This module provides tools for generating new components like incarnations and tools,
making it easy to extend the system without modifying core files.
"""

import logging
import os
from typing import List, Optional

import mcp.types as types
from pydantic import Field

from .incarnation_registry import registry as incarnation_registry

logger = logging.getLogger("mcp_neocoder.generators")

def create_incarnation_template(
    name: str = Field(..., description="Name for the new incarnation (e.g., 'visual_analysis')"),
    description: Optional[str] = Field(None, description="Description of what this incarnation does"),
    tool_names: Optional[List[str]] = Field(None, description="Names of tools to include in the template")
) -> List[types.TextContent]:
    """Create a new incarnation template file.

    This tool creates a Python file for a new incarnation with the necessary structure
    and boilerplate code, making it easy to extend the system with custom functionality.

    The generated incarnation will be auto-discovered and available for use immediately.
    """
    try:
        # Ensure name is in the right format
        name = name.lower().replace(' ', '_').replace('-', '_')
        if name.endswith('_incarnation'):
            name = name[:-12]  # Remove _incarnation suffix if present

        # Create the template file
        output_path = incarnation_registry.create_template_incarnation(name)

        response = f"""# Incarnation Template Created

A new incarnation template has been created:

**File path:** `{output_path}`
**Name:** {name}
**Class:** {name.title().replace('_', '')}Incarnation

## Next Steps

1. Edit the generated file to customize:
   - Tool methods to meet your specific needs
   - Schema queries for any required database structure
   - Hub content to provide guidance for users

2. Restart the NeoCoder server to load your new incarnation

3. Switch to your incarnation using:
   ```
   switch_incarnation(incarnation_type="{name}")
   ```

Your incarnation will be automatically discovered thanks to the plugin architecture, without requiring any changes to the core system.
"""

        return [types.TextContent(type="text", text=response)]
    except Exception as e:
        logger.error(f"Error creating incarnation template: {e}")
        return [types.TextContent(type="text", text=f"Error creating incarnation template: {e}")]


def create_tool_template(
    name: str = Field(..., description="Name for the new tool (e.g., 'analyze_data')"),
    incarnation: str = Field(..., description="Name of the incarnation to add this tool to"),
    description: Optional[str] = Field(None, description="Description of what this tool does"),
    parameters: Optional[List[str]] = Field(None, description="Parameter names for the tool (e.g., ['file_path', 'limit'])")
) -> List[types.TextContent]:
    """Create a new tool template in an existing incarnation.

    This tool adds a new tool method to an existing incarnation file, with the proper structure
    and annotations to ensure it's automatically registered with the system.
    """
    # Normalize names
    name = name.lower().replace(' ', '_').replace('-', '_')
    incarnation = incarnation.lower().replace(' ', '_').replace('-', '_')
    if incarnation.endswith('_incarnation'):
        incarnation = incarnation[:-12]

    # Find the incarnation file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    incarnation_file = os.path.join(current_dir, "incarnations", f"{incarnation}_incarnation.py")

    if not os.path.exists(incarnation_file):
        return [types.TextContent(
            type="text",
            text=f"Error: Incarnation file not found: {incarnation_file}\n\nPlease create the incarnation first."
        )]

    # Generate tool method template
    param_list = parameters or ["param1", "param2"]
    param_definitions = []
    for param in param_list:
        param_definitions.append(
            f"        {param}: str = Field(..., description=\"Description of {param}\")"
        )

    tool_template = f"""
    async def {name}(
        self,
{chr(10).join(param_definitions)}
    ) -> List[types.TextContent]:
        \"""{description or f"Tool for {name.replace('_', ' ')} functionality."}\"\"\"
        try:
            # Implementation goes here
            # For database operations, use safe_neo4j_session:
            # async with safe_neo4j_session(self.driver, self.database) as session:
            #     result = await session.run("YOUR CYPHER QUERY")
            #     data = await result.data()

            response = f"Executed {name} with {' and '.join(f'{param}={{{param}}}' for param in param_list)}"
            return [types.TextContent(type="text", text=response)]
        except Exception as e:
            logger.error(f"Error in {name}: {{e}}")
            return [types.TextContent(type="text", text=f"Error: {{e}}")]
"""

    try:
        # Read the incarnation file
        with open(incarnation_file, 'r') as f:
            content = f.read()

        # Find the end of the class
        lines = content.split('\n')
        class_found = False
        tool_methods_list = None
        insert_position = len(lines) - 1

        for i, line in enumerate(lines):
            # Check for class definition
            if line.startswith("class ") and "Incarnation" in line and "(" in line:
                class_found = True
                continue

            # Check for _tool_methods list
            if class_found and "_tool_methods" in line and "[" in line:
                tool_methods_list = i

            # Find a good position to insert the tool
            if class_found and line.startswith("    async def "):
                if i > insert_position:
                    insert_position = i

        # If we didn't find the class or a good insert position, insert at the end
        if not class_found:
            return [types.TextContent(
                type="text",
                text=f"Error: Could not find incarnation class in {incarnation_file}"
            )]

        # Insert the tool method
        lines.insert(insert_position + 1, tool_template)

        # If _tool_methods exists, add this tool to it
        if tool_methods_list is not None:
            tool_methods_line = lines[tool_methods_list]
            if tool_methods_line.endswith("]"):
                # Add the new tool to the list
                if "]" in tool_methods_line:
                    lines[tool_methods_list] = tool_methods_line.replace("]", f', "{name}"]')
                else:
                    # List continues on next line, find end
                    for j in range(tool_methods_list + 1, len(lines)):
                        if "]" in lines[j]:
                            list_end = lines[j].find("]")
                            lines[j] = lines[j][:list_end] + f', "{name}"' + lines[j][list_end:]
                            break

        # Write back to the file
        with open(incarnation_file, 'w') as f:
            f.write('\n'.join(lines))

        return [types.TextContent(
            type="text",
            text=f"""# Tool Template Added

The tool `{name}` has been added to the `{incarnation}` incarnation.

**File:** `{incarnation_file}`

## Next Steps

1. Edit the generated tool method to implement your specific functionality
2. Restart the NeoCoder server to make the new tool available
3. Switch to the incarnation: `switch_incarnation(incarnation_type="{incarnation}")`
4. Use your new tool: `{name}({', '.join(f'{p}="value"' for p in param_list)})`
"""
        )]
    except Exception as e:
        logger.error(f"Error creating tool template: {e}")
        return [types.TextContent(type="text", text=f"Error creating tool template: {e}")]
