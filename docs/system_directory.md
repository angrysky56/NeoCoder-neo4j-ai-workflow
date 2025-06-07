# NeoCoder System Directory

This directory provides a comprehensive listing of all incarnations, workflow templates, and tools available in the NeoCoder framework.

## Incarnations

| Incarnation | Description | Key Features |
|-------------|-------------|-------------|
| **code_analysis** | Code analysis using AST/ASG | Parse code structures, identify patterns, find code smells |
| **knowledge_graph** | Knowledge graph management | Create entities, define relationships, search knowledge |
| **research** | Scientific research platform | Track hypotheses, design experiments, record observations |
| **decision** | Decision support system | Create alternatives, track evidence, evaluate decisions |
| **data_analysis** | Data analysis and visualization | Analyze datasets, create visualizations, extract insights |
| **coding** | Original workflow management | Default incarnation for basic coding workflows |

To switch incarnations: `switch_incarnation(incarnation_type="incarnation_name")`

## Workflow Templates

| Template | Purpose | Key Steps |
|----------|---------|-----------|
| **FIX** | Fix reported bugs | Identify issue, reproduce, implement fix, test, document |
| **REFACTOR** | Improve code structure | Identify target, plan changes, implement, test, document |
| **FEATURE** | Add new functionality | Plan feature, implement, test, document |
| **DEPLOY** | Deploy to production | Prepare, validate, deploy, monitor |
| **TOOL_ADD** | Add new tool to NeoCoder | Design, implement, test, document, register |
| **CODE_ANALYZE** | Analyze code with AST | Parse, analyze structure, identify patterns, document |

To access a template: `get_action_template(keyword="TEMPLATE_NAME")`

## Core Tools

### System Tools
- `check_connection()`: Verify Neo4j connection status
- `get_guidance_hub()`: Access guidance for current incarnation
- `list_incarnations()`: List all available incarnations
- `switch_incarnation()`: Switch to a different incarnation
- `get_current_incarnation()`: Get currently active incarnation

### Workflow Tools
- `list_action_templates()`: List all available templates
- `get_action_template()`: Get specific workflow template
- `get_best_practices()`: Access coding best practices guide
- `log_workflow_execution()`: Record successful workflow completion
- `get_workflow_history()`: View completed workflows

### Project Tools
- `list_projects()`: List available projects
- `get_project()`: Get project details and README
- `suggest_tool()`: Get tool suggestions based on task description

### Cypher Tools
- `run_custom_query()`: Execute a read-only Cypher query
- `write_neo4j_cypher()`: Execute a write Cypher query
- `list_cypher_snippets()`: List available Cypher snippets
- `search_cypher_snippets()`: Search for Cypher patterns
- `get_cypher_snippet()`: Get a specific Cypher snippet
- `create_cypher_snippet()`: Add a new Cypher snippet
- `update_cypher_snippet()`: Update an existing snippet
- `delete_cypher_snippet()`: Delete a Cypher snippet
- `get_cypher_tags()`: Get all tags used for snippets

## Code Analysis Tools

### Direct AST Tools
- `parse_to_ast(code, language)`: Parse code into an AST
  ```python
  ast_result = parse_to_ast(code="def hello(): print('world')", language="python")
  ```

- `generate_asg(code, language)`: Generate an Abstract Semantic Graph
  ```python
  asg_result = generate_asg(code="def hello(): print('world')", language="python")
  ```

- `analyze_code(code, language)`: Analyze code structure and complexity
  ```python
  analysis = analyze_code(code="def hello(): print('world')", language="python")
  ```

- `supported_languages()`: Get supported programming languages
  ```python
  languages = supported_languages()
  ```

### Code Analysis Incarnation Tools
- `analyze_codebase(directory_path, ...)`: Analyze entire codebase
  ```python
  analyze_codebase(directory_path="/path/to/project", language="python")
  ```

- `analyze_file(file_path, ...)`: Analyze a single file
  ```python
  analyze_file(file_path="/path/to/file.py", analysis_type="both")
  ```

- `compare_versions(file_path, ...)`: Compare code versions
  ```python
  compare_versions(file_path="/path/to/file.py", old_version="v1.0", new_version="v2.0")
  ```

- `find_code_smells(target, ...)`: Identify code issues
  ```python
  find_code_smells(target="/path/to/file.py", threshold="medium")
  ```

- `generate_documentation(target, ...)`: Generate code documentation
  ```python
  generate_documentation(target="/path/to/project", doc_format="markdown")
  ```

- `explore_code_structure(target, ...)`: Explore code structure
  ```python
  explore_code_structure(target="/path/to/file.py", view_type="hierarchy")
  ```

- `search_code_constructs(query, ...)`: Search for code patterns
  ```python
  search_code_constructs(query="function.*add", search_type="pattern")
  ```

## Knowledge Graph Tools

- `create_entities(entities)`: Create entities with observations
  ```python
  create_entities(entities=[{
      "name": "Entity1", 
      "entityType": "Person", 
      "observations": ["Observation 1", "Observation 2"]
  }])
  ```

- `create_relations(relations)`: Create relationships between entities
  ```python
  create_relations(relations=[{
      "from": "Entity1", 
      "to": "Entity2", 
      "relationType": "KNOWS"
  }])
  ```

- `add_observations(observations)`: Add observations to entities
  ```python
  add_observations(observations=[{
      "entityName": "Entity1", 
      "contents": ["New observation 1", "New observation 2"]
  }])
  ```

- `delete_entities(entityNames)`: Delete entities from the graph
  ```python
  delete_entities(entityNames=["Entity1", "Entity2"])
  ```

- `delete_observations(deletions)`: Delete specific observations
  ```python
  delete_observations(deletions=[{
      "entityName": "Entity1", 
      "observations": ["Observation to delete"]
  }])
  ```

- `delete_relations(relations)`: Delete relationships
  ```python
  delete_relations(relations=[{
      "from": "Entity1", 
      "to": "Entity2", 
      "relationType": "KNOWS"
  }])
  ```

- `read_graph()`: View the entire knowledge graph
  ```python
  read_graph()
  ```

- `search_nodes(query)`: Search for entities
  ```python
  search_nodes(query="search term")
  ```

- `open_nodes(names)`: Get detailed entity information
  ```python
  open_nodes(names=["Entity1", "Entity2"])
  ```

## Research Tools

- `register_hypothesis(text, ...)`: Register a scientific hypothesis
  ```python
  register_hypothesis(
      text="Hypothesis statement",
      description="Detailed description",
      prior_probability=0.5
  )
  ```

- `list_hypotheses(...)`: List scientific hypotheses
  ```python
  list_hypotheses(status="Active")
  ```

- `get_hypothesis(id)`: Get a specific hypothesis
  ```python
  get_hypothesis(id="hypothesis-uuid")
  ```

- `update_hypothesis(id, ...)`: Update a hypothesis
  ```python
  update_hypothesis(
      id="hypothesis-uuid",
      current_probability=0.75,
      status="Confirmed"
  )
  ```

- `create_protocol(...)`: Create an experimental protocol
  ```python
  create_protocol(
      name="Protocol Name",
      description="Protocol description",
      steps=["Step 1", "Step 2"],
      expected_observations=["Expected result 1"]
  )
  ```

- `list_protocols(...)`: List available protocols
  ```python
  list_protocols()
  ```

- `get_protocol(id)`: Get a specific protocol
  ```python
  get_protocol(id="protocol-uuid")
  ```

- `create_experiment(...)`: Create a new experiment
  ```python
  create_experiment(
      name="Experiment Name",
      hypothesis_id="hypothesis-uuid",
      protocol_id="protocol-uuid"
  )
  ```

- `list_experiments(...)`: List experiments
  ```python
  list_experiments(status="In Progress")
  ```

- `get_experiment(id)`: Get a specific experiment
  ```python
  get_experiment(id="experiment-uuid")
  ```

- `update_experiment(id, ...)`: Update an experiment
  ```python
  update_experiment(
      id="experiment-uuid",
      status="Completed"
  )
  ```

- `record_observation(...)`: Record an experimental observation
  ```python
  record_observation(
      experiment_id="experiment-uuid",
      content="Observation content",
      supports_hypothesis=True
  )
  ```

- `list_observations(...)`: List observations for an experiment
  ```python
  list_observations(experiment_id="experiment-uuid")
  ```

- `compute_statistics(...)`: Calculate statistics for observations
  ```python
  compute_statistics(
      experiment_id="experiment-uuid",
      include_visualization=True
  )
  ```

- `create_publication_draft(...)`: Generate a publication draft
  ```python
  create_publication_draft(
      experiment_id="experiment-uuid",
      title="Publication Title",
      authors=["Author 1", "Author 2"]
  )
  ```

## Decision Support Tools

- `create_decision(...)`: Create a new decision
  ```python
  create_decision(
      title="Decision Title",
      description="Decision description"
  )
  ```

- `list_decisions(...)`: List decisions
  ```python
  list_decisions(status="Open")
  ```

- `get_decision(id)`: Get a specific decision
  ```python
  get_decision(id="decision-uuid")
  ```

- `add_alternative(...)`: Add an alternative to a decision
  ```python
  add_alternative(
      decision_id="decision-uuid",
      name="Alternative Name",
      description="Alternative description",
      expected_value=0.75
  )
  ```

- `add_metric(...)`: Add an evaluation metric
  ```python
  add_metric(
      decision_id="decision-uuid",
      name="Metric Name",
      description="Metric description",
      weight=5,
      target_direction="maximize"
  )
  ```

- `add_evidence(...)`: Add evidence for/against an alternative
  ```python
  add_evidence(
      alternative_id="alternative-uuid",
      content="Evidence content",
      impact="supports"
  )
  ```

## Data Analysis Tools

- `tool_one(...)`: Tool one for Data Analysis incarnation
  ```python
  tool_one(param1="value")
  ```

- `tool_two(...)`: Tool two for Data Analysis incarnation
  ```python
  tool_two(param1="value")
  ```

## Usage Patterns

### Core Workflow

```python
# 1. Switch to appropriate incarnation
switch_incarnation(incarnation_type="code_analysis")

# 2. Get guidance
guidance = get_guidance_hub()

# 3. Get workflow template
template = get_action_template(keyword="CODE_ANALYZE")

# 4. Execute workflow steps
# ...

# 5. Log completion
log_workflow_execution(
    project_id="project-id",
    action_keyword="CODE_ANALYZE",
    summary="Task summary",
    files_changed=["file1.py", "file2.py"]
)
```

### AST Analysis Workflow

```python
# 1. Switch to code analysis incarnation
switch_incarnation(incarnation_type="code_analysis")

# 2. Analyze code directly
ast_result = parse_to_ast(code=code_string, language="python")

# 3. Store in Neo4j
analyze_file(file_path="file.py", analysis_type="both")

# 4. Find code smells
find_code_smells(target="file.py", threshold="medium")

# 5. Generate documentation
generate_documentation(target="file.py", doc_format="markdown")
```

### Knowledge Graph Workflow

```python
# 1. Switch to knowledge graph incarnation
switch_incarnation(incarnation_type="knowledge_graph")

# 2. Create entities
create_entities(entities=[...])

# 3. Create relationships
create_relations(relations=[...])

# 4. Search nodes
search_nodes(query="search term")

# 5. View specific entities
open_nodes(names=["Entity1"])
```

## Related Documentation

- [Guidance Hub System](guidance_hub_system.md)
- [Incarnation Cypher Guide](incarnation_cypher_guide.md)
- [Cypher Patterns Library](cypher_patterns_library.md)
- [Code Analysis Incarnation](code_analysis_incarnation.md)
- [Knowledge Graph Incarnation](knowledge_graph_incarnation.md)
