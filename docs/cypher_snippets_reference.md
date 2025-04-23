# Cypher Snippets Reference Guide

This document provides a comprehensive reference for the Cypher snippet toolkit included in the NeoCoder Neo4j AI workflow. 
It preserves all original formatting and citation markers from the source material.

## Overview

The Cypher snippet toolkit creates a *mini-documentation graph* where every **`(:CypherSnippet)`** node stores a piece of Cypher syntax, an example, and metadata. Text and (optionally) vector indexes make the snippets instantly searchable from plain keywords *or* embeddings.

## 1 · Schema & safety constraints

```cypher
// 1-A Uniqueness for internal IDs
CREATE CONSTRAINT cypher_snippet_id IF NOT EXISTS
FOR   (c:CypherSnippet)
REQUIRE c.id IS UNIQUE;            // Neo4j 5 syntax
citeturn0search9

// 1-B Optional tag helper (one Tag node per word/phrase)
CREATE CONSTRAINT tag_name_unique IF NOT EXISTS
FOR   (t:Tag)
REQUIRE t.name IS UNIQUE;
citeturn0search9
```

## 2 · Indexes that power search

```cypher
// 2-A Quick label/property look-ups
CREATE LOOKUP INDEX snippetLabelLookup IF NOT EXISTS
FOR (n) ON EACH labels(n);
citeturn0search6

// 2-B Plain-text index (fast prefix / CONTAINS / = queries)
CREATE TEXT INDEX snippet_text IF NOT EXISTS
FOR (c:CypherSnippet) ON (c.syntax, c.description);
citeturn0search5

// 2-C Full-text scoring index (tokenised, ranked search)
CREATE FULLTEXT INDEX snippet_fulltext IF NOT EXISTS
FOR (c:CypherSnippet) ON EACH [c.syntax, c.example];
citeturn0search0

// 2-D (OPTIONAL) Vector index for embeddings ≥Neo4j 5.15
CREATE VECTOR INDEX snippet_vec IF NOT EXISTS
FOR (c:CypherSnippet) ON (c.embedding)
OPTIONS {indexConfig: {
  `vector.dimensions`: 384,
  `vector.similarity_function`: 'cosine'
}};
citeturn1search5
```

*If your build is ≤5.14, call `db.index.vector.createNodeIndex` instead.* citeturn1search0

## 3 · Template to store a snippet

```cypher
:params {
  snippet: {
    id:         'create-node-basic',
    name:       'CREATE node (basic)',
    syntax:     'CREATE (n:Label {prop: $value})',
    description:'Creates a single node with one label and properties.',
    example:    'CREATE (p:Person {name:$name, age:$age})',
    since:      5.0,
    tags:       ['create','insert','node']
  }
}

// 3-A MERGE guarantees idempotence
MERGE (c:CypherSnippet {id:$snippet.id})
SET   c += $snippet
WITH  c, $snippet.tags AS tags
UNWIND tags AS tag
  MERGE (t:Tag {name:tag})
  MERGE (c)-[:TAGGED_AS]->(t);
```  

Parameter maps keep code reusable and prevent query-plan recompilation. citeturn0search3turn0search8

## 4 · How to search

### 4-A Exact / prefix match via TEXT index
```cypher
MATCH (c:CypherSnippet)
WHERE c.name STARTS WITH $term      // fast TEXT index hit
RETURN c.name, c.syntax, c.example
ORDER BY c.name;
```

### 4-B Ranked full-text search
```cypher
CALL db.index.fulltext.queryNodes(
  'snippet_fulltext',               // index name
  $q                                // raw search string
) YIELD node, score
RETURN node.name, node.syntax, score
ORDER BY score DESC
LIMIT 10;
``` citeturn0search0turn0search12

### 4-C Embedding similarity (vector search)
```cypher
WITH $queryEmbedding AS vec
CALL db.index.vector.queryNodes(
  'snippet_vec', 5, vec            // top-5 cosine hits
) YIELD node, similarity
RETURN node.name, node.syntax, similarity
ORDER BY similarity DESC;
``` citeturn1search1

## 5 · Updating or deleting snippets

```cypher
// 5-A Edit description
MATCH (c:CypherSnippet {id:$id})
SET   c.description = $newText,
      c.lastUpdated = date()
RETURN c;

// 5-B Remove a snippet cleanly
MATCH (c:CypherSnippet {id:$id})
DETACH DELETE c;
```
Both operations automatically maintain index consistency – no extra work required. citeturn0search1

## 6 · Bulk export / import (APOC)

```cypher
CALL apoc.export.cypher.all(
  'cypher_snippets.cypher',
  {useOptimizations:true, format:'cypher-shell'}
);
```  
This writes share-ready Cypher that can be replayed with `cypher-shell < cypher_snippets.cypher`. citeturn0search4turn0search14

---

### Quick-start recap  
1. **Run Section 1 & 2** once per database to set up constraints and indexes.  
2. Use **Section 3** (param-driven) to add new documentation entries.  
3. Query with **Section 4**, and optionally add vector search if you store embeddings.  
4. Backup or publish with **Section 6**.

## Note on Citation Markers

The `citeturnXsearchY` markers in this document are citation references from the original source material. They should be preserved in this reference document but may cause rendering issues in GitHub's Markdown viewer. The main README.md file contains a clean version without these markers.
