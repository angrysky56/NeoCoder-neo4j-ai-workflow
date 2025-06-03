"""
Data Analysis incarnation of the NeoCoder framework.

Analyze and visualize data
"""

import json
import logging
from typing import List, Optional

import mcp.types as types
from pydantic import Field
from neo4j import AsyncTransaction

from .base_incarnation import BaseIncarnation

logger = logging.getLogger("mcp_neocoder.incarnations.data_analysis")


class DataAnalysisIncarnation(BaseIncarnation):
    """
    Data Analysis incarnation of the NeoCoder framework.

    Analyze and visualize data
    """

    # Define the incarnation name as a string identifier
    name = "data_analysis"

    # Metadata for display in the UI
    description = "Analyze and visualize data"
    version = "0.1.0"

    # Explicitly define which methods should be registered as tools
    _tool_methods = ["tool_one", "tool_two"]

    async def initialize_schema(self):
        """Initialize the Neo4j schema for Data Analysis."""
        # Define constraints and indexes for the schema
        schema_queries = [
            # Example constraints
            "CREATE CONSTRAINT data_analysis_entity_id IF NOT EXISTS FOR (e:Dataset) REQUIRE e.id IS UNIQUE",

            # Example indexes
            "CREATE INDEX data_analysis_entity_name IF NOT EXISTS FOR (e:Dataset) ON (e.name)",
        ]

        try:
            async with self.driver.session(database=self.database) as session:
                # Execute each constraint/index query individually
                for query in schema_queries:
                    await session.execute_write(lambda tx, q=query: tx.run(q))

                # Create base guidance hub for this incarnation if it doesn't exist
                await self.ensure_guidance_hub_exists()

            logger.info("Data Analysis incarnation schema initialized")
        except Exception as e:
            logger.error(f"Error initializing data_analysis schema: {e}")
            raise

    async def ensure_guidance_hub_exists(self):
        """Create the guidance hub for this incarnation if it doesn't exist."""
        query = """
        MERGE (hub:AiGuidanceHub {id: 'data_analysis_hub'})
        ON CREATE SET hub.description = $description
        RETURN hub
        """

        description = """
# Data Analysis

Welcome to the Data Analysis powered by the NeoCoder framework.
This system helps you analyze and visualize data with the following capabilities:

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
        MATCH (hub:AiGuidanceHub {id: 'data_analysis_hub'})
        RETURN hub.description AS description
        """

        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_read(lambda tx: tx.run(query, {}))
                records = await results_json.data()
                results = json.dumps(records)
                results = json.loads(results)

                if results and len(results) > 0:
                    return [types.TextContent(type="text", text=results[0]["description"])]
                else:
                    # If hub doesn't exist, create it
                    await self.ensure_guidance_hub_exists()
                    # Try again
                    return await self.get_guidance_hub()
        except Exception as e:
            logger.error(f"Error retrieving data_analysis guidance hub: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]
    def list_tool_methods(self):
        """List all methods in this class that are tools.

        Returns:
            list: List of method names that are tools
        """
        # Explicitly list tool methods with full logging
        tools = ["tool_one", "tool_two"]
        logger.info(f"Data Analysis incarnation providing tools: {tools}")

        # Verify that these methods actually exist
        for tool in tools:
            if hasattr(self, tool) and callable(getattr(self, tool)):
                logger.info(f"Verified tool method exists: {tool}")
            else:
                logger.error(f"Tool method does not exist or is not callable: {tool}")

        return tools

    # Example tool methods for this incarnation

    async def _read_query(self, tx: AsyncTransaction, query: str, params: dict):
        """Helper to run a read query and return results as JSON."""
        result = await tx.run(query, params)  # type: ignore[arg-type]
        records = await result.data()
        return json.dumps(records)

    async def tool_one(
        self,
        param1: str = Field(..., description="Description of parameter 1"),
        param2: Optional[int] = Field(None, description="Description of parameter 2")
    ) -> List[types.TextContent]:
        """Tool one for Data Analysis incarnation."""
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
        """Tool two for Data Analysis incarnation."""
        try:
            # Implementation goes here
            response = f"Executed tool_two with param1={param1}"
            return [types.TextContent(type="text", text=response)]
        except Exception as e:
            logger.error(f"Error in tool_two: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]
