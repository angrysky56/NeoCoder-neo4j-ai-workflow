// Cypher Snippet Toolkit Template
// This template provides guidance on using the Cypher snippet toolkit to manage Neo4j query patterns.

// Create the CYPHER_SNIPPETS template
MERGE (t:ActionTemplate {keyword: 'CYPHER_SNIPPETS', version: '1.0'})
ON CREATE SET
  t.description = 'Manage and use Cypher snippets for Neo4j queries',
  t.complexity = 'MEDIUM',
  t.estimatedEffort = 30,
  t.isCurrent = true,
  t.domain = 'database',
  t.steps = "# Using Cypher Snippets

This template guides you through using the Cypher snippet toolkit to find, use, and manage Neo4j query patterns.

## 1. Explore Available Snippets

Start by listing all available snippets to get an overview:
```
list_cypher_snippets()
```

You can also filter by tag:
```
list_cypher_snippets(tag=\"create\")
```

Or by Neo4j version compatibility:
```
list_cypher_snippets(since_version=5.0)
```

## 2. Searching for Snippets

Find relevant snippets using the search tool:

```
search_cypher_snippets(query_text=\"index\", search_type=\"text\")
```

Search types:
- **text**: Simple text matching (case-insensitive)
- **fulltext**: Ranked fulltext search for more complex queries
- **tag**: Search specifically by tag

## 3. View Detailed Snippet Information

Get complete information about a specific snippet:

```
get_cypher_snippet(id=\"create-node-basic\")
```

This will show all metadata, the syntax pattern, example usage, and associated tags.

## 4. Using Snippets in Queries

When writing Neo4j queries, apply the pattern from the snippet, adjusting parameters and structure as needed for the current task. Use `run_custom_query()` or `write_neo4j_cypher()` to execute the query.

## 5. Managing Snippets (Optional)

Add a new snippet:
```
create_cypher_snippet(
  id=\"your-snippet-id\",
  name=\"Your Snippet Name\",
  syntax=\"CYPHER SYNTAX PATTERN\",
  description=\"What this pattern does\",
  example=\"EXAMPLE USAGE\",
  since=5.0,
  tags=[\"tag1\", \"tag2\"]
)
```

Update an existing snippet:
```
update_cypher_snippet(
  id=\"existing-snippet-id\",
  description=\"Updated description\"
)
```

Delete a snippet (use with caution):
```
delete_cypher_snippet(id=\"snippet-to-delete\")
```

## 6. Record Your Work

After successfully using or managing snippets, record your work:
```
log_workflow_execution(
  project_id=\"the-project-id\",
  keyword=\"CYPHER_SNIPPETS\",
  description=\"Used pattern X to implement feature Y\",
  modified_files=[\"file/path1\", \"file/path2\"],
  execution_time_seconds=300
)
```

Remember: Only log successful workflow executions!
"

ON MATCH SET
  t.isCurrent = true,
  t.version = '1.0'

WITH t

// Add the template to the main hub
MATCH (hub:AiGuidanceHub {id: 'main_hub'})
MERGE (hub)-[:PROVIDES_TEMPLATE]->(t)

RETURN t.keyword + ' v' + t.version + ' template created or updated';