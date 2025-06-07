# Cypher Snippet Toolkit

Below is a consolidated, **Neo4j 5-series–ready** toolkit you can paste straight into Neo4j Browser, Cypher shell, or any driver.  
It creates a *mini-documentation graph* where every **`(:CypherSnippet)`** node stores a piece of Cypher syntax, an example, and metadata; text and (optionally) vector indexes make the snippets instantly searchable from plain keywords *or* embeddings.

---

## 1 · Schema & safety constraints

```cypher
// 1-A Uniqueness for internal IDs
CREATE CONSTRAINT cypher_snippet_id IF NOT EXISTS
FOR   (c:CypherSnippet)
REQUIRE c.id IS UNIQUE;            // Neo4j 5 syntax

// 1-B Optional tag helper (one Tag node per word/phrase)
CREATE CONSTRAINT tag_name_unique IF NOT EXISTS
FOR   (t:Tag)
REQUIRE t.name IS UNIQUE;
```

## 2 · Indexes that power search

```cypher
// 2-A Quick label/property look-ups
CREATE LOOKUP INDEX snippetLabelLookup IF NOT EXISTS
FOR (n) ON EACH labels(n);

// 2-B Plain-text index (fast prefix / CONTAINS / = queries)
CREATE TEXT INDEX snippet_text_syntax IF NOT EXISTS
FOR (c:CypherSnippet) ON (c.syntax);

CREATE TEXT INDEX snippet_text_description IF NOT EXISTS
FOR (c:CypherSnippet) ON (c.description);

// 2-C Full-text scoring index (tokenised, ranked search)
CREATE FULLTEXT INDEX snippet_fulltext IF NOT EXISTS
FOR (c:CypherSnippet) ON EACH [c.syntax, c.example];

// 2-D (OPTIONAL) Vector index for embeddings ≥Neo4j 5.15
CREATE VECTOR INDEX snippet_vec IF NOT EXISTS
FOR (c:CypherSnippet) ON (c.embedding)
OPTIONS {indexConfig: {
  `vector.dimensions`: 384,
  `vector.similarity_function`: 'cosine'
}};
```

*If your build is ≤5.14, call `db.index.vector.createNodeIndex` instead.*

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

Parameter maps keep code reusable and prevent query-plan recompilation.

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
```

### 4-C Embedding similarity (vector search)
```cypher
WITH $queryEmbedding AS vec
CALL db.index.vector.queryNodes(
  'snippet_vec', 5, vec            // top-5 cosine hits
) YIELD node, similarity
RETURN node.name, node.syntax, similarity
ORDER BY similarity DESC;
```

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

Both operations automatically maintain index consistency – no extra work required.

## 6 · Bulk export / import (APOC)

```cypher
CALL apoc.export.cypher.all(
  'cypher_snippets.cypher',
  {useOptimizations:true, format:'cypher-shell'}
);
```

This writes share-ready Cypher that can be replayed with `cypher-shell < cypher_snippets.cypher`.

---

### Quick-start recap

1. **Run Section 1 & 2** once per database to set up constraints and indexes.  
2. Use **Section 3** (param-driven) to add new documentation entries.  
3. Query with **Section 4**, and optionally add vector search if you store embeddings.  
4. Backup or publish with **Section 6**.

With these building blocks you now have a *living*, searchable "Cypher cheat-sheet inside Cypher" that always stays local, versionable, and extensible. Enjoy friction-free recall as your query repertoire grows!

*Note: A full reference version of this documentation that preserves all original formatting is available in the `/docs/cypher_snippets_reference.md` file.*
