# NeoCoder Incarnations Library

This directory contains the modular documentation, workflows, and resources for all incarnations in the NeoCoder framework. Each incarnation is self-contained in its own folder to manage context limits and keep documentation modular.

## Directory Structure

```
incarnations_library/
│
├── code_analysis/               # Code analysis incarnation
│   ├── README.md                # Overview
│   ├── workflows/               # Specific workflows
│   ├── cypher/                  # Cypher patterns
│   └── tools/                   # Tools documentation
│
├── knowledge_graph/             # Knowledge graph incarnation
│   ├── README.md                # Overview
│   ├── workflows/               # Specific workflows
│   ├── cypher/                  # Cypher patterns
│   └── tools/                   # Tools documentation
│
├── research/                    # Research incarnation
│   ├── README.md                # Overview
│   ├── workflows/               # Specific workflows
│   ├── cypher/                  # Cypher patterns
│   └── tools/                   # Tools documentation
│
└── common/                      # Shared resources
    ├── README.md                # Overview
    ├── cypher/                  # Common Cypher patterns
    └── guidance/                # Common guidance documents
```

## Navigation

1. **For overview information**: Start with the main NeoCoder README.md
2. **For incarnation-specific guidance**: Use the Neo4j guidance hub system
3. **For detailed documentation**: Navigate to the specific incarnation folder
4. **For common patterns and practices**: See the common/ directory

## Adding New Incarnations

When creating a new incarnation:

1. Create a new folder with the incarnation name
2. Add the standard structure (README.md, workflows/, cypher/, tools/, when required special_notes/, updates/, )
3. Document the incarnation's purpose, tools, and workflows
4. Update the appropriate incarnations guidance hub in Neo4j to reference this documentation
5. Register the incarnation in the system directory

## Incarnation Documentation Standards

Each incarnation folder should include:

1. **README.md**: Overview, purpose, and key concepts
2. **workflows/**: Step-by-step documentation for each workflow
3. **cypher/**: Verified Cypher patterns specific to the incarnation
4. **tools/**: Documentation for all tools provided by the incarnation

## Working with Neo4j Guidance Hubs

This documentation library complements the Neo4j guidance hubs. When updating:

1. Ensure documentation changes are reflected in corresponding guidance hubs
2. Cross-reference between documentation and guidance hubs
3. Use consistent terminology and structure

## Current Status

The current incarnations system is working properly. The main Neo4j guidance hub (`main_hub`) provides the entry point for all navigation.
