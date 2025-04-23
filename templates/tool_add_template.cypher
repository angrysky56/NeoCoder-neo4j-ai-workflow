// TOOL_ADD Template
// Provides guidance on adding new tools to the NeoCoder MCP server

// Create the TOOL_ADD template
MERGE (t:ActionTemplate {keyword: 'TOOL_ADD', version: '1.0'})
ON CREATE SET
  t.description = 'Process for adding new tool functionality to the NeoCoder MCP server',
  t.complexity = 'MEDIUM',
  t.estimatedEffort = 60,
  t.isCurrent = true,
  t.domain = 'development',
  t.steps = "# Adding New Tools to NeoCoder

This template guides you through adding a new tool to the NeoCoder MCP server.

## 1. Tool Definition & Requirements

-   Identify the purpose and functionality of the tool
-   Define the tool's parameters and return type
-   Determine if the tool requires a new module or fits within existing ones
-   Query Project README: `get_project(project_id=\"neocoder\")`
-   Review the existing MCP server architecture

## 2. Implementation Strategy

### Option A: Simple Tool Addition
If the tool fits within existing modules:

1. Identify the appropriate file to modify (`server.py` or specialized module)
2. Define the new method following the MCP tool pattern
3. Register the tool in the `_register_tools` method
4. Add tool description to the `get_tool_descriptions` method
5. Add tool patterns to the `suggest_tool` method

### Option B: Advanced Tool (New Module)
If the tool requires its own module:

1. Create a new Python module with appropriate class structure
2. Implement the MCP mixin pattern used in other modules
3. Update server.py to import and integrate the module
4. Register tools from the new module

## 3. Tool Method Implementation

-   Follow this pattern for implementing new tool methods:
```python
async def your_tool_name(
    self,
    param1: str = Field(..., description=\"Description of parameter 1\"),
    param2: Optional[int] = Field(None, description=\"Description of parameter 2\"),
) -> List[types.TextContent]:
    \"\"\"Tool description that appears in Claude's tool documentation.\"\"\"
    
    # Implementation logic here
    
    try:
        async with self.driver.session(database=self.database) as session:
            # Database operations (if needed)
            return [types.TextContent(type=\"text\", text=\"Tool response\")]
    except Exception as e:
        logger.error(f\"Error in your_tool_name: {e}\")
        return [types.TextContent(type=\"text\", text=f\"Error: {e}\")]
```

-   Implement proper error handling
-   Ensure consistent formatting of responses
-   Add appropriate logging

## 4. Integration

-   Register the new tool in the server's tool registry
-   Update the guidance hub to include information about the new tool
-   Add the tool to the README documentation
-   Ensure proper Neo4j schema updates if needed

## 5. !!! CRITICAL: Test Verification !!!

-   Create unit tests for the new tool
-   Test the tool with various inputs, including edge cases
-   Test integration with the rest of the MCP server
-   **ALL tests MUST pass before proceeding**
-   **If any test fails, STOP here and return to implementation. Do NOT proceed.**

## 6. Log Successful Execution (ONLY if Step 5 passed):

-   Use log_workflow_execution tool with parameters:
  - project_id: \"neocoder\"
  - keyword: 'TOOL_ADD'
  - description: Brief description of the new tool functionality
  - modified_files: List of file paths that were modified/created
  - execution_time_seconds: (Optional) Time taken to complete the workflow
  - test_results: (Optional) Summary of test results
-   Confirm successful creation of workflow execution node

## 7. Update Project Artifacts:

-   Update README.md with information about the new tool
-   Update the guidance hub description to include the new tool
-   Create usage examples for documentation

## 8. Example: Adding a Neo4j Schema Tool

Here's a simplified example of adding a schema management tool:

```python
# 1. Add the method to an appropriate class
async def get_schema_info(
    self,
    include_indexes: bool = Field(True, description=\"Include index information\"),
    include_constraints: bool = Field(True, description=\"Include constraint information\"),
) -> List[types.TextContent]:
    \"\"\"Get Neo4j database schema information including indexes and constraints.\"\"\"
    
    query = \"\"\"
    CALL apoc.meta.schema()
    RETURN *
    \"\"\"
    
    try:
        async with self.driver.session(database=self.database) as session:
            results_json = await session.execute_read(self._read_query, query, {})
            results = json.loads(results_json)
            
            # Format response
            text = \"# Neo4j Schema Information\\n\\n\"
            # ... format the schema information ...
            
            return [types.TextContent(type=\"text\", text=text)]
    except Exception as e:
        logger.error(f\"Error retrieving schema info: {e}\")
        return [types.TextContent(type=\"text\", text=f\"Error: {e}\")]

# 2. Register the tool
def _register_tools(self):
    # ... existing tool registrations ...
    self.mcp.add_tool(self.get_schema_info)
    
# 3. Add to tool descriptions
def get_tool_descriptions(self) -> dict:
    tools = {
        # ... existing tools ...
        \"get_schema_info\": \"Get Neo4j database schema including indexes and constraints\"
    }
    return tools
```

## 9. Final Integration Steps

1. Update `server.py` to register the new tool
2. Update `get_tool_descriptions` with description
3. Update AI Guidance Hub to include the new tool
4. Update the README documentation
"

ON MATCH SET
  t.isCurrent = true,
  t.version = '1.0'

// Create relationship to hub in a separate operation
WITH t
MATCH (hub:AiGuidanceHub {id: 'main_hub'})
MERGE (hub)-[:PROVIDES_TEMPLATE]->(t)

RETURN t.keyword + ' v' + t.version + ' template created successfully';