"""
Knowledge Graph incarnation of the NeoCoder framework.

Manage and analyze knowledge graphs
"""

import json
import logging
import uuid
from typing import Dict, Any, List, Optional, Union

import mcp.types as types
from pydantic import Field
from neo4j import AsyncTransaction

from .base_incarnation import BaseIncarnation, IncarnationType

logger = logging.getLogger("mcp_neocoder.incarnations.knowledge_graph")


class KnowledgeGraphIncarnation(BaseIncarnation):
    """
    Knowledge Graph incarnation of the NeoCoder framework.
    
    Manage and analyze knowledge graphs
    """
    
    # Define the incarnation type - must match an entry in IncarnationType enum
    incarnation_type = IncarnationType.KNOWLEDGE_GRAPH
    
    # Metadata for display in the UI
    description = "Manage and analyze knowledge graphs"
    version = "0.1.0"
    
    # Explicitly define which methods should be registered as tools
    _tool_methods = ["tool_one", "tool_two"]
    
    async def initialize_schema(self):
        """Initialize the Neo4j schema for Knowledge Graph."""
        # Define constraints and indexes for the schema
        schema_queries = [
            # Example constraints
            "CREATE CONSTRAINT knowledge_graph_entity_id IF NOT EXISTS FOR (e:KnowledgeNode) REQUIRE e.id IS UNIQUE",
            
            # Example indexes
            "CREATE INDEX knowledge_graph_entity_name IF NOT EXISTS FOR (e:KnowledgeNode) ON (e.name)",
        ]
        
        try:
            async with self.driver.session(database=self.database) as session:
                # Execute each constraint/index query individually
                for query in schema_queries:
                    await session.execute_write(lambda tx: tx.run(query))
                    
                # Create base guidance hub for this incarnation if it doesn't exist
                await self.ensure_guidance_hub_exists()
                
            logger.info("Knowledge Graph incarnation schema initialized")
        except Exception as e:
            logger.error(f"Error initializing knowledge_graph schema: {e}")
            raise
    
    async def ensure_guidance_hub_exists(self):
        """Create the guidance hub for this incarnation if it doesn't exist."""
        query = """
        MERGE (hub:AiGuidanceHub {id: 'knowledge_graph_hub'})
        ON CREATE SET hub.description = $description
        RETURN hub
        """
        
        description = """
# Knowledge Graph

Welcome to the Knowledge Graph powered by the NeoCoder framework.
This system helps you manage and analyze knowledge graphs with the following capabilities:

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
    
    async def get_guidance_hub(self):
        """Get the guidance hub for this incarnation."""
        query = """
        MATCH (hub:AiGuidanceHub {id: 'knowledge_graph_hub'})
        RETURN hub.description AS description
        """
        
        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_read(self._read_query, query, {})
                results = json.loads(results_json)
                
                if results and len(results) > 0:
                    return [types.TextContent(type="text", text=results[0]["description"])]
                else:
                    # If hub doesn't exist, create it
                    await self.ensure_guidance_hub_exists()
                    # Try again
                    return await self.get_guidance_hub()
        except Exception as e:
            logger.error(f"Error retrieving knowledge_graph guidance hub: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]
    
    # Example tool methods for this incarnation
    
    async def tool_one(
        self,
        param1: str = Field(..., description="Description of parameter 1"),
        param2: Optional[int] = Field(None, description="Description of parameter 2")
    ) -> List[types.TextContent]:
        """Tool one for Knowledge Graph incarnation."""
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
        """Tool two for Knowledge Graph incarnation."""
        try:
            # Implementation goes here
            response = f"Executed tool_two with param1={param1}"
            return [types.TextContent(type="text", text=response)]
        except Exception as e:
            logger.error(f"Error in tool_two: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]
