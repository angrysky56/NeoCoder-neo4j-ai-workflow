# NeoCoder Documentation

This directory contains comprehensive documentation for the NeoCoder Neo4j AI Workflow system.

## Documentation Structure

### Core Guides
- [**Incarnations Guide**](incarnations.md): Detailed guide to NeoCoder's incarnation system
- [**Workflow Guide**](workflow_guide.md): Instructions for using workflow templates
- [**System Instructions**](system_instructions.md): System instructions for AI assistants
- [**Graph Structure**](graph_structure.md): Neo4j graph architecture overview

### Incarnations
- [**Code Analysis**](code_analysis_incarnation.md): AST/ASG code analysis incarnation
- [**Knowledge Graph**](knowledge_graph_incarnation.md): Knowledge graph management incarnation
- [**Research**](research_incarnation.md): Scientific research platform
- [**Decision**](decision_incarnation.md): Decision support system
- [**Data Analysis**](data_analysis_incarnation.md): Data analysis and visualization

### Cypher Resources
- [**Cypher Snippets Reference**](cypher_snippets_reference.md): Complete reference for Cypher snippets
- [**Cypher Patterns Library**](cypher_patterns_library.md): Verified Cypher patterns and examples
- [**Incarnation Cypher Guide**](incarnation_cypher_guide.md): Incarnation-specific Cypher

### System Reference
- [**System Directory**](system_directory.md): Comprehensive listing of tools and templates
- [**API Reference**](api_reference.md): API documentation for programmatic access
- [**Guidance Hub System**](guidance_hub_system.md): Architecture of the guidance hub system

## Documentation Source of Truth

The documentation in this directory is synchronized with the Neo4j guidance hubs:

| Documentation File | Neo4j Guidance Hub |
|-------------------|-------------------|
| guidance_hub_system.md | main_hub |
| incarnation_cypher_guide.md | incarnation_cypher_guide |
| cypher_patterns_library.md | verified_cypher_library |
| system_directory.md | system_directory |

These guidance hubs provide the core navigation structure for AI assistants using the NeoCoder framework. The documentation files provide human-readable explanations and examples.

## Adding New Documentation

When adding new documentation:

1. Create markdown files in the appropriate subdirectory
2. Update the README.md with links to new documentation
3. Create corresponding guidance hubs in Neo4j
4. Add cross-references between documentation and guidance hubs

## Documentation Conventions

- Use Markdown for all documentation
- Include code examples in appropriate syntax highlighting
- Provide Cypher examples for Neo4j interaction
- Reference other documents using relative links
- Include a table of contents for longer documents

## Usage

This documentation can be:
- Read directly on GitHub
- Served as a static site using [Docsify](https://docsify.js.org/) or [MkDocs](https://www.mkdocs.org/)
- Integrated with AI assistants via the guidance hub system
- Referenced from the Neo4j database using linked IDs
