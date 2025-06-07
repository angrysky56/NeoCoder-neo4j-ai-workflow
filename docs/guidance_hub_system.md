# NeoCoder Guidance Hub System

This document explains the architecture and usage of the NeoCoder guidance hub system, which provides structured navigation and instructions for AI assistants.

## Overview

The guidance hub system is a network of interconnected nodes in the Neo4j database that serve as entry points and guides for AI assistants. These hubs provide context-sensitive instructions, references to workflow templates, tool documentation, and Cypher patterns.

![Guidance Hub Architecture](../image-2.png)

## Hub Architecture

The guidance hub system consists of:

1. **Main Hub** - Central entry point and navigation
2. **Incarnation Hubs** - Instructions for specific incarnations
3. **Workflow Templates** - Step-by-step workflow instructions
4. **Cypher Libraries** - Verified Cypher patterns and examples
5. **System Directories** - Comprehensive listings of resources

### Core Node Types

```cypher
(:AiGuidanceHub {id, description, createdAt, lastUpdated})
(:ActionTemplate {keyword, version, isCurrent, description, steps, createdAt, updatedAt})
```

## Guidance Hub Hierarchy

```
main_hub
│
├── incarnation_cypher_guide
│   └── (Incarnation-specific Cypher patterns)
│
├── verified_cypher_library
│   └── (Verified Cypher patterns by category)
│
├── system_directory
│   └── (Complete listings of resources)
│
└── incarnation_hubs
    ├── code_analysis_hub
    ├── knowledge_graph_hub
    ├── research_hub
    ├── decision_hub
    └── data_analysis_hub
```

## Accessing Guidance Hubs

AI assistants can access guidance hubs using:

1. **Direct Tool Access**:
   ```python
   get_guidance_hub()  # Returns the current incarnation's hub
   ```

2. **Cypher Queries**:
   ```cypher
   MATCH (hub:AiGuidanceHub {id: 'hub_id'})
   RETURN hub.description
   ```

3. **References from Other Hubs**:
   Each hub contains references to related hubs and resources.

## Hub Types and IDs

| Hub Type | Hub ID | Purpose |
|----------|--------|---------|
| Main Hub | main_hub | Central entry point and navigation |
| Incarnation Cypher Guide | incarnation_cypher_guide | Incarnation-specific Cypher |
| Verified Cypher Library | verified_cypher_library | Verified Cypher patterns |
| System Directory | system_directory | Comprehensive resource listings |
| Code Analysis | code_analysis_hub | Code analysis with AST/ASG |
| Knowledge Graph | knowledge_graph_hub | Knowledge graph management |
| Research | research_hub | Scientific research platform |
| Decision | decision_hub | Decision support system |
| Data Analysis | data_analysis_hub | Data analysis and visualization |

## Main Hub

The main hub (id: 'main_hub') serves as the primary entry point for AI assistants. It provides:

- Overview of core features
- Links to incarnations
- Getting started instructions
- References to other guidance resources

Accessing the main hub:
```cypher
MATCH (hub:AiGuidanceHub {id: 'main_hub'})
RETURN hub.description
```

## Incarnation Hubs

Each incarnation has its own guidance hub (id: 'incarnation_name_hub'). These hubs are automatically accessed when an assistant switches to that incarnation:

```python
switch_incarnation(incarnation_type="code_analysis")
get_guidance_hub()  # Now returns the code_analysis_hub
```

Incarnation hubs include:
- Overview of the incarnation's purpose
- Available tools and their usage
- Getting started instructions
- Examples and best practices

## Workflow Templates

Workflow templates (ActionTemplate nodes) provide step-by-step instructions for common tasks. They can be accessed with:

```python
get_action_template(keyword="TEMPLATE_NAME")
```

Each template includes:
- Description of the workflow
- Detailed steps to complete the task
- Verification requirements
- Instructions for logging completion

## Navigating Between Hubs

The guidance hub system is designed for easy navigation:

1. **Start at Main Hub**:
   ```cypher
   MATCH (hub:AiGuidanceHub {id: 'main_hub'})
   RETURN hub.description
   ```

2. **Access Referenced Hubs**:
   ```cypher
   MATCH (hub:AiGuidanceHub {id: 'incarnation_cypher_guide'})
   RETURN hub.description
   ```

3. **Find Related Templates**:
   ```cypher
   MATCH (t:ActionTemplate)
   WHERE t.isCurrent = true
   RETURN t.keyword, t.description
   ```

## Updating Guidance Hubs

When updating the system:

1. **Update Neo4j Hubs**:
   ```cypher
   MATCH (hub:AiGuidanceHub {id: 'hub_id'})
   SET hub.description = "New content...",
       hub.lastUpdated = datetime()
   ```

2. **Update Documentation Files**:
   Ensure the corresponding markdown files in the docs directory are updated to match.

3. **Log the Update**:
   ```python
   log_workflow_execution(
       project_id=project_id,
       action_keyword="FEATURE",
       summary="Updated guidance hub content",
       files_changed=["path/to/updated/file.md"],
       notes="Details of the update..."
   )
   ```

## Creating New Hubs

To create a new guidance hub:

1. Create the hub in Neo4j:
   ```cypher
   CREATE (hub:AiGuidanceHub {
       id: "new_hub_id",
       description: "Hub content...",
       createdAt: datetime()
   })
   ```

2. Add references from other hubs:
   ```cypher
   MATCH (main:AiGuidanceHub {id: 'main_hub'})
   SET main.description = main.description + "\n\n## New Section\n\nReference to new hub: new_hub_id"
   ```

3. Create corresponding documentation file

## Best Practices

1. **Consistency**: Maintain consistent formatting across all hubs
2. **Cross-References**: Include links to related hubs and resources
3. **Examples**: Provide concrete examples of tool usage and cypher queries
4. **Updates**: Keep both Neo4j hubs and markdown documentation in sync
5. **Versioning**: Include version information and update timestamps

## Implementation Details

The guidance hub system is implemented using:

1. **Neo4j Nodes**: AiGuidanceHub and ActionTemplate nodes
2. **Tools**: get_guidance_hub, get_action_template, run_custom_query
3. **Documentation**: Markdown files in the docs directory
4. **Synchronization**: Manual and programmatic updates

## Related Documentation

- [System Directory](system_directory.md) - Comprehensive listing of resources
- [Incarnation Cypher Guide](incarnation_cypher_guide.md) - Incarnation-specific Cypher
- [Cypher Patterns Library](cypher_patterns_library.md) - Verified Cypher patterns
