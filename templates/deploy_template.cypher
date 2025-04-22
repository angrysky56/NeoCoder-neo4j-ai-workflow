// Create or update DEPLOY template
MERGE (t:ActionTemplate {keyword: 'DEPLOY', version: '1.0'})
ON CREATE SET t.isCurrent = true
ON MATCH SET t.isCurrent = true
SET t.description = 'Guidance on deploying code to production environments with safety checks.'
SET t.complexity = 'HIGH'
SET t.estimatedEffort = 120
SET t.steps = """
1.  **Identify Context:**
    -   Input: Project ID: $projectId. Environment: $environment (e.g., staging, production). Release version: $releaseVersion.
    -   Query Project README: `MATCH (p:Project {projectId: $projectId}) RETURN p.readmeContent, p.readmeUrl`
    -   Review README for project context, architecture, and deployment-specific instructions.
    -   Identify existing deployment workflows and CI/CD configurations.

2.  **Pre-Deployment Checks:**
    -   **Code Quality:**
        - Run all tests across all components. **ALL tests MUST pass.**
        - Run static analysis tools to identify potential issues.
        - Verify code coverage meets minimum threshold.
    -   **Dependency Validation:**
        - Ensure all dependencies are at correct/compatible versions.
        - Check for security vulnerabilities in dependencies.
    -   **Environment Configuration:**
        - Verify environment configuration variables are properly set.
        - Confirm access to necessary external services and APIs.
        - Check infrastructure requirements (CPU, memory, storage).

3.  **Versioning and Documentation:**
    -   Update version numbers in relevant files (package.json, etc.).
    -   Create/update release notes documenting changes, fixes, and improvements.
    -   Update API documentation if applicable.
    -   Ensure all required documentation is complete and accurate.

4.  **Deployment Preparation:**
    -   Create deployment plan outlining steps, sequence, and rollback procedures.
    -   Prepare database migration scripts if necessary.
    -   Create backup of current production environment (data, configurations).
    -   Schedule deployment window with relevant stakeholders.
    -   Notify affected teams and prepare communication plan.

5.  **!!! CRITICAL: Deployment Validation !!!**
    -   Execute deployment to the target environment:
        - If CI/CD pipeline exists, trigger deployment.
        - If manual, follow the established deployment procedure.
    -   Verify deployment completion and service availability.
    -   Run health checks and smoke tests against deployed services.
    -   Monitor for unexpected errors or performance issues.
    -   **If ANY validation fails, STOP here and implement rollback procedure. Do NOT proceed.**

6.  **Post-Deployment Testing:**
    -   Execute integration and end-to-end tests against deployed environment.
    -   Verify critical user journeys and functionality.
    -   Monitor performance metrics (response times, resource utilization).
    -   Perform security tests if applicable.
    -   **If ANY test fails, evaluate severity:**
        - Critical: Execute rollback procedure.
        - Non-critical: Document for hotfix deployment.

7.  **Log Successful Deployment (ONLY if all validation and testing passed):**
    -   Prepare parameters: 
        - `$projectId` - The project identifier
        - `$workflowId` - Generate a new UUID
        - `$keyword` - 'DEPLOY'
        - `$description` - Description of deployment (include version and environment)
        - `$environment` - The environment deployed to
        - `$deployedVersion` - The version deployed
    -   Execute Logging Cypher:
    ```
    CREATE (exec:WorkflowExecution {
      id: $workflowId,
      timestamp: datetime(),
      keywordUsed: $keyword,
      description: $description,
      status: "Completed",
      environment: $environment,
      deployedVersion: $deployedVersion,
      executionTime: $executionTimeSeconds
    })
    WITH exec
    MATCH (p:Project {projectId: $projectId})
    MERGE (exec)-[:APPLIED_TO_PROJECT]->(p)
    WITH exec
    MATCH (t:ActionTemplate {keyword: $keyword, isCurrent: true})
    MERGE (exec)-[:USED_TEMPLATE]->(t)
    ```
    -   Confirm successful creation of `:WorkflowExecution` node.

8.  **Update Project Metadata (ONLY if deployment succeeded):**
    -   Update project environment status:
    ```
    MATCH (p:Project {projectId: $projectId})
    SET p.lastDeployment = datetime(),
        p.currentVersion = $deployedVersion
    ```
    -   Update deployment history:
    ```
    MATCH (p:Project {projectId: $projectId})
    MERGE (e:Environment {name: $environment, projectId: $projectId})
    MERGE (e)-[:HAS_VERSION]->(v:Version {number: $deployedVersion, projectId: $projectId})
    SET v.deploymentDate = datetime()
    ```

9.  **Post-Deployment Monitoring:**
    -   Monitor application logs for unexpected errors.
    -   Track key performance indicators and compare to pre-deployment baseline.
    -   Set up alerts for critical thresholds.
    -   Document any anomalies or concerns for follow-up.
    -   Define monitoring period (typically 24-48 hours for production).

10. **Deployment Review and Feedback:**
    -   Schedule post-deployment review meeting.
    -   Document lessons learned and improvement opportunities.
    -   Update deployment procedure based on experience.
    -   Create a `:Feedback` node with deployment insights:
    ```
    CREATE (f:Feedback {
      id: $feedbackId,
      content: $feedbackContent,
      timestamp: datetime(),
      source: $source,
      severity: $severity,
      tags: ['deployment_feedback']
    })
    WITH f
    MATCH (t:ActionTemplate {keyword: 'DEPLOY', isCurrent: true})
    MERGE (f)-[:REGARDING]->(t)
    ```
"""

// Make sure this is the only current version for this keyword
MATCH (old:ActionTemplate {keyword: 'DEPLOY', isCurrent: true})
WHERE old.version <> '1.0'
SET old.isCurrent = false
