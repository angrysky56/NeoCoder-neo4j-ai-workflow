# Incarnation Cypher Guide

This guide provides specific Cypher patterns for working with each incarnation in the NeoCoder framework. These patterns enable direct interaction with the Neo4j database for each specialized incarnation.

## General Approach

When working with any incarnation:
1. First switch to the appropriate incarnation
2. Use specialized tools provided by that incarnation
3. Use these Cypher patterns for direct database interaction when needed

## Code Analysis Incarnation

The Code Analysis incarnation stores code structure in Neo4j for advanced analysis.

### Querying Code Files and Analyses

```cypher
// Get all code files with their analyses
MATCH (file:CodeFile)-[:HAS_ANALYSIS]->(analysis:Analysis)
RETURN file.path, file.language, analysis.id, analysis.timestamp
ORDER BY analysis.timestamp DESC

// Get details for a specific file
MATCH (file:CodeFile {path: $filePath})
OPTIONAL MATCH (file)-[:HAS_ANALYSIS]->(analysis:Analysis)
RETURN file, collect(analysis) as analyses
```

### Finding Complex Code Structures

```cypher
// Find complex functions (high nesting level)
MATCH (file:CodeFile)-[:HAS_ANALYSIS]->(analysis:Analysis)
MATCH (analysis)-[:CONTAINS]->(node:ASTNode)
WHERE node.nodeType = 'function_definition' AND node.complexity > 10
RETURN file.path, node.name, node.complexity
ORDER BY node.complexity DESC

// Find deeply nested loops
MATCH (file:CodeFile)-[:HAS_ANALYSIS]->(analysis:Analysis)
MATCH (analysis)-[:CONTAINS]->(loop:ASTNode)
WHERE loop.nodeType IN ['for_statement', 'while_statement']
MATCH path = (loop)-[:HAS_CHILD*1..3]->(nested:ASTNode)
WHERE nested.nodeType IN ['for_statement', 'while_statement']
RETURN file.path, loop.nodeType, length(path) as nesting_level
ORDER BY nesting_level DESC
```

### Exploring Function Calls

```cypher
// Get function call graph
MATCH (caller:ASTNode)-[:CALLS]->(callee:ASTNode)
MATCH (analysis1)-[:CONTAINS]->(caller)
MATCH (analysis2)-[:CONTAINS]->(callee)
MATCH (file1:CodeFile)-[:HAS_ANALYSIS]->(analysis1)
MATCH (file2:CodeFile)-[:HAS_ANALYSIS]->(analysis2)
RETURN file1.path, caller.name, file2.path, callee.name

// Find unused functions
MATCH (file:CodeFile)-[:HAS_ANALYSIS]->(analysis:Analysis)
MATCH (analysis)-[:CONTAINS]->(func:ASTNode)
WHERE func.nodeType = 'function_definition'
AND NOT EXISTS {
    MATCH (other:ASTNode)-[:CALLS]->(func)
    WHERE other <> func
}
RETURN file.path, func.name
```

### Finding Code Smells

```cypher
// Find long methods
MATCH (file:CodeFile)-[:HAS_ANALYSIS]->(analysis:Analysis)
MATCH (analysis)-[:CONTAINS]->(func:ASTNode)
WHERE func.nodeType = 'function_definition'
MATCH (func)-[:HAS_CHILD*]->(child:ASTNode)
WITH file, func, count(child) as complexity
WHERE complexity > 50
RETURN file.path, func.name, complexity
ORDER BY complexity DESC

// Find duplicate code structures
MATCH (n1:ASTNode), (n2:ASTNode)
WHERE id(n1) < id(n2)
AND n1.hash = n2.hash
AND size(n1.hash) > 100
MATCH (a1:Analysis)-[:CONTAINS]->(n1)
MATCH (a2:Analysis)-[:CONTAINS]->(n2)
MATCH (f1:CodeFile)-[:HAS_ANALYSIS]->(a1)
MATCH (f2:CodeFile)-[:HAS_ANALYSIS]->(a2)
RETURN f1.path, f2.path, n1.type
```

## Knowledge Graph Incarnation

The Knowledge Graph incarnation manages entities and their relationships.

### Creating Entities and Observations

```cypher
// Create an entity with observations
MERGE (e:Entity {name: $name})
SET e.entityType = $entityType
WITH e
UNWIND $observations AS observation
CREATE (o:Observation {content: observation, timestamp: datetime()})
CREATE (e)-[:HAS_OBSERVATION]->(o)

// Add observations to an existing entity
MATCH (e:Entity {name: $entityName})
WITH e
UNWIND $observations AS observation
CREATE (o:Observation {content: observation, timestamp: datetime()})
CREATE (e)-[:HAS_OBSERVATION]->(o)
```

### Creating and Querying Relationships

```cypher
// Create a relationship between entities
MATCH (e1:Entity {name: $from})
MATCH (e2:Entity {name: $to})
MERGE (e1)-[r:RELATES_TO]->(e2)
SET r.type = $relationType, r.timestamp = datetime()

// Find entities related to a specific entity
MATCH (e:Entity {name: $entityName})-[r:RELATES_TO]->(related:Entity)
RETURN related.name, related.entityType, r.type

// Find entities by relationship depth
MATCH path = (start:Entity {name: $startEntity})-[:RELATES_TO*1..3]->(related:Entity)
RETURN related.name, length(path) as distance
ORDER BY distance
```

### Finding Entities by Content

```cypher
// Find entities by observation content
MATCH (e:Entity)-[:HAS_OBSERVATION]->(o:Observation)
WHERE o.content CONTAINS $searchTerm
RETURN e.name, e.entityType, o.content

// Find entities with a specific observation pattern
MATCH (e:Entity)-[:HAS_OBSERVATION]->(o:Observation)
WHERE o.content =~ $regexPattern
RETURN e.name, collect(o.content) as matchingObservations
```

## Research Incarnation

The Research incarnation supports scientific research and experimentation.

### Managing Hypotheses

```cypher
// Create a hypothesis
CREATE (h:Hypothesis {
  id: randomUUID(),
  text: $text,
  description: $description,
  priorProbability: $probability,
  status: 'Active',
  created: datetime()
})
RETURN h.id

// Update hypothesis probability based on evidence
MATCH (h:Hypothesis {id: $hypothesisId})
MATCH (e:Experiment)-[:TESTS]->(h)
MATCH (e)-[:PRODUCED]->(o:Observation)
WITH h, 
     sum(CASE WHEN o.supportsHypothesis = true THEN 1 ELSE 0 END) as supporting,
     count(o) as total
SET h.currentProbability = h.priorProbability * (supporting / total)
RETURN h.text, h.priorProbability, h.currentProbability
```

### Managing Experiments

```cypher
// Create an experiment linked to a hypothesis
MATCH (h:Hypothesis {id: $hypothesisId})
MATCH (p:Protocol {id: $protocolId})
CREATE (e:Experiment {
  id: randomUUID(),
  name: $name,
  description: $description,
  status: 'Planned',
  created: datetime()
})
CREATE (e)-[:TESTS]->(h)
CREATE (e)-[:FOLLOWS]->(p)
RETURN e.id

// Record experiment results
MATCH (e:Experiment {id: $experimentId})
CREATE (o:Observation {
  content: $observationContent,
  timestamp: datetime(),
  supportsHypothesis: $supports
})
CREATE (e)-[:PRODUCED]->(o)
RETURN o
```

## Decision Support Incarnation

The Decision incarnation helps with structured decision making.

### Creating and Managing Decisions

```cypher
// Create a decision with alternatives
CREATE (d:Decision {
  id: randomUUID(),
  title: $title,
  description: $description,
  createdAt: datetime(),
  status: 'Open'
})
WITH d
UNWIND $alternatives AS alt
CREATE (a:Alternative {
  id: randomUUID(),
  name: alt.name,
  description: alt.description,
  expectedValue: alt.value
})
CREATE (d)-[:HAS_ALTERNATIVE]->(a)
RETURN d.id

// Add a new alternative to an existing decision
MATCH (d:Decision {id: $decisionId})
CREATE (a:Alternative {
  id: randomUUID(),
  name: $name,
  description: $description,
  expectedValue: $expectedValue
})
CREATE (d)-[:HAS_ALTERNATIVE]->(a)
RETURN a.id
```

### Adding Evidence and Metrics

```cypher
// Add evidence to an alternative
MATCH (a:Alternative {id: $alternativeId})
CREATE (e:Evidence {
  content: $content,
  source: $source,
  strength: $strength,
  impact: $impact,
  timestamp: datetime()
})
CREATE (a)-[:HAS_EVIDENCE]->(e)
RETURN e

// Add evaluation metric to a decision
MATCH (d:Decision {id: $decisionId})
CREATE (m:Metric {
  name: $name,
  description: $description,
  weight: $weight,
  targetDirection: $targetDirection
})
CREATE (d)-[:HAS_METRIC]->(m)
RETURN m
```

## Data Analysis Incarnation

The Data Analysis incarnation supports data processing and visualization.

### Managing Datasets

```cypher
// Store dataset metadata
CREATE (d:Dataset {
  id: randomUUID(),
  name: $name,
  description: $description,
  rowCount: $rowCount,
  columnCount: $columnCount,
  createdAt: datetime()
})
WITH d
UNWIND $columns AS col
CREATE (c:Column {
  name: col.name,
  dataType: col.type,
  nullCount: col.nulls,
  uniqueCount: col.unique
})
CREATE (d)-[:HAS_COLUMN]->(c)
RETURN d.id

// Track dataset relationships
MATCH (source:Dataset {id: $sourceId})
MATCH (derived:Dataset {id: $derivedId})
CREATE (derived)-[:DERIVED_FROM {
  transformation: $transformation,
  timestamp: datetime()
}]->(source)
```

### Recording Analysis Results

```cypher
// Store analysis results
MATCH (d:Dataset {id: $datasetId})
CREATE (a:Analysis {
  id: randomUUID(),
  type: $analysisType,
  timestamp: datetime(),
  parameters: $parameters
})
CREATE (d)-[:HAS_ANALYSIS]->(a)
WITH a
UNWIND $results AS result
CREATE (r:Result {
  metric: result.metric,
  value: result.value
})
CREATE (a)-[:PRODUCED]->(r)
RETURN a.id

// Store visualization metadata
MATCH (d:Dataset {id: $datasetId})
CREATE (v:Visualization {
  id: randomUUID(),
  type: $visualizationType,
  title: $title,
  timestamp: datetime(),
  parameters: $parameters
})
CREATE (d)-[:HAS_VISUALIZATION]->(v)
RETURN v.id
```

## Incarnation-Specific Neo4j Schema

Each incarnation has its own Neo4j schema. Here are the key entities and relationships:

### Code Analysis Schema

```cypher
(:CodeFile {path, language, content})-[:HAS_ANALYSIS]->(:Analysis {id, type})
(:Analysis)-[:CONTAINS]->(:ASTNode {id, nodeType})
(:ASTNode)-[:HAS_CHILD]->(:ASTNode)
(:ASTNode)-[:CALLS]->(:ASTNode)
```

### Knowledge Graph Schema

```cypher
(:Entity {name, entityType})-[:HAS_OBSERVATION]->(:Observation {content})
(:Entity)-[:RELATES_TO {type}]->(:Entity)
```

### Research Schema

```cypher
(:Hypothesis {id, text, probability})-[:RELATED_TO]->(:Hypothesis)
(:Experiment {id, name})-[:TESTS]->(:Hypothesis)
(:Experiment)-[:FOLLOWS]->(:Protocol {id, name})
(:Experiment)-[:PRODUCED]->(:Observation {content})
```

### Decision Schema

```cypher
(:Decision {id, title})-[:HAS_ALTERNATIVE]->(:Alternative {id, name})
(:Decision)-[:HAS_METRIC]->(:Metric {name, weight})
(:Alternative)-[:HAS_EVIDENCE]->(:Evidence {content})
```

### Data Analysis Schema

```cypher
(:Dataset {id, name})-[:HAS_COLUMN]->(:Column {name, type})
(:Dataset)-[:HAS_ANALYSIS]->(:Analysis {id, type})
(:Dataset)-[:HAS_VISUALIZATION]->(:Visualization {id, type})
(:Dataset)-[:DERIVED_FROM]->(:Dataset)
```

## Best Practices

1. **Use Parameters**: Always use parameterized queries to avoid injection issues
2. **Transaction Management**: Ensure related operations are in a single transaction
3. **Error Handling**: Include proper error handling for database operations
4. **Indexing**: Create appropriate indexes for performance
5. **Constraints**: Use constraints to ensure data integrity

## Related Resources

- [Verified Cypher Library](cypher_patterns_library.md) - General-purpose verified Cypher patterns
- [Code Analysis Incarnation](code_analysis_incarnation.md) - Detailed documentation of the Code Analysis incarnation
- [Knowledge Graph Incarnation](knowledge_graph_incarnation.md) - Detailed documentation of the Knowledge Graph incarnation
