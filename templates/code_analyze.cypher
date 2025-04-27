// CODE_ANALYZE action template
// Version: 1.0

// Create the template
MERGE (t:ActionTemplate {keyword: "CODE_ANALYZE"})
ON CREATE SET t.version = 1.0, 
              t.createdAt = datetime(),
              t.isCurrent = true,
              t.description = "Structured workflow for analyzing code using AST and ASG tools"
ON MATCH SET t.updatedAt = datetime()

// Set the steps for the template
WITH t
SET t.steps = "# Code Analysis Workflow

This workflow guides you through using Abstract Syntax Tree (AST) and Abstract Semantic Graph (ASG) tools to analyze code and gain deeper understanding of its structure and behavior.

## Preparation

1. **Identify the code to analyze**
   - Determine whether you're analyzing a single file, multiple files, or an entire codebase
   - Note the programming language(s) involved
   - Identify any specific aspects you want to focus on (structure, complexity, patterns, etc.)

2. **Check available AST/ASG tools**
   - Basic Tools:
     - `parse_to_ast`: Parse code into an Abstract Syntax Tree
     - `generate_asg`: Generate an Abstract Semantic Graph from code
     - `analyze_code`: Analyze code structure and complexity
     - `supported_languages`: Get the list of supported programming languages
   - Enhanced Tools:
     - `parse_to_ast_incremental`: Parse code with incremental support
     - `generate_enhanced_asg`: Generate an enhanced ASG with better scope handling
     - `diff_ast`: Find differences between two versions of code
     - `find_node_at_position`: Locate a specific node at a given position

3. **Plan your analysis strategy**
   - For small, focused analysis: Use individual file processing
   - For larger codebases: Use hierarchical analysis
   - For tracking changes: Use diff-based analysis

## Analysis Execution

4. **Basic AST Analysis**
   - Begin with parsing the code:
     ```python
     ast_result = parse_to_ast(code=code_string, language=language)
     ```
   - Review the AST structure to understand the code's syntax
   - Store the result in Neo4j using the code analysis incarnation's tools:
     ```python
     # Store using the incarnation's tools
     await analyze_file(file_path=file_path, analysis_type='ast')
     ```

5. **Semantic Graph Analysis (if needed)**
   - Generate an Abstract Semantic Graph for deeper understanding:
     ```python
     asg_result = generate_asg(code=code_string, language=language)
     ```
   - Review the semantic relationships between code elements
   - Store the result in Neo4j:
     ```python
     # Store using the incarnation's tools
     await analyze_file(file_path=file_path, analysis_type='asg')
     ```

6. **Code Complexity Analysis**
   - Analyze code structure and metrics:
     ```python
     analysis_result = analyze_code(code=code_string, language=language)
     ```
   - Identify complex methods, classes, or functions
   - Note cyclomatic complexity, nesting depth, and other metrics
   - Use the results to guide refactoring decisions

7. **Code Comparison (if comparing versions)**
   - Use diff tools to compare versions:
     ```python
     diff_result = diff_ast(old_code=old_code, new_code=new_code, language=language)
     ```
   - Identify structural changes between versions
   - Analyze the impact of changes on code quality and behavior

## Results and Documentation

8. **Summarize Findings**
   - Create a structured summary of your analysis
   - Include key metrics, patterns, and potential issues
   - Highlight any code smells or optimization opportunities
   - Use `find_code_smells()` from the incarnation for automated detection

9. **Generate Documentation (if needed)**
   - Create documentation based on the AST/ASG analysis
   - Include diagrams of code structure and relationships
   - Document complex or critical sections in detail
   - Use `generate_documentation()` from the incarnation for automated generation

10. **Store Results in Neo4j**
    - Ensure all analysis results are properly stored in Neo4j
    - Add relationships between code elements and analysis results
    - Tag the analysis with appropriate metadata (timestamp, version, etc.)
    - Use `explore_code_structure()` to navigate the results

## Review and Verification

11. **Verify Analysis Results**
    - Check that the analysis correctly represents the code
    - Verify that all code elements are properly recognized
    - Confirm that complexity metrics are accurate
    - Test any generated documentation for accuracy

12. **Report Findings**
    - Create a final report summarizing your analysis
    - Include actionable recommendations
    - Provide links to stored analysis in Neo4j
    - Organize findings by priority and impact

## Log the Workflow Execution

13. **Record the execution of this workflow**
    - Use the following Cypher query to log this workflow:
    ```cypher
    MATCH (p:Project {id: $projectId})
    CREATE (w:WorkflowExecution {
      id: randomUUID(),
      timestamp: datetime(),
      summary: $summary,
      actionKeyword: 'CODE_ANALYZE'
    })
    CREATE (p)-[:HAS_WORKFLOW]->(w)
    WITH w
    UNWIND $filesAnalyzed AS file
    CREATE (f:File {path: file})
    CREATE (w)-[:ANALYZED]->(f)
    ```
    - Where:
      - `$projectId` is the ID of the current project
      - `$summary` is a brief summary of what was analyzed
      - `$filesAnalyzed` is an array of file paths that were analyzed
"

RETURN t.keyword, t.version, t.steps
