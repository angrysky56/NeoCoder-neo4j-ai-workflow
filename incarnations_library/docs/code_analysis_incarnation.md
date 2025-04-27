# Code Analysis Incarnation

The Code Analysis Incarnation extends NeoCoder with powerful code understanding capabilities using Abstract Syntax Tree (AST) and Abstract Semantic Graph (ASG) analysis tools. This incarnation provides a structured approach to parsing, analyzing, and storing code structure in Neo4j for deeper understanding and navigation.

## Overview

Code Analysis Incarnation integrates with external AST/ASG tools to create and store comprehensive code analysis results. It transforms the raw output of these tools into a graph structure that enables:

1. Navigation of code hierarchies and relationships
2. Identification of code patterns and anti-patterns
3. Documentation generation based on code structure
4. Comparison between code versions
5. Quality metrics tracking and analysis

## Getting Started

To use the Code Analysis Incarnation, first switch to it using:

```
switch_incarnation(incarnation_type="code_analysis")
```

Once activated, you can use the specialized tools for code analysis:

```python
# Analyze an entire project
analyze_codebase(directory_path="/path/to/project", language="python")

# Analyze a specific file
analyze_file(file_path="/path/to/file.py", analysis_type="both")

# Find potential issues
find_code_smells(target="/path/to/file.py", threshold="medium")
```

## Neo4j Schema

The Code Analysis Incarnation uses the following Neo4j schema:

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
- `(ASTNode)-[:REFERENCES]->(ASTNode)`: Represents cross-references in code

## Available Tools

### Basic Analysis

- `analyze_codebase(directory_path, language=None, include_patterns=None, exclude_patterns=None, analysis_depth="basic")`
  
  Recursively analyzes all code files in a directory, generating AST/ASG representations and storing them in Neo4j.
  
  **Parameters:**
  - `directory_path`: Path to the directory containing the codebase
  - `language`: Optional language filter (e.g., "python", "javascript")
  - `include_patterns`: Optional list of file patterns to include (e.g., ["*.py", "*.js"])
  - `exclude_patterns`: Optional list of file patterns to exclude (e.g., ["*_test.py", "node_modules/*"])
  - `analysis_depth`: Level of analysis detail: "basic", "detailed", or "comprehensive"

- `analyze_file(file_path, version_tag=None, analysis_type="ast", include_metrics=True)`
  
  Analyzes a single code file in depth, parsing it into AST/ASG and calculating complexity metrics.
  
  **Parameters:**
  - `file_path`: Path to the code file to analyze
  - `version_tag`: Optional tag to identify the code version
  - `analysis_type`: Type of analysis to perform: "ast", "asg", or "both"
  - `include_metrics`: Whether to include complexity metrics

- `compare_versions(file_path, old_version, new_version, comparison_level="structural")`
  
  Compares two versions of a code file by analyzing their AST/ASG structures.
  
  **Parameters:**
  - `file_path`: Path to the code file
  - `old_version`: Tag or identifier for the old version
  - `new_version`: Tag or identifier for the new version
  - `comparison_level`: Level of comparison detail: "structural", "semantic", or "detailed"

### Advanced Features

- `find_code_smells(target, smell_categories=None, threshold="medium")`
  
  Identifies potential code issues ("code smells") like complexity, duplication, or unused variables.
  
  **Parameters:**
  - `target`: File path or analysis ID to analyze
  - `smell_categories`: Optional list of smell categories to look for
  - `threshold`: Threshold for reporting issues: "low", "medium", or "high"

- `generate_documentation(target, doc_format="markdown", include_diagrams=True, detail_level="standard")`
  
  Automatically generates documentation from code analysis, including structure and relationships.
  
  **Parameters:**
  - `target`: File, directory, or analysis ID to document
  - `doc_format`: Format for documentation: "markdown", "html", or "text"
  - `include_diagrams`: Whether to include structure diagrams
  - `detail_level`: Level of detail: "minimal", "standard", or "comprehensive"

- `explore_code_structure(target, view_type="summary", include_metrics=True)`
  
  Provides visualizations and reports on code structure, showing hierarchies and dependencies.
  
  **Parameters:**
  - `target`: File, directory, or analysis ID to explore
  - `view_type`: Type of view: "summary", "detailed", "hierarchy", or "dependencies"
  - `include_metrics`: Whether to include complexity metrics

- `search_code_constructs(query, search_type="pattern", scope=None, limit=20)`
  
  Searches through analyzed code to find specific patterns, constructs, or elements.
  
  **Parameters:**
  - `query`: Search query string
  - `search_type`: Type of search: "pattern", "semantic", or "structure"
  - `scope`: Optional scope restriction (file, directory)
  - `limit`: Maximum number of results to return

## AST/ASG Tool Integration

The Code Analysis Incarnation integrates with the following AST/ASG tools:

### Basic Tools
- `parse_to_ast`: Parse code into an Abstract Syntax Tree
- `generate_asg`: Generate an Abstract Semantic Graph from code
- `analyze_code`: Analyze code structure and complexity
- `supported_languages`: Get the list of supported programming languages
- `parse_and_cache`: Parse code into an AST and cache it for resource access
- `generate_and_cache_asg`: Generate an ASG and cache it for resource access
- `analyze_and_cache`: Analyze code and cache the results for resource access

### Enhanced Tools
- `parse_to_ast_incremental`: Parse code with incremental support for faster processing
- `generate_enhanced_asg`: Generate an enhanced ASG with better scope handling
- `diff_ast`: Find differences between two versions of code
- `find_node_at_position`: Locate a specific node at a given line and column
- `parse_and_cache_incremental`: Parse code incrementally and cache the results
- `generate_and_cache_enhanced_asg`: Generate an enhanced ASG and cache it
- `ast_diff_and_cache`: Generate an AST diff and cache it

## CODE_ANALYZE Template

The CODE_ANALYZE action template provides a structured workflow for using the AST/ASG tools. To use this template, follow these steps:

1. Switch to the Code Analysis incarnation:
   ```
   switch_incarnation(incarnation_type="code_analysis")
   ```

2. Get the detailed steps from the template:
   ```
   get_action_template(keyword="CODE_ANALYZE")
   ```

3. Follow the steps in the template to analyze your code

## Use Cases

### Code Quality Assessment

Use the code analysis tools to assess code quality:

```python
# Analyze project
analyze_codebase(directory_path="/path/to/project")

# Find code smells
find_code_smells(target="/path/to/project", threshold="medium")
```

### Code Documentation Generation

Generate documentation from code structure:

```python
# Generate documentation
generate_documentation(target="/path/to/project", doc_format="markdown", include_diagrams=True)
```

### Code Evolution Analysis

Track and analyze code changes:

```python
# Compare versions
compare_versions(file_path="/path/to/file.py", old_version="v1.0", new_version="v2.0")
```

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

## Neo4j Queries

### Getting All Analyzed Files

```cypher
MATCH (f:CodeFile)
RETURN f.path, f.language, f.lastAnalyzed
ORDER BY f.lastAnalyzed DESC
```

### Finding Complex Functions

```cypher
MATCH (f:CodeFile)-[:HAS_ANALYSIS]->(a:Analysis)-[:CONTAINS]->(n:ASTNode)
WHERE n.nodeType = 'FunctionDeclaration' AND n.complexity > 10
RETURN f.path, n.name, n.complexity
ORDER BY n.complexity DESC
```

### Exploring Function Calls

```cypher
MATCH (caller:ASTNode)-[:CALLS]->(callee:ASTNode)
MATCH (caller_file:CodeFile)-[:HAS_ANALYSIS]->(:Analysis)-[:CONTAINS]->(caller)
MATCH (callee_file:CodeFile)-[:HAS_ANALYSIS]->(:Analysis)-[:CONTAINS]->(callee)
RETURN caller_file.path, caller.name, callee_file.path, callee.name
```

## Future Enhancements

1. **Visual Code Navigator**: Interactive visualization of code structure
2. **Automatic Refactoring Suggestions**: AI-powered refactoring recommendations
3. **Code Quality Metrics Dashboard**: Comprehensive quality metrics tracking
4. **Cross-Language Analysis**: Support for analyzing relationships between different languages
5. **Version Control Integration**: Direct integration with Git history

## Contributing

Contributions to the Code Analysis Incarnation are welcome! Key areas for enhancement:

1. Implementing the tool methods with actual AST/ASG integration
2. Adding support for more languages
3. Developing more sophisticated code smell detection
4. Creating visualization components for code structure
5. Implementing advanced metrics and quality analysis

Please follow the standard NeoCoder contribution guidelines when submitting pull requests.
