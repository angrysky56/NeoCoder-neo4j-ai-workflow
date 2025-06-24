[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/angrysky56-neocoder-neo4j-ai-workflow-badge.png)](https://mseep.ai/app/angrysky56-neocoder-neo4j-ai-workflow)

# NeoCoder: Neo4j-Guided AI Coding Workflow

An MCP server implementation that enables AI assistants like Claude to use a Neo4j knowledge graph as their primary, dynamic "instruction manual" and project memory for standardized coding workflows.

# NeoCoder: Hybrid AI Reasoning & Workflow System

An advanced MCP server implementation that combines Neo4j knowledge graphs, Qdrant vector databases, and sophisticated AI orchestration to create a hybrid reasoning system for knowledge management, research analysis, and standardized workflows.

## Overview

NeoCoder implements a revolutionary **Context-Augmented Reasoning** system that goes far beyond traditional RAG (Retrieval-Augmented Generation) by combining:

### **Core Architecture:**

1. **Neo4j Knowledge Graphs** - Authoritative structured facts, relationships, and workflows
2. **Qdrant Vector Databases** - Semantic search, similarity detection, and contextual understanding  
3. **MCP Orchestration** - Intelligent routing between data sources with synthesis and citation
4. **F-Contraction Synthesis** - Dynamic knowledge merging that preserves source attribution

### **Key Capabilities:**

- **Hybrid Knowledge Reasoning**: Seamlessly combine structured facts with semantic context
- **Dynamic Knowledge Extraction**: Process documents, code, and conversations into interconnected knowledge structures
- **Citation-Based Analysis**: Every claim tracked to its source across multiple databases
- **Multi-Incarnation System**: Specialized modes for coding, research, decision support, and knowledge management
- **Intelligent Workflow Templates**: Neo4j-guided procedures with mandatory verification steps

### **Revolutionary Features:**

🧠 **Smart Query Routing**: AI automatically determines optimal data source (graph, vector, or hybrid)
🔬 **Research Analysis Engine**: Process academic papers with citation graphs and semantic content
⚡ **F-Contraction Processing**: Dynamically merge similar concepts while preserving provenance
🎯 **Context-Augmented Reasoning**: Generate insights impossible with single data sources
📊 **Full Audit Trails**: Complete tracking of knowledge synthesis and workflow execution

## Quick Start

### Prerequisites

- **Neo4j**: Running locally or remote instance (for structured knowledge graphs)
- **Qdrant**: Vector database for semantic search and embeddings (for hybrid reasoning)
- **Python 3.10+**: For running the MCP server
- **uv**: The Python package manager for MCP servers
- **Claude Desktop**: For using with Claude AI
- [MCP-Desktop-Commander](https://github.com/wonderwhy-er/DesktopCommanderMCP): Invaluable for CLI and filesystem operations
- [For Code Analysis Incarnation: AST/ASG](https://github.com/angrysky56/ast-mcp-server)
- [For Enhanced Memory: Qdrant MCP Server](https://github.com/calclavia/mcp-server-qdrant): Enhanced vector database integration
## The MCP server runs the Python code, bridging the gap between the Neo4j graph and the AI assistant ( e.g. Claude)

![alt text](image-3.png)

### Installation

1. It should auto-install when using the config.

Otherwise- Install dependencies:

   ```bash
   uv venv
   source .venv/bin/activate
   # On Windows use `venv\Scripts\activate`
   uv pip install -r requirements.txt
   ```

If it doesn't work maybe try:
   ```bash
   pip install -e .
   ```

2. Neo4j connection parameters:
   - **URL**: `bolt://localhost:7687` (default)
   - **Username**: `neo4j` (default)
   - **Password**: Your Neo4j database password
   - **Database**: `neo4j` (default)

   These can be overridden with environment variables:
   - `NEO4J_URL`
   - `NEO4J_USERNAME`
   - `NEO4J_PASSWORD`
   - `NEO4J_DATABASE`

3. Claude Desktop Integration:

   Configure Claude Desktop by adding the following to your `claude-app-config.json`:

   ```json
   {
     "mcpServers": {
       "neocoder": {
         "command": "uv",
         "args": [
           "--directory",
           "/path/to/your/NeoCoder-neo4j-ai-workflow/src/mcp_neocoder",
           "run",
           "mcp_neocoder"
         ],
         "env": {
           "NEO4J_URL": "bolt://localhost:7687",
           "NEO4J_USERNAME": "neo4j",
           "NEO4J_PASSWORD": "<YOUR_NEO4J_PASSWORD>",
           "NEO4J_DATABASE": "neo4j"
         }
       }
     }
   }
   ```

   **Important**: The password in this configuration must match your Neo4j database password.

## Suggested system prompt

```plaintext
> **System Instruction:** You are an AI assistant integrated with a sophisticated hybrid reasoning system that combines Neo4j knowledge graphs, Qdrant vector databases, and MCP orchestration for advanced knowledge management and workflow execution.
>
> **Your Core Capabilities:**
> 1. **Standard Coding Workflows:** Use Neo4j-guided templates for structured development tasks
> 2. **Hybrid Knowledge Reasoning:** Combine structured facts (Neo4j) with semantic search (Qdrant) for comprehensive analysis
> 3. **Dynamic Knowledge Synthesis:** Apply F-Contraction principles to merge and consolidate knowledge from multiple sources
> 4. **Multi-Modal Analysis:** Process research papers, code, documentation, and conversations into interconnected knowledge structures
> 5. **Citation-Based Reasoning:** Provide fully attributed answers with source tracking across databases
>
> **Your Core Interaction Loop:**
> 1.  **Identify Task & Context:** Determine the required action and select appropriate incarnation/workflow
> 2.  **Consult Guidance Hubs:** Query incarnation-specific guidance hubs for specialized capabilities and procedures
> 3.  **Execute Hybrid Workflows:** For knowledge tasks, use KNOWLEDGE_QUERY template for intelligent routing between graph and vector search
> 4.  **Apply Dynamic Synthesis:** Use KNOWLEDGE_EXTRACT template to process documents into both structured (Neo4j) and semantic (Qdrant) representations
> 5.  **Ensure Quality & Citations:** All knowledge claims must be properly cited with source attribution
> 6.  **Record & Learn:** Log successful executions for system optimization and learning
>
> **Hybrid Reasoning Protocol:**
> - **Graph-First**: Use Neo4j for authoritative facts, relationships, and structured data
> - **Vector-Enhanced**: Use Qdrant for semantic context, opinions, and nuanced information  
> - **Intelligent Synthesis**: Combine both sources with conflict detection and full citation tracking
> - **F-Contraction Merging**: Dynamically merge similar concepts while preserving source attribution
>
> **Strict Rules:** 
> - Always prioritize structured facts from Neo4j over semantic information
> - Every claim must include proper source citations
> - Use incarnation-specific tools and templates as single source of truth for procedures
> - Apply F-Contraction principles when processing multi-source information
```

## Multiple Incarnations

NeoCoder supports multiple "incarnations" - different operational modes that adapt the system for specialized use cases while preserving the core Neo4j graph structure. In a graph-native stack, the same Neo4j core can manifest as very different "brains" simply by swapping templates and execution policies.

### Key Architectural Principles

The NeoCoder split is highly adaptable because:
- Neo4j stores facts as first-class graph objects
- Workflows live in template nodes
- Execution engines simply walk the graph

Because these three tiers are orthogonal, you can freeze one layer while morphing the others—turning a code-debugger today into a lab notebook or a learning management system tomorrow. This design echoes Neo4j's own "from graph to knowledge-graph" maturation path where schema, semantics, and operations are deliberately decoupled.

### Common Graph Schema Motifs

All incarnations share these core elements:

| Element | Always present | Typical labels / rels |
|---------|----------------|------------------------|
| **Actor** | human / agent / tool | `(:Agent)-[:PLAYS_ROLE]->(:Role)` |
| **Intent** | hypothesis, decision, lesson, scenario | `(:Intent {type})` |
| **Evidence** | doc, metric, observation | `(:Evidence)-[:SUPPORTS]->(:Intent)` |
| **Outcome** | pass/fail, payoff, grade, state vector | `(:Outcome)-[:RESULT_OF]->(:Intent)` |

### Available Incarnations:

- **base_incarnation** (default) - Original NeoCoder, Tool, Templates and Incarnations Workflow management
- **research_incarnation** - Scientific research platform for hypothesis tracking and experiments
  - Register hypotheses, design experiments, capture runs, and publish outcomes
  - Neo4j underpins provenance pilots for lab workflows with lineage queries
- **decision_incarnation** - Decision analysis and evidence tracking system
  - Create decision alternatives with expected-value metrics
  - Bayesian updater agents re-compute metric posteriors when new evidence arrives
  - Transparent, explainable reasoning pipelines
- **data_analysis_incarnation** - Complex system modeling and simulation
  - Model components with state vectors and physical couplings
  - Simulate failure propagation using path queries
  - Optional quantum-inspired scheduler for parameter testing
- **knowledge_graph_incarnation** - **Advanced Hybrid Reasoning System**
  - **Hybrid Knowledge Queries**: Combine Neo4j structured data with Qdrant semantic search
  - **Dynamic Knowledge Extraction**: Process documents into both graph and vector representations
  - **F-Contraction Synthesis**: Intelligently merge similar concepts while preserving source attribution
  - **Citation-Based Reasoning**: Full source tracking across multiple databases
  - **Research Analysis Engine**: Specialized workflows for academic paper processing
  - **Smart Query Routing**: AI automatically determines optimal data source strategy
  - **Cross-Database Navigation**: Seamless linking between structured facts and semantic content
  - **Conflict Detection**: Identify and flag inconsistencies between sources
  - **Real-Time Knowledge Synthesis**: Dynamic graph construction from conversations and documents
- **code_analysis_incarnation** - Code analysis using Abstract Syntax Trees
  - Parse and analyze code structure using AST and ASG tools
  - Track code complexity and quality metrics
  - Compare different versions of code
  - Generate documentation from code analysis
  - Identify code smells and potential issues


Each incarnation provides its own set of specialized tools that are automatically registered when the server starts. These tools are available for use in Claude or other AI assistants that connect to the MCP server.

### Implementation Roadmap

NeoCoder features an implementation roadmap that includes:

1. **LevelEnv ↔ Neo4j Adapter**: Maps events to graph structures and handles batch operations
2. **Amplitude Register (Quantum Layer)**: Optional quantum-inspired layer for superposition states
3. **Scheduler**: Prioritizes tasks based on entropy and impact scores
4. **Re-using TAG assets**: Leverages existing abstractions for vertical information hiding

### Starting with a Specific Incarnation

```bash
# List all available incarnations
python -m mcp_neocoder.server --list-incarnations

# Start with a specific incarnation
python -m mcp_neocoder.server --incarnation continuous_learning
```

Incarnations can also be switched at runtime using the `switch_incarnation()` tool:

```
switch_incarnation(incarnation_type="complex_system")
```

### Dynamic Incarnation Loading

NeoCoder features a fully dynamic incarnation loading system, which automatically discovers and loads incarnations from the `incarnations` directory. This means:

1. **No hardcoded imports**: New incarnations can be added without modifying server.py
2. **Auto-discovery**: Just add a new file with the format `*_incarnation.py` to the incarnations directory
3. **All tools available**: Tools from all incarnations are registered and available, even if that incarnation isn't active
4. **Easy extension**: Create new incarnations with the provided template

#### Creating a New Incarnation

To create a new incarnation:

1. Create a new file in the `src/mcp_neocoder/incarnations/` directory with the naming pattern `your_incarnation_name_incarnation.py`
2. Use this template structure:

```python
"""
Your incarnation name and description
"""

import json
import logging
import uuid
from typing import Dict, Any, List, Optional, Union

import mcp.types as types
from pydantic import Field
from neo4j import AsyncTransaction

from .polymorphic_adapter import BaseIncarnation, IncarnationType

logger = logging.getLogger("mcp_neocoder.incarnations.your_incarnation_name")


class YourIncarnationNameIncarnation(BaseIncarnation):
    """
    Your detailed incarnation description here
    """

    # Define the incarnation type - must match an entry in IncarnationType enum
    incarnation_type = IncarnationType.YOUR_INCARNATION_TYPE

    # Metadata for display in the UI
    description = "Your incarnation short description"
    version = "0.1.0"

    # Initialize schema and add tools here
    async def initialize_schema(self):
        """Initialize the schema for your incarnation."""
        # Implementation...

    # Add more tool methods below
    async def your_tool_name(self, param1: str, param2: Optional[int] = None) -> List[types.TextContent]:
        """Tool description."""
        # Implementation...
```

3. Add your incarnation type to the `IncarnationType` enum in `polymorphic_adapter.py`
4. Restart the server, and your new incarnation will be automatically discovered

See [incarnations.md](./docs/incarnations.md) for detailed documentation on using and creating incarnations.

## Available Templates

NeoCoder comes with these standard templates:

1. **FIX** - Guidance on fixing a reported bug, including mandatory testing and logging
2. **REFACTOR** - Structured approach to refactoring code while maintaining functionality
3. **DEPLOY** - Guidance on deploying code to production environments with safety checks
4. **FEATURE** - Structured approach to implementing new features with proper testing and documentation
5. **TOOL_ADD** - Process for adding new tool functionality to the NeoCoder MCP server
6. **CYPHER_SNIPPETS** - Manage and use Cypher snippets for Neo4j queries
7. **CODE_ANALYZE** - Structured workflow for analyzing code using AST and ASG tools
8. **KNOWLEDGE_QUERY** - Hybrid Knowledge Query System for intelligent multi-source reasoning
9. **KNOWLEDGE_EXTRACT** - Dynamic Knowledge Extraction & Synthesis with F-Contraction merging

## Advanced Hybrid Reasoning System

NeoCoder features a revolutionary **Context-Augmented Reasoning** architecture that combines multiple data sources for unprecedented knowledge synthesis capabilities.

### Hybrid Query Architecture

The `KNOWLEDGE_QUERY` template implements a sophisticated 3-step reasoning process:

#### **Step 1: Smart Query Router**
- **Intent Classification**: AI analyzes queries to determine optimal data source strategy
- **Query Types**:
  - *Graph-centric*: "Who works with whom?", "Show dependency chain"
  - *Vector-centric*: "What are opinions on X?", "Find discussions about Y"  
  - *Hybrid*: "What did [person from graph] say about [semantic topic]?"
- **Execution Planning**: Designs multi-step plans for complex hybrid queries

#### **Step 2: Parallelized Data Retrieval**
- **Neo4j Queries**: Execute Cypher queries for structured facts and relationships
- **Qdrant Searches**: Perform semantic searches across document collections
- **Sequential Optimization**: For hybrid queries, use graph results to refine vector searches

#### **Step 3: Cross-Database Synthesizer**
- **Intelligent Synthesis**: Combine structured facts with semantic context
- **Source Prioritization**: Neo4j facts as authoritative, Qdrant for nuance and opinion
- **Mandatory Citations**: Every claim attributed to specific sources
- **Conflict Detection**: Identify and flag inconsistencies between data sources

### Dynamic Knowledge Extraction (F-Contraction)

The `KNOWLEDGE_EXTRACT` template implements dynamic knowledge synthesis inspired by graph contraction principles:

#### **Core F-Contraction Concepts:**
- **Vertices as Concepts**: Each distinct concept becomes a graph entity
- **Edges as Relationships**: Track co-occurrence and explicit connections
- **Dynamic Merging**: LLM-powered detection of duplicate/similar concepts
- **Source Preservation**: Maintain pointers to all original sources after merging

#### **Knowledge Processing Pipeline:**
1. **Document Ingestion**: Parse PDFs, text, code, conversations
2. **Dual Storage**: Chunk text for Qdrant, extract entities for Neo4j
3. **Entity Extraction**: Identify Papers, Authors, Concepts, Methods, etc.
4. **Relationship Discovery**: Find citations, dependencies, semantic connections
5. **F-Contraction Merging**: Intelligently consolidate similar entities
6. **Cross-Reference Mapping**: Link graph entities to vector document chunks
7. **Quality Validation**: Ensure consistency and completeness

### Research Analysis Engine

Specialized capabilities for academic and technical document processing:

- **Citation Graph Construction**: Build networks of paper relationships
- **Multi-Hop Reasoning**: "Trace evolution of transformer architecture through citation links"
- **Conflict Analysis**: "How does definition of X in Paper A differ from Paper B?"
- **Temporal Synthesis**: Track concept evolution across time and sources
- **Cross-Domain Integration**: Combine findings from multiple research domains

### Benefits of Hybrid Reasoning

1. **Unprecedented Synthesis**: Answers impossible with single data sources
2. **Source Transparency**: Complete audit trail from raw data to conclusions
3. **Conflict Awareness**: Explicit handling of contradictory information
4. **Semantic Enrichment**: Structured facts enhanced with contextual understanding
5. **Dynamic Learning**: Knowledge base improves through F-Contraction merging
6. **Research Acceleration**: Rapid analysis of complex academic literature

## Architecture

### Knowledge Graph Structure

- **:AiGuidanceHub**: Central navigation hub for the AI
- **:ActionTemplate**: Templates for standard workflows (FIX, REFACTOR, etc.)
- **:Project**: Project data including README and structure
- **:File/Directory**: Project file structure representation
- **:WorkflowExecution**: Audit trail of completed workflows
- **:BestPracticesGuide**: Coding standards and guidelines
- **:TemplatingGuide**: How to create/modify templates
- **:SystemUsageGuide**: How to use the graph system

### MCP Server Tools

The MCP server provides the following tools to AI assistants:

#### Core Tools
- **check_connection**: Verify Neo4j connection status
- **get_guidance_hub**: Entry point for AI navigation
- **get_action_template**: Get a specific workflow template
- **list_action_templates**: See all available templates
- **get_best_practices**: View coding standards
- **get_project**: View project details including README
- **list_projects**: List all projects in the system
- **log_workflow_execution**: Record a successful workflow completion
- **get_workflow_history**: View audit trail of work done
- **add_template_feedback**: Provide feedback on templates
- **run_custom_query**: Run direct Cypher queries
- **write_neo4j_cypher**: Execute write operations on the graph

#### Incarnation Management Tools
- **get_current_incarnation**: Get the currently active incarnation
- **list_incarnations**: List all available incarnations
- **switch_incarnation**: Switch to a different incarnation
- **suggest_tool**: Get tool suggestions based on task description

Each incarnation provides additional specialized tools that are automatically registered when the incarnation is activated.

#### Knowledge Graph & Hybrid Reasoning Tools

The Knowledge Graph incarnation provides advanced hybrid reasoning capabilities that combine structured graph data with semantic vector search:

**Core Knowledge Management:**
- **create_entities**: Create multiple entities with observations and proper Neo4j labeling
- **create_relations**: Connect entities with typed relationships and timestamps
- **add_observations**: Add timestamped observations to existing entities
- **delete_entities**: Remove entities with cascading deletion of relationships
- **delete_observations**: Targeted removal of specific observation content
- **delete_relations**: Remove specific relationships while preserving entities
- **read_graph**: View entire knowledge graph with entities, observations, and relationships
- **search_nodes**: Full-text search across entity names, types, and observation content
- **open_nodes**: Get detailed entity information with incoming/outgoing relationships

**Advanced Hybrid Reasoning Tools:**
- **KNOWLEDGE_QUERY Workflow**: Intelligent hybrid querying system
  - Smart query routing (graph-centric, vector-centric, or hybrid)
  - Parallelized data retrieval from Neo4j and Qdrant
  - Cross-database synthesis with mandatory citation tracking
  - Conflict detection and source prioritization
  
- **KNOWLEDGE_EXTRACT Workflow**: Dynamic knowledge extraction with F-Contraction
  - Document ingestion with metadata extraction
  - Dual storage: text chunks in Qdrant, entities in Neo4j
  - LLM-powered entity extraction and relationship discovery
  - F-Contraction merging of similar concepts with source preservation
  - Cross-reference mapping between graph and vector data
  - Quality validation and extraction reporting

**Research Analysis Capabilities:**
- **Citation Graph Construction**: Build paper-author-institution networks
- **Multi-Hop Synthesis**: Trace concept evolution through connected sources
- **Temporal Analysis**: Track changes and developments over time
- **Conflict Resolution**: Handle contradictory information from multiple sources
- **Source Attribution**: Complete provenance tracking from raw data to conclusions

**Integration Features:**
- **Qdrant Collections**: Seamless integration with vector databases for semantic search
- **Cross-Database Navigation**: Bi-directional linking between structured and semantic data
- **Memory Integration**: Connect with long-term memory systems for continuity
- **MCP Orchestration**: Advanced tool coordination and workflow management

#### Cypher Snippet Toolkit

The MCP server includes a toolkit for managing and searching Cypher query snippets:

- **list_cypher_snippets**: List all available Cypher snippets with optional filtering
- **get_cypher_snippet**: Get a specific Cypher snippet by ID
- **search_cypher_snippets**: Search for Cypher snippets by keyword, tag, or pattern
- **create_cypher_snippet**: Add a new Cypher snippet to the database
- **update_cypher_snippet**: Update an existing Cypher snippet
- **delete_cypher_snippet**: Delete a Cypher snippet from the database
- **get_cypher_tags**: Get all tags used for Cypher snippets

This toolkit provides a searchable repository of Cypher query patterns and examples that can be used as a reference and learning tool.

#### Tool Proposal System

The MCP server includes a system for proposing and requesting new tools:

- **propose_tool**: Propose a new tool for the NeoCoder system
- **request_tool**: Request a new tool feature as a user
- **get_tool_proposal**: Get details of a specific tool proposal
- **get_tool_request**: Get details of a specific tool request
- **list_tool_proposals**: List all tool proposals with optional filtering
- **list_tool_requests**: List all tool requests with optional filtering

This system allows AI assistants to suggest new tools and users to request new functionality, providing a structured way to manage and track feature requests.

![alt text](image-2.png)

## Customizing Templates

Templates are stored in the `templates` directory as `.cypher` files. You can edit existing templates or create new ones.

To add a new template:

1. Create a new file in the `templates` directory (e.g., `custom_template.cypher`)
2. Follow the format of existing templates
3. Initialize the database to load the template into Neo4j

## The 'Cypher Snippet Toolkit' tools operate on the graph structure defined below

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

Created by [angrysky56](https://github.com/angrysky56)
Claude 3.7 Sonnet
Gemini 2.5 Pro Preview 3-25
ChatGPT o3

## Code Analysis

A comprehensive analysis of the NeoCoder codebase is available in the `/analysis` directory. This includes:

- Architecture overview
- Incarnation system analysis
- Code metrics and structure
- Workflow template analysis
- Integration points
- Recommendations for future development

## Recent Updates

### 2025-06-24: Revolutionary Hybrid Reasoning System (v2.0.0)
- **BREAKTHROUGH**: Implemented Context-Augmented Reasoning architecture combining Neo4j + Qdrant + LLM synthesis
- **NEW**: `KNOWLEDGE_QUERY` action template - 3-step hybrid reasoning system:
  - Smart Query Router: AI classifies intent and plans execution strategy
  - Parallelized Data Retrieval: Seamlessly queries both Neo4j and Qdrant
  - Cross-Database Synthesizer: Intelligent synthesis with mandatory citation tracking
- **NEW**: `KNOWLEDGE_EXTRACT` action template - F-Contraction knowledge synthesis:
  - Dynamic document processing into both graph and vector representations
  - LLM-powered entity extraction and relationship discovery
  - Intelligent concept merging while preserving source attribution
  - Cross-reference mapping between structured and semantic data
- **ENHANCED**: Knowledge Graph incarnation with advanced hybrid capabilities:
  - Fixed guidance hub transaction errors for seamless user experience
  - Implemented sophisticated research analysis workflows
  - Added conflict detection and source prioritization
  - Full integration with Qdrant vector databases for semantic search
- **ARCHITECTURE**: Established foundation for Context-Augmented Reasoning that goes far beyond traditional RAG
- **VALIDATION**: Successfully tested with real research paper corpus demonstrating citation graphs + semantic analysis
- **IMPACT**: Enables unprecedented knowledge synthesis impossible with single data sources

### 2025-06-14: Fixed Critical Async/Event Loop Management Issues (v1.4.1)
- **CRITICAL FIX**: Resolved async context manager protocol errors in `safe_neo4j_session` function
- **Root Cause**: AsyncMock in tests and some driver configurations returned coroutines instead of async context managers
- **Solution**: Added `_handle_session_creation` helper function to detect and properly handle both coroutines and context managers
- **Impact**: Eliminates "TypeError: 'coroutine' object does not support the asynchronous context manager protocol" errors
- **Testing**: Added comprehensive test suite (`test_event_loop_fix.py`) to prevent regression
- **Compatibility**: Maintains full backward compatibility with existing Neo4j driver usage
- **Files Modified**: `src/mcp_neocoder/event_loop_manager.py`, `tests/test_event_loop_fix.py`

### 2025-04-27: Added Code Analysis Incarnation with AST/ASG Support (v1.4.0)
- Added new `code_analysis_incarnation.py` for deep code analysis using AST and ASG tools
- Implemented Neo4j schema for storing code structure and analysis results
- Added CODE_ANALYZE action template with step-by-step workflow
- Created specialized tools for code analysis:
  - `analyze_codebase`: Analyze entire directory structures
  - `analyze_file`: Deep analysis of individual files
  - `compare_versions`: Compare different versions of code
  - `find_code_smells`: Identify potential code issues
  - `generate_documentation`: Auto-generate code documentation
  - `explore_code_structure`: Navigate code structure
  - `search_code_constructs`: Find specific patterns in code
- Integrated with external AST/ASG tools
- Added proper documentation in guidance hub
- Updated IncarnationType enum to include CODE_ANALYSIS type

### 2025-04-27: Eliminated Knowledge Graph Transaction Error Messages (v1.3.2)
- Completely eliminated error messages related to transaction scope issues in knowledge graph functions
- Implemented server-side error message interception and replacement for a smoother user experience
- Added a new safer execution pattern for all database operations:
  - Created `_safe_execute_write` method to eliminate transaction scope errors in write operations
  - Created `_safe_read_query` method to ensure proper transaction handling for read operations
  - Improved entity count tracking for accurate operation feedback
- Enhanced error recovery to continue operations even when JSON parsing fails
- Simplified and improved all knowledge graph tool implementations
- Maintained full backward compatibility with existing knowledge graph data
- Enhanced guidance hub with clearer usage examples

### 2025-04-27: Fixed Knowledge Graph Transaction Scope Issues (v1.3.1)
- Fixed critical issue with knowledge graph functions returning "transaction out of scope" errors
- Implemented a transaction-safe approach for all knowledge graph operations
- Updated all knowledge graph tools to properly handle transaction contexts:
  - Fixed `create_entities` to properly return results
  - Fixed `create_relations` with a simplified approach
  - Fixed `add_observations` to ensure data is committed
  - Fixed `delete_entities`, `delete_observations`, and `delete_relations` functions
  - Fixed `read_graph` to fetch data in multiple safe transactions
  - Fixed `search_nodes` with a more robust query approach
  - Fixed `open_nodes` to query entity details safely
- Enhanced guidance hub with clear examples of knowledge graph tool usage
- Improved error handling throughout knowledge graph operations
- Maintained backward compatibility with existing knowledge graph data

### 2025-04-26: Fixed Knowledge Graph API Functions (v1.3.0)
- Fixed the issue with Knowledge Graph API functions not properly integrating with Neo4j node labeling system
- Implemented properly labeled entities with :Entity label instead of generic :KnowledgeNode
- Added full set of knowledge graph management functions:
  - `create_entities`: Create entities with proper labeling and observations
  - `create_relations`: Connect entities with typed relationships
  - `add_observations`: Add observations to existing entities
  - `delete_entities`: Remove entities and their connections
  - `delete_observations`: Remove specific observations from entities
  - `delete_relations`: Remove relationships between entities
  - `read_graph`: View the entire knowledge graph structure
  - `search_nodes`: Find entities by name, type, or observation content
  - `open_nodes`: Get detailed information about specific entities
- Added fulltext search support with fallback for non-fulltext environments
- Added proper schema initialization with constraints and indexes for knowledge graph
- Updated guidance hub content with usage instructions for the new API functions

### 2025-04-25: Expanded Incarnation Documentation (v1.2.0)
- Added detailed documentation on the architectural principles behind multiple incarnations
- Enhanced description of each incarnation type with operational patterns and use cases
- Added information about common graph schema motifs across incarnations
- Included implementation roadmap for integrating quantum-inspired approaches

### 2025-04-24: Fixed Incarnation Tool Registration (v1.1.0)
- Fixed the issue where incarnation tools weren't being properly registered on server startup
- Fixed circular dependency issues with duplicate class definitions
- Added explicit tool method declaration support via `_tool_methods` class attribute
- Improved the tool discovery mechanism to ensure all tools from each incarnation are properly detected
- Enhanced event loop handling to prevent issues during server initialization
- Added comprehensive logging to aid in troubleshooting
- Fixed schema initialization to properly defer until needed

See the [CHANGELOG.md](./CHANGELOG.md) file for detailed implementation notes.

## License

MIT License
