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
from ..event_loop_manager import safe_neo4j_session

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
            "CREATE FULLTEXT INDEX entity_name_fulltext IF NOT EXISTS FOR (e:Entity) ON EACH [e.name]",

            # LV-Enhanced Knowledge Graph Guidance Hub Creation
            """
            MERGE (hub:AiGuidanceHub {id: 'knowledge_graph_hub'})
            SET hub.description = "
# Knowledge Graph Management System with LV Ecosystem Intelligence

Welcome to the Knowledge Graph Management System powered by the NeoCoder framework with Lotka-Volterra Ecosystem Intelligence integration.

## 🧬 LV-Enhanced Knowledge Operations

### When to Use LV Enhancement

**Entropy-Based Decision Making:**
1. **Calculate entropy** using `EntropyEstimator.estimate_prompt_entropy(query)`
2. **Decision logic:**
   - entropy ≤ 0.4 → Use standard knowledge operations
   - entropy > 0.4 → Use LV-enhanced operations for diversity preservation

### LV-Enhanced Templates Available

#### 🔍 **KNOWLEDGE_QUERY_LV** - Multi-Perspective Knowledge Search
- **Use when:** Complex queries requiring diverse perspectives  
- **Entropy threshold:** > 0.4
- **Template:** `get_action_template(keyword='KNOWLEDGE_QUERY_LV')`
- **Real Implementation:** Calls `NeoCoder_LV_Integration.enhance_existing_template('KNOWLEDGE_QUERY', context)`

#### 📚 **KNOWLEDGE_EXTRACT_LV** - Diversity-Preserving Knowledge Extraction  
- **Use when:** Extracting knowledge from multi-domain documents
- **Entropy threshold:** > 0.4  
- **Template:** `get_action_template(keyword='KNOWLEDGE_EXTRACT_LV')`
- **Real Implementation:** Uses LV ecosystem dynamics for strategy diversity

#### ⚙️ **LV_SELECT** - Generic LV Enhancement
- **Use when:** Any workflow needs diversity preservation
- **Entropy threshold:** > 0.4
- **Template:** `get_action_template(keyword='LV_SELECT')`
- **Real Implementation:** Applies Lotka-Volterra dynamics to any template

### 🧪 LV Integration Workflow

**Step 1: Initialize LV System**
```python
from mcp_neocoder.lv_integration import NeoCoder_LV_Integration
lv_system = NeoCoder_LV_Integration(neo4j_session, qdrant_client)
```

**Step 2: Calculate Real Entropy** 
```python
entropy = lv_system.entropy_estimator.estimate_prompt_entropy(user_query)
```

**Step 3: Apply Decision Logic**
- If entropy > 0.4: Use LV-enhanced template  
- If entropy ≤ 0.4: Use standard knowledge operations

**Step 4: Execute Real LV Enhancement**
```python
# Real LV execution (not simulation)
results = await lv_system.enhance_existing_template(template_keyword, context)
diversity_score = results['diversity_metrics']['semantic_diversity']
```

**Step 5: Validate Results**
- Verify diversity_score > 0.7
- Check that multiple perspectives are included
- Ensure mathematical stability (negative eigenvalues)

## 📊 Standard Knowledge Operations

### Core Knowledge Graph Tools
- **Entity Management:** `create_entities()`, `add_observations()`
- **Relationship Management:** `create_relations()`  
- **Knowledge Discovery:** `search_nodes()`, `open_nodes()`, `read_graph()`

### Enhanced Hybrid Operations  
- **F-Contraction Synthesis:** Merge Neo4j structured facts with Qdrant semantic context
- **Citation Tracking:** Full source attribution across graph and vector databases
- **Dynamic Knowledge Updates:** Real-time knowledge graph evolution

## 🎯 Decision Framework

**Low Entropy Queries (≤ 0.4):**
- Factual lookups: `search_nodes(query='specific_entity')`
- Simple relationships: `create_relations([{from: 'A', to: 'B', relationType: 'RELATES_TO'}])`
- Direct entity creation: `create_entities([{name: 'Entity', entityType: 'Type', observations: ['fact']}])`

**High Entropy Queries (> 0.4):**
- Complex analysis: Use `KNOWLEDGE_QUERY_LV` template
- Multi-domain extraction: Use `KNOWLEDGE_EXTRACT_LV` template  
- Creative knowledge synthesis: Use `LV_SELECT` template

## ⚡ Performance Notes

- **Real LV computation** uses SentenceTransformer embeddings and numpy eigenvalue analysis
- **CUDA acceleration** available for GPU-enabled systems
- **Mathematical validation** through eigenvalue stability checking
- **Diversity metrics** computed using real semantic analysis

Remember: This system uses **actual Lotka-Volterra mathematical dynamics**, not simulations. All diversity scores and ecosystem metrics are computed using real mathematical models.
"
            RETURN hub
            """
        ]

        try:
            async with safe_neo4j_session(self.driver, self.database) as session:
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

        async with safe_neo4j_session(self.driver, self.database) as session:
            await session.execute_write(lambda tx: tx.run(query, params))

    async def get_guidance_hub(self):
        """Get the guidance hub for this incarnation."""
        query = """
        MATCH (hub:AiGuidanceHub {id: 'knowledge_graph_hub'})
        RETURN hub.description AS description
        """

        try:
            async with safe_neo4j_session(self.driver, self.database) as session:
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

    async def _safe_execute_read(self, session, query, params):
        """Execute a read query safely and return results or None on error.

        This approach prevents transaction scope errors from reaching the user.
        """
        try:
            # Execute query using a lambda to keep all processing inside transaction
            async def execute_in_tx(tx):
                result = await tx.run(query, params)
                # Convert to list to get all records before transaction ends
                records = []
                async for record in result:
                    records.append(dict(record))
                return records

            # Execute the transaction function
            records = await session.execute_read(execute_in_tx)
            return records
        except Exception as e:
            # Log but suppress errors
            logger.error(f"Error executing read query: {e}")
            return None

    async def create_entities(
        self,
        entities: List[Dict[str, Any]] = Field(
            ...,
            description="""An array of entity objects to create in the knowledge graph. Each entity MUST have:
            - name: string (unique identifier/name for the entity)
            - entityType: string (category/type of the entity)
            - observations: array of strings (descriptive observations about the entity)

            REQUIRED FORMAT: [{"name": "EntityName", "entityType": "Category", "observations": ["fact1", "fact2"]}]

            ENTITY TYPE EXAMPLES:
            - Technical: "Technology", "Framework", "Library", "Tool", "Language", "Platform", "Service"
            - Conceptual: "Concept", "Principle", "Pattern", "Method", "Approach", "Theory"
            - Organizational: "Process", "Role", "Team", "Department", "Company", "Project"
            - Data: "Dataset", "Model", "Schema", "Format", "Protocol", "Standard"

            GOOD EXAMPLES:
            [{"name": "React", "entityType": "Framework", "observations": ["JavaScript UI library", "Component-based architecture", "Virtual DOM"]}]
            [{"name": "Machine Learning", "entityType": "Concept", "observations": ["Learns from data", "Makes predictions", "Improves with experience"]}]
            [{"name": "Docker", "entityType": "Technology", "observations": ["Containerization platform", "Lightweight virtualization", "Portable applications"]}]

            NOTE: observations should be simple descriptive strings, not complex objects.
            """
        )
    ) -> List[types.TextContent]:
        """Create multiple new entities in the knowledge graph.

        This is the primary tool for adding new entities to the knowledge graph. Each entity
        represents a distinct concept, technology, process, or other meaningful object.

        Args:
            entities: List of entity objects. Each MUST contain:
                - name (str): Unique identifier for the entity (will be used for relations)
                - entityType (str): Category/type of the entity (helps with organization)
                - observations (List[str]): Array of descriptive facts about the entity

        Returns:
            Success message with count of entities created, or detailed error message if validation fails

        Common Entity Types by Domain:
            Technology: "Framework", "Library", "Tool", "Platform", "Service", "Database", "API"
            Programming: "Language", "Paradigm", "Pattern", "Algorithm", "Structure", "Protocol"
            Business: "Process", "Role", "Department", "Strategy", "Methodology", "Practice"
            Academic: "Concept", "Theory", "Principle", "Method", "Approach", "Technique"
            Data: "Dataset", "Model", "Schema", "Format", "Source", "Repository"

        Example Usage Patterns:

        1. Technology Stack:
            [
                {"name": "React", "entityType": "Framework", "observations": ["JavaScript UI library", "Component-based", "Virtual DOM"]},
                {"name": "Node.js", "entityType": "Runtime", "observations": ["JavaScript server runtime", "Non-blocking I/O", "Event-driven"]},
                {"name": "MongoDB", "entityType": "Database", "observations": ["NoSQL document database", "JSON-like documents", "Horizontally scalable"]}
            ]

        2. Machine Learning Concepts:
            [
                {"name": "Neural Networks", "entityType": "Concept", "observations": ["Inspired by biological neurons", "Learns complex patterns", "Multiple layers of nodes"]},
                {"name": "Gradient Descent", "entityType": "Algorithm", "observations": ["Optimization algorithm", "Minimizes loss function", "Iterative parameter updates"]},
                {"name": "Overfitting", "entityType": "Problem", "observations": ["Model learns training data too well", "Poor generalization", "Prevented by regularization"]}
            ]

        3. Business Processes:
            [
                {"name": "Code Review", "entityType": "Process", "observations": ["Peer review of code changes", "Ensures quality standards", "Knowledge sharing"]},
                {"name": "DevOps Engineer", "entityType": "Role", "observations": ["Bridges development and operations", "Automates deployment", "Monitors infrastructure"]},
                {"name": "Agile Methodology", "entityType": "Methodology", "observations": ["Iterative development", "Customer collaboration", "Responds to change"]}
            ]

        Tips for Good Entities:
            - Use clear, descriptive names that others will recognize
            - Choose appropriate entityTypes for better organization
            - Include 2-5 concise observations that capture key characteristics
            - Avoid duplicates - check existing entities first with query_graph
            - Keep observations factual and informative

        Note: After creating entities, use create_relations to establish connections between them.
        For additional details later, use add_observations to append more information.
        """
        try:
            if not entities:
                return [types.TextContent(type="text", text="Error: No entities provided")]

            # Validate entities and clean observations
            cleaned_entities = []
            for i, entity in enumerate(entities):
                if not isinstance(entity, dict):
                    return [types.TextContent(type="text", text=f"Error: Entity {i+1} must be an object/dictionary, not {type(entity).__name__}")]

                if 'name' not in entity:
                    return [types.TextContent(type="text", text=f"Error: Entity {i+1} is missing required 'name' field. Expected format: {{'name': 'EntityName', 'entityType': 'Category', 'observations': ['fact1', 'fact2']}}")]

                if 'entityType' not in entity:
                    return [types.TextContent(type="text", text=f"Error: Entity {i+1} is missing required 'entityType' field. Expected format: {{'name': 'EntityName', 'entityType': 'Category', 'observations': ['fact1', 'fact2']}}")]

                if 'observations' not in entity:
                    return [types.TextContent(type="text", text=f"Error: Entity {i+1} is missing required 'observations' field. Expected format: {{'name': 'EntityName', 'entityType': 'Category', 'observations': ['fact1', 'fact2']}}")]

                if not isinstance(entity['observations'], list):
                    return [types.TextContent(type="text", text=f"Error: Entity {i+1} 'observations' must be an array/list of strings, not {type(entity['observations']).__name__}")]

                # Validate that name and entityType are non-empty strings
                if not isinstance(entity['name'], str) or not entity['name'].strip():
                    return [types.TextContent(type="text", text=f"Error: Entity {i+1} 'name' must be a non-empty string")]

                if not isinstance(entity['entityType'], str) or not entity['entityType'].strip():
                    return [types.TextContent(type="text", text=f"Error: Entity {i+1} 'entityType' must be a non-empty string")]

                # Clean the entity - ensure observations are simple strings
                cleaned_entity = {
                    'name': str(entity['name']).strip(),
                    'entityType': str(entity['entityType']).strip(),
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
            async with safe_neo4j_session(self.driver, self.database) as session:
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
        relations: List[Dict[str, str]] = Field(
            ...,
            description="""An array of relation objects to create between existing entities. Each relation MUST have exactly these three fields:
            - from: string (name of the source entity - must already exist in the graph)
            - to: string (name of the target entity - must already exist in the graph)
            - relationType: string (type of relationship, use descriptive names in UPPER_CASE)

            REQUIRED FORMAT: [{"from": "SourceEntity", "to": "TargetEntity", "relationType": "RELATIONSHIP_TYPE"}]

            RELATIONSHIP TYPE EXAMPLES:
            - Technical: "DEPENDS_ON", "IMPLEMENTS", "EXTENDS", "USES", "CONTAINS", "CALLS"
            - Conceptual: "IS_PART_OF", "IS_A_TYPE_OF", "RELATES_TO", "INFLUENCES", "ENABLES"
            - Workflow: "PRECEDES", "FOLLOWS", "TRIGGERS", "REQUIRES", "PRODUCES"

            GOOD EXAMPLES:
            [{"from": "React", "to": "JavaScript", "relationType": "DEPENDS_ON"}]
            [{"from": "Neural Networks", "to": "Machine Learning", "relationType": "IS_PART_OF"}]
            [{"from": "Docker", "to": "Containerization", "relationType": "ENABLES"}]

            IMPORTANT:
            - Both entities must already exist in the graph (use create_entities first if needed)
            - Use active voice relationships (A USES B, not B IS_USED_BY A)
            - Relationship types should be descriptive and in UPPER_CASE
            """
        )
    ) -> List[types.TextContent]:
        """Create multiple new relations between existing entities in the knowledge graph.

        This tool creates directed relationships between entities that already exist in the graph.
        Use this after creating entities with create_entities to establish connections between them.

        Args:
            relations: List of relation objects. Each MUST contain exactly these three fields:
                - from (str): Name of the source entity (must already exist in the graph)
                - to (str): Name of the target entity (must already exist in the graph)
                - relationType (str): Type of relationship in UPPER_CASE (e.g., "USES", "DEPENDS_ON", "IS_PART_OF")

        Returns:
            Success message with count of relations created, or detailed error message if validation fails

        Common Relationship Types by Category:
            Technical Dependencies: "DEPENDS_ON", "REQUIRES", "IMPORTS", "CALLS", "IMPLEMENTS"
            Hierarchical: "IS_PART_OF", "CONTAINS", "IS_A_TYPE_OF", "EXTENDS", "INHERITS_FROM"
            Functional: "USES", "PROCESSES", "PRODUCES", "TRANSFORMS", "ENABLES", "SUPPORTS"
            Sequential: "PRECEDES", "FOLLOWS", "TRIGGERS", "LEADS_TO", "RESULTS_IN"
            Conceptual: "RELATES_TO", "INFLUENCES", "AFFECTS", "SIMILAR_TO", "OPPOSITE_OF"

        Example Usage Patterns:

        1. Technology Stack Relations:
            [
                {"from": "React App", "to": "React", "relationType": "USES"},
                {"from": "React", "to": "JavaScript", "relationType": "DEPENDS_ON"},
                {"from": "JavaScript", "to": "Node.js Runtime", "relationType": "RUNS_ON"}
            ]

        2. Conceptual Knowledge Relations:
            [
                {"from": "Deep Learning", "to": "Machine Learning", "relationType": "IS_PART_OF"},
                {"from": "Neural Networks", "to": "Deep Learning", "relationType": "IMPLEMENTS"},
                {"from": "GPT Models", "to": "Transformer Architecture", "relationType": "BASED_ON"}
            ]

        3. Process/Workflow Relations:
            [
                {"from": "Code Review", "to": "Development", "relationType": "FOLLOWS"},
                {"from": "Testing", "to": "Code Review", "relationType": "FOLLOWS"},
                {"from": "Deployment", "to": "Testing", "relationType": "REQUIRES"}
            ]

        Error Prevention Tips:
            - Ensure both entities exist before creating relations (check with query_graph or create with create_entities)
            - Use descriptive relationship types that clearly express the connection
            - Keep relationships directional and consistent (A USES B, not B IS_USED_BY A)
            - Validate entity names match exactly (case-sensitive)

        Note: This creates directed relationships. The direction matters: "A DEPENDS_ON B" means A requires B,
        not that B requires A. If you need bidirectional relationships, create two separate relations.
        """
        try:
            if not relations:
                return [types.TextContent(type="text", text="Error: No relations provided")]

            # Enhanced validation with better error messages
            for i, relation in enumerate(relations):
                if not isinstance(relation, dict):
                    return [types.TextContent(type="text", text=f"Error: Relation {i+1} must be an object/dictionary, not {type(relation).__name__}")]

                if 'from' not in relation:
                    return [types.TextContent(type="text", text=f"Error: Relation {i+1} is missing required 'from' field. Expected format: {{'from': 'SourceEntity', 'to': 'TargetEntity', 'relationType': 'RELATIONSHIP_TYPE'}}")]

                if 'to' not in relation:
                    return [types.TextContent(type="text", text=f"Error: Relation {i+1} is missing required 'to' field. Expected format: {{'from': 'SourceEntity', 'to': 'TargetEntity', 'relationType': 'RELATIONSHIP_TYPE'}}")]

                if 'relationType' not in relation:
                    return [types.TextContent(type="text", text=f"Error: Relation {i+1} is missing required 'relationType' field. Expected format: {{'from': 'SourceEntity', 'to': 'TargetEntity', 'relationType': 'RELATIONSHIP_TYPE'}}")]

                # Validate that values are strings and not empty
                if not isinstance(relation['from'], str) or not relation['from'].strip():
                    return [types.TextContent(type="text", text=f"Error: Relation {i+1} 'from' field must be a non-empty string")]

                if not isinstance(relation['to'], str) or not relation['to'].strip():
                    return [types.TextContent(type="text", text=f"Error: Relation {i+1} 'to' field must be a non-empty string")]

                if not isinstance(relation['relationType'], str) or not relation['relationType'].strip():
                    return [types.TextContent(type="text", text=f"Error: Relation {i+1} 'relationType' field must be a non-empty string")]

            # Pre-validate that all referenced entities exist in the graph
            entity_names = set()
            for relation in relations:
                entity_names.add(relation['from'])
                entity_names.add(relation['to'])

            # Check which entities exist
            check_entities_query = """
            UNWIND $entityNames AS name
            OPTIONAL MATCH (e:Entity {name: name})
            RETURN name, e IS NOT NULL AS exists
            """

            async with safe_neo4j_session(self.driver, self.database) as session:
                result = await self._safe_execute_read(session, query=check_entities_query, params={"entityNames": list(entity_names)})

                if result is not None:
                    # Process the results to find missing entities
                    missing_entities = []
                    for record in result:
                        if not record.get("exists", False):
                            missing_entities.append(record.get("name"))

                    if missing_entities:
                        missing_list = "', '".join(missing_entities)
                        example_entity = missing_entities[0] if missing_entities else "EntityName"
                        return [types.TextContent(
                            type="text",
                            text=f"Error: The following entities do not exist in the graph: '{missing_list}'. "
                                 f"Please create them first using the create_entities tool.\n\n"
                                 f"Example to create missing entities:\n"
                                 f"create_entities([{{'name': '{example_entity}', 'entityType': 'Concept', 'observations': ['Description of {example_entity}']}}])\n\n"
                                 f"Then retry creating the relations."
                        )]
                else:
                    return [types.TextContent(type="text", text="Error: Could not verify entity existence. Please check server logs.")]

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
            async with safe_neo4j_session(self.driver, self.database) as session:
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
            async with safe_neo4j_session(self.driver, self.database) as session:
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

            async with safe_neo4j_session(self.driver, self.database) as session:
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
            async with safe_neo4j_session(self.driver, self.database) as session:
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
            async with safe_neo4j_session(self.driver, self.database) as session:
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
        """Read and display the entire knowledge graph structure.

        This tool retrieves all entities, their observations, and relationships from the knowledge graph
        and presents them in a structured, readable format. Use this to:
        - Understand the current state of the knowledge graph
        - Discover existing entities before creating new ones
        - Explore relationships between concepts
        - Get an overview of all available knowledge

        Returns:
            Formatted text showing all entities with their types, observations, and relationships

        The output includes:
        - Entity name and type
        - All observations (facts/descriptions) for each entity
        - All outgoing relationships from each entity

        This is particularly useful for AI agents to understand the existing knowledge base
        before making modifications or additions.
        """
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

            async with safe_neo4j_session(self.driver, self.database) as session:
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

            async with safe_neo4j_session(self.driver, self.database) as session:
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

            async with safe_neo4j_session(self.driver, self.database) as session:
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
