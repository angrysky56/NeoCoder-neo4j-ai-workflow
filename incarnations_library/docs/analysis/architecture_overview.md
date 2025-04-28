# NeoCoder Architecture Overview

## System Architecture

NeoCoder implements a three-tier architecture that separates concerns and enables flexibility:

1. **Neo4j Knowledge Graph Layer**
   - Serves as the "brain" of the system
   - Stores templates, workflows, project information, and execution history
   - Provides a queryable graph structure that AI assistants can traverse

2. **MCP Server Layer**
   - Implements the Model Context Protocol (MCP) server interface
   - Provides tools for AI assistants to interact with Neo4j and the file system
   - Manages incarnations and dynamically loads specialized functionality
   - Handles event loops and manages asynchronous operations

3. **AI Assistant Layer**
   - Claude or other AI assistants interact with the MCP server
   - Follows instructions stored in the Neo4j graph
   - Executes workflows and records results back to the graph

## Key Components

### Neo4j Schema

The Neo4j database schema includes these key node types:

1. **:AiGuidanceHub** - Central navigation hubs for AI assistants
2. **:ActionTemplate** - Templates for standard workflows (FIX, REFACTOR, etc.)
3. **:Project** - Project data including README and structure
4. **:File/Directory** - Project file structure representation
5. **:WorkflowExecution** - Audit trail of completed workflows
6. **:BestPracticesGuide** - Coding standards and guidelines
7. **:CypherSnippet** - Reusable Cypher query patterns

### MCP Server Components

1. **server.py** - Main server implementation that handles MCP protocol
2. **incarnation_registry.py** - Registry for tracking available incarnations
3. **tool_registry.py** - Registry for tracking available tools
4. **incarnations/** - Directory of specialized incarnation implementations
5. **decorators.py** - Utility decorators for tool methods
6. **action_templates.py** - Functionality for managing action templates
7. **cypher_snippets.py** - Functionality for managing Cypher snippets
8. **init_db.py** - Database initialization and setup

### Incarnation System

The incarnation system is a core architectural feature that allows the NeoCoder platform to adapt for different use cases:

1. **BaseIncarnation** - Base class for all incarnations
2. **Specialized Incarnations**:
   - **base_incarnation.py** - Original NeoCoder coding workflow
   - **research_incarnation.py** - Scientific research platform
   - **decision_incarnation.py** - Decision analysis system
   - **data_analysis_incarnation.py** - Data analysis tools
   - **knowledge_graph_incarnation.py** - Knowledge graph management
   - **code_analysis_incarnation.py** - Code analysis with AST/ASG support

Each incarnation provides specialized tools that are automatically registered with the MCP server, allowing them to be used by AI assistants.

## Communication Flow

1. AI assistant receives a prompt containing guidance to consult the Neo4j graph
2. AI formulates Cypher queries to find relevant templates and guides
3. MCP server executes these queries against the Neo4j database
4. Results are returned to the AI assistant
5. AI follows the template instructions, using file system tools as needed
6. AI performs verification steps as specified in the template
7. Results are recorded back to the Neo4j graph

## Implementation Details

### Asynchronous Architecture

The MCP server uses Python's asyncio for asynchronous operation:

- `event_loop_manager.py` manages the async event loop
- Neo4j interactions use the asynchronous Neo4j driver
- Tool methods are implemented as async coroutines

### Dynamic Tool Discovery

The system uses reflection and introspection to discover and register tools:

- `list_tool_methods()` finds tool methods in incarnation classes
- `register_tools()` registers these methods with the MCP server
- Tools can be explicitly declared via the `_tool_methods` class attribute

### Incarnation Management

The system dynamically loads incarnations:

- Incarnations are discovered by file naming pattern (`*_incarnation.py`)
- Each incarnation declares its type using the `IncarnationType` enum
- Incarnations can be switched at runtime using the `switch_incarnation()` tool

### Schema Management

Each incarnation can define its own Neo4j schema:

- Schema queries are defined in the `schema_queries` class attribute
- `initialize_schema()` method executes these queries
- Each incarnation has its own guidance hub in the Neo4j database

## Extension Points

NeoCoder is designed for extension at multiple levels:

1. **New Incarnations** - Create new specialized versions of the system
2. **Additional Tools** - Add new tools to existing incarnations
3. **Custom Templates** - Define new workflow templates
4. **Schema Extensions** - Extend the Neo4j schema for new node types
5. **Integration with Other Systems** - Connect with external tools and services

The modular architecture allows for extending the system while maintaining the core workflow pattern of template-guided AI assistance.
