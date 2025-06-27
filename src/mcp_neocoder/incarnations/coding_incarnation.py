"""
Coding Incarnation for the NeoCoder framework.

This incarnation provides the original NeoCoder functionality for AI-assisted coding workflows,
including action templates, project management, workflow tracking, and best practices guidance.
"""

import logging

from .base_incarnation import BaseIncarnation
from ..action_templates import ActionTemplateMixin
from ..event_loop_manager import safe_neo4j_session

logger = logging.getLogger("mcp_neocoder.incarnations.coding")


class CodingIncarnation(BaseIncarnation, ActionTemplateMixin):
    """
    Coding Incarnation for the NeoCoder framework.

    This is the original NeoCoder incarnation that provides structured coding workflows,
    action templates (FIX, REFACTOR, DEPLOY, etc.), project management, and workflow tracking.
    """

    # Define the incarnation name
    name = "coding"

    # Metadata for display in the UI
    description = "Original NeoCoder for AI-assisted coding workflows"
    version = "1.0.0"

    # Only register coding-specific tools here (if any in the future)
    _tool_methods = []

    # Only include coding-specific schema queries (project, workflow, file, directory)
    schema_queries = [
        # Drop any existing conflicting indexes before creating constraints
        "DROP INDEX file_path IF EXISTS",
        
        # Project constraints
        "CREATE CONSTRAINT project_id IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE",

        # Workflow execution constraints
        "CREATE CONSTRAINT workflow_id IF NOT EXISTS FOR (w:WorkflowExecution) REQUIRE w.id IS UNIQUE",

        # File and directory constraints (project-scoped to allow multiple projects)
        "CREATE CONSTRAINT unique_file_path IF NOT EXISTS FOR (f:File) REQUIRE (f.project_id, f.path) IS UNIQUE",
        "CREATE CONSTRAINT unique_dir_path IF NOT EXISTS FOR (d:Directory) REQUIRE (d.project_id, d.path) IS UNIQUE",

        # Indexes for efficient querying
        "CREATE INDEX project_name IF NOT EXISTS FOR (p:Project) ON (p.name)",
        "CREATE INDEX workflow_timestamp IF NOT EXISTS FOR (w:WorkflowExecution) ON (w.timestamp)",
        "CREATE INDEX file_name IF NOT EXISTS FOR (f:File) ON (f.name)",
        "CREATE INDEX dir_name IF NOT EXISTS FOR (d:Directory) ON (d.name)"
    ]

    # Hub content - guidance for coding workflows
    hub_content = """
# NeoCoder Coding Workflow System

Welcome to the NeoCoder Coding Workflow System. This incarnation provides structured guidance for AI-assisted coding tasks through action templates and workflow tracking.

## Core Concepts

1. **Action Templates**: Structured workflows for common coding tasks
   - `FIX`: Bug fixing workflow with mandatory testing
   - `REFACTOR`: Code refactoring with safety checks
   - `DEPLOY`: Deployment workflow with verification steps
   - `FEATURE`: New feature implementation
   - `TOOL_ADD`: Adding new tools to the system
   - `CODE_ANALYZE`: Analyzing code structure and quality

2. **Projects**: Organized code repositories with tracking
   - README content stored in Neo4j
   - File structure representation
   - Change history tracking

3. **Workflow Execution**: Audit trail of completed work
   - Only logged after successful test execution
   - Links changes to templates and projects
   - Provides accountability and history

## Getting Started

1. **Get an Action Template**:
   ```
   get_action_template(keyword="FIX")
   ```
   This retrieves the step-by-step workflow for fixing bugs.

2. **Follow the Template Steps**:
   - Each template has specific steps to follow
   - Critical steps (like testing) are mandatory
   - Document changes as you go

3. **Log Successful Completion**:
   ```
   log_workflow_execution(
       project_id="my_project",
       action_keyword="FIX",
       summary="Fixed null pointer exception in user service",
       files_changed=["src/services/user.py"]
   )
   ```
   Only log after all tests pass!

## Available Commands

### Navigation & Guidance
- `get_guidance_hub()` - Return here for orientation
- `suggest_tool(task_description="...")` - Get tool suggestions for a task
- `get_best_practices()` - View coding standards and guidelines

### Action Templates
- `list_action_templates()` - See all available workflows
- `get_action_template(keyword="...")` - Get specific workflow steps
- `add_template_feedback(keyword="...", feedback="...")` - Improve templates

### Project Management
- `list_projects()` - View all projects in the system
- `get_project(project_id="...")` - Get project details and README

### Workflow Tracking
- `log_workflow_execution(...)` - Record completed work (tests must pass!)
- `get_workflow_history(...)` - View past work with filters

### Direct Neo4j Queries
- `run_custom_query(query="...")` - Execute read queries
- `write_neo4j_cypher(query="...")` - Execute write queries

## Best Practices

1. **Always Test Before Logging**: The system enforces quality by requiring test success before logging workflow completion.

2. **Use Templates Consistently**: Templates ensure standardized approaches to common tasks.

3. **Document As You Go**: Include clear summaries and file change lists in workflow logs.

4. **Check History**: Use `get_workflow_history()` to learn from past work.

5. **Provide Feedback**: Help improve templates with `add_template_feedback()`.

## Example Workflow: Fixing a Bug

1. Get the FIX template:
   ```
   get_action_template(keyword="FIX")
   ```

2. Follow the steps:
   - Review the bug report
   - Locate the issue in code
   - Implement the fix
   - **Run all tests** (mandatory!)
   - Update documentation

3. Log the completion:
   ```
   log_workflow_execution(
       project_id="my_app",
       action_keyword="FIX",
       summary="Fixed date parsing error in API endpoint",
       files_changed=["src/api/dates.py", "tests/test_dates.py"]
   )
   ```

Remember: The key to NeoCoder is following structured workflows that ensure quality and maintainability!
"""

    async def initialize_schema(self):
        """Initialize the Neo4j schema for the Coding incarnation."""
        try:
            # First run the parent class initialization
            await super().initialize_schema()

            # Then create the coding-specific action templates
            await self._create_action_templates()

            # Create sample projects if needed
            await self._create_sample_projects()

            # Create best practices guide
            await self._create_best_practices()

            logger.info("Coding incarnation schema initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing coding schema: {e}")
            raise

    async def _create_action_templates(self):
        """Create the standard action templates for coding workflows."""
        templates = [
            {
                "keyword": "FIX",
                "name": "Bug Fix Workflow",
                "description": "Structured approach to fixing bugs with mandatory testing",
                "steps": """1. Review the bug report and understand the issue
2. Locate the relevant code files
3. Analyze the root cause
4. Implement the fix
5. Run ALL relevant tests (mandatory!)
6. Update documentation if needed
7. Create or update tests for the bug
8. Verify the fix resolves the issue"""
            },
            {
                "keyword": "REFACTOR",
                "name": "Code Refactoring Workflow",
                "description": "Safe refactoring with regression testing",
                "steps": """1. Identify the code to refactor
2. Understand current functionality
3. Run existing tests to establish baseline
4. Plan the refactoring approach
5. Implement refactoring incrementally
6. Run tests after each change
7. Ensure no functionality is broken
8. Update documentation"""
            },
            {
                "keyword": "DEPLOY",
                "name": "Deployment Workflow",
                "description": "Safe deployment process with verification",
                "steps": """1. Review all changes to be deployed
2. Run full test suite
3. Check deployment checklist
4. Prepare deployment notes
5. Execute deployment process
6. Verify deployment success
7. Monitor for issues
8. Document deployment"""
            },
            {
                "keyword": "FEATURE",
                "name": "Feature Implementation Workflow",
                "description": "Adding new features with proper testing",
                "steps": """1. Review feature requirements
2. Design implementation approach
3. Create feature branch
4. Implement feature incrementally
5. Write tests for new functionality
6. Run all tests
7. Update documentation
8. Prepare for code review"""
            },
            {
                "keyword": "TOOL_ADD",
                "name": "Add Tool to NeoCoder",
                "description": "Process for adding new tools to the MCP server",
                "steps": """1. Define tool purpose and parameters
2. Add tool method to appropriate module
3. Include proper type hints and docstring
4. Register tool in server initialization
5. Test tool functionality
6. Update documentation
7. Add to tool suggestions
8. Create usage examples"""
            },
            {
                "keyword": "CODE_ANALYZE",
                "name": "Code Analysis Workflow",
                "description": "Analyzing code structure and quality",
                "steps": """1. Select code to analyze
2. Run AST/ASG analysis tools
3. Review code metrics
4. Identify code smells
5. Document findings
6. Suggest improvements
7. Create refactoring plan if needed
8. Update project documentation"""
            }
        ]

        try:
            async with safe_neo4j_session(self.driver, self.database) as session:
                for template in templates:
                    query = """
                    MERGE (t:ActionTemplate {keyword: $keyword})
                    SET t.name = $name,
                        t.description = $description,
                        t.steps = $steps,
                        t.isCurrent = true,
                        t.version = 1,
                        t.created = datetime(),
                        t.updated = datetime()
                    """
                    from typing import cast, LiteralString
                    await session.execute_write(lambda tx: tx.run(cast(LiteralString, query), template))
                    logger.info(f"Created action template: {template['keyword']}")
        except Exception as e:
            logger.error(f"Error creating action templates: {e}")
            raise

    async def _create_sample_projects(self):
        """Create sample projects if none exist."""
        try:
            async with safe_neo4j_session(self.driver, self.database) as session:
                # Check if any projects exist
                result = await session.run("MATCH (p:Project) RETURN count(p) as count")
                data = await result.single()

                if data and data["count"] == 0:
                    # Create a sample project
                    query = """
                    CREATE (p:Project {
                        id: 'neocoder_project',
                        name: 'NeoCoder System',
                        description: 'The NeoCoder MCP server system',
                        readme: 'This is the NeoCoder system for AI-assisted coding workflows.',
                        created: datetime(),
                        updated: datetime()
                    })
                    """
                    await session.execute_write(lambda tx: tx.run(query))
                    logger.info("Created sample project")
        except Exception as e:
            logger.error(f"Error creating sample projects: {e}")

    async def _create_best_practices(self):
        """Create the best practices guide."""
        try:
            async with safe_neo4j_session(self.driver, self.database) as session:
                query = """
                MERGE (bp:BestPracticesGuide {id: 'main'})
                SET bp.content = $content,
                    bp.updated = datetime()
                """

                content = """# NeoCoder Best Practices

## Code Quality
1. Always write tests before marking work as complete
2. Follow consistent naming conventions
3. Document complex logic
4. Keep functions focused and small
5. Handle errors gracefully

## Workflow Practices
1. Use action templates for consistency
2. Log all significant changes
3. Include clear commit messages
4. Review code before deployment
5. Monitor after deployment

## Documentation
1. Keep README files updated
2. Document API changes
3. Include examples in documentation
4. Explain the "why" not just the "what"
5. Use clear, concise language"""

                await session.execute_write(lambda tx: tx.run(query, {"content": content}))
                logger.info("Created best practices guide")
        except Exception as e:
            logger.error(f"Error creating best practices: {e}")

# End of coding incarnation
