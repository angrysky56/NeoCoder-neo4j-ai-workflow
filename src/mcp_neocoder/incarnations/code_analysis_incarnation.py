"""
Code Analysis incarnation of the NeoCoder framework.

Provides a structured approach to analyzing and understanding codebases using
Abstract Syntax Tree (AST) and Abstract Semantic Graph (ASG) tools.
"""

import json
import logging
import uuid
import os
import asyncio
from typing import Dict, Any, List, Optional, Union, Tuple

import mcp.types as types
from pydantic import Field
from neo4j import AsyncTransaction

from .base_incarnation import BaseIncarnation

logger = logging.getLogger("mcp_neocoder.incarnations.code_analysis")


class CodeAnalysisIncarnation(BaseIncarnation):
    """
    Code Analysis incarnation of the NeoCoder framework.

    This incarnation specializes in code analysis through Abstract Syntax Trees (AST)
    and Abstract Semantic Graphs (ASG). It provides a structured workflow for:

    1. Parsing source code to AST/ASG representations
    2. Analyzing code complexity and structure
    3. Storing analysis results in Neo4j for reference
    4. Supporting incremental analysis and diffing between versions

    The incarnation integrates with existing AST tools to create a comprehensive
    code analysis and understanding system.
    """

    # Define the incarnation name as a string value
    name = "code_analysis"

    # Metadata for display in the UI
    description = "Code analysis using Abstract Syntax Trees and Abstract Semantic Graphs"
    version = "1.0.0"

    # Explicitly define which methods should be registered as tools
    _tool_methods = [
        "analyze_codebase",
        "analyze_file",
        "compare_versions",
        "find_code_smells",
        "generate_documentation",
        "explore_code_structure",
        "search_code_constructs"
    ]

    # Schema queries for Neo4j setup
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

    async def _safe_execute_write(self, session, query, params=None):
        """Execute a write query safely and handle all errors internally."""
        if params is None:
            params = {}

        try:
            async def execute_in_tx(tx):
                result = await tx.run(query, params)
                try:
                    summary = await result.consume()
                    stats = {
                        "nodes_created": summary.counters.nodes_created,
                        "relationships_created": summary.counters.relationships_created,
                        "properties_set": summary.counters.properties_set,
                        "nodes_deleted": summary.counters.nodes_deleted,
                        "relationships_deleted": summary.counters.relationships_deleted
                    }
                    return True, stats
                except Exception as inner_e:
                    logger.warning(f"Query executed but couldn't get stats: {inner_e}")
                    return True, {}

            success, stats = await session.execute_write(execute_in_tx)
            return success, stats
        except Exception as e:
            logger.error(f"Error executing write query: {e}")
            return False, {}

    async def _safe_read_query(self, session, query, params=None):
        """Execute a read query safely, handling all errors internally."""
        if params is None:
            params = {}

        try:
            async def execute_and_process_in_tx(tx):
                try:
                    result = await tx.run(query, params)
                    records = await result.values()

                    processed_data = []
                    for record in records:
                        if isinstance(record, (list, tuple)):
                            field_names = ['col0', 'col1', 'col2', 'col3', 'col4', 'col5']
                            row_data = {}

                            for i, value in enumerate(record):
                                if i < len(field_names):
                                    row_data[field_names[i]] = value
                                else:
                                    row_data[f'col{i}'] = value

                            processed_data.append(row_data)
                        else:
                            processed_data.append(record)

                    return json.dumps(processed_data, default=str)
                except Exception as inner_e:
                    logger.error(f"Error inside transaction: {inner_e}")
                    return json.dumps([])

            result_json = await session.execute_read(execute_and_process_in_tx)

            try:
                return json.loads(result_json)
            except json.JSONDecodeError as json_error:
                logger.error(f"Error parsing JSON result: {json_error}")
                return []

        except Exception as e:
            logger.error(f"Error executing read query: {e}")
            return []

    async def get_guidance_hub(self) -> List[types.TextContent]:
        """Get the guidance hub for this incarnation."""
        hub_description = """
# Code Analysis with AST/ASG Tools

Welcome to the Code Analysis System powered by the NeoCoder framework. This system helps you analyze and understand codebases using Abstract Syntax Trees (AST) and Abstract Semantic Graphs (ASG).

## Getting Started

1. **Switch to Code Analysis Mode**
   - Use `switch_incarnation(incarnation_type=\"code_analysis\")`
   - This activates all the specialized code analysis tools

2. **Select Analysis Scope**
   - Single file analysis for focused inspection
   - Directory/codebase analysis for broader insights
   - Version comparison for understanding changes

3. **Choose Analysis Type**
   - AST (Abstract Syntax Tree): For syntax and structure
   - ASG (Abstract Semantic Graph): For deeper semantic understanding
   - Combined analysis for comprehensive insights

## Available Tools

### Basic Analysis Tools
- `analyze_file(file_path, analysis_type, include_metrics)`: Analyze a single file
  - **Parameters**:
    - `file_path`: Path to the file to analyze
    - `analysis_type`: \"ast\", \"asg\", or \"both\"
    - `include_metrics`: Boolean to include complexity metrics

- `analyze_codebase(directory_path, language, include_patterns, exclude_patterns, analysis_depth)`: Analyze entire codebase
  - **Parameters**:
    - `directory_path`: Root directory of the codebase
    - `language`: Optional language filter (e.g., \"python\", \"javascript\")
    - `include_patterns`: Optional file patterns to include (e.g., [\"*.py\", \"*.js\"])
    - `exclude_patterns`: Optional file patterns to exclude (e.g., [\"*_test.py\", \"node_modules/*\"])
    - `analysis_depth`: \"basic\", \"detailed\", or \"comprehensive\"

- `compare_versions(file_path, old_version, new_version, comparison_level)`: Compare code versions
  - **Parameters**:
    - `file_path`: Path to the file
    - `old_version`: Reference to older version
    - `new_version`: Reference to newer version
    - `comparison_level`: \"structural\", \"semantic\", or \"detailed\"

### Advanced Analysis Tools

- `find_code_smells(target, smell_categories, threshold)`: Identify code issues
  - **Parameters**:
    - `target`: File path or directory
    - `smell_categories`: Optional categories of issues to find
    - `threshold`: \"low\", \"medium\", or \"high\" sensitivity

- `generate_documentation(target, doc_format, include_diagrams, detail_level)`: Create docs from code
  - **Parameters**:
    - `target`: File or directory to document
    - `doc_format`: \"markdown\", \"html\", or \"text\"
    - `include_diagrams`: Boolean to include structure diagrams
    - `detail_level`: \"minimal\", \"standard\", or \"comprehensive\"

- `explore_code_structure(target, view_type, include_metrics)`: Visualize code structure
  - **Parameters**:
    - `target`: File or directory to explore
    - `view_type`: \"summary\", \"detailed\", \"hierarchy\", or \"dependencies\"
    - `include_metrics`: Boolean to include complexity metrics

- `search_code_constructs(query, search_type, scope, limit)`: Find specific patterns
  - **Parameters**:
    - `query`: Search pattern
    - `search_type`: \"pattern\", \"semantic\", or \"structure\"
    - `scope`: Optional path to limit search scope
    - `limit`: Maximum results to return

## Analysis Workflow

For structured code analysis, follow the `CODE_ANALYZE` action template:
```
get_action_template(keyword=\"CODE_ANALYZE\")
```

This template provides step-by-step guidance for conducting thorough code analysis and documenting the results.

## Understanding AST/ASG

- **Abstract Syntax Tree (AST)**: Represents the syntactic structure of code as a tree
  - Nodes represent language constructs (functions, classes, loops)
  - Shows code structure but not semantic meaning

- **Abstract Semantic Graph (ASG)**: Extends AST with semantic information
  - Includes type information and data flow analysis
  - Shows relationships between code elements (variable usage, function calls)

## Storage in Neo4j

Analysis results are stored in Neo4j with the following structure:

- `(:CodeFile)` - Represents source code files
- `(:Analysis)` - Represents analysis results
- `(:ASTNode)` - Represents nodes in the AST/ASG
- `[:HAS_ANALYSIS]` - Links files to analysis results
- `[:CONTAINS]` - Links analysis to AST nodes
- `[:HAS_CHILD]` - Links parent-child relationships in AST

## Best Practices

1. Start with high-level codebase analysis to get an overview
2. Follow up with detailed analysis of specific files or components
3. Use `find_code_smells()` to identify improvement opportunities
4. Document analysis results and recommendations
5. Tag analyses with version information for future comparison
"""
        # Directly return the guidance hub content
        return [types.TextContent(type="text", text=hub_description)]

    async def initialize_schema(self):
        """Initialize the Neo4j schema for Code Analysis."""
        try:
            async with self.driver.session(database=self.database) as session:
                # Execute each constraint/index query individually
                for query in self.schema_queries:
                    await session.execute_write(lambda tx: tx.run(query))

                # Create base guidance hub for this incarnation if it doesn't exist
                await self.ensure_hub_exists()

            logger.info("Code Analysis incarnation schema initialized")
        except Exception as e:
            logger.error(f"Error initializing code_analysis schema: {e}")
            raise

    async def ensure_hub_exists(self):
        """Create the guidance hub for this incarnation if it doesn't exist."""
        query = """
        MERGE (hub:AiGuidanceHub {id: 'code_analysis_hub'})
        ON CREATE SET hub.description = $description
        RETURN hub
        """

        description = """
# Code Analysis with AST/ASG Tools

Welcome to the Code Analysis System powered by the NeoCoder framework. This system helps you analyze and understand codebases using Abstract Syntax Trees (AST) and Abstract Semantic Graphs (ASG).

## Getting Started

1. **Switch to Code Analysis Mode**
   - Use `switch_incarnation(incarnation_type=\"code_analysis\")`
   - This activates all the specialized code analysis tools

2. **Select Analysis Scope**
   - Single file analysis for focused inspection
   - Directory/codebase analysis for broader insights
   - Version comparison for understanding changes

3. **Choose Analysis Type**
   - AST (Abstract Syntax Tree): For syntax and structure
   - ASG (Abstract Semantic Graph): For deeper semantic understanding
   - Combined analysis for comprehensive insights

## Available Tools

### Basic Analysis Tools
- `analyze_file(file_path, analysis_type, include_metrics)`: Analyze a single file
  - **Parameters**:
    - `file_path`: Path to the file to analyze
    - `analysis_type`: \"ast\", \"asg\", or \"both\"
    - `include_metrics`: Boolean to include complexity metrics

- `analyze_codebase(directory_path, language, include_patterns, exclude_patterns, analysis_depth)`: Analyze entire codebase
  - **Parameters**:
    - `directory_path`: Root directory of the codebase
    - `language`: Optional language filter (e.g., \"python\", \"javascript\")
    - `include_patterns`: Optional file patterns to include (e.g., [\"*.py\", \"*.js\"])
    - `exclude_patterns`: Optional file patterns to exclude (e.g., [\"*_test.py\", \"node_modules/*\"])
    - `analysis_depth`: \"basic\", \"detailed\", or \"comprehensive\"

- `compare_versions(file_path, old_version, new_version, comparison_level)`: Compare code versions
  - **Parameters**:
    - `file_path`: Path to the file
    - `old_version`: Reference to older version
    - `new_version`: Reference to newer version
    - `comparison_level`: \"structural\", \"semantic\", or \"detailed\"

### Advanced Analysis Tools

- `find_code_smells(target, smell_categories, threshold)`: Identify code issues
  - **Parameters**:
    - `target`: File path or directory
    - `smell_categories`: Optional categories of issues to find
    - `threshold`: \"low\", \"medium\", or \"high\" sensitivity

- `generate_documentation(target, doc_format, include_diagrams, detail_level)`: Create docs from code
  - **Parameters**:
    - `target`: File or directory to document
    - `doc_format`: \"markdown\", \"html\", or \"text\"
    - `include_diagrams`: Boolean to include structure diagrams
    - `detail_level`: \"minimal\", \"standard\", or \"comprehensive\"

- `explore_code_structure(target, view_type, include_metrics)`: Visualize code structure
  - **Parameters**:
    - `target`: File or directory to explore
    - `view_type`: \"summary\", \"detailed\", \"hierarchy\", or \"dependencies\"
    - `include_metrics`: Boolean to include complexity metrics

- `search_code_constructs(query, search_type, scope, limit)`: Find specific patterns
  - **Parameters**:
    - `query`: Search pattern
    - `search_type`: \"pattern\", \"semantic\", or \"structure\"
    - `scope`: Optional path to limit search scope
    - `limit`: Maximum results to return

## Analysis Workflow

For structured code analysis, follow the `CODE_ANALYZE` action template:
```
get_action_template(keyword=\"CODE_ANALYZE\")
```

This template provides step-by-step guidance for conducting thorough code analysis and documenting the results.

## Understanding AST/ASG

- **Abstract Syntax Tree (AST)**: Represents the syntactic structure of code as a tree
  - Nodes represent language constructs (functions, classes, loops)
  - Shows code structure but not semantic meaning

- **Abstract Semantic Graph (ASG)**: Extends AST with semantic information
  - Includes type information and data flow analysis
  - Shows relationships between code elements (variable usage, function calls)

## Storage in Neo4j

Analysis results are stored in Neo4j with the following structure:

- `(:CodeFile)` - Represents source code files
- `(:Analysis)` - Represents analysis results
- `(:ASTNode)` - Represents nodes in the AST/ASG
- `[:HAS_ANALYSIS]` - Links files to analysis results
- `[:CONTAINS]` - Links analysis to AST nodes
- `[:HAS_CHILD]` - Links parent-child relationships in AST

## Best Practices

1. Start with high-level codebase analysis to get an overview
2. Follow up with detailed analysis of specific files or components
3. Use `find_code_smells()` to identify improvement opportunities
4. Document analysis results and recommendations
5. Tag analyses with version information for future comparison
        """

        params = {"description": description}

        async with self.driver.session(database=self.database) as session:
            await session.execute_write(lambda tx: tx.run(query, params))

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

        try:
            async with self.driver.session(database=self.database) as session:
                # Create file node
                success1, _ = await self._safe_execute_write(
                    session,
                    file_query,
                    {"path": file_path, "language": ast_processed["language"]}
                )

                # Create analysis node
                success2, _ = await self._safe_execute_write(
                    session,
                    analysis_query,
                    {
                        "id": analysis_id,
                        "path": file_path,
                        "nodeCount": ast_processed["node_count"],
                        "language": ast_processed["language"]
                    }
                )

                # Create AST nodes (in batches to avoid transaction size limits)
                nodes = ast_processed["nodes"]
                batch_size = 100

                for i in range(0, len(nodes), batch_size):
                    batch = nodes[i:i+batch_size]
                    batch_success, _ = await self._safe_execute_write(
                        session,
                        nodes_query,
                        {"nodes": batch, "analysisId": analysis_id}
                    )

                    if not batch_success:
                        logger.error(f"Failed to store batch of AST nodes")
                        return False, ""

                if success1 and success2:
                    return True, analysis_id
                else:
                    return False, ""

        except Exception as e:
            logger.error(f"Error storing AST in Neo4j: {e}")
            return False, ""

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

        Args:
            directory_path: Path to the directory containing the codebase
            language: Optional language filter (e.g., "python", "javascript")
            include_patterns: Optional list of file patterns to include (e.g., ["*.py", "*.js"])
            exclude_patterns: Optional list of file patterns to exclude (e.g., ["*_test.py", "node_modules/*"])
            analysis_depth: Level of analysis detail: "basic", "detailed", or "comprehensive"

        Returns:
            Summary of the analysis results
        """
        # This would be implemented using the actual AST tools
        # Here's a sketch of the implementation

        return [types.TextContent(type="text", text=f"""
# Codebase Analysis: Not Yet Implemented

This tool would analyze the codebase at:
- Directory: {directory_path}
- Language: {language or "All languages"}
- Include patterns: {include_patterns or "All files"}
- Exclude patterns: {exclude_patterns or "None"}
- Analysis depth: {analysis_depth}

Implementation would:
1. Recursively scan the directory for code files
2. For each file:
   - Parse to AST using `parse_to_ast` tool
   - Store AST structure in Neo4j
   - Run analysis on the AST structure
3. Generate aggregate metrics and insights
4. Provide a summary report

The analysis would be stored in Neo4j for future reference and exploration.
        """)]

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

        Args:
            file_path: Path to the code file to analyze
            version_tag: Optional tag to identify the version of the code
            analysis_type: Type of analysis to perform: "ast", "asg", or "both"
            include_metrics: Whether to include complexity metrics in the analysis

        Returns:
            Detailed analysis of the code file
        """
        try:
            # Read the file content
            try:
                with open(file_path, 'r') as f:
                    code_content = f.read()
            except Exception as e:
                return [types.TextContent(type="text", text=f"Error reading file: {e}")]
            
            # Determine language based on file extension
            ext = os.path.splitext(file_path)[1].lower()
            language_map = {
                '.py': 'python',
                '.js': 'javascript',
                '.jsx': 'javascript',
                '.ts': 'typescript',
                '.tsx': 'typescript',
                '.java': 'java',
                '.c': 'c',
                '.cpp': 'cpp',
                '.h': 'c',
                '.hpp': 'cpp',
                '.cs': 'csharp',
                '.go': 'go',
                '.rb': 'ruby',
                '.php': 'php',
                '.swift': 'swift',
                '.kt': 'kotlin',
                '.rs': 'rust'
            }
            language = language_map.get(ext)
            
            if not language:
                return [types.TextContent(type="text", text=f"Unsupported file extension: {ext}. Please specify language manually.")]
            
            # Store analysis results
            results = {}
            
            # Perform AST analysis
            if analysis_type in ["ast", "both"]:
                try:
                    # Use the existing parse_to_ast tool
                    from mcp.tools import invoke_tool
                    ast_result = await invoke_tool("parse_to_ast", {"code": code_content, "language": language})
                    
                    # Process and store AST data in Neo4j
                    processed_ast = await self._process_ast_data(ast_result)
                    success, analysis_id = await self._store_ast_in_neo4j(file_path, processed_ast)
                    
                    if success:
                        results["ast"] = {
                            "analysis_id": analysis_id,
                            "node_count": processed_ast["node_count"],
                            "root_type": processed_ast["root_node_type"]
                        }
                    else:
                        results["ast"] = {"error": "Failed to store AST in Neo4j"}
                except Exception as e:
                    results["ast"] = {"error": f"AST analysis failed: {str(e)}"}
            
            # Perform ASG analysis
            if analysis_type in ["asg", "both"]:
                try:
                    # Use the existing generate_asg tool
                    from mcp.tools import invoke_tool
                    asg_result = await invoke_tool("generate_asg", {"code": code_content, "language": language})
                    
                    # Store ASG data (similar processing as AST)
                    results["asg"] = {
                        "node_count": len(asg_result.get("nodes", [])),
                        "edge_count": len(asg_result.get("edges", []))
                    }
                except Exception as e:
                    results["asg"] = {"error": f"ASG analysis failed: {str(e)}"}
            
            # Include code metrics if requested
            if include_metrics:
                try:
                    # Use the existing analyze_code tool
                    from mcp.tools import invoke_tool
                    metrics_result = await invoke_tool("analyze_code", {"code": code_content, "language": language})
                    
                    # Extract and store metrics
                    results["metrics"] = {
                        "code_length": metrics_result.get("code_length", 0),
                        "function_count": len(metrics_result.get("functions", [])),
                        "class_count": len(metrics_result.get("classes", [])),
                        "complexity": metrics_result.get("complexity_metrics", {})
                    }
                except Exception as e:
                    results["metrics"] = {"error": f"Metrics analysis failed: {str(e)}"}
            
            # Generate summary report
            summary = f"""
# Code Analysis: {os.path.basename(file_path)}

## File Information
- **Path:** {file_path}
- **Language:** {language}
- **Size:** {len(code_content)} bytes
- **Version Tag:** {version_tag or "None"}

## Analysis Results
"""
            
            # Add AST section if performed
            if "ast" in results:
                ast_data = results["ast"]
                if "error" in ast_data:
                    summary += f"""
### Abstract Syntax Tree (AST) Analysis
- **Status:** Failed
- **Error:** {ast_data["error"]}
"""
                else:
                    summary += f"""
### Abstract Syntax Tree (AST) Analysis
- **Status:** Success
- **Analysis ID:** {ast_data["analysis_id"]}
- **Node Count:** {ast_data["node_count"]}
- **Root Node Type:** {ast_data["root_type"]}
"""
            
            # Add ASG section if performed
            if "asg" in results:
                asg_data = results["asg"]
                if "error" in asg_data:
                    summary += f"""
### Abstract Semantic Graph (ASG) Analysis
- **Status:** Failed
- **Error:** {asg_data["error"]}
"""
                else:
                    summary += f"""
### Abstract Semantic Graph (ASG) Analysis
- **Status:** Success
- **Node Count:** {asg_data["node_count"]}
- **Edge Count:** {asg_data["edge_count"]}
"""
            
            # Add metrics section if performed
            if "metrics" in results:
                metrics_data = results["metrics"]
                if "error" in metrics_data:
                    summary += f"""
### Code Metrics
- **Status:** Failed
- **Error:** {metrics_data["error"]}
"""
                else:
                    complexity = metrics_data.get("complexity", {})
                    summary += f"""
### Code Metrics
- **Status:** Success
- **Code Length:** {metrics_data["code_length"]} bytes
- **Function Count:** {metrics_data["function_count"]}
- **Class Count:** {metrics_data["class_count"]}
- **Max Nesting Level:** {complexity.get("max_nesting_level", "N/A")}
- **Total Nodes:** {complexity.get("total_nodes", "N/A")}
"""
            
            # Add storage information
            summary += """
## Storage Information
The analysis results have been stored in Neo4j and can be explored using:
- `explore_code_structure(target="{file_path}")` - To visualize the code structure
- `find_code_smells(target="{file_path}")` - To identify potential issues
"""
            
            return [types.TextContent(type="text", text=summary)]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error analyzing file: {str(e)}")]

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

        Args:
            file_path: Path to the code file
            old_version: Tag or identifier for the old version
            new_version: Tag or identifier for the new version
            comparison_level: Level of comparison detail

        Returns:
            Detailed comparison between the two code versions
        """
        # This would be implemented using the actual AST diff tools
        # Here's a sketch of the implementation

        return [types.TextContent(type="text", text=f"""
# Version Comparison: Not Yet Implemented

This tool would compare versions of:
- File: {file_path}
- Old version: {old_version}
- New version: {new_version}
- Comparison level: {comparison_level}

Implementation would:
1. Retrieve both versions' AST/ASG data from Neo4j
2. If not available, parse them using the AST tools
3. Compute differences using the AST diff tool
4. Categorize changes (additions, deletions, modifications)
5. Generate a structured report of the differences
6. Store the comparison results in Neo4j

The comparison would highlight structural and semantic changes between versions.
        """)]

    async def find_code_smells(
        self,
        target: str,  # Either a file path or analysis ID
        smell_categories: Optional[List[str]] = None,  # Categories of code smells to look for
        threshold: str = "medium"  # Options: "low", "medium", "high"
    ) -> List[types.TextContent]:
        """Identify potential code issues and suggestions.

        This tool analyzes code to find potential issues ("code smells") like overly complex methods,
        duplicate code, unused variables, and other patterns that might indicate problems.

        Args:
            target: File path or analysis ID to analyze
            smell_categories: Optional list of smell categories to look for
            threshold: Threshold for reporting issues

        Returns:
            List of identified code smells with suggestions for improvement
        """
        try:
            # Check if target is a file path or analysis ID
            is_file = os.path.exists(target)
            
            # If it's a file path, analyze it first
            if is_file:
                # Read the file content
                try:
                    with open(target, 'r') as f:
                        code_content = f.read()
                except Exception as e:
                    return [types.TextContent(type="text", text=f"Error reading file: {e}")]
                
                # Determine language based on file extension
                ext = os.path.splitext(target)[1].lower()
                language_map = {
                    '.py': 'python',
                    '.js': 'javascript',
                    '.jsx': 'javascript',
                    '.ts': 'typescript',
                    '.tsx': 'typescript',
                    '.java': 'java',
                    '.c': 'c',
                    '.cpp': 'cpp',
                    '.h': 'c',
                    '.hpp': 'cpp',
                    '.cs': 'csharp',
                    '.go': 'go',
                    '.rb': 'ruby',
                    '.php': 'php',
                    '.swift': 'swift',
                    '.kt': 'kotlin',
                    '.rs': 'rust'
                }
                language = language_map.get(ext)
                
                if not language:
                    return [types.TextContent(type="text", text=f"Unsupported file extension: {ext}. Please specify language manually.")]
                
                # Use existing AST and code analysis tools
                from mcp.tools import invoke_tool
                
                # Get AST data
                ast_result = await invoke_tool("parse_to_ast", {"code": code_content, "language": language})
                
                # Get code metrics
                metrics_result = await invoke_tool("analyze_code", {"code": code_content, "language": language})
                
                # Get ASG data for more context
                asg_result = await invoke_tool("generate_asg", {"code": code_content, "language": language})
            else:
                # Try to retrieve analysis from Neo4j using the ID
                async with self.driver.session(database=self.database) as session:
                    query = """
                    MATCH (a:Analysis {id: $id})
                    OPTIONAL MATCH (f:CodeFile)-[:HAS_ANALYSIS]->(a)
                    RETURN a, f.language as language, f.path as file_path
                    """
                    result = await self._safe_read_query(session, query, {"id": target})
                    
                    if not result or len(result) == 0:
                        return [types.TextContent(type="text", text=f"No analysis found with ID: {target}")]
                    
                    # We have the analysis, but we'll still need to get the code content for accurate analysis
                    analysis = result[0]
                    language = analysis.get("language", "unknown")
                    file_path = analysis.get("file_path")
                    
                    if not file_path or not os.path.exists(file_path):
                        return [types.TextContent(type="text", text=f"Cannot find original file for analysis: {target}")]
                    
                    # Read the file content
                    try:
                        with open(file_path, 'r') as f:
                            code_content = f.read()
                    except Exception as e:
                        return [types.TextContent(type="text", text=f"Error reading file: {e}")]
                    
                    # Use existing tools for fresh analysis
                    from mcp.tools import invoke_tool
                    
                    # Get AST data
                    ast_result = await invoke_tool("parse_to_ast", {"code": code_content, "language": language})
                    
                    # Get code metrics
                    metrics_result = await invoke_tool("analyze_code", {"code": code_content, "language": language})
                    
                    # Get ASG data for more context
                    asg_result = await invoke_tool("generate_asg", {"code": code_content, "language": language})
            
            # Define code smell detection functions
            def detect_complex_functions(ast_data, metrics_data, threshold_level):
                """Detect overly complex functions based on nesting and complexity."""
                smells = []
                threshold_map = {"low": 3, "medium": 5, "high": 8}
                complexity_threshold = threshold_map.get(threshold_level, 5)
                
                functions = metrics_data.get("functions", [])
                for func in functions:
                    # Use metrics data to detect complexity
                    func_name = func.get("name", "unknown")
                    location = func.get("location", {})
                    start_line = location.get("start_line", 0)
                    end_line = location.get("end_line", 0)
                    line_count = end_line - start_line + 1
                    
                    # Check for overly long functions
                    if line_count > complexity_threshold * 5:
                        smells.append({
                            "type": "long_function",
                            "name": func_name,
                            "location": location,
                            "severity": "medium" if line_count > complexity_threshold * 10 else "low",
                            "description": f"Function '{func_name}' is {line_count} lines long, which may indicate it's doing too much.",
                            "suggestion": "Consider breaking it down into smaller, focused functions."
                        })
                
                return smells
            
            def detect_unused_imports(ast_data, language):
                """Detect unused imports in the code."""
                smells = []
                
                # This is a simplified implementation; a real one would trace usage through the AST
                if language == "python":
                    # Find all import nodes and declared identifiers
                    imported_modules = []
                    imported_names = []
                    
                    # Extract imports from AST
                    for node in ast_data.get("ast", {}).get("children", []):
                        if node.get("type") in ["import_statement", "import_from_statement"]:
                            for child in node.get("children", []):
                                if child.get("type") == "dotted_name":
                                    module_name = child.get("text", "")
                                    if module_name:
                                        imported_modules.append(module_name)
                                        imported_names.append(module_name)
                    
                    # Simple check: if 'logging' is imported but not used
                    if "logging" in imported_modules and "logging" not in code_content[100:]:
                        smells.append({
                            "type": "unused_import",
                            "name": "logging",
                            "severity": "low",
                            "description": "The 'logging' module appears to be imported but not used.",
                            "suggestion": "Remove unused imports to improve code clarity and execution time."
                        })
                
                return smells
            
            def detect_magic_numbers(ast_data):
                """Detect magic numbers in the code."""
                smells = []
                
                # Find all integer literals outside of variable declarations
                for node_id, node in ast_data.items():
                    if node.get("type") == "integer" and node.get("text") not in ["0", "1", "-1"]:
                        # Check if within variable declaration
                        in_declaration = False
                        # Simple heuristic - in a real implementation we'd traverse the AST properly
                        
                        if not in_declaration:
                            smells.append({
                                "type": "magic_number",
                                "value": node.get("text", ""),
                                "location": {"start_line": node.get("start_line", 0), "start_col": node.get("start_col", 0)},
                                "severity": "low",
                                "description": f"Magic number {node.get('text', '')} found in code.",
                                "suggestion": "Consider replacing with a named constant for better readability."
                            })
                
                return smells
            
            # Collect all detected code smells
            all_smells = []
            
            # Apply appropriate detectors based on requested categories
            if not smell_categories or "complexity" in smell_categories:
                all_smells.extend(detect_complex_functions(ast_result, metrics_result, threshold))
            
            if not smell_categories or "unused" in smell_categories:
                all_smells.extend(detect_unused_imports(ast_result, language))
            
            if not smell_categories or "magic_numbers" in smell_categories:
                all_smells.extend(detect_magic_numbers(ast_result))
            
            # Filter smells based on threshold
            threshold_levels = {"low": 0, "medium": 1, "high": 2}
            severity_levels = {"low": 0, "medium": 1, "high": 2}
            threshold_value = threshold_levels.get(threshold, 1)
            
            filtered_smells = [
                smell for smell in all_smells 
                if severity_levels.get(smell.get("severity", "medium"), 1) >= threshold_value
            ]
            
            # Generate report
            report = f"""
# Code Smell Analysis

## Analysis Parameters
- **Target:** {target}
- **Categories:** {smell_categories or "All categories"}
- **Threshold:** {threshold}

## Summary
- **Total smells detected:** {len(all_smells)}
- **Smells meeting threshold:** {len(filtered_smells)}
- **File analyzed:** {os.path.basename(target) if is_file else "From analysis ID"}
- **Language:** {language}

## Detected Issues
"""
            
            if filtered_smells:
                for i, smell in enumerate(filtered_smells, 1):
                    report += f"""
### {i}. {smell.get('type', 'Unknown').replace('_', ' ').title()} - {smell.get('severity', 'medium').title()} Severity

**Description:** {smell.get('description', 'No description available.')}

**Location:** {smell.get('location', 'Unknown location')}

**Suggestion:** {smell.get('suggestion', 'No suggestion available.')}

"""
            else:
                report += """
No code smells meeting the specified threshold were detected!

This could mean:
- The code is well-written and maintained
- The threshold is set too high for the kinds of issues present
- The specific categories of smells are not present
"""
            
            report += """
## Next Steps

1. Review each identified issue and determine its impact
2. Prioritize fixes based on severity and importance
3. Consider using `compare_versions()` after making changes to verify improvements
4. Use `generate_documentation()` to document any complex sections properly
"""
            
            return [types.TextContent(type="text", text=report)]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error analyzing code smells: {str(e)}")]

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

        Args:
            target: File, directory, or analysis ID to document
            doc_format: Format for the generated documentation
            include_diagrams: Whether to include structure diagrams
            detail_level: Level of detail in the documentation

        Returns:
            Generated documentation in the specified format
        """
        # This would be implemented using the AST analysis tools
        # Here's a sketch of the implementation

        return [types.TextContent(type="text", text=f"""
# Documentation Generator: Not Yet Implemented

This tool would generate documentation for:
- Target: {target}
- Format: {doc_format}
- Include diagrams: {include_diagrams}
- Detail level: {detail_level}

Implementation would:
1. Retrieve or generate AST/ASG data for the target
2. Extract key structures:
   - Modules/namespaces
   - Classes and their relationships
   - Functions/methods and their signatures
   - Constants and variables
3. Generate documentation in the requested format
4. Include structure diagrams if requested
5. Store the documentation in Neo4j linked to the analysis

The documentation would include properly formatted descriptions of code elements.
        """)]

    async def explore_code_structure(
        self,
        target: str,  # Either a file path, directory path, or analysis ID
        view_type: str = "summary",  # Options: "summary", "detailed", "hierarchy", "dependencies"
        include_metrics: bool = True
    ) -> List[types.TextContent]:
        """Explore the structure of a codebase.

        This tool provides visualizations and reports on the structure of code, showing
        hierarchies, dependencies, and relationships between components.

        Args:
            target: File, directory, or analysis ID to explore
            view_type: Type of structure view to generate
            include_metrics: Whether to include complexity metrics

        Returns:
            Structured report on the code organization
        """
        # This would be implemented using the AST analysis tools and Neo4j queries
        # Here's a sketch of the implementation

        return [types.TextContent(type="text", text=f"""
# Code Structure Explorer: Not Yet Implemented

This tool would explore code structure in:
- Target: {target}
- View type: {view_type}
- Include metrics: {include_metrics}

Implementation would:
1. Retrieve structure information from Neo4j or generate it
2. Generate the requested view:
   - Summary: High-level overview of components
   - Detailed: In-depth breakdown of all elements
   - Hierarchy: Parent-child relationships
   - Dependencies: Import/usage relationships
3. Calculate and include metrics if requested
4. Format the results for easy comprehension

For a real implementation, this would query the Neo4j database for structure information
stored from previous analyses and present it in a structured format.
        """)]

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

        Args:
            query: Search query string
            search_type: Type of search to perform
            scope: Optional scope to restrict the search
            limit: Maximum number of results to return

        Returns:
            Search results matching the query
        """
        # This would be implemented using Neo4j queries on the stored AST data
        # Here's a sketch of the implementation

        return [types.TextContent(type="text", text=f"""
# Code Construct Search: Not Yet Implemented

This tool would search for code constructs:
- Query: {query}
- Search type: {search_type}
- Scope: {scope or "All analyzed code"}
- Limit: {limit} results

Implementation would:
1. Convert the query to the appropriate search format:
   - Pattern: Regular expression or text search
   - Semantic: Concept or meaning-based search
   - Structure: AST/ASG pattern matching
2. Execute the search against stored code analyses in Neo4j
3. Rank and filter results
4. Format results with context and location information

For a real implementation, this would use Neo4j's query capabilities to search
through stored AST/ASG structures and return matching code elements.
        """)]
