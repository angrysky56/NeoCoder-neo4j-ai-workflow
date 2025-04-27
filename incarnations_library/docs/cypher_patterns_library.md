# Verified Cypher Patterns Library

This library contains tested and verified Cypher patterns that have been used successfully in workflows. These patterns serve as reliable building blocks for interacting with the Neo4j database in the NeoCoder framework.

## Node and Relationship Management

### Creating Nodes with Properties

```cypher
// Create a single node with properties
CREATE (n:Label {property1: value1, property2: value2})
RETURN n

// Create multiple nodes in one operation
UNWIND $nodeList AS node
CREATE (n:Label {
  id: node.id,
  property1: node.property1,
  property2: node.property2
})
RETURN count(n) AS created
```

### Merging Nodes (Create or Update)

```cypher
// Merge on a unique property
MERGE (n:Label {uniqueProperty: $value})
ON CREATE SET n.created = datetime(), n.property2 = $property2
ON MATCH SET n.lastUpdated = datetime(), n.property2 = $property2
RETURN n

// Merge with different properties for create vs. match
MERGE (n:Label {uniqueProperty: $value})
ON CREATE 
  SET n += $createProperties
ON MATCH 
  SET n += $updateProperties
RETURN n
```

### Creating Relationships

```cypher
// Create relationship between existing nodes
MATCH (a:LabelA {identifier: $value1})
MATCH (b:LabelB {identifier: $value2})
CREATE (a)-[:RELATIONSHIP_TYPE {property: $value}]->(b)

// Create or merge relationship
MATCH (a:LabelA {identifier: $value1})
MATCH (b:LabelB {identifier: $value2})
MERGE (a)-[r:RELATIONSHIP_TYPE]->(b)
ON CREATE SET r.created = datetime(), r.property = $value
ON MATCH SET r.lastUpdated = datetime(), r.property = $value
```

### Updating Nodes

```cypher
// Update specific properties
MATCH (n:Label {identifier: $value})
SET n.property1 = $newValue1, n.property2 = $newValue2
RETURN n

// Update using property map
MATCH (n:Label {identifier: $value})
SET n += $propertyMap
RETURN n

// Conditional updates
MATCH (n:Label)
WHERE n.property1 > $threshold
SET n.category = 'high'
```

### Deleting Nodes and Relationships

```cypher
// Delete a single node
MATCH (n:Label {identifier: $value})
DELETE n

// Delete node and all its relationships
MATCH (n:Label {identifier: $value})
DETACH DELETE n

// Delete specific relationships
MATCH (a:LabelA)-[r:RELATIONSHIP_TYPE]->(b:LabelB)
WHERE r.property = $value
DELETE r

// Delete a node's relationships but keep the node
MATCH (n:Label {identifier: $value})-[r]-()
DELETE r
```

## Querying Patterns

### Basic Pattern Matching

```cypher
// Match nodes by property
MATCH (n:Label)
WHERE n.property = $value
RETURN n

// Match relationship patterns
MATCH (a:LabelA)-[:RELATIONSHIP_TYPE]->(b:LabelB)
WHERE a.property = $value
RETURN a, b

// Match with variable relationship types
MATCH (a:LabelA)-[r]->(b:LabelB)
WHERE type(r) IN $relationshipTypes
RETURN a, b, type(r)
```

### Advanced Pattern Matching

```cypher
// Optional pattern matching
MATCH (a:LabelA {identifier: $value})
OPTIONAL MATCH (a)-[:RELATIONSHIP_TYPE]->(b:LabelB)
RETURN a, b

// Variable-length paths
MATCH path = (start:Label {identifier: $startValue})-[:RELATIONSHIP_TYPE*1..3]->(end:Label)
RETURN path

// Shortest path
MATCH p = shortestPath((start:Label {identifier: $startValue})-[:RELATIONSHIP_TYPE*]->
                       (end:Label {identifier: $endValue}))
RETURN p
```

### Filtering and Sorting

```cypher
// Complex filtering
MATCH (n:Label)
WHERE n.property1 > $minValue
  AND n.property2 < $maxValue
  AND n.property3 IN $valueList
RETURN n

// Pattern-based filtering
MATCH (n:Label)
WHERE (n)-[:RELATIONSHIP_TYPE]->(:AnotherLabel)
RETURN n

// Sorting results
MATCH (n:Label)
RETURN n
ORDER BY n.property1 DESC, n.property2
```

### Aggregation Queries

```cypher
// Count related nodes
MATCH (n:Label)-[:RELATIONSHIP_TYPE]->(related)
RETURN n.property, count(related) AS relatedCount
ORDER BY relatedCount DESC

// Group by multiple properties
MATCH (n:Label)
RETURN n.property1, n.property2, count(*) AS count
ORDER BY count DESC

// Advanced aggregation
MATCH (n:Label)-[:RELATIONSHIP_TYPE]->(related)
RETURN n.property, 
       count(related) AS relatedCount,
       sum(related.numericProperty) AS total,
       avg(related.numericProperty) AS average
```

## Workflow Patterns

### FIX Workflow

```cypher
// Log a successful fix
MATCH (p:Project {id: $projectId})
CREATE (w:WorkflowExecution {
  id: randomUUID(),
  timestamp: datetime(),
  summary: $summary,
  actionKeyword: 'FIX',
  notes: $notes
})
CREATE (p)-[:HAS_WORKFLOW]->(w)
WITH w
UNWIND $filesChanged AS file
CREATE (f:File {path: file})
CREATE (w)-[:MODIFIED]->(f)
```

### REFACTOR Workflow

```cypher
// Log a successful refactoring
MATCH (p:Project {id: $projectId})
CREATE (w:WorkflowExecution {
  id: randomUUID(),
  timestamp: datetime(),
  summary: $summary,
  actionKeyword: 'REFACTOR',
  notes: $notes
})
CREATE (p)-[:HAS_WORKFLOW]->(w)
WITH w
UNWIND $filesChanged AS file
CREATE (f:File {path: file})
CREATE (w)-[:MODIFIED]->(f)
```

### FEATURE Workflow

```cypher
// Log a successful feature implementation
MATCH (p:Project {id: $projectId})
CREATE (w:WorkflowExecution {
  id: randomUUID(),
  timestamp: datetime(),
  summary: $summary,
  actionKeyword: 'FEATURE',
  notes: $notes
})
CREATE (p)-[:HAS_WORKFLOW]->(w)
WITH w
UNWIND $filesChanged AS file
CREATE (f:File {path: file})
CREATE (w)-[:MODIFIED]->(f)
```

### DEPLOY Workflow

```cypher
// Log a successful deployment
MATCH (p:Project {id: $projectId})
CREATE (w:WorkflowExecution {
  id: randomUUID(),
  timestamp: datetime(),
  summary: $summary,
  actionKeyword: 'DEPLOY',
  notes: $notes,
  environment: $environment,
  deployedVersion: $version
})
CREATE (p)-[:HAS_WORKFLOW]->(w)
WITH w
UNWIND $filesChanged AS file
CREATE (f:File {path: file})
CREATE (w)-[:DEPLOYED]->(f)
```

### TOOL_ADD Workflow

```cypher
// Log a successful tool addition
MATCH (p:Project {id: $projectId})
CREATE (w:WorkflowExecution {
  id: randomUUID(),
  timestamp: datetime(),
  summary: $summary,
  actionKeyword: 'TOOL_ADD',
  notes: $notes
})
CREATE (p)-[:HAS_WORKFLOW]->(w)
WITH w
UNWIND $filesChanged AS file
CREATE (f:File {path: file})
CREATE (w)-[:MODIFIED]->(f)
```

## Guidance Hub Patterns

### Creating and Updating Guidance Hubs

```cypher
// Create a new guidance hub
CREATE (hub:AiGuidanceHub {
  id: $hubId,
  description: $description,
  createdAt: datetime()
})
RETURN hub

// Update an existing guidance hub
MATCH (hub:AiGuidanceHub {id: $hubId})
SET hub.description = $description,
    hub.lastUpdated = datetime()
RETURN hub
```

### Creating and Updating Action Templates

```cypher
// Create a new action template
CREATE (t:ActionTemplate {
  keyword: $keyword,
  version: $version,
  isCurrent: true,
  description: $description,
  steps: $steps,
  createdAt: datetime()
})
RETURN t

// Update an existing template
MATCH (t:ActionTemplate {keyword: $keyword, version: $version})
SET t.steps = $steps,
    t.description = $description,
    t.updatedAt = datetime()
RETURN t

// Create a new version of a template
MATCH (old:ActionTemplate {keyword: $keyword, isCurrent: true})
SET old.isCurrent = false
CREATE (new:ActionTemplate {
  keyword: $keyword,
  version: old.version + 0.1,
  isCurrent: true,
  description: $description,
  steps: $steps,
  createdAt: datetime()
})
RETURN new
```

## Incarnation-Specific Patterns

### Knowledge Graph

```cypher
// Create entities with observations
UNWIND $entities AS entity
MERGE (e:Entity {name: entity.name})
ON CREATE SET e.entityType = entity.entityType
WITH e, entity
UNWIND entity.observations AS obs
CREATE (o:Observation {content: obs, timestamp: datetime()})
CREATE (e)-[:HAS_OBSERVATION]->(o)

// Create relations between entities
UNWIND $relations AS rel
MATCH (from:Entity {name: rel.from})
MATCH (to:Entity {name: rel.to})
MERGE (from)-[r:RELATES_TO]->(to)
SET r.type = rel.relationType, r.timestamp = datetime()
```

### Code Analysis

```cypher
// Store code file for analysis
MERGE (f:CodeFile {path: $path})
ON CREATE SET f.language = $language, 
              f.firstAnalyzed = datetime()
SET f.lastAnalyzed = datetime()
RETURN f

// Store AST nodes with relationships
MATCH (a:Analysis {id: $analysisId})
UNWIND $nodes AS node
CREATE (n:ASTNode {
  id: node.id,
  nodeType: node.type,
  value: node.value,
  name: node.name
})
CREATE (a)-[:CONTAINS]->(n)
WITH n, node
MATCH (parent:ASTNode {id: node.parentId})
WHERE node.parentId IS NOT NULL
CREATE (parent)-[:HAS_CHILD]->(n)
```

### Research

```cypher
// Create a hypothesis with timestamp
CREATE (h:Hypothesis {
  id: randomUUID(),
  text: $text,
  description: $description,
  priorProbability: $probability,
  status: 'Active',
  created: datetime()
})
RETURN h.id

// Create experiment with protocol
MATCH (h:Hypothesis {id: $hypothesisId})
MATCH (p:Protocol {id: $protocolId})
CREATE (e:Experiment {
  id: randomUUID(),
  name: $name,
  status: 'Planned',
  created: datetime()
})
CREATE (e)-[:TESTS]->(h)
CREATE (e)-[:FOLLOWS]->(p)
RETURN e.id
```

## Performance Optimized Patterns

### Batch Processing

```cypher
// Batch node creation
UNWIND $batchData AS item
CREATE (n:Label {
  id: item.id,
  property1: item.property1,
  property2: item.property2
})

// Batch relationship creation
UNWIND $batchData AS item
MATCH (a:LabelA {id: item.sourceId})
MATCH (b:LabelB {id: item.targetId})
CREATE (a)-[:RELATIONSHIP_TYPE {property: item.property}]->(b)
```

### Index-Aware Queries

```cypher
// Optimized for index usage
MATCH (n:Label {indexedProperty: $value})
RETURN n

// Force index usage
MATCH (n:Label)
USING INDEX n:Label(indexedProperty)
WHERE n.indexedProperty = $value
RETURN n
```

## Update Patterns

### Transactional Updates

```cypher
// Update with all-or-nothing semantics
MATCH (a:LabelA {id: $idA})
MATCH (b:LabelB {id: $idB})
SET a.property = $value1
SET b.property = $value2
CREATE (a)-[:RELATED_TO]->(b)
```

### Conditional Updates

```cypher
// Update only if condition is met
MATCH (n:Label {id: $id})
WHERE n.property1 > $threshold
SET n.property2 = $newValue
RETURN n

// Using CASE expressions
MATCH (n:Label)
SET n.category = CASE
  WHEN n.value > 100 THEN 'high'
  WHEN n.value > 50 THEN 'medium'
  ELSE 'low'
END
```

## Best Practices

1. **Use Parameters**: Always parameterize queries:
   ```cypher
   MATCH (n:Label {property: $value})
   RETURN n
   ```

2. **Create Constraints for Uniqueness**:
   ```cypher
   CREATE CONSTRAINT label_id_unique IF NOT EXISTS
   FOR (n:Label) REQUIRE n.id IS UNIQUE
   ```

3. **Add Appropriate Indexes**:
   ```cypher
   CREATE INDEX label_property IF NOT EXISTS
   FOR (n:Label) ON (n.property)
   ```

4. **Use EXPLAIN/PROFILE for Query Optimization**:
   ```cypher
   EXPLAIN MATCH (n:Label)-[:RELATIONSHIP]->(m)
   WHERE n.property = $value
   RETURN n, m
   ```

5. **Batch Processing for Large Operations**:
   ```cypher
   UNWIND $batchData AS item
   MERGE (n:Label {id: item.id})
   ```

## Related Documentation

- [Incarnation Cypher Guide](incarnation_cypher_guide.md) - Incarnation-specific Cypher patterns
- [Cypher Snippets Reference](cypher_snippets_reference.md) - Complete reference for Cypher snippets
- [System Directory](system_directory.md) - Comprehensive listing of resources
