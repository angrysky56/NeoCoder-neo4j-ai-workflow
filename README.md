# NeoCoder: Neo4j-Guided AI Coding Workflow

An MCP server implementation that enables AI assistants like Claude to use a Neo4j knowledge graph as their primary, dynamic "instruction manual" and project memory for standardized coding workflows.

## Overview

NeoCoder implements a system where:

1. AI assistants query a Neo4j database for standardized workflows (`ActionTemplates`) triggered by keywords (e.g., `FIX`, `REFACTOR`)
2. The AI follows specific steps in these templates when performing coding tasks
3. Critical steps like testing are enforced before logging success
4. A complete audit trail of changes is maintained in the graph itself

## Quick Start

### Prerequisites

- **Neo4j**: Running locally or a remote instance
- **Python 3.8+**: For running the MCP server
- **uv**: The Python package manager for MCP servers
- **Claude Desktop**: For using with Claude AI

### Installation

Requires a running Neo4j database and UV.

1. Install uv (if not already installed):

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

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

### MCP Server Tools- write cypher may not work right

The MCP server provides the following tools to AI assistants:

- **write_neo4j_cypher**: Execute Cypher queries against the graph
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

## To run just add the Claude App Config, only tested in Linux but should work on other OS

```json
{
  "mcpServers": {
    "neocoder": {
      "command": "uv",
      "args": [
        "--directory",
        "/home/ty/Repositories/ai_workspace/NeoCoder-neo4j-ai-workflow/src/mcp_neocoder",
        "run",
        "mcp_neocoder"
      ],
      "env": {
        "NEO4J_URL": "bolt://localhost:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "NEO4J_PASSWORD",
        "NEO4J_DATABASE": "neo4j"
      }    
    }    
  }
}
```

The default Neo4j connection parameters:

- **URL**: `bolt://localhost:7687`
- **Username**: `neo4j`
- **Password**: `password`
- **Database**: `neo4j`

These can be overridden with environment variables, maybe:

- `NEO4J_URL`
- `NEO4J_USERNAME`
- `NEO4J_PASSWORD`
- `NEO4J_DATABASE`

## Docker Support will be added later, maybe

The project includes Docker configuration for running Neo4j:

```bash
docker-compose up -d neo4j
``

## License

MIT License
