# NeoCoder Incarnations Guide

This document provides detailed information about NeoCoder's incarnation system and how to use and create incarnations.

## What are Incarnations?

Incarnations are different operational modes that allow the NeoCoder framework to adapt to different use cases while preserving the core Neo4j graph structure. Each incarnation provides specialized tools and schema optimized for particular tasks.

Think of incarnations as "brains" that can be swapped in and out of the same Neo4j core, transforming the system's functionality and purpose.

## Available Incarnations

The NeoCoder framework currently supports the following incarnations:

| Incarnation Type | Description | Focus Area |
|------------------|-------------|------------|
| `coding` | Original coding workflow management | Software development |
| `research_orchestration` | Scientific research platform | Research and experimentation |
| `decision_support` | Decision analysis system | Decision-making processes |
| `continuous_learning` | Adaptive learning environment | Education and training |
| `complex_system` | Complex system simulator | System modeling & simulation |
| `knowledge_graph` | Knowledge graph management | Knowledge representation |
| `data_analysis` | Data analysis workflow | Data analytics & visualization |

## Using Incarnations

### Starting with a Specific Incarnation

You can start the NeoCoder server with a specific incarnation in several ways:

```bash
# List available incarnations
python -m mcp_neocoder.server --list-incarnations

# Start with a specific incarnation
python -m mcp_neocoder.server --incarnation continuous_learning

# Start with debug logging
python -m mcp_neocoder.server --incarnation data_analysis --debug
```

You can also set the default incarnation in your environment variables:

```bash
export DEFAULT_INCARNATION=research_orchestration
python -m mcp_neocoder.server
```

### Switching Incarnations at Runtime

Incarnations can be switched at runtime using the `switch_incarnation()` tool:

```
switch_incarnation(incarnation_type="complex_system")
```

The system will dynamically load the incarnation, initialize its schema, and register its tools.

### Finding Available Incarnations

You can list all available incarnations using the `list_incarnations()` tool:

```
list_incarnations()
```

## Creating a New Incarnation

### Basic Structure

To create a new incarnation, you need to:

1. Add your incarnation type to the `IncarnationType` enum in `polymorphic_adapter.py`
2. Create a new file in the `src/mcp_neocoder/incarnations/` directory with naming pattern `your_incarnation_name_incarnation.py`
3. Implement the required class structure

### Template

Here's a template for creating a new incarnation:

```python
"""
Your incarnation name and description
"""

import json
import logging
import uuid
from typing import Dict, Any, List, Optional, Union

import mcp.types as types
from pydantic import Field
from neo4j import AsyncTransaction

from .polymorphic_adapter import BaseIncarnation, IncarnationType

logger = logging.getLogger("mcp_neocoder.incarnations.your_incarnation_name")


class YourIncarnationNameIncarnation(BaseIncarnation):
    """
    Your detailed incarnation description here
    """
    
    # Define the incarnation type - must match an entry in IncarnationType enum
    incarnation_type = IncarnationType.YOUR_INCARNATION_TYPE
    
    # Metadata for display in the UI
    description = "Your incarnation short description"
    version = "0.1.0"
    
    # Initialize schema and define hub content
    async def initialize_schema(self):
        """Initialize the Neo4j schema for this incarnation."""
        # Define constraints and indexes for your schema
        schema_queries = [
            "CREATE CONSTRAINT your_entity_id IF NOT EXISTS FOR (e:YourEntity) REQUIRE e.id IS UNIQUE",
            "CREATE INDEX your_entity_name IF NOT EXISTS FOR (e:YourEntity) ON (e.name)",
        ]
        
        try:
            async with self.driver.session(database=self.database) as session:
                # Execute each constraint/index query individually
                for query in schema_queries:
                    await session.execute_write(lambda tx: tx.run(query))
                    
                # Create guidance hub for this incarnation
                await self.ensure_guidance_hub_exists()
                
            logger.info("Your incarnation schema initialized")
        except Exception as e:
            logger.error(f"Error initializing your incarnation schema: {e}")
            raise
    
    async def ensure_guidance_hub_exists(self):
        """Create the guidance hub for this incarnation if it doesn't exist."""
        query = """
        MERGE (hub:AiGuidanceHub {id: 'your_incarnation_type_hub'})
        ON CREATE SET hub.description = $description
        RETURN hub
        """
        
        description = """
# Your Incarnation Name

Welcome to Your Incarnation Name powered by the NeoCoder framework.
This system helps you do X with the following capabilities:

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
        
        params = {"description": description}
        
        async with self.driver.session(database=self.database) as session:
            await session.execute_write(lambda tx: tx.run(query, params))
    
    # Example tools for your incarnation
    
    async def tool_one(
        self,
        param1: str = Field(..., description="Description of parameter 1"),
        param2: Optional[int] = Field(None, description="Description of parameter 2")
    ) -> List[types.TextContent]:
        """Tool one for your incarnation."""
        try:
            # Implementation goes here
            response = f"Executed tool_one with param1={param1} and param2={param2}"
            return [types.TextContent(type="text", text=response)]
        except Exception as e:
            logger.error(f"Error in tool_one: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]
    
    async def tool_two(
        self,
        param1: str = Field(..., description="Description of parameter 1")
    ) -> List[types.TextContent]:
        """Tool two for your incarnation."""
        try:
            # Implementation goes here
            response = f"Executed tool_two with param1={param1}"
            return [types.TextContent(type="text", text=response)]
        except Exception as e:
            logger.error(f"Error in tool_two: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]
```

### Adding Your Incarnation Type

You'll need to add your incarnation type to the `IncarnationType` enum in `polymorphic_adapter.py`:

```python
class IncarnationType(str, Enum):
    """Currently supported incarnation types for the NeoCoder framework."""
    DATA_ANALYSIS = "data_analysis"         # Data analysis incarnation
    CODING = "coding"                       # Original coding workflow
    RESEARCH = "research_orchestration"     # Research lab notebook
    DECISION = "decision_support"           # Decision-making system
    LEARNING = "continuous_learning"        # Learning environment
    SIMULATION = "complex_system"           # Complex system simulator
    KNOWLEDGE_GRAPH = "knowledge_graph"     # Knowledge graph management
    YOUR_TYPE = "your_incarnation_type"     # Your new incarnation
```

### Tool Registration

Tools are automatically registered based on method signatures. Any method in your incarnation class that:

1. Has `async def` and returns `List[types.TextContent]`
2. Does not start with `_` (private methods)

will be automatically registered as a tool. The MCP server will make these tools available to AI assistants.

## Best Practices

1. **Naming Convention**: Use the `name_incarnation.py` format for file names
2. **Schema Initialization**: Always include schema initialization with constraints and indexes
3. **Hub Content**: Provide detailed guidance hub content to explain your incarnation's purpose and tools
4. **Error Handling**: Include try/except blocks in all tool methods
5. **Logging**: Use the logger for important operations and errors
6. **Documentation**: Document all parameters and their descriptions
7. **Consistency**: Follow existing patterns for schema and tool design

## Debugging Incarnations

If you're having issues with your incarnation, you can enable debug logging:

```bash
python -m mcp_neocoder.server --debug --incarnation your_incarnation_type
```

This will show detailed logs about the incarnation loading and tool registration process.

## Recommended Incarnation Schema Pattern

For each incarnation, we recommend following this general schema pattern:

```
(:AiGuidanceHub {id: 'incarnation_hub'})
    |
    |-- (:EntityType1 {id, ...properties})
    |     |-- [:RELATES_TO]->(:EntityType2)
    |
    |-- (:EntityType2 {id, ...properties})
          |-- [:HAS_PROPERTY]->(:PropertyType)
```

This ensures consistency across incarnations while allowing for specialized entity types.
