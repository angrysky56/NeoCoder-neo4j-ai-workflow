"""
Tool Proposal System for NeoCoder Neo4j AI Workflow

This module provides functionality for AI assistants to propose new tools
and for users to request new tool capabilities in the NeoCoder system.
"""

import json
import logging
import uuid
from typing import List, Optional, Dict, Any

import mcp.types as types
from .event_loop_manager import safe_neo4j_session
from pydantic import Field
from neo4j import AsyncManagedTransaction

logger = logging.getLogger("mcp_neocoder.tool_proposals")


class ToolProposalMixin:
    """Mixin class providing tool proposal functionality for the Neo4jWorkflowServer."""

    database: str  # Define the database attribute
    driver: Any

    async def _read_query(self, tx: AsyncManagedTransaction, query: str, params: dict) -> str:
        """Execute a read query and return results as JSON string."""
        raise NotImplementedError("_read_query must be implemented by the parent class")

    async def _write(self, tx: AsyncManagedTransaction, query: str, params: dict):
        """Execute a write query and return results as JSON string."""
        raise NotImplementedError("_write must be implemented by the parent class")

    async def propose_tool(
        self,
        name: str = Field(..., description="Proposed tool name"),
        description: str = Field(..., description="Description of the tool's functionality"),
        parameters: List[Dict[str, Any]] = Field(..., description="List of parameter definitions for the tool"),
        rationale: str = Field(..., description="Rationale for why this tool would be valuable"),
        implementation_notes: Optional[str] = Field(None, description="Optional technical notes for implementation"),
        example_usage: Optional[str] = Field(None, description="Optional example of how the tool would be used")
    ) -> List[types.TextContent]:
        """Propose a new tool for the NeoCoder system."""

        # Generate a proposal ID
        proposal_id = str(uuid.uuid4())

        # Organize parameters as a JSON string for storage
        parameters_json = json.dumps(parameters)

        # Build query for creating the proposal
        query = """
        CREATE (p:ToolProposal {
            id: $id,
            name: $name,
            description: $description,
            parameters: $parameters,
            rationale: $rationale,
            timestamp: datetime(),
            status: "Proposed"
        })
        """

        params = {
            "id": proposal_id,
            "name": name,
            "description": description,
            "parameters": parameters_json,
            "rationale": rationale
        }

        # Add optional fields if provided
        if implementation_notes:
            query = query.replace("status: \"Proposed\"", "status: \"Proposed\", implementationNotes: $implementationNotes")
            params["implementationNotes"] = implementation_notes

        if example_usage:
            query = query.replace("status: \"Proposed\"", "status: \"Proposed\", exampleUsage: $exampleUsage")
            params["exampleUsage"] = example_usage

        # Complete the query
        query += """
        WITH p
        MATCH (hub:AiGuidanceHub {id: 'main_hub'})
        CREATE (hub)-[:HAS_PROPOSAL]->(p)
        RETURN p.id AS id, p.name AS name
        """

        try:
            async with safe_neo4j_session(self.driver, self.database) as session:
                results_json = await session.execute_write(self._read_query, query, params)
                results = json.loads(results_json)

                if results and len(results) > 0:
                    text = "# Tool Proposal Submitted\n\n"
                    text += "Thank you for proposing a new tool. Your proposal has been recorded.\n\n"
                    text += f"**Proposal ID:** {proposal_id}\n"
                    text += f"**Tool Name:** {name}\n"
                    text += "**Status:** Proposed\n\n"
                    text += f"The proposal will be reviewed by the development team. You can check the status of your proposal using `get_tool_proposal(id=\"{proposal_id}\")`."

                    return [types.TextContent(type="text", text=text)]
                else:
                    return [types.TextContent(type="text", text="Error submitting tool proposal")]
        except Exception as e:
            logger.error(f"Error proposing tool: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]
    async def request_tool(
        self,
        description: str = Field(..., description="Description of the desired tool functionality"),
        use_case: str = Field(..., description="How you would use this tool"),
        priority: str = Field("MEDIUM", description="Priority of the request (LOW, MEDIUM, HIGH)"),
        requested_by: Optional[str] = Field(None, description="Name of the person requesting the tool")
    ) -> List[types.TextContent]:
        """Request a new tool feature for the NeoCoder system."""

        # Generate a request ID
        request_id = str(uuid.uuid4())

        # Build query for creating the tool request
        query = """
        CREATE (r:ToolRequest {
            id: $id,
            description: $description,
            useCase: $useCase,
            priority: $priority,
            timestamp: datetime(),
            status: "Submitted"
        })
        """

        params = {
            "id": request_id,
            "description": description,
            "useCase": use_case,
            "priority": priority
        }

        # Add requester name if provided
        if requested_by:
            query = query.replace("status: \"Submitted\"", "status: \"Submitted\", requestedBy: $requestedBy")
            params["requestedBy"] = requested_by

        # Complete the query
        query += """
        WITH r
        MATCH (hub:AiGuidanceHub {id: 'main_hub'})
        CREATE (hub)-[:HAS_REQUEST]->(r)
        RETURN r.id AS id, r.description AS description
        """

        try:
            async with safe_neo4j_session(self.driver, self.database) as session:
                results_json = await session.execute_write(self._read_query, query, params)
                results = json.loads(results_json)

                if results and len(results) > 0:
                    text = "# Tool Request Submitted\n\n"
                    text += "Thank you for requesting a new tool. Your request has been recorded.\n\n"
                    text += f"**Request ID:** {request_id}\n"
                    text += f"**Description:** {description}\n"
                    text += f"**Priority:** {priority}\n"
                    text += "**Status:** Submitted\n\n"
                    text += f"The request will be reviewed by the development team. You can check the status of your request using `get_tool_request(id=\"{request_id}\")`."

                    return [types.TextContent(type="text", text=text)]
                else:
                    return [types.TextContent(type="text", text="Error submitting tool request")]
        except Exception as e:
            logger.error(f"Error requesting tool: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def get_tool_proposal(
        self,
        id: str = Field(..., description="ID of the tool proposal to retrieve")
    ) -> List[types.TextContent]:
        """Get a specific tool proposal by ID."""
        query = """
        MATCH (p:ToolProposal {id: $id})
        RETURN p.id AS id,
               p.name AS name,
               p.description AS description,
               p.parameters AS parameters,
               p.rationale AS rationale,
               p.timestamp AS timestamp,
               p.status AS status,
               p.implementationNotes AS implementationNotes,
               p.exampleUsage AS exampleUsage
        """

        try:
            async with safe_neo4j_session(self.driver, self.database) as session:
                results_json = await session.execute_read(self._read_query, query, {"id": id})
                results = json.loads(results_json)

                if results and len(results) > 0:
                    proposal = results[0]

                    # Parse parameters from JSON
                    parameters = []
                    if proposal.get("parameters"):
                        try:
                            parameters = json.loads(proposal["parameters"])
                        except json.JSONDecodeError:
                            parameters = [{"error": "Could not parse parameters"}]

                    text = f"# Tool Proposal: {proposal.get('name', 'Unnamed')}\n\n"
                    text += f"**ID:** {proposal.get('id', id)}\n"
                    text += f"**Status:** {proposal.get('status', 'Unknown')}\n"
                    text += f"**Submitted:** {proposal.get('timestamp', 'Unknown')}\n\n"

                    text += f"## Description\n\n{proposal.get('description', 'No description')}\n\n"
                    text += f"## Rationale\n\n{proposal.get('rationale', 'No rationale provided')}\n\n"

                    text += "## Parameters\n\n"
                    if parameters:
                        for i, param in enumerate(parameters, 1):
                            text += f"### {i}. {param.get('name', 'Unnamed parameter')}\n"
                            text += f"- **Type:** {param.get('type', 'Not specified')}\n"
                            text += f"- **Description:** {param.get('description', 'No description')}\n"
                            text += f"- **Required:** {param.get('required', False)}\n\n"
                    else:
                        text += "No parameters defined.\n\n"

                    if proposal.get("exampleUsage"):
                        text += f"## Example Usage\n\n{proposal['exampleUsage']}\n\n"

                    if proposal.get("implementationNotes"):
                        text += f"## Implementation Notes\n\n{proposal['implementationNotes']}\n\n"

                    return [types.TextContent(type="text", text=text)]
                else:
                    return [types.TextContent(type="text", text=f"No tool proposal found with ID '{id}'")]
        except Exception as e:
            logger.error(f"Error retrieving tool proposal: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def get_tool_request(
        self,
        id: str = Field(..., description="ID of the tool request to retrieve")
    ) -> List[types.TextContent]:
        """Get a specific tool request by ID."""
        query = """
        MATCH (r:ToolRequest {id: $id})
        OPTIONAL MATCH (r)-[:IMPLEMENTED_AS]->(p:ToolProposal)
        RETURN r.id AS id,
               r.description AS description,
               r.useCase AS useCase,
               r.priority AS priority,
               r.timestamp AS timestamp,
               r.status AS status,
               r.requestedBy AS requestedBy,
               p.id AS proposalId,
               p.name AS proposalName
        """

        try:
            async with safe_neo4j_session(self.driver, self.database) as session:
                results_json = await session.execute_read(self._read_query, query, {"id": id})
                results = json.loads(results_json)

                if results and len(results) > 0:
                    request = results[0]

                    text = "# Tool Request\n\n"
                    text += f"**ID:** {request.get('id', id)}\n"
                    text += f"**Status:** {request.get('status', 'Unknown')}\n"
                    text += f"**Priority:** {request.get('priority', 'MEDIUM')}\n"
                    text += f"**Submitted:** {request.get('timestamp', 'Unknown')}\n"

                    if request.get("requestedBy"):
                        text += f"**Requested By:** {request['requestedBy']}\n"

                    text += f"\n## Description\n\n{request.get('description', 'No description')}\n\n"
                    text += f"## Use Case\n\n{request.get('useCase', 'No use case provided')}\n\n"

                    if request.get("proposalId"):
                        text += "## Implementation\n\n"
                        text += f"This request has been implemented as the tool proposal '{request.get('proposalName', 'Unnamed')}'.\n"
                        text += f"You can view the full proposal with `get_tool_proposal(id=\"{request['proposalId']}\")`\n"

                    return [types.TextContent(type="text", text=text)]
                else:
                    return [types.TextContent(type="text", text=f"No tool request found with ID '{id}'")]
        except Exception as e:
            logger.error(f"Error retrieving tool request: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def list_tool_proposals(
        self,
        status: Optional[str] = Field(None, description="Filter by status (Proposed, Approved, Implemented, Rejected)"),
        limit: int = Field(10, description="Maximum number of proposals to return")
    ) -> List[types.TextContent]:
        """List all tool proposals with optional filtering."""
        query = """
        MATCH (p:ToolProposal)
        WHERE 1=1
        """

        params: Dict[str, Any] = {"limit": limit}

        if status:
            query += " AND p.status = $status"
            params["status"] = status

        query += """
        RETURN p.id AS id,
               p.name AS name,
               p.description AS description,
               p.timestamp AS timestamp,
               p.status AS status
        ORDER BY p.timestamp DESC
        LIMIT $limit
        """

        try:
            async with safe_neo4j_session(self.driver, self.database) as session:
                results_json = await session.execute_read(self._read_query, query, params)
                results = json.loads(results_json)

                if results and len(results) > 0:
                    status_filter = f" ({status})" if status else ""

                    text = f"# Tool Proposals{status_filter}\n\n"
                    text += "| ID | Name | Status | Submitted | Description |\n"
                    text += "| -- | ---- | ------ | --------- | ----------- |\n"

                    for p in results:
                        text += f"| {p.get('id', 'N/A')[:8]}... | {p.get('name', 'Unnamed')} | {p.get('status', 'Unknown')} | {p.get('timestamp', 'Unknown')[:10]} | {p.get('description', 'No description')[:50]}... |\n"

                    text += "\nTo view full details of a proposal, use `get_tool_proposal(id=\"proposal-id\")`"

                    return [types.TextContent(type="text", text=text)]
                else:
                    status_msg = f" with status '{status}'" if status else ""
                    return [types.TextContent(type="text", text=f"No tool proposals found{status_msg}.")]
        except Exception as e:
            logger.error(f"Error listing tool proposals: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def list_tool_requests(
        self,
        status: Optional[str] = Field(None, description="Filter by status (Submitted, In Review, Implemented, Rejected)"),
        priority: Optional[str] = Field(None, description="Filter by priority (LOW, MEDIUM, HIGH)"),
        limit: int = Field(10, description="Maximum number of requests to return")
    ) -> List[types.TextContent]:
        """List all tool requests with optional filtering."""
        query = """
        MATCH (r:ToolRequest)
        WHERE 1=1
        """

        params: Dict[str, Any] = {"limit": limit}

        if status:
            query += " AND r.status = $status"
            params["status"] = status

        if priority:
            query += " AND r.priority = $priority"
            params["priority"] = priority

        query += """
        RETURN r.id AS id,
               r.description AS description,
               r.priority AS priority,
               r.timestamp AS timestamp,
               r.status AS status,
               r.requestedBy AS requestedBy
        ORDER BY
            CASE r.priority
                WHEN 'HIGH' THEN 1
                WHEN 'MEDIUM' THEN 2
                WHEN 'LOW' THEN 3
                ELSE 4
            END,
            r.timestamp DESC
        LIMIT $limit
        """

        try:
            async with safe_neo4j_session(self.driver, self.database) as session:
                results_json = await session.execute_read(self._read_query, query, params)
                results = json.loads(results_json)

                if results and len(results) > 0:
                    filters = []
                    if status:
                        filters.append(f"Status: {status}")
                    if priority:
                        filters.append(f"Priority: {priority}")

                    filter_text = f" ({', '.join(filters)})" if filters else ""

                    text = f"# Tool Requests{filter_text}\n\n"
                    text += "| ID | Priority | Status | Submitted | Description |\n"
                    text += "| -- | -------- | ------ | --------- | ----------- |\n"

                    for r in results:
                        text += f"| {r.get('id', 'N/A')[:8]}... | {r.get('priority', 'MEDIUM')} | {r.get('status', 'Unknown')} | {r.get('timestamp', 'Unknown')[:10]} | {r.get('description', 'No description')[:50]}... |\n"

                    text += "\nTo view full details of a request, use `get_tool_request(id=\"request-id\")`"

                    return [types.TextContent(type="text", text=text)]
                else:
                    filters = []
                    if status:
                        filters.append(f"status '{status}'")
                    if priority:
                        filters.append(f"priority '{priority}'")

                    filter_text = f" with {' and '.join(filters)}" if filters else ""
                    return [types.TextContent(type="text", text=f"No tool requests found{filter_text}.")]
        except Exception as e:
            logger.error(f"Error listing tool requests: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]
