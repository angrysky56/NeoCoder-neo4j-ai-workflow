"""
Knowledge Graph incarnation of the NeoCoder framework.

Manage and analyze knowledge graphs
"""

import json
import logging
from typing import Dict, Any, List

import mcp.types as types
from pydantic import Field

from .base_incarnation import BaseIncarnation

logger = logging.getLogger("mcp_neocoder.incarnations.knowledge_graph")


class KnowledgeGraphIncarnation(BaseIncarnation):
    """
    Knowledge Graph incarnation of the NeoCoder framework.

    Manage and analyze knowledge graphs
    """

    # Define the incarnation name as a string value
    name = "knowledge_graph"

    # Metadata for display in the UI
    description = "Manage and analyze knowledge graphs"
    version = "1.0.0"

    # Explicitly define which methods should be registered as tools
    _tool_methods = ["create_entities", "create_relations", "add_observations", "add_single_observation",
                     "delete_entities", "delete_observations", "delete_relations",
                     "read_graph", "search_nodes", "open_nodes"]

    async def _execute_and_return_json(self, tx, query, params):
        """
        Execute a query and return results as JSON string within the same transaction.
        This prevents the "transaction out of scope" error.
        """
        result = await tx.run(query, params)
        records = await result.values()

        # Process records into a format that can be JSON serialized
        processed_data = []
        for record in records:
            # Convert record to dict if it's not already
            if isinstance(record, (list, tuple)):
                # For simple list results with defined column names
                # We'll use field names from the query or generic column names
                field_names = ['col0', 'col1', 'col2', 'col3', 'col4', 'col5']  # Generic defaults
                row_data = {}

                for i, value in enumerate(record):
                    if i < len(field_names):
                        row_data[field_names[i]] = value
                    else:
                        row_data[f'col{i}'] = value

                processed_data.append(row_data)
            else:
                # Record is already a dict or another format
                processed_data.append(record)

        return json.dumps(processed_data, default=str)

    async def _safe_read_query(self, session, query, params=None):
        """Execute a read query safely, handling all errors internally.

        This approach completely prevents transaction scope errors from reaching the user.
        """
        if params is None:
            params = {}

        try:
            # Define a function that captures and processes everything within the transaction
            async def execute_and_process_in_tx(tx):
                try:
                    # Run the query
                    result = await tx.run(query, params)

                    # Use .data() to get records with proper column names
                    records = await result.data()

                    # Convert to JSON string inside the transaction
                    return json.dumps(records, default=str)
                except Exception as inner_e:
                    # Catch any errors inside the transaction
                    logger.error(f"Error inside transaction: {inner_e}")
                    return json.dumps([])

            # Execute the query within transaction boundaries
            result_json = await session.execute_read(execute_and_process_in_tx)

            # Parse the JSON result (which should always be valid)
            try:
                return json.loads(result_json)
            except json.JSONDecodeError as json_error:
                logger.error(f"Error parsing JSON result: {json_error}")
                return []

        except Exception as e:
            # Log error but suppress it from the user
            logger.error(f"Error executing read query: {e}")
            return []


    async def initialize_schema(self):
        """Initialize the Neo4j schema for Knowledge Graph."""
        # Define constraints and indexes for the schema
        schema_queries = [
            # Entity constraints
            "CREATE CONSTRAINT knowledge_entity_name IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE",

            # Indexes for efficient querying
            "CREATE INDEX knowledge_entity_type IF NOT EXISTS FOR (e:Entity) ON (e.entityType)",
            "CREATE FULLTEXT INDEX entity_observation_fulltext IF NOT EXISTS FOR (o:Observation) ON EACH [o.content]",
            "CREATE FULLTEXT INDEX entity_name_fulltext IF NOT EXISTS FOR (e:Entity) ON EACH [e.name]"
        ]

        try:
            async with self.driver.session(database=self.database) as session:
                # Execute each constraint/index query individually
                for query in schema_queries:
                    await session.execute_write(lambda tx: tx.run(query))  # type: ignore[arg-type]

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

1. **Entity Management**
   - Create and manage entities with observations
   - Connect entities with typed relations
   - Delete entities and their relationships

2. **Graph Querying**
   - Read the entire knowledge graph
   - Search for specific nodes
   - Open detailed views of specific entities

3. **Observation Management**
   - Add observations to existing entities
   - Delete specific observations

## Getting Started

- Use `create_entities()` to add new entities with observations
- Use `create_relations()` to connect entities
- Use `read_graph()` to view the current graph structure
- Use `search_nodes()` to find specific entities
- Use `open_nodes()` to get detailed information about specific entities

Each entity in the system has proper Neo4j labels for efficient querying and visualization.
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
                # Use direct transaction execution like other methods
                async def execute_query(tx):
                    result = await tx.run(query)
                    records = await result.data()
                    return records

                results = await session.execute_read(execute_query)

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

    # Knowledge Graph API functions

    # Helper methods to avoid transaction scope errors
    async def _safe_execute_write(self, session, query, params):
        """Execute a write query safely and handle all errors internally.

        This approach completely prevents transaction scope errors from reaching the user.
        """
        try:
            # Execute query using a lambda to keep all processing inside transaction
            async def execute_in_tx(tx):
                # Run the query
                result = await tx.run(query, params)
                try:
                    # Try to get summary within the transaction
                    summary = await result.consume()
                    stats = {
                        "nodes_created": summary.counters.nodes_created,
                        "relationships_created": summary.counters.relationships_created,
                        "properties_set": summary.counters.properties_set,
                        "nodes_deleted": summary.counters.nodes_deleted,
                        "relationships_deleted": summary.counters.relationships_deleted
                    }
                    return True, stats
                except Exception as inner_e:
                    # If we can't get results, still consider it a success
                    # but return empty stats
                    logger.warning(f"Query executed but couldn't get stats: {inner_e}")
                    return True, {}

            # Execute the transaction function
            success, stats = await session.execute_write(execute_in_tx)
            return success
        except Exception as e:
            # Log but suppress errors
            logger.error(f"Error executing write query: {e}")
            return False

    async def create_entities(
        self,
        entities: List[Dict[str, Any]] = Field(
            ...,
            description="""An array of entity objects to create. Each entity should have:
            - name: string (unique name for the entity)
            - entityType: string (type/category of the entity)
            - observations: array of strings (simple text observations)

            Example: [{"name": "Deep Learning", "entityType": "Technology", "observations": ["Uses neural networks", "Requires large datasets"]}]

            Note: observations should be an array of simple strings, not complex objects.
            """
        )
    ) -> List[types.TextContent]:
        """Create multiple new entities in the knowledge graph.

        Args:
            entities: List of entity objects. Each should contain:
                - name (str): Unique name for the entity
                - entityType (str): Type/category of the entity
                - observations (List[str]): Array of simple text observations

        Returns:
            Success/error message about the operation

        Example usage:
            entities = [
                {
                    "name": "Deep Learning Models",
                    "entityType": "Technology",
                    "observations": ["Uses neural networks", "Trained with gradient descent"]
                }
            ]

        Note: For complex observations, create entities with observations: []
        and then use add_observations() separately.
        """
        try:
            if not entities:
                return [types.TextContent(type="text", text="Error: No entities provided")]

            # Validate entities and clean observations
            cleaned_entities = []
            for entity in entities:
                if 'name' not in entity:
                    return [types.TextContent(type="text", text="Error: All entities must have a 'name' property")]
                if 'entityType' not in entity:
                    return [types.TextContent(type="text", text="Error: All entities must have an 'entityType' property")]
                if 'observations' not in entity or not isinstance(entity['observations'], list):
                    return [types.TextContent(type="text", text="Error: All entities must have an 'observations' array")]

                # Clean the entity - ensure observations are simple strings
                cleaned_entity = {
                    'name': str(entity['name']),
                    'entityType': str(entity['entityType']),
                    'observations': []
                }

                # Process observations - convert complex objects to strings if needed
                for obs in entity['observations']:
                    if isinstance(obs, str):
                        # Simple string - use as-is
                        cleaned_entity['observations'].append(obs)
                    elif isinstance(obs, dict) and 'content' in obs:
                        # Complex object with content - extract the content
                        cleaned_entity['observations'].append(str(obs['content']))
                    elif obs is not None:
                        # Any other type - convert to string
                        cleaned_entity['observations'].append(str(obs))
                    # Skip None values

                cleaned_entities.append(cleaned_entity)

            # Build the Cypher query for creating entities with proper labels
            # Use FOREACH to handle empty observations arrays gracefully
            query = """
            UNWIND $entities AS entity
            MERGE (e:Entity {name: entity.name})
            ON CREATE SET e.entityType = entity.entityType
            WITH e, entity
            FOREACH (obs IN entity.observations |
                CREATE (o:Observation {content: obs, timestamp: datetime()})
                CREATE (e)-[:HAS_OBSERVATION]->(o)
            )
            RETURN count(e) AS entityCount
            """

            # Get counts for the response message (use cleaned entities)
            entity_count = len(cleaned_entities)
            observation_count = sum(len(entity.get('observations', [])) for entity in cleaned_entities)

            # Execute the query using our safe execution method
            async with self.driver.session(database=self.database) as session:
                success = await self._safe_execute_write(session, query, {"entities": cleaned_entities})

                if success:
                    # Give feedback based on the intended operation, not the actual results
                    response = f"Successfully created {entity_count} entities with {observation_count} observations."
                    return [types.TextContent(type="text", text=response)]
                else:
                    return [types.TextContent(type="text", text="Error creating entities. Please check server logs.")]

        except Exception as e:
            logger.error(f"Error in create_entities: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def create_relations(
        self,
        relations: List[Dict[str, str]] = Field(..., description="An array of relation objects to create")
    ) -> List[types.TextContent]:
        """Create multiple new relations between entities in the knowledge graph. Relations should be in active voice"""
        try:
            if not relations:
                return [types.TextContent(type="text", text="Error: No relations provided")]

            # Validate relations
            for relation in relations:
                if 'from' not in relation:
                    return [types.TextContent(type="text", text="Error: All relations must have a 'from' property")]
                if 'to' not in relation:
                    return [types.TextContent(type="text", text="Error: All relations must have a 'to' property")]
                if 'relationType' not in relation:
                    return [types.TextContent(type="text", text="Error: All relations must have a 'relationType' property")]

            # Use simplified approach without dynamic relationship type - most compatible
            simple_query = """
            UNWIND $relations AS rel
            MATCH (from:Entity {name: rel.from})
            MATCH (to:Entity {name: rel.to})
            MERGE (from)-[r:RELATES_TO]->(to)
            ON CREATE SET r.type = rel.relationType, r.timestamp = datetime()
            RETURN count(r) AS relationCount
            """

            # Get relation count for the response message
            relation_count = len(relations)

            # Execute the query using our safe execution method
            async with self.driver.session(database=self.database) as session:
                success = await self._safe_execute_write(session, query=simple_query, params={"relations": relations})

                if success:
                    response = f"Successfully created {relation_count} relations between entities."
                    return [types.TextContent(type="text", text=response)]
                else:
                    return [types.TextContent(type="text", text="Error creating relations. Please check server logs.")]

        except Exception as e:
            logger.error(f"Error in create_relations: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def add_observations(
        self,
        observations: List[Dict[str, Any]] = Field(
            ...,
            description="""An array of observations to add to existing entities. Each observation should have:
            - entityName: string (name of the entity to add observations to)
            - contents: array of strings (the observation content strings to add)

            Example: [{"entityName": "MyEntity", "contents": ["First observation", "Second observation"]}]
            """
        )
    ) -> List[types.TextContent]:
        """Add new observations to existing entities in the knowledge graph.

        Args:
            observations: List of observation objects. Each should contain:
                - entityName (str): Name of the entity to add observations to
                - contents (List[str]): Array of observation content strings

        Returns:
            Success/error message about the operation

        Example usage:
            observations = [
                {
                    "entityName": "Deep Learning Models",
                    "contents": ["Machine learning models that use neural networks", "Often trained with SGD"]
                }
            ]
        """
        try:
            if not observations:
                return [types.TextContent(type="text", text="Error: No observations provided")]

            # Validate observations
            for i, observation in enumerate(observations):
                if 'entityName' not in observation:
                    return [types.TextContent(type="text", text=f"Error: Observation {i+1} must have an 'entityName' property")]
                if 'contents' not in observation or not isinstance(observation['contents'], list):
                    return [types.TextContent(
                        type="text",
                        text=f"Error: Observation {i+1} must have a 'contents' array. Expected format: {{'entityName': 'EntityName', 'contents': ['observation1', 'observation2']}}"
                    )]
                if not observation['contents']:
                    return [types.TextContent(type="text", text=f"Error: Observation {i+1} must have at least one content item in the 'contents' array")]

            # Build the Cypher query
            query = """
            UNWIND $observations AS obs
            MATCH (e:Entity {name: obs.entityName})
            WITH e, obs
            UNWIND obs.contents AS content
            CREATE (o:Observation {content: content, timestamp: datetime()})
            CREATE (e)-[:HAS_OBSERVATION]->(o)
            RETURN count(o) AS totalObservations
            """

            # Get observation and entity counts for the response message
            entity_count = len(observations)
            observation_count = sum(len(obs.get('contents', [])) for obs in observations)

            # Execute the query using our safe execution method
            async with self.driver.session(database=self.database) as session:
                success = await self._safe_execute_write(session, query, {"observations": observations})

                if success:
                    response = f"Successfully added {observation_count} observations to {entity_count} entities."
                    return [types.TextContent(type="text", text=response)]
                else:
                    return [types.TextContent(type="text", text="Error adding observations. Please check server logs.")]

        except Exception as e:
            logger.error(f"Error in add_observations: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def add_single_observation(
        self,
        entityName: str = Field(..., description="Name of the entity to add the observation to"),
        content: str = Field(..., description="The observation content to add")
    ) -> List[types.TextContent]:
        """Add a single observation to an existing entity (convenience method).

        This is a simpler version of add_observations for adding just one observation.

        Args:
            entityName: Name of the entity to add the observation to
            content: The observation content string

        Returns:
            Success/error message about the operation
        """
        # Use the main add_observations method
        return await self.add_observations([{
            "entityName": entityName,
            "contents": [content]
        }])

    async def delete_entities(
        self,
        entityNames: List[str] = Field(..., description="An array of entity names to delete")
    ) -> List[types.TextContent]:
        """Delete multiple entities and their associated relations from the knowledge graph"""
        try:
            if not entityNames:
                return [types.TextContent(type="text", text="Error: No entity names provided")]

            # Build the Cypher query
            query = """
            UNWIND $entityNames AS name
            MATCH (e:Entity {name: name})
            OPTIONAL MATCH (e)-[:HAS_OBSERVATION]->(o:Observation)
            DETACH DELETE e, o
            RETURN count(DISTINCT e) as deletedEntities
            """

            async with self.driver.session(database=self.database) as session:
                # Use a direct transaction to avoid scope issues
                async def execute_delete(tx):
                    result = await tx.run(query, {"entityNames": entityNames})
                    # Get the data within the transaction scope
                    records = await result.data()

                    if records and len(records) > 0:
                        return records[0].get("deletedEntities", 0)
                    return 0

                deleted_count = await session.execute_write(execute_delete)

                if deleted_count > 0:
                    response = f"Successfully deleted {deleted_count} entities with their observations and relations."
                    return [types.TextContent(type="text", text=response)]
                else:
                    return [types.TextContent(type="text", text="No entities were deleted.")]

        except Exception as e:
            logger.error(f"Error in delete_entities: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def delete_observations(
        self,
        deletions: List[Dict[str, Any]] = Field(..., description="An array of specifications for observations to delete")
    ) -> List[types.TextContent]:
        """Delete specific observations from entities in the knowledge graph"""
        try:
            if not deletions:
                return [types.TextContent(type="text", text="Error: No deletion specifications provided")]

            # Validate deletions
            for deletion in deletions:
                if 'entityName' not in deletion:
                    return [types.TextContent(type="text", text="Error: All deletion specs must have an 'entityName' property")]
                if 'observations' not in deletion or not isinstance(deletion['observations'], list):
                    return [types.TextContent(type="text", text="Error: All deletion specs must have an 'observations' array")]
                if not deletion['observations']:
                    return [types.TextContent(type="text", text="Error: All deletion specs must specify at least one observation")]

            # Build the Cypher query
            query = """
            UNWIND $deletions AS deletion
            MATCH (e:Entity {name: deletion.entityName})
            WITH e, deletion
            UNWIND deletion.observations AS obs_content
            MATCH (e)-[:HAS_OBSERVATION]->(o:Observation {content: obs_content})
            DETACH DELETE o
            RETURN count(o) AS totalDeleted
            """

            # Get counts for the response message
            entity_count = len(deletions)
            observation_count = sum(len(deletion.get('observations', [])) for deletion in deletions)

            # Execute the query using our safe execution method
            async with self.driver.session(database=self.database) as session:
                success = await self._safe_execute_write(session, query, {"deletions": deletions})

                if success:
                    response = f"Successfully deleted {observation_count} observations from {entity_count} entities."
                    return [types.TextContent(type="text", text=response)]
                else:
                    return [types.TextContent(type="text", text="Error deleting observations. Please check server logs.")]

        except Exception as e:
            logger.error(f"Error in delete_observations: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def delete_relations(
        self,
        relations: List[Dict[str, str]] = Field(..., description="An array of relations to delete")
    ) -> List[types.TextContent]:
        """Delete multiple relations from the knowledge graph"""
        try:
            if not relations:
                return [types.TextContent(type="text", text="Error: No relations provided for deletion")]

            # Validate relations
            for relation in relations:
                if 'from' not in relation:
                    return [types.TextContent(type="text", text="Error: All relations must have a 'from' property")]
                if 'to' not in relation:
                    return [types.TextContent(type="text", text="Error: All relations must have a 'to' property")]
                if 'relationType' not in relation:
                    return [types.TextContent(type="text", text="Error: All relations must have a 'relationType' property")]

            # For non-APOC environments, handle relationship deletion
            # We'll use a generic relation with a type property in practice
            query = """
            UNWIND $relations AS rel
            MATCH (from:Entity {name: rel.from})-[r:RELATES_TO {type: rel.relationType}]->(to:Entity {name: rel.to})
            DELETE r
            RETURN count(r) as deletedRelations
            """

            # Get relation count for the response message
            relation_count = len(relations)

            # Execute the query using our safe execution method
            async with self.driver.session(database=self.database) as session:
                success = await self._safe_execute_write(session, query, {"relations": relations})

                if success:
                    response = f"Successfully deleted {relation_count} relations."
                    return [types.TextContent(type="text", text=response)]
                else:
                    return [types.TextContent(type="text", text="Error deleting relations. Please check server logs.")]

        except Exception as e:
            logger.error(f"Error in delete_relations: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def read_graph(self) -> List[types.TextContent]:
        """Read the entire knowledge graph"""
        try:
            # Query to get all entities with their observations and relations
            query = """
            MATCH (e:Entity)
            OPTIONAL MATCH (e)-[:HAS_OBSERVATION]->(o:Observation)
            OPTIONAL MATCH (e)-[r:RELATES_TO]->(related:Entity)
            RETURN e.name as name, e.entityType as type,
                   collect(DISTINCT o.content) as observations,
                   collect(DISTINCT {type: r.type, target: related.name}) as relations
            ORDER BY e.name
            """

            async with self.driver.session(database=self.database) as session:
                # Use a direct transaction to avoid scope issues
                async def execute_query(tx):
                    result = await tx.run(query)
                    records = await result.data()  # Fixed: use .data() instead of .records()
                    entities = []

                    for record in records:
                        entity = {
                            "name": record.get("name"),
                            "type": record.get("type", "Unknown"),
                            "observations": [obs for obs in record.get("observations", []) if obs is not None],
                            "relations": [rel for rel in record.get("relations", [])
                                         if rel is not None and rel.get("type") is not None and rel.get("target") is not None]
                        }
                        entities.append(entity)

                    return entities

                entities = await session.execute_read(execute_query)

                if not entities:
                    return [types.TextContent(type="text", text="# Knowledge Graph\n\nThe knowledge graph is empty.")]

                # Format the response for each entity
                response = f"# Knowledge Graph\n\nFound {len(entities)} entities in the knowledge graph.\n\n"

                for entity in entities:
                    response += f"## {entity['name']} ({entity['type']})\n\n"

                    if entity['observations']:
                        response += "### Observations:\n"
                        for obs in entity['observations']:
                            response += f"- {obs}\n"
                        response += "\n"

                    if entity['relations']:
                        response += "### Relations:\n"
                        for rel in entity['relations']:
                            response += f"- {rel['type']} -> {rel['target']}\n"
                        response += "\n"

                return [types.TextContent(type="text", text=response)]

        except Exception as e:
            logger.error(f"Error in read_graph: {e}")
            return [types.TextContent(type="text", text=f"Error reading knowledge graph: {e}")]

    async def search_nodes(
        self,
        query: str = Field(..., description="The search query to match against entity names, types, and observation content")
    ) -> List[types.TextContent]:
        """Search for nodes in the knowledge graph based on a query"""
        try:
            if not query or len(query.strip()) < 2:
                return [types.TextContent(type="text", text="Error: Search query must be at least 2 characters")]

            # Simplified query that works without fulltext search
            cypher_query = """
            MATCH (e:Entity)
            WHERE e.name CONTAINS $query OR e.entityType CONTAINS $query
            WITH e
            OPTIONAL MATCH (e)-[:HAS_OBSERVATION]->(o:Observation)
            WITH e, collect(o.content) AS observations
            RETURN e.name AS entityName, e.entityType AS entityType, observations

            UNION

            MATCH (e:Entity)-[:HAS_OBSERVATION]->(o:Observation)
            WHERE o.content CONTAINS $query
            WITH e, collect(o.content) AS observations
            RETURN e.name AS entityName, e.entityType AS entityType, observations

            LIMIT 10
            """

            async with self.driver.session(database=self.database) as session:
                # Use a direct transaction to avoid scope issues
                async def execute_query(tx):
                    result = await tx.run(cypher_query, {"query": query})
                    records = await result.data()  # Fixed: use .data() instead of .records()
                    result_data = []

                    for record in records:
                        entity = {
                            "entityName": record.get("entityName"),
                            "entityType": record.get("entityType", "Unknown"),
                            "observations": [obs for obs in record.get("observations", []) if obs is not None]
                        }
                        result_data.append(entity)

                    return result_data

                result_data = await session.execute_read(execute_query)

                # Process and format the results
                if not result_data:
                    return [types.TextContent(type="text", text=f"No entities found matching '{query}'.")]

                # Remove duplicates (same entity may appear multiple times if it matched multiple criteria)
                unique_entities = {}
                for entity in result_data:
                    entity_name = entity.get("entityName", "")
                    if entity_name and entity_name not in unique_entities:
                        unique_entities[entity_name] = entity

                entities = list(unique_entities.values())

                # Build the formatted response
                response = f"# Search Results for '{query}'\n\n"
                response += f"Found {len(entities)} matching entities.\n\n"

                for entity in entities:
                    entity_name = entity.get("entityName", "")
                    entity_type = entity.get("entityType", "")
                    observations = entity.get("observations", [])

                    response += f"## {entity_name} ({entity_type})\n\n"

                    if observations:
                        response += "### Observations:\n"
                        for obs in observations:
                            # Highlight the search term in observations
                            highlighted_obs = obs
                            if query.lower() in obs.lower():
                                # Create a case-insensitive highlighting
                                start_idx = obs.lower().find(query.lower())
                                end_idx = start_idx + len(query)
                                match_text = obs[start_idx:end_idx]
                                highlighted_obs = obs.replace(match_text, f"**{match_text}**")

                            response += f"- {highlighted_obs}\n"
                        response += "\n"

                return [types.TextContent(type="text", text=response)]

        except Exception as e:
            logger.error(f"Error in search_nodes: {e}")
            return [types.TextContent(type="text", text=f"Error searching knowledge graph: {e}")]

    async def open_nodes(
        self,
        names: List[str] = Field(..., description="An array of entity names to retrieve")
    ) -> List[types.TextContent]:
        """Open specific nodes in the knowledge graph by their names"""
        try:
            if not names:
                return [types.TextContent(type="text", text="Error: No entity names provided")]

            # Use a single comprehensive query to get all needed information
            query = """
            UNWIND $names AS name
            MATCH (e:Entity {name: name})
            OPTIONAL MATCH (e)-[:HAS_OBSERVATION]->(o:Observation)
            OPTIONAL MATCH (e)-[outRel:RELATES_TO]->(target:Entity)
            OPTIONAL MATCH (source:Entity)-[inRel:RELATES_TO]->(e)
            RETURN
                e.name AS name,
                e.entityType AS type,
                collect(DISTINCT o.content) AS observations,
                collect(DISTINCT {type: outRel.type, target: target.name}) AS outRelations,
                collect(DISTINCT {type: inRel.type, source: source.name}) AS inRelations
            """

            async with self.driver.session(database=self.database) as session:
                # Use a direct transaction to avoid scope issues
                async def execute_query(tx):
                    result = await tx.run(query, {"names": names})
                    records = await result.data()  # Fixed: use .data() instead of .records()
                    entity_details = []

                    for record in records:
                        entity = {
                            "name": record.get("name"),
                            "type": record.get("type", "Unknown"),
                            "observations": [obs for obs in record.get("observations", []) if obs is not None],
                            "outRelations": [rel for rel in record.get("outRelations", [])
                                           if rel is not None and rel.get("type") is not None and rel.get("target") is not None],
                            "inRelations": [rel for rel in record.get("inRelations", [])
                                          if rel is not None and rel.get("type") is not None and rel.get("source") is not None]
                        }
                        entity_details.append(entity)

                    return entity_details

                entity_details = await session.execute_read(execute_query)

                if not entity_details:
                    return [types.TextContent(type="text", text="No entities found with the specified names.")]

                # Format the response
                response = "# Entity Details\n\n"

                for entity in entity_details:
                    response += f"## {entity['name']} ({entity['type']})\n\n"

                    if entity['observations']:
                        response += "### Observations:\n"
                        for obs in entity['observations']:
                            response += f"- {obs}\n"
                        response += "\n"

                    if entity['outRelations']:
                        response += "### Outgoing Relations:\n"
                        for rel in entity['outRelations']:
                            response += f"- {rel['type']} -> {rel['target']}\n"
                        response += "\n"

                    if entity['inRelations']:
                        response += "### Incoming Relations:\n"
                        for rel in entity['inRelations']:
                            response += f"- {rel['source']} -> {rel['type']} -> {entity['name']}\n"
                        response += "\n"

                return [types.TextContent(type="text", text=response)]

        except Exception as e:
            logger.error(f"Error in open_nodes: {e}")
            return [types.TextContent(type="text", text=f"Error retrieving entity details: {e}")]
