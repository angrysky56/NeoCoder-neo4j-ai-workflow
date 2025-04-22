// Create or update FIX template
MERGE (t:ActionTemplate {keyword: 'FIX', version: '1.2'})
ON CREATE SET t.isCurrent = true
ON MATCH SET t.isCurrent = true
SET t.description = 'Guidance on fixing a reported bug, including mandatory testing and logging.'
SET t.complexity = 'MEDIUM'
SET t.estimatedEffort = 45
SET t.steps = """
1.  **Identify Context:**
    -   Input: Bug report ID/details. Project ID: $projectId. Files suspected: [$filePaths]
    -   Query Project README: `MATCH (p:Project {projectId: $projectId}) RETURN p.readmeContent, p.readmeUrl`
    -   Review README for project context, setup, and relevant sections.

2.  **Reproduce & Isolate:**
    -   Ensure you can reliably trigger the bug.
    -   Use debugging tools to pinpoint the faulty code.
    -   Identify root cause (logic, data, environmental issue).
    -   Document reproduction steps clearly.

3.  **Write Failing Test:**
    -   Create an automated test specifically demonstrating the bug. It must fail initially.
    -   Ensure test name clearly indicates the issue being addressed.
    -   Add appropriate assertions to validate correct behavior.

4.  **Implement Fix:**
    -   Modify code to correct the issue, adhering to project coding standards.
    -   Consider edge cases that may be related to this bug.
    -   Add comments explaining the fix if the solution is non-obvious.
    -   Reference the root cause in your documentation.

5.  **!!! CRITICAL: Test Verification !!!**
    -   Run the previously failing test; **it MUST now pass**.
    -   Run all related unit/integration tests for the affected module(s). **ALL relevant tests MUST pass**.
    -   Perform additional manual testing if appropriate.
    -   **If any test fails, STOP here and return to Step 4. Do NOT proceed.**

6.  **Log Successful Execution (ONLY if Step 5 passed):**
    -   Prepare parameters: 
        - `$projectId` - The project identifier
        - `$workflowId` - Generate a new UUID
        - `$keyword` - 'FIX'
        - `$description` - Brief summary of the fix
        - `$modifiedFiles` - List of paths changed
        - `$testResults` - Summary of test results
    -   Execute Logging Cypher:
    ```
    CREATE (exec:WorkflowExecution {
      id: $workflowId,
      timestamp: datetime(),
      keywordUsed: $keyword,
      description: $description,
      status: "Completed",
      testResults: $testResults,
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

7.  **Update Project Artifacts (ONLY if Step 5 passed):**
    -   Update Neo4j Project Tree (already done by logging query in Step 6).
    -   Update Project README if necessary:
        - Add fix to changelog if present
        - Update known issues section if relevant
    -   Execute README Update if needed: 
    ```
    MATCH (p:Project {projectId: $projectId}) 
    SET p.readmeContent = $newReadmeContent
    ```

8.  **Risk Assessment:**
    -   Assess potential side effects of the fix.
    -   Document any areas that may need monitoring after deployment.
    -   Flag if additional regression testing is recommended before release.

9.  **Knowledge Sharing:**
    -   Document the fix and root cause for team knowledge sharing.
    -   Consider if this fix suggests improvements to existing practices.
    -   If multiple similar bugs exist, consider a more comprehensive solution.
"""

// Make sure this is the only current version for this keyword
MATCH (old:ActionTemplate {keyword: 'FIX', isCurrent: true})
WHERE old.version <> '1.2'
SET old.isCurrent = false
