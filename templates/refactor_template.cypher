// Create or update REFACTOR template
MERGE (t:ActionTemplate {keyword: 'REFACTOR', version: '1.1'})
ON CREATE SET t.isCurrent = true
ON MATCH SET t.isCurrent = true
SET t.description = 'Structured approach to refactoring code while maintaining functionality and ensuring test coverage.'
SET t.complexity = 'MEDIUM'
SET t.estimatedEffort = 90
SET t.steps = '
1. **Identify Context:** 
   - Review Project README and codebase structure using get_project tool
   - Identify specific code area needing refactoring
   - Document the need for refactoring (technical debt, performance, etc.)
   
2. **Analyze Current Code:**
   - Document current functionality in detail
   - Identify pain points or code smells
   - Establish metrics for improvement (performance, readability, etc.)
   - Use appropriate tools to measure code quality and complexity metrics

3. **Write Tests:**
   - Ensure comprehensive test coverage before refactoring
   - Document current behavior for regression testing
   - Create additional tests if coverage is insufficient

4. **Plan Refactoring Strategy:**
   - Choose appropriate refactoring patterns
   - Break down into smaller, manageable steps
   - Consider backwards compatibility needs
   - Evaluate potential risks

5. **Implement Refactoring:**
   - Make changes incrementally
   - Run tests after each significant change
   - Follow best practices for naming and structure
   - Keep commits focused and well-documented

6. **!!! CRITICAL: Test Verification !!!**
   - Run ALL tests to ensure no regression
   - Verify improved metrics over previous implementation
   - Compare before/after metrics to quantify improvements
   - **If tests fail, STOP here and return to implementation step. Do NOT proceed.**

7. **Log Successful Execution (ONLY if Step 6 passed):**
   - Use log_workflow_execution tool with parameters:
     - project_id: The project identifier
     - keyword: REFACTOR
     - description: Brief summary of the refactoring
     - modified_files: List of file paths that were modified
     - execution_time_seconds: (Optional) Time taken to complete the workflow
     - test_results: (Optional) Summary of test results
   - Confirm successful creation of workflow execution node.

8. **Update Documentation:**
   - Update README and other documentation
   - Document design decisions and improvements
   - Add comments to complex logic if necessary
'

// Make sure this is the only current version for this keyword
MATCH (old:ActionTemplate {keyword: 'REFACTOR', isCurrent: true})
WHERE old.version <> '1.1'
SET old.isCurrent = false
