# Code Analysis Incarnation

The Code Analysis incarnation extends NeoCoder with powerful code understanding capabilities using Abstract Syntax Tree (AST) and Abstract Semantic Graph (ASG) analysis tools. This incarnation provides a structured approach to parsing, analyzing, and storing code structure in Neo4j.

## Purpose

This incarnation helps you:

1. Parse code into Abstract Syntax Trees (AST) and Abstract Semantic Graphs (ASG)
2. Analyze code structure, complexity, and quality metrics
3. Store analysis results in Neo4j for querying and visualization
4. Generate documentation based on code structure
5. Find code smells and quality issues
6. Compare different versions of code

## Getting Started

To use the Code Analysis incarnation, first switch to it using:

```python
switch_incarnation(incarnation_type="code_analysis")
```

Once activated, you can use the specialized tools for code analysis.

## Available Tools

This incarnation provides the following tools:

### Direct AST Tools
- `parse_to_ast(code, language)`: Parse code into an AST
- `generate_asg(code, language)`: Generate an Abstract Semantic Graph 
- `analyze_code(code, language)`: Analyze code structure and complexity
- `supported_languages()`: Get the list of supported programming languages

### High-Level Analysis Tools
- `analyze_codebase(directory_path, ...)`: Analyze entire codebase
- `analyze_file(file_path, ...)`: Analyze a single file
- `compare_versions(file_path, ...)`: Compare code versions
- `find_code_smells(target, ...)`: Identify code issues
- `generate_documentation(target, ...)`: Generate code documentation
- `explore_code_structure(target, ...)`: Explore code structure
- `search_code_constructs(query, ...)`: Search for code patterns

For detailed documentation on each tool, see the [tools/](tools/) directory.

## Workflows

The Code Analysis incarnation supports the following workflows:

- **[CODE_ANALYZE](workflows/CODE_ANALYZE.md)**: Analyze code structure and quality
- **[AST_DIFF](workflows/AST_DIFF.md)**: Compare different versions of code
- **[CODE_METRICS](workflows/CODE_METRICS.md)**: Extract and analyze code metrics
- **[CODE_DOCS](workflows/CODE_DOCS.md)**: Generate documentation from code

For detailed workflow steps, see the [workflows/](workflows/) directory.

## Cypher Patterns

This incarnation uses specific Cypher patterns for:

- **[AST Storage](cypher/ast_storage.cypher)**: Storing AST nodes in Neo4j
- **[Code Queries](cypher/code_queries.cypher)**: Querying code structure
- **[Complexity Analysis](cypher/complexity_analysis.cypher)**: Analyzing code complexity
- **[Function Relations](cypher/function_relations.cypher)**: Tracking function relationships

For detailed Cypher patterns, see the [cypher/](cypher/) directory.

## Neo4j Schema

The Code Analysis incarnation uses the following Neo4j schema:

### Nodes

- `CodeFile`: Represents a source code file
  - Properties: `path`, `language`, `content`, `firstAnalyzed`, `lastAnalyzed`

- `Analysis`: Represents an analysis run
  - Properties: `id`, `timestamp`, `type` (AST/ASG), `nodeCount`, `language`

- `ASTNode`: Represents a node in the Abstract Syntax Tree
  - Properties: `id`, `nodeType`, `value`, `name`

### Relationships

- `(CodeFile)-[:HAS_ANALYSIS]->(Analysis)`: Links files to their analyses
- `(Analysis)-[:CONTAINS]->(ASTNode)`: Links analyses to their AST nodes
- `(ASTNode)-[:HAS_CHILD]->(ASTNode)`: Represents the AST hierarchy
- `(ASTNode)-[:CALLS]->(ASTNode)`: Represents function calls

## Examples

### Basic AST Analysis

```python
# Analyze a Python file
await analyze_file(file_path="/path/to/file.py", analysis_type="ast")

# Explore the structure
await explore_code_structure(target="/path/to/file.py", view_type="hierarchy")
```

### Finding Complex Methods

```python
# Find complex methods in a file
await find_code_smells(target="/path/to/file.py", smell_categories=["complexity"], threshold="medium")
```

### Generating Documentation

```python
# Generate markdown documentation
await generate_documentation(target="/path/to/project", doc_format="markdown", detail_level="comprehensive")
```

## Related Resources

- [CODE_ANALYZE Template](workflows/CODE_ANALYZE.md) - Step-by-step workflow for code analysis
- [AST Tools Documentation](tools/ast_tools.md) - Detailed documentation of AST tools
- [Cypher Patterns for Code Analysis](cypher/code_queries.cypher) - Neo4j query patterns
