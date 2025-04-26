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
    _tool_methods = ["create_entities", "create_relations", "add_observations", 
                     "delete_entities", "delete_observations", "delete_relations",
                     "read_graph", "search_nodes", "open_nodes"]
    
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
    
    # Knowledge Graph API functions
    
    async def create_entities(
        self,
        entities: List[Dict[str, Any]] = Field(..., description="An array of entity objects to create")
    ) -> List[types.TextContent]:
        """Create multiple new entities in the knowledge graph"""
        try:
            if not entities:
                return [types.TextContent(type="text", text="Error: No entities provided")]
            
            # Validate entities
            for entity in entities:
                if 'name' not in entity:
                    return [types.TextContent(type="text", text="Error: All entities must have a 'name' property")]
                if 'entityType' not in entity:
                    return [types.TextContent(type="text", text="Error: All entities must have an 'entityType' property")]
                if 'observations' not in entity or not isinstance(entity['observations'], list):
                    return [types.TextContent(type="text", text="Error: All entities must have an 'observations' array")]
            
            # Build the Cypher query for creating entities with proper labels
            query = """
            UNWIND $entities AS entity
            MERGE (e:Entity {name: entity.name})
            ON CREATE SET e.entityType = entity.entityType
            WITH e, entity
            UNWIND entity.observations AS obs
            CREATE (o:Observation {content: obs, timestamp: datetime()})
            CREATE (e)-[:HAS_OBSERVATION]->(o)
            RETURN e.name AS entityName, collect(o.content) AS observations
            """
            
            async with self.driver.session(database=self.database) as session:
                result = await session.execute_write(
                    lambda tx: tx.run(query, {"entities": entities})
                )
                records = await result.values()
                
                # Process results
                created_entities = []
                for record in records:
                    created_entities.append({
                        "name": record[0],
                        "observations": record[1]
                    })
                
                response = f"Successfully created {len(created_entities)} entities with their observations."
                return [types.TextContent(type="text", text=response)]
                
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
            
            # Build dynamic relationship query
            query = """
            UNWIND $relations AS rel
            MATCH (from:Entity {name: rel.from})
            MATCH (to:Entity {name: rel.to})
            WITH from, to, rel
            CALL apoc.create.relationship(from, rel.relationType, {timestamp: datetime()}, to) YIELD rel as created
            RETURN from.name AS fromEntity, type(created) AS relationType, to.name AS toEntity
            """
            
            # Fallback query if APOC is not available
            fallback_query = """
            UNWIND $relations AS rel
            MATCH (from:Entity {name: rel.from})
            MATCH (to:Entity {name: rel.to})
            WITH from, to, rel
            CALL {
                WITH from, to, rel
                CALL {
                    WITH from, to, rel
                    CALL db.create.relationship(from, rel.relationType, {timestamp: datetime()}, to) YIELD relationship as created
                    RETURN type(created) AS relType
                }
                RETURN relType
            }
            RETURN from.name AS fromEntity, relType AS relationType, to.name AS toEntity
            """
            
            # Start with the more powerful APOC version, fall back if needed
            try:
                async with self.driver.session(database=self.database) as session:
                    result = await session.execute_write(
                        lambda tx: tx.run(query, {"relations": relations})
                    )
                    records = await result.values()
            except Exception as apoc_error:
                logger.warning(f"APOC not available, using fallback: {apoc_error}")
                try:
                    # Try a different approach using hardcoded relationships
                    fallback_dynamic_query = """
                    UNWIND $relations AS rel
                    MATCH (from:Entity {name: rel.from})
                    MATCH (to:Entity {name: rel.to})
                    WITH from, to, rel
                    CALL {
                        WITH from, to, rel
                        WITH from, to, rel.relationType AS type
                        CALL {
                            WITH from, to, type
                            WITH from, to, type
                            CALL {
                                WITH from, to, type
                                // Create with proper dynamic relationship type
                                MERGE (from)-[r:`${type}`]->(to)
                                ON CREATE SET r.timestamp = datetime()
                                RETURN type(r) AS relType
                            }
                            RETURN relType
                        }
                        RETURN relType
                    }
                    RETURN from.name AS fromEntity, rel.relationType AS relationType, to.name AS toEntity
                    """
                
                    async with self.driver.session(database=self.database) as session:
                        # Try simplified approach without dynamic relationship type
                        simple_query = """
                        UNWIND $relations AS rel
                        MATCH (from:Entity {name: rel.from})
                        MATCH (to:Entity {name: rel.to})
                        MERGE (from)-[r:RELATES_TO]->(to)
                        ON CREATE SET r.type = rel.relationType, r.timestamp = datetime()
                        RETURN from.name AS fromEntity, r.type AS relationType, to.name AS toEntity
                        """
                        
                        result = await session.execute_write(
                            lambda tx: tx.run(simple_query, {"relations": relations})
                        )
                        records = await result.values()
                except Exception as e:
                    logger.error(f"Error in fallback relation creation: {e}")
                    return [types.TextContent(type="text", text=f"Error creating relations: {e}")]
            
            # Process results
            created_relations = []
            for record in records:
                created_relations.append({
                    "from": record[0],
                    "relationType": record[1],
                    "to": record[2]
                })
            
            response = f"Successfully created {len(created_relations)} relations between entities."
            return [types.TextContent(type="text", text=response)]
                
        except Exception as e:
            logger.error(f"Error in create_relations: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]
    
    async def add_observations(
        self,
        observations: List[Dict[str, Any]] = Field(..., description="An array of observations to add to existing entities")
    ) -> List[types.TextContent]:
        """Add new observations to existing entities in the knowledge graph"""
        try:
            if not observations:
                return [types.TextContent(type="text", text="Error: No observations provided")]
            
            # Validate observations
            for observation in observations:
                if 'entityName' not in observation:
                    return [types.TextContent(type="text", text="Error: All observations must have an 'entityName' property")]
                if 'contents' not in observation or not isinstance(observation['contents'], list):
                    return [types.TextContent(type="text", text="Error: All observations must have a 'contents' array")]
                if not observation['contents']:
                    return [types.TextContent(type="text", text="Error: All observations must have at least one content item")]
            
            # Build the Cypher query
            query = """
            UNWIND $observations AS obs
            MATCH (e:Entity {name: obs.entityName})
            WITH e, obs
            UNWIND obs.contents AS content
            CREATE (o:Observation {content: content, timestamp: datetime()})
            CREATE (e)-[:HAS_OBSERVATION]->(o)
            RETURN e.name AS entityName, collect(o.content) AS observations
            """
            
            async with self.driver.session(database=self.database) as session:
                result = await session.execute_write(
                    lambda tx: tx.run(query, {"observations": observations})
                )
                records = await result.values()
                
                # Process results
                updated_entities = []
                for record in records:
                    updated_entities.append({
                        "name": record[0],
                        "observations": record[1]
                    })
                
                response = f"Successfully added observations to {len(updated_entities)} entities."
                return [types.TextContent(type="text", text=response)]
                
        except Exception as e:
            logger.error(f"Error in add_observations: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]
    
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
                result = await session.execute_write(
                    lambda tx: tx.run(query, {"entityNames": entityNames})
                )
                records = await result.values()
                
                if records and len(records) > 0:
                    deleted_count = records[0][0]
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
            RETURN e.name AS entityName, count(o) AS deletedObservations
            """
            
            async with self.driver.session(database=self.database) as session:
                result = await session.execute_write(
                    lambda tx: tx.run(query, {"deletions": deletions})
                )
                records = await result.values()
                
                # Process results
                deleted_counts = {}
                for record in records:
                    deleted_counts[record[0]] = record[1]
                
                total_deleted = sum(deleted_counts.values())
                response = f"Successfully deleted {total_deleted} observations from {len(deleted_counts)} entities."
                return [types.TextContent(type="text", text=response)]
                
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
            
            async with self.driver.session(database=self.database) as session:
                result = await session.execute_write(
                    lambda tx: tx.run(query, {"relations": relations})
                )
                records = await result.values()
                
                deleted_count = 0
                if records and len(records) > 0:
                    deleted_count = records[0][0]
                
                response = f"Successfully deleted {deleted_count} relations."
                return [types.TextContent(type="text", text=response)]
                
        except Exception as e:
            logger.error(f"Error in delete_relations: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]
    
    async def read_graph(self) -> List[types.TextContent]:
        """Read the entire knowledge graph"""
        try:
            # Build the Cypher query to get entities, observations, and relations
            query = """
            MATCH (e:Entity)
            OPTIONAL MATCH (e)-[:HAS_OBSERVATION]->(o:Observation)
            WITH e, collect(o.content) AS observations
            OPTIONAL MATCH (e)-[r:RELATES_TO]->(related:Entity)
            RETURN e.name AS entityName, e.entityType AS entityType, 
                   observations,
                   collect({type: r.type, target: related.name}) AS relations
            """
            
            async with self.driver.session(database=self.database) as session:
                result = await session.execute_read(
                    lambda tx: tx.run(query, {})
                )
                records = await result.values()
                
                # Process results into a readable format
                entities = []
                for record in records:
                    entity_name = record[0]
                    entity_type = record[1]
                    observations = record[2] or []
                    relations = [r for r in record[3] if r['target']] if record[3] else []
                    
                    entities.append({
                        "name": entity_name,
                        "type": entity_type,
                        "observations": observations,
                        "relations": relations
                    })
                
                # Format the response
                if not entities:
                    return [types.TextContent(type="text", text="The knowledge graph is empty.")]
                
                response = "# Knowledge Graph\n\n"
                response += f"Found {len(entities)} entities in the knowledge graph.\n\n"
                
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
            return [types.TextContent(type="text", text=f"Error: {e}")]
    
    async def search_nodes(
        self,
        query: str = Field(..., description="The search query to match against entity names, types, and observation content")
    ) -> List[types.TextContent]:
        """Search for nodes in the knowledge graph based on a query"""
        try:
            if not query or len(query.strip()) < 2:
                return [types.TextContent(type="text", text="Error: Search query must be at least 2 characters")]
            
            # Build the Cypher query
            search_query = """
            // Search in entity names
            CALL db.index.fulltext.queryNodes("entity_name_fulltext", $query) YIELD node, score
            WITH node AS e, score
            WHERE e:Entity
            
            // Get observations for those entities
            OPTIONAL MATCH (e)-[:HAS_OBSERVATION]->(o:Observation)
            WITH e, score, collect(o.content) AS observations
            
            RETURN e.name AS entityName, e.entityType AS entityType, observations, score
            
            UNION
            
            // Search in observation content
            CALL db.index.fulltext.queryNodes("entity_observation_fulltext", $query) YIELD node, score
            WITH node AS o, score
            WHERE o:Observation
            
            // Get entity for those observations
            MATCH (e:Entity)-[:HAS_OBSERVATION]->(o)
            WITH e, o, score
            
            // Get all observations for that entity
            MATCH (e)-[:HAS_OBSERVATION]->(all_o:Observation)
            WITH e, collect(all_o.content) AS observations, score
            
            RETURN e.name AS entityName, e.entityType AS entityType, observations, score
            
            ORDER BY score DESC
            LIMIT 10
            """
            
            # Fallback if fulltext search is not available
            fallback_query = """
            MATCH (e:Entity)
            WHERE e.name CONTAINS $query OR e.entityType CONTAINS $query
            OPTIONAL MATCH (e)-[:HAS_OBSERVATION]->(o:Observation)
            WITH e, collect(o.content) AS observations
            RETURN e.name AS entityName, e.entityType AS entityType, observations, 1.0 AS score
            
            UNION
            
            MATCH (e:Entity)-[:HAS_OBSERVATION]->(o:Observation)
            WHERE o.content CONTAINS $query
            WITH e, collect(o.content) AS observations
            RETURN e.name AS entityName, e.entityType AS entityType, observations, 0.5 AS score
            
            ORDER BY score DESC
            LIMIT 10
            """
            
            try:
                async with self.driver.session(database=self.database) as session:
                    # Try fulltext search first
                    result = await session.execute_read(
                        lambda tx: tx.run(search_query, {"query": query})
                    )
                    records = await result.values()
            except Exception as fulltext_error:
                logger.warning(f"Fulltext search not available, using fallback: {fulltext_error}")
                async with self.driver.session(database=self.database) as session:
                    result = await session.execute_read(
                        lambda tx: tx.run(fallback_query, {"query": query})
                    )
                    records = await result.values()
            
            # Process results
            entities = []
            for record in records:
                entity_name = record[0]
                entity_type = record[1]
                observations = record[2] or []
                score = record[3]
                
                # Avoid duplicates
                if not any(e['name'] == entity_name for e in entities):
                    entities.append({
                        "name": entity_name,
                        "type": entity_type,
                        "observations": observations,
                        "score": score
                    })
            
            # Format the response
            if not entities:
                return [types.TextContent(type="text", text=f"No entities found matching '{query}'.")]
            
            response = f"# Search Results for '{query}'\n\n"
            response += f"Found {len(entities)} matching entities.\n\n"
            
            for entity in entities:
                response += f"## {entity['name']} ({entity['type']})\n\n"
                
                if entity['observations']:
                    response += "### Observations:\n"
                    for obs in entity['observations']:
                        # Highlight the query term in observations
                        highlighted_obs = obs
                        if query.lower() in obs.lower():
                            parts = obs.lower().split(query.lower())
                            highlighted_obs = ""
                            start_idx = 0
                            for i, part in enumerate(parts):
                                if i > 0:
                                    match_start = start_idx + len(part)
                                    match_end = match_start + len(query)
                                    highlighted_obs += f"**{obs[match_start:match_end]}**"
                                    start_idx = match_end
                                highlighted_obs += obs[start_idx:start_idx+len(part)]
                                start_idx += len(part)
                        
                        response += f"- {highlighted_obs}\n"
                    response += "\n"
                
            return [types.TextContent(type="text", text=response)]
                
        except Exception as e:
            logger.error(f"Error in search_nodes: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]
    
    async def open_nodes(
        self,
        names: List[str] = Field(..., description="An array of entity names to retrieve")
    ) -> List[types.TextContent]:
        """Open specific nodes in the knowledge graph by their names"""
        try:
            if not names:
                return [types.TextContent(type="text", text="Error: No entity names provided")]
            
            # Build the Cypher query
            query = """
            UNWIND $names AS name
            MATCH (e:Entity {name: name})
            OPTIONAL MATCH (e)-[:HAS_OBSERVATION]->(o:Observation)
            WITH e, collect(o.content) AS observations
            OPTIONAL MATCH (e)-[r:RELATES_TO]->(related:Entity)
            WITH e, observations, collect({type: r.type, target: related.name}) AS outRelations
            OPTIONAL MATCH (other:Entity)-[r2:RELATES_TO]->(e)
            RETURN e.name AS entityName, e.entityType AS entityType, 
                   observations,
                   outRelations,
                   collect({type: r2.type, source: other.name}) AS inRelations
            """
            
            async with self.driver.session(database=self.database) as session:
                result = await session.execute_read(
                    lambda tx: tx.run(query, {"names": names})
                )
                records = await result.values()
                
                # Process results
                entities = []
                for record in records:
                    entity_name = record[0]
                    entity_type = record[1]
                    observations = record[2] or []
                    out_relations = [r for r in record[3] if r['target']] if record[3] else []
                    in_relations = [r for r in record[4] if r['source']] if record[4] else []
                    
                    entities.append({
                        "name": entity_name,
                        "type": entity_type,
                        "observations": observations,
                        "outRelations": out_relations,
                        "inRelations": in_relations
                    })
                
                # Format the response
                if not entities:
                    return [types.TextContent(type="text", text=f"No entities found with the specified names.")]
                
                response = f"# Entity Details\n\n"
                
                for entity in entities:
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
            return [types.TextContent(type="text", text=f"Error: {e}")]
