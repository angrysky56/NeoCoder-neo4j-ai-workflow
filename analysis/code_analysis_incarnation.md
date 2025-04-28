# Code Analysis Incarnation

## Overview

The Code Analysis incarnation is the newest addition to the NeoCoder framework, added in April 2025. This incarnation specializes in analyzing code using Abstract Syntax Trees (AST) and Abstract Semantic Graphs (ASG) to provide deep insights into code structure, quality, and complexity.

## Purpose and Capabilities

The Code Analysis incarnation is designed to:

1. **Parse Source Code** - Convert code into structured AST/ASG representations
2. **Analyze Code Structure** - Examine relationships and patterns in code
3. **Identify Code Issues** - Detect code smells and potential problems
4. **Generate Documentation** - Create documentation based on code analysis
5. **Compare Code Versions** - Track changes between code iterations

## Implementation Structure

The incarnation is implemented in `code_analysis_incarnation.py` with a class structure that follows the standard NeoCoder incarnation pattern:

```python
class CodeAnalysisIncarnation(BaseIncarnation):
    """
    Code Analysis incarnation of the NeoCoder framework.
    
    This incarnation specializes in code analysis through Abstract Syntax Trees (AST)
    and Abstract Semantic Graphs (ASG). It provides a structured workflow for:
    
    1. Parsing source code to AST/ASG representations
    2. Analyzing code complexity and structure
    3. Storing analysis results in Neo4j for reference
    4. Supporting incremental analysis and diffing between versions
    """
    
    # Define the incarnation type
    incarnation_type = IncarnationType.CODE_ANALYSIS
    
    # Metadata
    description = "Code analysis using Abstract Syntax Trees and Abstract Semantic Graphs"
    version = "1.0.0"
    
    # Explicitly define tools
    _tool_methods = [
        "analyze_codebase", 
        "analyze_file",
        "compare_versions",
        "find_code_smells",
        "generate_documentation",
        "explore_code_structure",
        "search_code_constructs"
    ]
```

## Neo4j Schema

The incarnation defines a specialized Neo4j schema for storing code analysis results:

```python
schema_queries = [
    # CodeFile constraints
    "CREATE CONSTRAINT code_file_path IF NOT EXISTS FOR (f:CodeFile) REQUIRE f.path IS UNIQUE",
    
    # AST nodes
    "CREATE CONSTRAINT ast_node_id IF NOT EXISTS FOR (n:ASTNode) REQUIRE n.id IS UNIQUE",
    
    # Analyses
    "CREATE CONSTRAINT analysis_id IF NOT EXISTS FOR (a:Analysis) REQUIRE a.id IS UNIQUE",
    
    # Indexes for efficient querying
    "CREATE INDEX code_file_language IF NOT EXISTS FOR (f:CodeFile) ON (f.language)",
    "CREATE INDEX ast_node_type IF NOT EXISTS FOR (n:ASTNode) ON (n.nodeType)",
    "CREATE FULLTEXT INDEX code_content_fulltext IF NOT EXISTS FOR (f:CodeFile) ON EACH [f.content]",
    "CREATE FULLTEXT INDEX code_construct_fulltext IF NOT EXISTS FOR (n:ASTNode) ON EACH [n.name, n.value]"
]
```

This schema enables efficient storage and retrieval of:
- Code files and their metadata
- AST node structures and relationships
- Analysis results and metrics
- Code structure patterns and constructs

## Core Tools

The incarnation provides several specialized tools for code analysis:

### 1. `analyze_codebase`

Analyzes an entire codebase or directory structure:

```python
async def analyze_codebase(
    self, 
    directory_path: str,
    language: Optional[str] = None,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    analysis_depth: str = "basic"  # Options: "basic", "detailed", "comprehensive"
) -> List[types.TextContent]:
    """Analyze an entire codebase or directory structure.
    
    This tool recursively processes all code files in a directory, parsing them into
    Abstract Syntax Trees and storing the results in Neo4j for further analysis.
    """
```

### 2. `analyze_file`

Performs detailed analysis of a single file:

```python
async def analyze_file(
    self,
    file_path: str,
    version_tag: Optional[str] = None,
    analysis_type: str = "ast",  # Options: "ast", "asg", "both"
    include_metrics: bool = True
) -> List[types.TextContent]:
    """Analyze a single code file in depth.
    
    This tool parses a code file into an Abstract Syntax Tree or Abstract Semantic Graph,
    analyzes its structure and complexity, and stores the results in Neo4j.
    """
```

### 3. `compare_versions`

Compares different versions of code:

```python
async def compare_versions(
    self,
    file_path: str,
    old_version: str,
    new_version: str,
    comparison_level: str = "structural"  # Options: "structural", "semantic", "detailed"
) -> List[types.TextContent]:
    """Compare different versions of the same code.
    
    This tool compares two versions of a code file by analyzing their AST/ASG structures
    and identifying the differences between them.
    """
```

### 4. `find_code_smells`

Identifies potential code issues:

```python
async def find_code_smells(
    self,
    target: str,  # Either a file path or analysis ID
    smell_categories: Optional[List[str]] = None,  # Categories of code smells to look for
    threshold: str = "medium"  # Options: "low", "medium", "high"
) -> List[types.TextContent]:
    """Identify potential code issues and suggestions.
    
    This tool analyzes code to find potential issues ("code smells") like overly complex methods,
    duplicate code, unused variables, and other patterns that might indicate problems.
    """
```

### 5. `generate_documentation`

Creates documentation from code analysis:

```python
async def generate_documentation(
    self,
    target: str,  # Either a file path, directory path, or analysis ID
    doc_format: str = "markdown",  # Options: "markdown", "html", "text"
    include_diagrams: bool = True,
    detail_level: str = "standard"  # Options: "minimal", "standard", "comprehensive"
) -> List[types.TextContent]:
    """Generate documentation from code analysis.
    
    This tool uses AST/ASG analysis to automatically generate documentation for code,
    including function/class descriptions, parameter lists, relationships, and diagrams.
    """
```

### 6. `explore_code_structure`

Visualizes and explores code structure:

```python
async def explore_code_structure(
    self,
    target: str,  # Either a file path, directory path, or analysis ID
    view_type: str = "summary",  # Options: "summary", "detailed", "hierarchy", "dependencies"
    include_metrics: bool = True
) -> List[types.TextContent]:
    """Explore the structure of a codebase.
    
    This tool provides visualizations and reports on the structure of code, showing
    hierarchies, dependencies, and relationships between components.
    """
```

### 7. `search_code_constructs`

Searches for specific code patterns:

```python
async def search_code_constructs(
    self,
    query: str,  # Search query
    search_type: str = "pattern",  # Options: "pattern", "semantic", "structure"
    scope: Optional[str] = None,  # Optional scope restriction (file, directory)
    limit: int = 20
) -> List[types.TextContent]:
    """Search for specific code constructs.
    
    This tool searches through analyzed code to find specific patterns, constructs,
    or semantic elements that match the query.
    """
```

## AST Processing

The incarnation includes utilities for processing AST data:

```python
async def _process_ast_data(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process AST data into a format suitable for Neo4j storage."""
    processed_data = {
        "id": str(uuid.uuid4()),
        "language": ast_data.get("language", "unknown"),
        "node_count": 0,
        "root_node_type": "unknown",
        "nodes": []
    }
    
    # Extract the root node and process the tree
    root = ast_data.get("ast", {})
    if root:
        processed_data["root_node_type"] = root.get("type", "unknown")
        
        # Process nodes (simplified for the example)
        nodes = []
        self._extract_nodes(root, nodes)
        processed_data["nodes"] = nodes
        processed_data["node_count"] = len(nodes)
    
    return processed_data
```

And node extraction:

```python
def _extract_nodes(self, node: Dict[str, Any], nodes: List[Dict[str, Any]], parent_id: str = None):
    """Extract nodes from AST for Neo4j storage."""
    if not node or not isinstance(node, dict):
        return
    
    # Create a unique ID for this node
    node_id = str(uuid.uuid4())
    
    # Extract relevant properties
    node_data = {
        "id": node_id,
        "node_type": node.get("type", "unknown"),
        "parent_id": parent_id,
        "value": node.get("value", ""),
        "name": node.get("name", ""),
        "location": {
            "start": node.get("start", {}),
            "end": node.get("end", {})
        }
    }
    
    # Add to the nodes list
    nodes.append(node_data)
    
    # Process children
    for key, value in node.items():
        if key in ["type", "value", "name", "start", "end"]:
            continue
            
        if isinstance(value, dict):
            self._extract_nodes(value, nodes, node_id)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    self._extract_nodes(item, nodes, node_id)
```

## Neo4j Storage

The incarnation stores AST data in Neo4j for persistent reference:

```python
async def _store_ast_in_neo4j(self, file_path: str, ast_processed: Dict[str, Any]) -> Tuple[bool, str]:
    """Store processed AST data in Neo4j."""
    # Generate a unique analysis ID
    analysis_id = str(uuid.uuid4())
    
    # Query to create the code file node
    file_query = """
    MERGE (f:CodeFile {path: $path})
    ON CREATE SET f.language = $language, 
                 f.firstAnalyzed = datetime()
    SET f.lastAnalyzed = datetime()
    RETURN f
    """
    
    # Query to create the analysis node
    analysis_query = """
    CREATE (a:Analysis {
        id: $id,
        timestamp: datetime(),
        type: 'AST',
        nodeCount: $nodeCount,
        language: $language
    })
    WITH a
    MATCH (f:CodeFile {path: $path})
    CREATE (f)-[:HAS_ANALYSIS]->(a)
    RETURN a
    """
    
    # Query to create AST nodes
    nodes_query = """
    UNWIND $nodes AS node
    CREATE (n:ASTNode {
        id: node.id,
        nodeType: node.node_type,
        value: node.value,
        name: node.name
    })
    WITH n, node
    MATCH (a:Analysis {id: $analysisId})
    CREATE (a)-[:CONTAINS]->(n)
    WITH n, node
    MATCH (parent:ASTNode {id: node.parent_id})
    WHERE node.parent_id IS NOT NULL
    CREATE (parent)-[:HAS_CHILD]->(n)
    """
```

## Implementation Status

The Code Analysis incarnation is in the early stages of implementation. As of the analysis, the tool method declarations and documentation are complete, but the actual implementations are stubbed out with placeholder content. For example:

```python
async def analyze_codebase(self, directory_path: str, ...):
    return [types.TextContent(type="text", text=f"""
# Codebase Analysis: Not Yet Implemented

This tool would analyze the codebase at:
- Directory: {directory_path}
- Language: {language or "All languages"}
...
    """)]
```

The core architecture and Neo4j schema are defined, but the actual AST/ASG processing is not yet fully implemented. The planned integration with external AST tools is prepared but not completed.

## Integration with External AST Tools

The incarnation is designed to integrate with external AST parsing tools through a structured interface:

1. **Code Parsing** - Converting code files to AST/ASG structures
2. **Structure Analysis** - Analyzing the parsed structures for patterns and metrics
3. **Storage** - Storing results in Neo4j for persistent reference
4. **Querying** - Implementing specialized queries for code analysis

The supported languages for AST parsing are intended to include:
- Python
- JavaScript
- Java
- C/C++
- Go
- And others

## Future Development Paths

Based on the code analysis, several development paths are apparent:

1. **Complete Tool Implementations** - Finish implementing the core tools
2. **Expand Language Support** - Add support for more programming languages
3. **Enhanced Visualization** - Add visualization capabilities for code structures
4. **Metrics System** - Implement a comprehensive code metrics system
5. **IDE Integration** - Develop integration with common IDE environments
6. **Automated Refactoring** - Add capabilities for automated code refactoring based on analysis

## Conclusion

The Code Analysis incarnation represents a significant expansion of the NeoCoder framework's capabilities. By leveraging AST/ASG analysis, it provides a foundation for sophisticated code understanding, documentation, and improvement. While currently in the early stages of implementation, the architecture is well-designed and positioned for growth.

The integration of code analysis with the existing Neo4j-based knowledge system creates opportunities for advanced code navigation, exploration, and transformation. As this incarnation matures, it has the potential to significantly enhance AI-assisted coding workflows with deep code understanding capabilities.
