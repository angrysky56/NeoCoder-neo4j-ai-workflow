"""
Decision Support System Incarnation

This module implements the Decision Support System incarnation of the NeoCoder framework,
providing tools for tracking decisions, alternatives, metrics, and evidence.
"""

import json
import logging
import uuid
from typing import Dict, Any, List, Optional

import mcp.types as types
from pydantic import Field
from neo4j import AsyncDriver, AsyncTransaction

from .base_incarnation import BaseIncarnation

logger = logging.getLogger("mcp_neocoder.decision_incarnation")


class DecisionIncarnation(BaseIncarnation):
    """Decision Support System incarnation of the NeoCoder framework.

    Provides tools for tracking decisions, alternatives, metrics, and evidence
    to support transparent, data-driven decision-making processes.
    """

    # Define name as a string identifier
    name = "decision_support"
    description = "Decision Support System for data-driven decision making"
    version = "0.1.0"

    # Explicitly define which methods should be registered as tools
    _tool_methods = [
        "create_decision",
        "list_decisions",
        "get_decision",
        "add_alternative",
        "add_metric",
        "add_evidence"
    ]

    def __init__(self, driver: AsyncDriver, database: str = "neo4j"):
        """Initialize the decision support incarnation."""
        self.driver = driver
        self.database = database
        # Call base class __init__ which will register tools
        super().__init__(driver, database)

    async def _read_query(self, tx: AsyncTransaction, query: str, params: dict) -> str:
        """Execute a read query and return results as JSON string."""
        raw_results = await tx.run(query, params)
        eager_results = await raw_results.to_eager_result()
        return json.dumps([r.data() for r in eager_results.records], default=str)

    async def _write(self, tx: AsyncTransaction, query: str, params: dict):
        """Execute a write query and return results as JSON string."""
        result = await tx.run(query, params or {})
        summary = await result.consume()
        return summary

    async def initialize_schema(self):
        """Initialize the Neo4j schema for decision support system."""
        # Define constraints and indexes for decision schema
        schema_query = """
        // Create constraints for unique IDs
        CREATE CONSTRAINT decision_id IF NOT EXISTS FOR (d:Decision) REQUIRE d.id IS UNIQUE;
        CREATE CONSTRAINT alternative_id IF NOT EXISTS FOR (a:Alternative) REQUIRE a.id IS UNIQUE;
        CREATE CONSTRAINT metric_id IF NOT EXISTS FOR (m:Metric) REQUIRE m.id IS UNIQUE;
        CREATE CONSTRAINT evidence_id IF NOT EXISTS FOR (e:Evidence) REQUIRE e.id IS UNIQUE;

        // Create indexes for performance
        CREATE INDEX decision_status IF NOT EXISTS FOR (d:Decision) ON (d.status);
        CREATE INDEX alternative_name IF NOT EXISTS FOR (a:Alternative) ON (a.name);
        """

        try:
            async with self.driver.session(database=self.database) as session:
                await session.execute_write(lambda tx: tx.run(schema_query))

                # Create base guidance hub for decisions if it doesn't exist
                await self.ensure_decision_hub_exists()

            logger.info("Decision support schema initialized")
        except Exception as e:
            logger.error(f"Error initializing decision schema: {e}")
            raise

    async def ensure_decision_hub_exists(self):
        """Create the decision guidance hub if it doesn't exist."""
        query = """
        MERGE (hub:AiGuidanceHub {id: 'decision_hub'})
        ON CREATE SET hub.description = $description
        RETURN hub
        """

        description = """
# Decision Support System

Welcome to the decision_incarnation powered by the NeoCoder framework.
This Decision Support System helps you make better decisions with the following capabilities:

## Key Features

1. **Decision Tracking**
   - Create and document decisions
   - Track decision status and timeline
   - Link related decisions

2. **Alternative Analysis**
   - Define and compare alternatives
   - Assign expected values and confidence intervals
   - Calculate utility scores

3. **Evidence Management**
   - Attach supporting evidence to alternatives
   - Calculate Bayesian probability updates
   - Track evidence provenance

4. **Stakeholder Input**
   - Record stakeholder preferences
   - Weigh inputs based on expertise
   - Track consensus building

## Getting Started

- Use `create_decision()` to define a new decision to be made
- Add alternatives with `add_alternative()`
- Define metrics for comparison with `add_metric()`
- Record evidence using `add_evidence()`
- Compare alternatives with `compare_alternatives()`

Each decision maintains a complete audit trail of all inputs, evidence, and reasoning.
        """

        params = {"description": description}

        async with self.driver.session(database=self.database) as session:
            await session.execute_write(lambda tx: tx.run(query, params))

    async def register_tools(self, server):
        """Register decision incarnation-specific tools with the server."""
        server.mcp.add_tool(self.create_decision)
        server.mcp.add_tool(self.list_decisions)
        server.mcp.add_tool(self.get_decision)
        server.mcp.add_tool(self.add_alternative)
        server.mcp.add_tool(self.add_metric)
        server.mcp.add_tool(self.add_evidence)

        logger.info("Decision support tools registered")

    async def get_guidance_hub(self):
        """Get the guidance hub for decision incarnation."""
        query = """
        MATCH (hub:AiGuidanceHub {id: 'decision_hub'})
        RETURN hub.description AS description
        """

        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_read(self._read_query, query, {})
                results = json.loads(results_json)

                if results and len(results) > 0:
                    return [types.TextContent(type="text", text=results[0]["description"])]
                else:
                    # If hub doesn't exist, create it
                    await self.ensure_decision_hub_exists()
                    # Try again
                    return await self.get_guidance_hub()
        except Exception as e:
            logger.error(f"Error retrieving decision guidance hub: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def create_decision(
        self,
        title: str = Field(..., description="Title of the decision to be made"),
        description: str = Field(..., description="Description of the decision context and goals"),
        deadline: Optional[str] = Field(None, description="Optional deadline for the decision (YYYY-MM-DD)"),
        stakeholders: Optional[List[str]] = Field(None, description="List of stakeholders involved"),
        tags: Optional[List[str]] = Field(None, description="Tags for categorizing the decision")
    ) -> List[types.TextContent]:
        """Create a new decision in the decision support system."""
        decision_id = str(uuid.uuid4())
        decision_tags = tags or []
        decision_stakeholders = stakeholders or []

        query = """
        CREATE (d:Decision {
            id: $id,
            title: $title,
            description: $description,
            created_at: datetime(),
            status: 'Open',
            tags: $tags,
            stakeholders: $stakeholders
        })
        """

        params = {
            "id": decision_id,
            "title": title,
            "description": description,
            "tags": decision_tags,
            "stakeholders": decision_stakeholders
        }

        if deadline:
            query = query.replace("stakeholders: $stakeholders", "stakeholders: $stakeholders, deadline: $deadline")
            params["deadline"] = deadline

        query += """
        WITH d
        MATCH (hub:AiGuidanceHub {id: 'decision_hub'})
        CREATE (hub)-[:CONTAINS]->(d)
        RETURN d.id AS id, d.title AS title
        """

        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_write(self._read_query, query, params)
                results = json.loads(results_json)

                if results and len(results) > 0:
                    text_response = "# Decision Created\n\n"
                    text_response += f"**ID:** {decision_id}\n"
                    text_response += f"**Title:** {title}\n"
                    text_response += f"**Status:** Open\n\n"
                    text_response += f"**Description:** {description}\n\n"

                    if deadline:
                        text_response += f"**Deadline:** {deadline}\n\n"

                    if stakeholders:
                        text_response += f"**Stakeholders:** {', '.join(stakeholders)}\n\n"

                    if tags:
                        text_response += f"**Tags:** {', '.join(tags)}\n\n"

                    text_response += "You can now add alternatives using `add_alternative(decision_id=\"" + decision_id + "\", name=\"...\", description=\"...\")`"

                    return [types.TextContent(type="text", text=text_response)]
                else:
                    return [types.TextContent(type="text", text="Error creating decision")]
        except Exception as e:
            logger.error(f"Error creating decision: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def list_decisions(
        self,
        status: Optional[str] = Field(None, description="Filter by status (Open, In Progress, Decided)"),
        tag: Optional[str] = Field(None, description="Filter by tag"),
        limit: int = Field(10, description="Maximum number of decisions to return")
    ) -> List[types.TextContent]:
        """List decisions with optional filtering."""
        query = """
        MATCH (d:Decision)
        WHERE 1=1
        """

        params = {"limit": limit}

        if status:
            query += " AND d.status = $status"
            params["status"] = status

        if tag:
            query += " AND $tag IN d.tags"
            params["tag"] = tag

        query += """
        OPTIONAL MATCH (d)<-[:FOR_DECISION]-(a:Alternative)
        WITH d, count(a) as alternative_count
        RETURN d.id AS id,
               d.title AS title,
               d.description AS description,
               d.status AS status,
               d.created_at AS created_at,
               d.deadline AS deadline,
               d.tags AS tags,
               alternative_count
        ORDER BY d.created_at DESC
        LIMIT $limit
        """

        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_read(self._read_query, query, params)
                results = json.loads(results_json)

                if results and len(results) > 0:
                    text_response = "# Decisions\n\n"

                    if status:
                        text_response += f"**Status:** {status}\n\n"
                    if tag:
                        text_response += f"**Tag:** {tag}\n\n"

                    text_response += "| ID | Title | Status | Alternatives | Deadline |\n"
                    text_response += "| -- | ----- | ------ | ------------ | -------- |\n"

                    for d in results:
                        deadline = d.get('deadline', '-')
                        title = d.get('title', 'Untitled')[:30]
                        if len(d.get('title', '')) > 30:
                            title += "..."

                        text_response += f"| {d.get('id', 'unknown')} | {title} | {d.get('status', 'Unknown')} | {d.get('alternative_count', 0)} | {deadline} |\n"

                    text_response += "\nTo view full details of a decision, use `get_decision(id=\"decision-id\")`"

                    return [types.TextContent(type="text", text=text_response)]
                else:
                    filter_msg = ""
                    if status:
                        filter_msg += f" with status '{status}'"
                    if tag:
                        if filter_msg:
                            filter_msg += " and"
                        filter_msg += f" tagged as '{tag}'"

                    if filter_msg:
                        return [types.TextContent(type="text", text=f"No decisions found{filter_msg}.")]
                    else:
                        return [types.TextContent(type="text", text="No decisions found in the database.")]
        except Exception as e:
            logger.error(f"Error listing decisions: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def get_decision(
        self,
        id: str = Field(..., description="ID of the decision to retrieve")
    ) -> List[types.TextContent]:
        """Get detailed information about a specific decision."""
        query = """
        MATCH (d:Decision {id: $id})
        OPTIONAL MATCH (d)<-[:FOR_DECISION]-(a:Alternative)
        OPTIONAL MATCH (d)<-[:FOR_DECISION]-(m:Metric)
        WITH d, count(DISTINCT a) as alternative_count, count(DISTINCT m) as metric_count
        RETURN d.id AS id,
               d.title AS title,
               d.description AS description,
               d.status AS status,
               d.created_at AS created_at,
               d.deadline AS deadline,
               d.stakeholders AS stakeholders,
               d.tags AS tags,
               alternative_count,
               metric_count
        """

        params = {"id": id}

        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_read(self._read_query, query, params)
                results = json.loads(results_json)

                if results and len(results) > 0:
                    d = results[0]

                    text_response = f"# Decision: {d.get('title', 'Untitled')}\n\n"
                    text_response += f"**ID:** {d.get('id', id)}\n"
                    text_response += f"**Status:** {d.get('status', 'Unknown')}\n"
                    text_response += f"**Created:** {d.get('created_at', 'Unknown')}\n"

                    if d.get('deadline'):
                        text_response += f"**Deadline:** {d.get('deadline')}\n"

                    if d.get('stakeholders'):
                        text_response += f"**Stakeholders:** {', '.join(d.get('stakeholders', []))}\n"

                    if d.get('tags'):
                        text_response += f"**Tags:** {', '.join(d.get('tags', []))}\n"

                    text_response += f"\n## Description\n\n{d.get('description', 'No description')}\n\n"

                    text_response += f"## Summary\n\n"
                    text_response += f"This decision has {d.get('alternative_count', 0)} alternatives "
                    text_response += f"and {d.get('metric_count', 0)} evaluation metrics.\n\n"

                    if d.get('alternative_count', 0) > 0:
                        text_response += "Use `list_alternatives(decision_id=\"" + id + "\")` to view alternatives.\n"
                    else:
                        text_response += "Add alternatives using `add_alternative(decision_id=\"" + id + "\", name=\"...\", description=\"...\").\n"

                    if d.get('metric_count', 0) > 0:
                        text_response += "Use `list_metrics(decision_id=\"" + id + "\")` to view metrics.\n"
                    else:
                        text_response += "Add metrics using `add_metric(decision_id=\"" + id + "\", name=\"...\", description=\"...\").\n"

                    return [types.TextContent(type="text", text=text_response)]
                else:
                    return [types.TextContent(type="text", text=f"No decision found with ID '{id}'")]
        except Exception as e:
            logger.error(f"Error retrieving decision: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def add_alternative(
        self,
        decision_id: str = Field(..., description="ID of the decision"),
        name: str = Field(..., description="Name of the alternative"),
        description: str = Field(..., description="Description of the alternative"),
        expected_value: Optional[float] = Field(None, description="Initial expected value assessment"),
        confidence: Optional[float] = Field(None, description="Confidence in the expected value (0-1)"),
        pros: Optional[List[str]] = Field(None, description="List of pros for this alternative"),
        cons: Optional[List[str]] = Field(None, description="List of cons for this alternative")
    ) -> List[types.TextContent]:
        """Add an alternative to a decision."""
        alternative_id = str(uuid.uuid4())
        alternative_pros = pros or []
        alternative_cons = cons or []

        query = """
        MATCH (d:Decision {id: $decision_id})
        CREATE (a:Alternative {
            id: $id,
            name: $name,
            description: $description,
            created_at: datetime(),
            pros: $pros,
            cons: $cons
        })
        CREATE (a)-[:FOR_DECISION]->(d)
        """

        params = {
            "id": alternative_id,
            "decision_id": decision_id,
            "name": name,
            "description": description,
            "pros": alternative_pros,
            "cons": alternative_cons
        }

        if expected_value is not None:
            query = query.replace("cons: $cons", "cons: $cons, expected_value: $expected_value")
            params["expected_value"] = expected_value

        if confidence is not None:
            query = query.replace("cons: $cons", "cons: $cons, confidence: $confidence")
            params["confidence"] = confidence

        query += """
        WITH a, d
        SET d.status = CASE WHEN d.status = 'Open' THEN 'In Progress' ELSE d.status END
        RETURN a.id AS id, a.name AS name, d.title AS decision_title
        """

        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_write(self._read_query, query, params)
                results = json.loads(results_json)

                if results and len(results) > 0:
                    text_response = "# Alternative Added\n\n"
                    text_response += f"**ID:** {alternative_id}\n"
                    text_response += f"**Name:** {name}\n"
                    text_response += f"**For Decision:** {results[0].get('decision_title', decision_id)}\n\n"

                    text_response += f"**Description:** {description}\n\n"

                    if expected_value is not None:
                        text_response += f"**Expected Value:** {expected_value}\n"

                    if confidence is not None:
                        text_response += f"**Confidence:** {confidence}\n"

                    if pros:
                        text_response += "\n## Pros\n\n"
                        for i, pro in enumerate(pros, 1):
                            text_response += f"{i}. {pro}\n"

                    if cons:
                        text_response += "\n## Cons\n\n"
                        for i, con in enumerate(cons, 1):
                            text_response += f"{i}. {con}\n"

                    text_response += "\nYou can now add evidence using `add_evidence(alternative_id=\"" + alternative_id + "\", content=\"...\", impact=\"...\")`"

                    return [types.TextContent(type="text", text=text_response)]
                else:
                    return [types.TextContent(type="text", text=f"Error adding alternative. Check if decision ID {decision_id} exists.")]
        except Exception as e:
            logger.error(f"Error adding alternative: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def add_metric(
        self,
        decision_id: str = Field(..., description="ID of the decision"),
        name: str = Field(..., description="Name of the metric"),
        description: str = Field(..., description="Description of what the metric measures"),
        weight: float = Field(1.0, description="Weight of this metric in decision-making (0-10)"),
        target_direction: str = Field("maximize", description="Whether to maximize or minimize this metric"),
        scale: Optional[str] = Field(None, description="Scale of measurement (e.g., 'monetary', 'percentage', 'rating')"),
        unit: Optional[str] = Field(None, description="Unit of measurement (e.g., '$', '%', '1-5')")
    ) -> List[types.TextContent]:
        """Add an evaluation metric to a decision."""
        metric_id = str(uuid.uuid4())

        query = """
        MATCH (d:Decision {id: $decision_id})
        CREATE (m:Metric {
            id: $id,
            name: $name,
            description: $description,
            weight: $weight,
            target_direction: $target_direction,
            created_at: datetime()
        })
        CREATE (m)-[:FOR_DECISION]->(d)
        """

        params = {
            "id": metric_id,
            "decision_id": decision_id,
            "name": name,
            "description": description,
            "weight": weight,
            "target_direction": target_direction
        }

        if scale:
            query = query.replace("created_at: datetime()", "created_at: datetime(), scale: $scale")
            params["scale"] = scale

        if unit:
            query = query.replace("created_at: datetime()", "created_at: datetime(), unit: $unit")
            params["unit"] = unit

        query += """
        RETURN m.id AS id, m.name AS name, d.title AS decision_title
        """

        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_write(self._read_query, query, params)
                results = json.loads(results_json)

                if results and len(results) > 0:
                    text_response = "# Metric Added\n\n"
                    text_response += f"**ID:** {metric_id}\n"
                    text_response += f"**Name:** {name}\n"
                    text_response += f"**For Decision:** {results[0].get('decision_title', decision_id)}\n\n"

                    text_response += f"**Description:** {description}\n\n"

                    text_response += f"**Weight:** {weight}\n"
                    text_response += f"**Target:** {target_direction.capitalize()}\n"

                    if scale:
                        text_response += f"**Scale:** {scale}\n"

                    if unit:
                        text_response += f"**Unit:** {unit}\n"

                    text_response += "\nYou can now rate alternatives on this metric using `rate_alternative(metric_id=\"" + metric_id + "\", alternative_id=\"...\", value=\"...\")`"

                    return [types.TextContent(type="text", text=text_response)]
                else:
                    return [types.TextContent(type="text", text=f"Error adding metric. Check if decision ID {decision_id} exists.")]
        except Exception as e:
            logger.error(f"Error adding metric: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def add_evidence(
        self,
        alternative_id: str = Field(..., description="ID of the alternative"),
        content: str = Field(..., description="Evidence content"),
        impact: str = Field(..., description="Whether this evidence supports or contradicts the alternative (supports, contradicts, neutral)"),
        strength: Optional[float] = Field(None, description="Strength of the evidence (0-1)"),
        source: Optional[str] = Field(None, description="Source of the evidence"),
        metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata about the evidence")
    ) -> List[types.TextContent]:
        """Add evidence for or against an alternative."""
        evidence_id = str(uuid.uuid4())

        query = """
        MATCH (a:Alternative {id: $alternative_id})
        CREATE (e:Evidence {
            id: $id,
            content: $content,
            impact: $impact,
            created_at: datetime()
        })
        CREATE (e)-[:FOR_ALTERNATIVE]->(a)
        """

        params = {
            "id": evidence_id,
            "alternative_id": alternative_id,
            "content": content,
            "impact": impact
        }

        if strength is not None:
            query = query.replace("created_at: datetime()", "created_at: datetime(), strength: $strength")
            params["strength"] = strength

        if source:
            query = query.replace("created_at: datetime()", "created_at: datetime(), source: $source")
            params["source"] = source

        if metadata:
            metadata_json = json.dumps(metadata)
            query = query.replace("created_at: datetime()", "created_at: datetime(), metadata: $metadata")
            params["metadata"] = metadata_json

        # Update alternative's expected value if strength is provided
        if strength is not None and impact in ["supports", "contradicts"]:
            query += """
            WITH e, a
            MATCH (a)-[:FOR_DECISION]->(d:Decision)

            // Update the expected value based on new evidence
            SET a.expected_value = CASE
                WHEN a.expected_value IS NULL THEN CASE
                    WHEN $impact = 'supports' THEN $strength
                    WHEN $impact = 'contradicts' THEN 1 - $strength
                    ELSE 0.5
                END
                ELSE CASE
                    WHEN $impact = 'supports' THEN a.expected_value + (1 - a.expected_value) * $strength * 0.1
                    WHEN $impact = 'contradicts' THEN a.expected_value * (1 - $strength * 0.1)
                    ELSE a.expected_value
                END
            END

            RETURN e.id AS id, e.content AS content, a.name AS alternative_name, d.title AS decision_title
            """
        else:
            query += """
            WITH e, a
            MATCH (a)-[:FOR_DECISION]->(d:Decision)
            RETURN e.id AS id, e.content AS content, a.name AS alternative_name, d.title AS decision_title
            """

        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_write(self._read_query, query, params)
                results = json.loads(results_json)

                if results and len(results) > 0:
                    result = results[0]

                    text_response = "# Evidence Added\n\n"
                    text_response += f"**ID:** {evidence_id}\n"
                    text_response += f"**For Alternative:** {result.get('alternative_name', alternative_id)}\n"
                    text_response += f"**For Decision:** {result.get('decision_title', 'Unknown')}\n\n"

                    text_response += f"**Impact:** {impact.capitalize()}\n"

                    if strength is not None:
                        text_response += f"**Strength:** {strength}\n"

                    if source:
                        text_response += f"**Source:** {source}\n"

                    text_response += f"\n**Content:**\n{content}\n"

                    if metadata:
                        text_response += "\n**Metadata:**\n"
                        for key, value in metadata.items():
                            text_response += f"- **{key}:** {value}\n"

                    return [types.TextContent(type="text", text=text_response)]
                else:
                    return [types.TextContent(type="text", text=f"Error adding evidence. Check if alternative ID {alternative_id} exists.")]
        except Exception as e:
            logger.error(f"Error adding evidence: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]
