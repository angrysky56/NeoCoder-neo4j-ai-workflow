// Create or update REFACTOR template
MERGE (t:ActionTemplate {keyword: 'REFACTOR', version: '1.1'})
ON CREATE SET t.isCurrent = true
ON MATCH SET t.isCurrent = true
SET t.description = 'Guidance on refactoring code to improve quality without changing functionality.'
SET t.complexity = 'HIGH'
SET t.estimatedEffort = 90
SET t.steps = """
1.  **Identify Context:**
    -   Input: Project ID: $projectId. Target component/module: [$targetComponent]
    -   Query Project README: `MATCH (p:Project {projectId: $projectId}) RETURN p.readmeContent, p.readmeUrl`
    -   Review README for project context, architecture, and design principles.
    -   Identify existing tests for the target component.

2.  **Document Current Behavior:**
    -   Run existing tests to establish current behavior.
    -   Document key inputs/outputs and behaviors.
    -   Create any additional tests needed to verify functionality remains unchanged.
    -   Capture metrics on the current code (complexity, performance benchmarks).

3.  **Plan Refactoring Strategy:**
    -   Identify specific code smells or issues to address.
    -   Determine refactoring patterns to apply.
    -   Break down refactoring into incremental steps.
    -   Establish clear completion criteria.
    -   Assess impact on related components.

4.  **Incremental Implementation:**
    -   Implement refactoring in small, testable increments.
    -   After each increment:
        - Run tests to verify behavior is preserved.
        - Ensure code style consistency.
        - Review for new code smells/issues.
    -   Document each step for later review.
    -   Update any documentation affected by structural changes.

5.  **!!! CRITICAL: Test Verification !!!**
    -   Run ALL tests related to the refactored component; **ALL MUST pass**.
    -   Verify metrics improvements (reduced complexity, etc.).
    -   Check for any performance regressions.
    -   Conduct peer review if available.
    -   **If any test fails or metrics degrade, STOP here and fix issues. Do NOT proceed.**

6.  **Log Successful Execution (ONLY if Step 5 passed):**
    -   Prepare parameters: 
        - `$projectId` - The project identifier
        - `$workflowId` - Generate a new UUID
        - `$keyword` - 'REFACTOR'
        - `$description` - Description of refactoring performed
        - `$modifiedFiles` - List of paths changed
        - `$metricsChange` - Before/after metrics showing improvements
    -   Execute Logging Cypher:
    ```
    CREATE (exec:WorkflowExecution {
      id: $workflowId,
      timestamp: datetime(),
      keywordUsed: $keyword,
      description: $description,
      status: "Completed",
      metrics: $metricsChange,
      executionTime: $executionTimeSeconds
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
    -   Confirm successful creation of `:WorkflowExecution` node.

7.  **Update Project Documentation:**
    -   Update architecture diagrams if structural changes were made.
    -   Document design decisions and patterns applied.
    -   Update developer guidelines if new patterns were introduced.
    -   Update Project README if necessary:
    ```
    MATCH (p:Project {projectId: $projectId}) 
    SET p.readmeContent = $newReadmeContent
    ```

8.  **Knowledge Sharing:**
    -   Document the refactoring for team knowledge sharing.
    -   Highlight improvements in metrics/maintainability.
    -   Note any patterns that could be applied elsewhere in the codebase.
    -   Consider creating a `:Feedback` node with suggestions for similar refactoring elsewhere:
    ```
    CREATE (f:Feedback {
      id: $feedbackId,
      content: $feedbackContent,
      timestamp: datetime(),
      source: $source,
      severity: $severity
    })
    WITH f
    MATCH (t:ActionTemplate {keyword: 'REFACTOR', isCurrent: true})
    MERGE (f)-[:REGARDING]->(t)
    ```
"""

// Make sure this is the only current version for this keyword
MATCH (old:ActionTemplate {keyword: 'REFACTOR', isCurrent: true})
WHERE old.version <> '1.1'
SET old.isCurrent = false
