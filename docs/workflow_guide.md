# Neo4j-Guided AI Coding Workflow - User Guide

This guide explains how to effectively use the Neo4j-guided AI coding workflow system in your development process. By combining the power of AI coding assistants with a structured knowledge graph, you can achieve greater consistency, reliability, and traceability in your software development.

## Table of Contents

1. [System Overview](#system-overview)
2. [Getting Started](#getting-started)
3. [Using Action Templates](#using-action-templates)
4. [Working with the AI Assistant](#working-with-the-ai-assistant)
5. [Managing Templates](#managing-templates)
6. [Tracking and Visualization](#tracking-and-visualization)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

## System Overview

The Neo4j-guided AI coding workflow uses a graph database to:

- **Guide AI behavior** through standardized templates for common coding tasks
- **Enforce testing** before logging changes
- **Create an audit trail** of all changes linked to files and projects
- **Maintain context** across AI conversations
- **Track metrics** on workflow efficiency and effectiveness

The core components include:

- **AI Guidance Hub**: The central entry point for AI navigation
- **Action Templates**: Standardized workflows for common tasks (FIX, REFACTOR, DEPLOY)
- **Project Structure**: Graph representation of your codebase
- **Workflow Execution**: Records of completed tasks with metadata
- **Feedback System**: Mechanism to improve templates over time

## Getting Started

### Prerequisites

- Neo4j database (4.4+)
- Python 3.8+ with required packages
- AI assistant with access to Neo4j (e.g., Claude with MCP)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/neo4j-ai-workflow.git
   cd neo4j-ai-workflow
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Initialize the Neo4j database structure:
   ```bash
   python scripts/init_graph.py --uri bolt://localhost:7687 --username neo4j --password your_password
   ```

4. Create your project in Neo4j:
   ```bash
   python scripts/template_manager.py --uri bolt://localhost:7687 --username neo4j --password your_password create --keyword "CREATE_PROJECT" --description "Create a new project node" --steps templates/create_project_steps.txt
   ```

### Setting Up Your Project

To register a new project in the graph:

1. Create a Cypher query to add your project:
   ```cypher
   CREATE (p:Project {
     projectId: "your-project-id",
     name: "Your Project Name",
     readmeContent: "This is the project README content...",
     readmeUrl: "https://github.com/yourusername/your-repo/blob/main/README.md"
   })
   ```

2. Execute the query using the Neo4j Browser or the `write_neo4j_cypher` tool if available.

3. Import your project file structure:
   ```bash
   # Use the visualization tool to sync the project structure
   python utils/visualization.py --uri bolt://localhost:7687 --username neo4j --password your_password sync-project-files --project-id "your-project-id" --directory "/path/to/your/project"
   ```

## Using Action Templates

The system comes with three pre-defined action templates:

1. **FIX**: For fixing bugs and issues in code
2. **REFACTOR**: For improving code quality without changing functionality
3. **DEPLOY**: For safely deploying code to production environments

Each template defines a standardized workflow with specific steps, including mandatory testing before registering completion.

### Template Structure

Templates contain:

- **Keyword**: Unique identifier (e.g., FIX, REFACTOR)
- **Version**: Version number for tracking changes
- **Description**: Purpose of the template
- **Complexity**: Estimated complexity (LOW, MEDIUM, HIGH)
- **Estimated Effort**: Expected time to complete in minutes
- **Steps**: Detailed workflow steps in a structured format

### Creating Custom Templates

You can create custom templates for your organization's specific needs:

1. Create a template file (YAML or JSON):
   ```yaml
   keyword: "CODE_REVIEW"
   version: "1.0"
   description: "Perform a comprehensive code review"
   complexity: "MEDIUM"
   estimatedEffort: 60
   steps: |
     1. **Identify Context:**
        - Input: PR ID, Project ID, Files to review
        - ...
     
     2. **Code Quality Assessment:**
        - ...
   ```

2. Import the template:
   ```bash
   python scripts/template_manager.py --uri bolt://localhost:7687 --username neo4j --password your_password import --input templates/code_review.yaml
   ```

## Working with the AI Assistant

The AI assistant is instructed to use the Neo4j graph as its primary guide for executing coding tasks.

### System Instructions

To instruct your AI assistant, use the following system instruction:

```
You are an AI coding assistant integrated with a Neo4j knowledge graph that defines our standard coding procedures and tracks project changes.

Your Core Interaction Loop:
1. Identify Task & Keyword: Determine the coding action required (e.g., fix a bug -> `FIX`).
2. Consult the Hub: If unsure, query `:AiGuidanceHub {id: 'main_hub'}` for guidance.
3. Retrieve Instructions: Fetch the steps from the current `:ActionTemplate` matching the keyword.
4. Execute Guided Workflow: Follow the retrieved steps meticulously.
5. Perform Verification: Execute the testing steps defined in the template. ALL required tests MUST pass before considering the task complete.
6. Record Completion (Post-Testing): Only if tests pass, create a `:WorkflowExecution` node.
7. Finalize Updates: Update project README as instructed.

Always prioritize instructions from the Neo4j graph over your general knowledge for workflow procedures.
```

### Example Interaction

Here's an example of how to interact with the AI assistant:

```
User: I need help fixing a bug in our authentication system. The login form sometimes fails to submit when the username contains special characters.

AI: I'll help you fix this bug. I'll use the FIX workflow for this task.

First, let me query the Neo4j graph to get the standard FIX workflow:

[AI queries the graph for the FIX template]

Following the FIX workflow steps:

1. Context: I understand there's an issue with the login form when usernames contain special characters.
   
2. Let's reproduce the issue first...

[AI continues following the template steps methodically]
```

### Key Principles

When working with the AI assistant:

1. **Be specific** about the task type (fix, refactor, deploy)
2. **Provide context** about the project and issue
3. **Follow the workflow** prescribed by the template
4. **Verify testing** before accepting changes
5. **Request logging** once the task is complete

## Managing Templates

The `template_manager.py` script provides tools for managing your templates:

### Listing Templates

```bash
# List all current templates
python scripts/template_manager.py --uri bolt://localhost:7687 --username neo4j --password your_password list

# Include non-current versions
python scripts/template_manager.py --uri bolt://localhost:7687 --username neo4j --password your_password list --include-inactive
```

### Viewing Template Details

```bash
# View a specific template
python scripts/template_manager.py --uri bolt://localhost:7687 --username neo4j --password your_password show --keyword FIX
```

### Updating Templates

```bash
# Update a template to a new version
python scripts/template_manager.py --uri bolt://localhost:7687 --username neo4j --password your_password update --keyword FIX --new-version 1.3 --steps new_fix_steps.txt
```

### Exporting and Importing

```bash
# Export a template
python scripts/template_manager.py --uri bolt://localhost:7687 --username neo4j --password your_password export --keyword FIX --output fix_template.yaml

# Import a template
python scripts/template_manager.py --uri bolt://localhost:7687 --username neo4j --password your_password import --input fix_template.yaml
```

## Tracking and Visualization

The system provides tools for visualizing and analyzing workflow execution:

### Core Structure Visualization

```bash
python utils/visualization.py --uri bolt://localhost:7687 --username neo4j --password your_password core-structure
```

### Project Structure

```bash
python utils/visualization.py --uri bolt://localhost:7687 --username neo4j --password your_password project-structure --project-id your-project-id
```

### Workflow History

```bash
python utils/visualization.py --uri bolt://localhost:7687 --username neo4j --password your_password workflow-history --project-id your-project-id --days 30
```

### File Modifications

```bash
python utils/visualization.py --uri bolt://localhost:7687 --username neo4j --password your_password file-modifications --project-id your-project-id
```

### Metrics Collection

The `metrics_collector.py` script helps track workflow efficiency:

```bash
# Generate a comprehensive report
python utils/metrics_collector.py --uri bolt://localhost:7687 --username neo4j --password your_password generate-report --days 30 --output-dir reports
```

## Best Practices

### Template Design

1. **Be explicit** about critical checkpoints
2. **Include detailed testing** instructions
3. **Split complex workflows** into manageable steps
4. **Define clear completion criteria**
5. **Maintain backwards compatibility** when updating templates

### AI Interaction

1. **Verify the AI follows the workflow** exactly
2. **Request explanation** of each step as the AI executes it
3. **Review test results** carefully before approving logging
4. **Provide feedback** on template effectiveness
5. **Maintain consistent keywords** across your organization

### Workflow Management

1. **Regularly review** workflow execution metrics
2. **Update templates** based on feedback and metrics
3. **Archive obsolete** templates rather than deleting them
4. **Document template changes** clearly
5. **Sync project structure** when adding new files

## Troubleshooting

### Common Issues

1. **AI not using templates correctly**
   - Ensure the system instruction is properly configured
   - Check that the template exists and is marked as current
   - Verify the Neo4j connection details

2. **Template not found**
   - Check the keyword spelling
   - Verify the template exists in the database
   - Confirm the template is marked as current

3. **Logging failures**
   - Verify all testing steps passed
   - Check Neo4j database connectivity
   - Ensure proper parameters are provided

4. **Graph visualization issues**
   - Install required dependencies (networkx, pyvis)
   - Check file permissions in the output directory
   - Verify Neo4j connection details

### Getting Help

If you encounter issues:

1. Check the logs in `logs/` directory
2. Review the documentation in `docs/`
3. Submit an issue on GitHub
4. Reach out to your organization's administrator

## Conclusion

The Neo4j-guided AI coding workflow provides a structured, consistent approach to AI-assisted coding. By leveraging standardized templates, enforcing testing, and maintaining comprehensive audit trails, it addresses key challenges in AI-assisted development while improving code quality and team collaboration.

---

## Appendix: Cypher Queries

### Useful Queries for Workflow Analysis

#### Most Active Projects

```cypher
MATCH (w:WorkflowExecution)-[:APPLIED_TO_PROJECT]->(p:Project)
RETURN p.name as project, count(w) as workflow_count
ORDER BY workflow_count DESC
LIMIT 10
```

#### Template Success Rates

```cypher
MATCH (w:WorkflowExecution)-[:USED_TEMPLATE]->(t:ActionTemplate)
WITH t.keyword as template, count(w) as total
OPTIONAL MATCH (w:WorkflowExecution)-[:USED_TEMPLATE]->(t:ActionTemplate)
WHERE w.status = "Failed"
WITH template, total, count(w) as failed
RETURN template, total, failed, (total-failed)/toFloat(total) as success_rate
ORDER BY success_rate DESC
```

#### Most Modified Files

```cypher
MATCH (w:WorkflowExecution)-[:MODIFIED]->(f:File)
RETURN f.path as file, count(w) as modification_count
ORDER BY modification_count DESC
LIMIT 20
```

#### Template Usage Over Time

```cypher
MATCH (w:WorkflowExecution)
WHERE w.timestamp > datetime() - duration({days: 30})
RETURN w.keywordUsed as template, date(w.timestamp) as date, count(*) as count
ORDER BY date, template
```
