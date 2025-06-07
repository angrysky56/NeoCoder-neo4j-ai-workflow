# NeoCoder Neo4j Schema Analysis

## Overview

The NeoCoder framework leverages Neo4j as its core knowledge graph database. This analysis examines the Neo4j schema design, node structures, relationship patterns, and how the different incarnations extend and interact with this schema.

## Core Schema Components

The NeoCoder database schema is built around these primary node types:

### 1. AiGuidanceHub

The `AiGuidanceHub` node serves as the central entry point for AI navigation:

```cypher
MERGE (hub:AiGuidanceHub {id: 'main_hub'})
ON CREATE SET hub.description = $description
```

Properties:
- `id` - Unique identifier (e.g., 'main_hub', 'research_hub')
- `description` - Markdown formatted guidance text

This node is critical as it serves as the primary entry point for AI assistants to navigate the system.

### 2. ActionTemplate

`ActionTemplate` nodes store step-by-step workflow instructions:

```cypher
MERGE (t:ActionTemplate {keyword: 'FIX', version: '1.2'})
ON CREATE SET t.isCurrent = true
ON MATCH SET t.isCurrent = true
SET t.description = 'Guidance on fixing a reported bug...'
SET t.complexity = 'MEDIUM'
SET t.estimatedEffort = 45
SET t.steps = '...'
```

Properties:
- `keyword` - Unique action identifier (e.g., 'FIX', 'REFACTOR')
- `version` - Version string (e.g., '1.2')
- `isCurrent` - Boolean flag for current version
- `description` - Brief description
- `complexity` - Estimated complexity (e.g., 'LOW', 'MEDIUM', 'HIGH')
- `estimatedEffort` - Estimated effort in minutes
- `steps` - Markdown formatted step-by-step instructions

Templates are versioned, with only one current version per keyword.

### 3. Project

`Project` nodes store information about coding projects:

```cypher
MERGE (p:Project {id: $projectId})
SET p.name = $name
SET p.description = $description
SET p.readme = $readme
```

Properties:
- `id` - Unique project identifier
- `name` - Project name
- `description` - Brief project description
- `readme` - README content in markdown format

### 4. WorkflowExecution

`WorkflowExecution` nodes record completed workflows:

```cypher
CREATE (w:WorkflowExecution {
    id: $id,
    timestamp: datetime(),
    summary: $summary,
    executionTimeSeconds: $executionTimeSeconds
})
WITH w
MATCH (p:Project {id: $projectId})
MATCH (t:ActionTemplate {keyword: $actionKeyword, isCurrent: true})
CREATE (w)-[:EXECUTED_ON]->(p)
CREATE (w)-[:FOLLOWED]->(t)
```

Properties:
- `id` - Unique execution identifier
- `timestamp` - Execution timestamp
- `summary` - Brief summary of what was done
- `executionTimeSeconds` - Duration in seconds
- `filesChanged` - List of modified files

Relationships:
- `EXECUTED_ON` - Links to the project
- `FOLLOWED` - Links to the template that was followed

### 5. CypherSnippet

`CypherSnippet` nodes store reusable Cypher query patterns:

```cypher
MERGE (c:CypherSnippet {id: $id})
SET c += $snippet
```

Properties:
- `id` - Unique snippet identifier
- `name` - Display name
- `syntax` - Query syntax pattern
- `description` - Explanation of the snippet
- `example` - Example usage
- `since` - Neo4j version since supported

Relationships:
- `TAGGED_AS` - Links to tags for categorization

## Incarnation-Specific Schema Elements

Each incarnation extends the core schema with specialized node types and relationships:

### Research Incarnation Schema

```cypher
// Hypothesis nodes
CREATE CONSTRAINT hypothesis_id IF NOT EXISTS
FOR (h:Hypothesis) REQUIRE h.id IS UNIQUE;

// Protocol nodes
CREATE CONSTRAINT protocol_id IF NOT EXISTS
FOR (p:Protocol) REQUIRE p.id IS UNIQUE;

// Experiment nodes
CREATE CONSTRAINT experiment_id IF NOT EXISTS
FOR (e:Experiment) REQUIRE e.id IS UNIQUE;
```

Node types:
- `Hypothesis` - Scientific hypotheses
- `Protocol` - Experimental protocols
- `Experiment` - Specific experiments
- `Observation` - Experimental observations

Relationships:
- `TESTS` - Links experiment to hypothesis
- `FOLLOWS` - Links experiment to protocol
- `OBSERVED_IN` - Links observation to experiment
- `SUPPORTS` - Links observation to hypothesis

### Decision Incarnation Schema

```cypher
// Decision nodes
CREATE CONSTRAINT decision_id IF NOT EXISTS
FOR (d:Decision) REQUIRE d.id IS UNIQUE;

// Alternative nodes
CREATE CONSTRAINT alternative_id IF NOT EXISTS
FOR (a:Alternative) REQUIRE a.id IS UNIQUE;

// Metric nodes
CREATE CONSTRAINT metric_id IF NOT EXISTS
FOR (m:Metric) REQUIRE m.id IS UNIQUE;
```

Node types:
- `Decision` - Decision to be made
- `Alternative` - Decision alternatives
- `Metric` - Evaluation metrics
- `Evidence` - Supporting evidence

Relationships:
- `HAS_ALTERNATIVE` - Links decision to alternative
- `EVALUATED_BY` - Links decision to metric
- `SUPPORTS` - Links evidence to alternative
- `CONTRADICTS` - Links evidence to alternative

### Knowledge Graph Incarnation Schema

```cypher
// Entity constraints
CREATE CONSTRAINT knowledge_entity_name IF NOT EXISTS 
FOR (e:Entity) REQUIRE e.name IS UNIQUE

// Indexes for efficient querying
CREATE INDEX knowledge_entity_type IF NOT EXISTS 
FOR (e:Entity) ON (e.entityType)
CREATE FULLTEXT INDEX entity_observation_fulltext IF NOT EXISTS 
FOR (o:Observation) ON EACH [o.content]
```

Node types:
- `Entity` - Knowledge entities
- `Observation` - Entity observations

Relationships:
- `HAS_OBSERVATION` - Links entity to observation
- `RELATES_TO` - Links entities together with typed relationships

### Code Analysis Incarnation Schema

```cypher
// CodeFile constraints
CREATE CONSTRAINT code_file_path IF NOT EXISTS 
FOR (f:CodeFile) REQUIRE f.path IS UNIQUE

// AST nodes
CREATE CONSTRAINT ast_node_id IF NOT EXISTS 
FOR (n:ASTNode) REQUIRE n.id IS UNIQUE

// Analyses
CREATE CONSTRAINT analysis_id IF NOT EXISTS 
FOR (a:Analysis) REQUIRE a.id IS UNIQUE
```

Node types:
- `CodeFile` - Source code files
- `ASTNode` - Abstract Syntax Tree nodes
- `Analysis` - Code analysis results

Relationships:
- `HAS_ANALYSIS` - Links file to analysis
- `CONTAINS` - Links analysis to AST nodes
- `HAS_CHILD` - Links AST nodes in a tree structure

## Schema Relationships

The schema includes several key relationship types that connect the various node types:

### Core Relationships

1. **Navigation Relationships**
   - `HAS_INCARNATION` - Links main hub to incarnation hubs
   - `LINKS_TO` - Generic navigational link between nodes

2. **Project Relationships**
   - `HAS_FILE` - Links project to file structure
   - `CONTAINS` - Links directories to files
   - `DEPENDS_ON` - Links project to dependencies

3. **Workflow Relationships**
   - `EXECUTED_ON` - Links workflow execution to project
   - `FOLLOWED` - Links workflow execution to template
   - `MODIFIED` - Links workflow execution to modified files

### Hierarchical Structure

The schema uses hierarchical relationships to organize information:

```
(AiGuidanceHub:main_hub)
  |
  |-[HAS_INCARNATION]-> (AiGuidanceHub:research_hub)
  |
  |-[HAS_INCARNATION]-> (AiGuidanceHub:decision_hub)
  |
  |-[HAS_INCARNATION]-> (AiGuidanceHub:knowledge_graph_hub)
  |
  |-[HAS_INCARNATION]-> (AiGuidanceHub:code_analysis_hub)
```

Each incarnation hub then links to its specialized node types.

## Schema Implementation

The schema is implemented through initialization scripts that are run during database setup:

```python
async def _ensure_db_initialized(self):
    """Check if the database is initialized and run initialization if needed."""
    init_needed = False
    
    # Check if main hub exists
    hub_query = "MATCH (hub:AiGuidanceHub {id: 'main_hub'}) RETURN count(hub) as count"
    
    # Check if action templates exist
    template_query = "MATCH (t:ActionTemplate) RETURN count(t) as count"
    
    if init_needed:
        await init_db(INCARNATION_TYPES)
```

The `init_db.py` module handles database initialization:

```python
async def init_db(incarnation_types=None):
    """Initialize the Neo4j database with required schema and data."""
    # Create constraints
    await create_constraints()
    
    # Create guidance hub
    await create_guidance_hub()
    
    # Load templates
    await load_templates_from_dir('templates')
    
    # Initialize incarnations
    for inc_type in incarnation_types or []:
        await init_incarnation(inc_type)
```

## Schema Extensions

Each incarnation extends the schema through its `initialize_schema` method:

```python
async def initialize_schema(self):
    """Initialize the Neo4j schema for this incarnation."""
    # Execute schema queries if defined
    if self.schema_queries:
        try:
            async with self.driver.session(database=self.database) as session:
                # Execute each constraint/index query individually
                for query in self.schema_queries:
                    await session.execute_write(lambda tx: tx.run(query))
                
                # Create guidance hub if needed
                await self.ensure_hub_exists()
        except Exception as e:
            logger.error(f"Error initializing schema: {e}")
```

## Indexing Strategy

The schema uses a comprehensive indexing strategy to ensure efficient queries:

1. **Unique Constraints** - Ensure uniqueness of key identifiers
2. **Property Indexes** - Enable efficient property lookups
3. **Fulltext Indexes** - Enable fulltext search capabilities
4. **Label Lookup Indexes** - Enable efficient label-based searches

For example, the Knowledge Graph incarnation uses:

```cypher
CREATE INDEX knowledge_entity_type IF NOT EXISTS FOR (e:Entity) ON (e.entityType)
CREATE FULLTEXT INDEX entity_observation_fulltext IF NOT EXISTS FOR (o:Observation) ON EACH [o.content]
CREATE FULLTEXT INDEX entity_name_fulltext IF NOT EXISTS FOR (e:Entity) ON EACH [e.name]
```

## Query Patterns

The schema is designed to support several common query patterns:

### 1. Template Retrieval

```cypher
MATCH (t:ActionTemplate {keyword: 'FIX', isCurrent: true}) 
RETURN t.steps
```

### 2. Project Navigation

```cypher
MATCH (p:Project {id: $projectId})
OPTIONAL MATCH (p)-[:HAS_FILE]->(f:File)
RETURN p, collect(f) as files
```

### 3. Workflow History

```cypher
MATCH (w:WorkflowExecution)-[:EXECUTED_ON]->(p:Project {id: $projectId})
MATCH (w)-[:FOLLOWED]->(t:ActionTemplate)
RETURN w.timestamp, w.summary, t.keyword
ORDER BY w.timestamp DESC
```

### 4. Knowledge Graph Exploration

```cypher
MATCH (e:Entity {name: $name})
OPTIONAL MATCH (e)-[:HAS_OBSERVATION]->(o:Observation)
OPTIONAL MATCH (e)-[r:RELATES_TO]->(related:Entity)
RETURN e, collect(o) as observations, collect({relation: r.type, entity: related}) as relations
```

### 5. Code Analysis

```cypher
MATCH (f:CodeFile {path: $path})
MATCH (f)-[:HAS_ANALYSIS]->(a:Analysis)
MATCH (a)-[:CONTAINS]->(root:ASTNode)
WHERE NOT (root)<-[:HAS_CHILD]-()
RETURN root
```

## Schema Evolution

The schema has been designed to evolve over time, with the database version tracked:

```cypher
MERGE (v:DatabaseVersion {id: 'current'})
ON CREATE SET v.version = '1.0.0', v.updated = datetime()
ON MATCH SET v.version = '1.0.1', v.updated = datetime()
```

New incarnations, node types, and relationships can be added without breaking existing functionality, following the principle of schema evolution rather than schema migration.

## Conclusion

The NeoCoder Neo4j schema demonstrates a well-designed knowledge graph architecture that supports multiple specialized incarnations while maintaining a consistent core structure. The use of labeled property graphs allows for flexible extension and adaptation for different domains, from coding workflows to scientific research and code analysis.

The schema's design follows best practices for Neo4j, with appropriate constraints, indexes, and relationship patterns. The modular approach, with each incarnation defining its specialized schema elements, enables clean separation of concerns while maintaining the ability to query across domains.

As the NeoCoder system continues to evolve, this schema provides a solid foundation for growth, with clear paths for extending to new domains or enhancing existing capabilities.
