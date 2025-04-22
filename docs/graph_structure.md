# Neo4j Graph Structure Documentation

This document outlines the core node types, relationships, and properties used in the Neo4j-guided AI coding workflow system.

## Core Node Types

### `:AiGuidanceHub`

The central entry point for AI navigation within the knowledge graph.

**Properties:**
- `id` (String): Unique identifier (e.g., "main_hub")
- `description` (String): Multi-line description providing navigation guidance and basic instructions

**Relationships:**
- `-[:LINKS_TO]->` to various guide nodes

### `:ActionTemplate`

Defines standardized workflows for specific coding tasks.

**Properties:**
- `keyword` (String): Unique identifier for the action (e.g., "FIX", "REFACTOR")
- `version` (String): Version number of this template
- `isCurrent` (Boolean): Flag indicating whether this is the current version (only one per keyword)
- `description` (String): Brief description of the template's purpose
- `steps` (String): Detailed, multi-line instructions for executing the workflow
- `complexity` (String, optional): Estimation of task complexity (e.g., "LOW", "MEDIUM", "HIGH")
- `estimatedEffort` (Integer, optional): Estimated time in minutes to complete the task

**Relationships:**
- `<-[:USED_TEMPLATE]-` from `:WorkflowExecution` nodes
- `-[:MAY_TRIGGER]->` to other `:ActionTemplate` nodes (optional)

### `:Project`

Represents a software project or codebase.

**Properties:**
- `projectId` (String): Unique identifier
- `name` (String): Project name
- `readmeContent` (String): Project README content
- `readmeUrl` (String, optional): Link to external README
- `repositoryUrl` (String, optional): Link to code repository

**Relationships:**
- `-[:CONTAINS]->` to `:Directory` and `:File` nodes
- `<-[:APPLIED_TO_PROJECT]-` from `:WorkflowExecution` nodes

### `:Directory` and `:File`

Represent the file system structure of a project.

**Properties:**
- `path` (String): File or directory path
- `project_id` (String): Reference to parent project

**Relationships:**
- `<-[:CONTAINS]-` from parent `:Project` or `:Directory` nodes
- `:Directory` `-[:CONTAINS]->` to child `:Directory` or `:File` nodes
- `<-[:MODIFIED]-` from `:WorkflowExecution` nodes

### `:WorkflowExecution`

Records a successfully completed instance of an `ActionTemplate` workflow.

**Properties:**
- `id` (String): Unique identifier
- `timestamp` (DateTime): When the workflow was executed
- `keywordUsed` (String): Reference to the ActionTemplate keyword used
- `description` (String): Description of what was done
- `status` (String): Execution status (typically "Completed")
- `testResults` (String, optional): Summary of test results
- `executionTime` (Integer, optional): Time taken to complete the workflow in seconds
- `humanCollaborator` (String, optional): Name/ID of human collaborator if applicable

**Relationships:**
- `-[:APPLIED_TO_PROJECT]->` to `:Project` node
- `-[:USED_TEMPLATE]->` to `:ActionTemplate` node
- `-[:MODIFIED]->` to `:File` or `:Directory` nodes

### Guide Nodes

Various guide nodes provide documentation and best practices.

**Types:**
- `:BestPracticesGuide`
- `:TemplatingGuide`
- `:SystemUsageGuide`

**Properties:**
- `id` (String): Unique identifier
- `content` (String): Multi-line content of the guide

**Relationships:**
- `<-[:LINKS_TO]-` from `:AiGuidanceHub`

### `:Feedback`

Stores feedback on template effectiveness.

**Properties:**
- `id` (String): Unique identifier
- `content` (String): Feedback description
- `timestamp` (DateTime): When feedback was recorded
- `source` (String): Who provided the feedback (AI or human)
- `severity` (String, optional): Importance level (e.g., "LOW", "MEDIUM", "HIGH")

**Relationships:**
- `-[:REGARDING]->` to `:ActionTemplate` node

## Key Relationships

- `:AiGuidanceHub` `-[:LINKS_TO]->` `:BestPracticesGuide`, `:TemplatingGuide`, `:SystemUsageGuide`
- `:Project` `-[:CONTAINS]->` `:Directory`
- `:Directory` `-[:CONTAINS]->` `:Directory` or `:File` 
- `:WorkflowExecution` `-[:APPLIED_TO_PROJECT]->` `:Project`
- `:WorkflowExecution` `-[:USED_TEMPLATE]->` `:ActionTemplate`
- `:WorkflowExecution` `-[:MODIFIED]->` `:File` or `:Directory`
- `:Feedback` `-[:REGARDING]->` `:ActionTemplate`
- `:ActionTemplate` `-[:MAY_TRIGGER]->` `:ActionTemplate` (optional)

## Common Cypher Queries

### Retrieve Current Action Template

```cypher
MATCH (t:ActionTemplate {keyword: $keyword, isCurrent: true}) 
RETURN t.steps
```

### Create Workflow Execution Record

```cypher
CREATE (exec:WorkflowExecution {
  id: $workflowId,
  timestamp: datetime(),
  keywordUsed: $keyword,
  description: $description,
  status: "Completed"
})
WITH exec
MATCH (p:Project {projectId: $projectId})
MERGE (exec)-[:APPLIED_TO_PROJECT]->(p)
WITH exec
MATCH (t:ActionTemplate {keyword: $keyword, isCurrent: true})
MERGE (exec)-[:USED_TEMPLATE]->(t)
WITH exec
FOREACH (filePath IN $modifiedFiles | 
  MERGE (f:File {path: filePath, project_id: $projectId})
  MERGE (exec)-[:MODIFIED]->(f)
)
```

### Query Project History

```cypher
MATCH (p:Project {projectId: $projectId})<-[:APPLIED_TO_PROJECT]-(exec:WorkflowExecution)
RETURN exec.timestamp, exec.keywordUsed, exec.description
ORDER BY exec.timestamp DESC
```

### Find Template Feedback

```cypher
MATCH (f:Feedback)-[:REGARDING]->(t:ActionTemplate {keyword: $keyword})
RETURN f.content, f.timestamp, f.source
ORDER BY f.timestamp DESC
```

## Constraints and Indexes

For optimal performance and data integrity, the following constraints and indexes should be created:

```cypher
// Constraints
CREATE CONSTRAINT unique_action_template_current IF NOT EXISTS
FOR (t:ActionTemplate)
REQUIRE (t.keyword, t.isCurrent) IS UNIQUE;

CREATE CONSTRAINT unique_project_id IF NOT EXISTS
FOR (p:Project)
REQUIRE p.projectId IS UNIQUE;

CREATE CONSTRAINT unique_workflow_execution_id IF NOT EXISTS
FOR (w:WorkflowExecution)
REQUIRE w.id IS UNIQUE;

// Indexes
CREATE INDEX action_template_keyword IF NOT EXISTS
FOR (t:ActionTemplate)
ON (t.keyword);

CREATE INDEX file_path IF NOT EXISTS
FOR (f:File)
ON (f.path);
```
