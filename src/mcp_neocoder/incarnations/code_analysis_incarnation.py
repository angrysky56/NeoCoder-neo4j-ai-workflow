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

from .base_incarnation import BaseIncarnation, IncarnationType

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
    
    # Define the incarnation type - must match an entry in IncarnationType enum
    incarnation_type = IncarnationType.CODE_ANALYSIS
    
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
# Code Analysis with AST/ASG

Welcome to the Code Analysis System powered by the NeoCoder framework. This system helps you analyze and understand codebases using Abstract Syntax Trees (AST) and Abstract Semantic Graphs (ASG).

## Key Features

1. **Code Parsing and Analysis**
   - Parse code files into Abstract Syntax Trees
   - Generate Abstract Semantic Graphs for deeper code understanding
   - Analyze code structure, complexity, and patterns

2. **Codebase Exploration**
   - Store and explore code structures in a Neo4j graph
   - Track code changes and evolution over time
   - Compare different versions of code

3. **Code Quality Tools**
   - Identify code smells and potential issues
   - Analyze code complexity metrics
   - Generate documentation from code

## Available Tools

### Basic Analysis
- `analyze_codebase()`: Analyze an entire codebase or directory
- `analyze_file()`: Analyze a single code file in depth
- `compare_versions()`: Compare different versions of the same code

### Advanced Features
- `find_code_smells()`: Identify potential code issues and suggestions
- `generate_documentation()`: Generate documentation from code analysis
- `explore_code_structure()`: Explore the structure of a codebase
- `search_code_constructs()`: Search for specific code constructs

## Getting Started

1. Use `analyze_codebase()` to begin analysis of a project
2. Explore results with `explore_code_structure()`
3. Identify issues with `find_code_smells()`
4. Generate documentation with `generate_documentation()`

Each analysis is stored in the Neo4j graph for future reference and comparison.
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
# Code Analysis with AST/ASG

Welcome to the Code Analysis System powered by the NeoCoder framework. This system helps you analyze and understand codebases using Abstract Syntax Trees (AST) and Abstract Semantic Graphs (ASG).

## Key Features

1. **Code Parsing and Analysis**
   - Parse code files into Abstract Syntax Trees
   - Generate Abstract Semantic Graphs for deeper code understanding
   - Analyze code structure, complexity, and patterns

2. **Codebase Exploration**
   - Store and explore code structures in a Neo4j graph
   - Track code changes and evolution over time
   - Compare different versions of code

3. **Code Quality Tools**
   - Identify code smells and potential issues
   - Analyze code complexity metrics
   - Generate documentation from code

## Available Tools

### Basic Analysis
- `analyze_codebase()`: Analyze an entire codebase or directory
- `analyze_file()`: Analyze a single code file in depth
- `compare_versions()`: Compare different versions of the same code

### Advanced Features
- `find_code_smells()`: Identify potential code issues and suggestions
- `generate_documentation()`: Generate documentation from code analysis
- `explore_code_structure()`: Explore the structure of a codebase
- `search_code_constructs()`: Search for specific code constructs

## Getting Started

1. Use `analyze_codebase()` to begin analysis of a project
2. Explore results with `explore_code_structure()`
3. Identify issues with `find_code_smells()`
4. Generate documentation with `generate_documentation()`

Each analysis is stored in the Neo4j graph for future reference and comparison.
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
        # This would be implemented using the actual AST tools
        # Here's a sketch of the implementation
        
        return [types.TextContent(type="text", text=f"""
# File Analysis: Not Yet Implemented

This tool would analyze the code file:
- File: {file_path}
- Version tag: {version_tag or "None"}
- Analysis type: {analysis_type}
- Include metrics: {include_metrics}

Implementation would:
1. Read the file content
2. Determine the language based on file extension or content
3. Parse the code using the appropriate AST/ASG tool
4. Store the structure in Neo4j
5. Calculate metrics (if requested)
6. Generate a detailed report

The analysis would be stored in Neo4j with the specified version tag for future reference.
        """)]
    
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
        # This would be implemented using the AST analysis tools
        # Here's a sketch of the implementation
        
        return [types.TextContent(type="text", text=f"""
# Code Smell Analysis: Not Yet Implemented

This tool would analyze code smells in:
- Target: {target}
- Smell categories: {smell_categories or "All categories"}
- Threshold: {threshold}

Implementation would:
1. Retrieve or generate AST/ASG data for the target
2. Apply code smell detection algorithms:
   - Complexity analysis
   - Duplicate code detection
   - Dead code identification
   - Anti-pattern recognition
3. Filter results based on the threshold
4. Generate a report with suggested improvements
5. Store findings in Neo4j linked to the analysis

The report would prioritize issues and provide specific refactoring suggestions.
        """)]
    
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
