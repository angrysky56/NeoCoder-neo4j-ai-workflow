// Create or update FIX template
MERGE (t:ActionTemplate {keyword: 'FIX', version: '1.2'})
ON CREATE SET t.isCurrent = true
ON MATCH SET t.isCurrent = true
SET t.description = 'Guidance on fixing a reported bug, including mandatory testing and logging.'
SET t.complexity = 'MEDIUM'
SET t.estimatedEffort = 45
SET t.steps = '
1.  **Identify Context:**
    -   Input: Bug report ID/details. Project ID. Files suspected.
    -   Query Project README: Use get_project tool with project_id parameter.
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
    -   Use log_workflow_execution tool with parameters:
      - project_id: The project identifier
      - keyword: FIX
      - description: Brief summary of the fix
      - modified_files: List of file paths that were modified
      - execution_time_seconds: (Optional) Time taken to complete the workflow
      - test_results: (Optional) Summary of test results
    -   Confirm successful creation of workflow execution node.

7.  **Update Project Artifacts (ONLY if Step 5 passed):**
    -   Update Project README if necessary with information about the fix.
    -   Update documentation to reflect the changes made.

8.  **Risk Assessment:**
    -   Assess potential side effects of the fix.
    -   Document any areas that may need monitoring after deployment.
'

// Make sure this is the only current version for this keyword
MATCH (old:ActionTemplate {keyword: 'FIX', isCurrent: true})
WITH old.version <> '1.2'
SET old.isCurrent = false
