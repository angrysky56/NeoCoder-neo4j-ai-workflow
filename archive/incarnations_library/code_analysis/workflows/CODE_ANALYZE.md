# CODE_ANALYZE Workflow

This workflow guides you through using Abstract Syntax Tree (AST) and Abstract Semantic Graph (ASG) tools to analyze code and gain deeper understanding of its structure and behavior.

## Overview

The CODE_ANALYZE workflow helps you:

1. Parse code into Abstract Syntax Trees and Semantic Graphs
2. Analyze code structure, complexity, and quality
3. Identify potential code smells and issues
4. Generate documentation and visualizations
5. Store results in Neo4j for later reference

## Prerequisites

- Switch to the code_analysis incarnation: `switch_incarnation(incarnation_type="code_analysis")`
- Ensure you have access to the code files you want to analyze
- Supported languages: python, javascript (check with `supported_languages()`)

## Workflow Steps

### 1. Preparation

1. **Identify the code to analyze**
   - Determine whether you're analyzing a single file, multiple files, or an entire codebase
   - Note the programming language(s) involved (supported: python, javascript)
   - Identify specific aspects to focus on (structure, complexity, patterns, quality issues)

2. **Verify available AST/ASG tools**
   - Direct tools (always available):
     - parse_to_ast: Parse code into AST
     - generate_asg: Generate ASG 
     - analyze_code: Analyze code structure
     - supported_languages: Get supported languages
   - Incarnation tools (require code_analysis incarnation):
     - analyze_file: Analyze a file
     - analyze_codebase: Analyze a codebase
     - find_code_smells: Find quality issues
     - generate_documentation: Generate docs

### 2. Basic AST Analysis

1. **For quick direct analysis of code snippets**:
   ```python
   # Direct AST parsing
   ast_result = parse_to_ast(code=code_string, language=language)
   
   # Examine the AST structure
   print(f"Root node type: {ast_result['ast']['type']}")
   print(f"Children count: {len(ast_result['ast']['children'])}")
   ```

2. **For file analysis with Neo4j storage**:
   ```python
   # Analyze with incarnation tools
   result = await analyze_file(
       file_path=file_path, 
       analysis_type='ast',
       include_metrics=True
   )
   ```

### 3. Semantic Graph Analysis

1. **For direct ASG generation**:
   ```python
   # Generate ASG
   asg_result = generate_asg(code=code_string, language=language)
   
   # Examine the graph structure
   print(f"Nodes: {len(asg_result['nodes'])}")
   print(f"Edges: {len(asg_result['edges'])}")
   ```

2. **For file analysis with Neo4j storage**:
   ```python
   # Analyze with incarnation tools
   result = await analyze_file(
       file_path=file_path, 
       analysis_type='asg'
   )
   ```

### 4. Code Complexity Analysis

1. **For direct complexity analysis**:
   ```python
   # Analyze code structure and metrics
   analysis_result = analyze_code(code=code_string, language=language)
   
   # Examine complexity metrics
   print(f"Functions: {len(analysis_result['functions'])}")
   print(f"Classes: {len(analysis_result['classes'])}")
   print(f"Max nesting: {analysis_result['complexity_metrics']['max_nesting_level']}")
   ```

2. **For identifying code smells**:
   ```python
   # Find code smells
   smells = await find_code_smells(
       target=file_path,
       smell_categories=["complexity", "duplication", "naming"],
       threshold="medium"
   )
   ```

### 5. Results and Documentation

1. **Generate Documentation**:
   ```python
   # Generate docs
   docs = await generate_documentation(
       target=file_path,
       doc_format="markdown",
       include_diagrams=True,
       detail_level="standard"
   )
   ```

2. **Explore Code Structure**:
   ```python
   # Explore structure
   structure = await explore_code_structure(
       target=file_path,
       view_type="hierarchy",
       include_metrics=True
   )
   ```

3. **Search for Code Patterns**:
   ```python
   # Search for patterns
   results = await search_code_constructs(
       query="function.*add",
       search_type="pattern",
       scope=file_path,
       limit=20
   )
   ```

### 6. Summarize Findings

1. **Create Analysis Report**:
   - Code size and complexity metrics
   - Identified code smells and quality issues
   - Architectural patterns and dependencies
   - Recommendations for improvement

2. **Visualize Results**:
   - Class hierarchies and relationships
   - Function call graphs
   - Complexity hotspots
   - Code smells distribution

### 7. Log the Workflow Execution

Record the execution of this workflow:

```python
log_workflow_execution(
    project_id=project_id,
    action_keyword="CODE_ANALYZE",
    summary="Analyzed code structure and identified quality issues",
    files_changed=analyzed_files,
    notes="Found 5 code smell patterns and generated documentation"
)
```

## Neo4j Queries for Code Analysis

Once the code is analyzed and stored in Neo4j, you can use these queries to explore the results:

```cypher
// Get all analyzed files
MATCH (f:CodeFile)
RETURN f.path, f.language, f.lastAnalyzed
ORDER BY f.lastAnalyzed DESC

// Find complex functions
MATCH (f:CodeFile)-[:HAS_ANALYSIS]->(a:Analysis)-[:CONTAINS]->(n:ASTNode)
WHERE n.nodeType = 'function_definition' AND n.complexity > 10
RETURN f.path, n.name, n.complexity
ORDER BY n.complexity DESC

// Get function call graph
MATCH (caller:ASTNode)-[:CALLS]->(callee:ASTNode)
MATCH (analysis1)-[:CONTAINS]->(caller)
MATCH (analysis2)-[:CONTAINS]->(callee)
MATCH (file1:CodeFile)-[:HAS_ANALYSIS]->(analysis1)
MATCH (file2:CodeFile)-[:HAS_ANALYSIS]->(analysis2)
RETURN file1.path, caller.name, file2.path, callee.name
```

## Best Practices

- Always specify the language parameter for accurate parsing
- Use the code_analysis incarnation for Neo4j storage and advanced analysis
- Combine direct AST tools with incarnation tools for comprehensive analysis
- Focus on actionable insights rather than just metrics
- Store analysis results in Neo4j for future reference and comparison

## Related Resources

- [AST Tools Documentation](../tools/ast_tools.md)
- [Code Metrics Documentation](../tools/code_metrics.md)
- [AST Storage Cypher Patterns](../cypher/ast_storage.cypher)
