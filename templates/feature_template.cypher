// FEATURE Template
// Provides guidance on adding new features to projects

// Create the FEATURE template
MERGE (t:ActionTemplate {keyword: 'FEATURE', version: '1.0'})
ON CREATE SET
  t.description = 'Structured approach to implementing new features with proper testing and documentation',
  t.complexity = 'MEDIUM',
  t.estimatedEffort = 90,
  t.isCurrent = true,
  t.domain = 'development',
  t.steps = "# FEATURE Implementation

This template guides you through implementing a new feature while adhering to best practices.

## 1. Identify Requirements

-   Clearly define the scope of the feature
-   Identify the project and relevant components
-   Query Project README: `get_project(project_id=\"project-id\")`
-   Review existing architecture and design patterns

## 2. Design Phase

-   Design the feature with a focus on:
    -   Modularity and extensibility
    -   Consistency with existing codebase
    -   Performance considerations
    -   Security implications
-   Create a technical specification if needed

## 3. Test-Driven Development

-   Write tests that define the expected behavior of the feature
-   These tests should initially fail (since the feature doesn't exist yet)
-   Ensure test coverage for normal usage, edge cases, and error handling

## 4. Implementation

-   Implement the feature following project's coding standards
-   Add proper documentation (code comments, user documentation)
-   Adhere to Best Practices Guide (efficiency, meaningful naming)
-   Make incremental commits with descriptive messages

## 5. !!! CRITICAL: Test Verification !!!

-   Run the new tests; **they MUST now pass**
-   Run all existing tests to ensure no regressions; **ALL tests MUST pass**
-   **If any test fails, STOP here and return to Step 4. Do NOT proceed.**
-   Manually test the feature if applicable

## 6. Log Successful Execution (ONLY if Step 5 passed):

-   Use log_workflow_execution tool with parameters:
  - project_id: The project identifier
  - keyword: 'FEATURE'
  - description: Brief summary of the implemented feature
  - modified_files: List of file paths that were modified/created
  - execution_time_seconds: (Optional) Time taken to complete the workflow
  - test_results: (Optional) Summary of test results
-   Confirm successful creation of workflow execution node

## 7. Update Project Artifacts:

-   Update README.md with information about the new feature
-   Update any relevant documentation
-   Update Neo4j project structure if new files/directories were added

## 8. Code Review & Merge:

-   Submit changes for code review
-   Address any feedback and iterate
-   Merge the feature into the main branch when approved
"

ON MATCH SET
  t.isCurrent = true,
  t.version = '1.0'

// Create relationship to hub in a separate operation
WITH t
MATCH (hub:AiGuidanceHub {id: 'main_hub'})
MERGE (hub)-[:PROVIDES_TEMPLATE]->(t)

RETURN t.keyword + ' v' + t.version + ' template created successfully';