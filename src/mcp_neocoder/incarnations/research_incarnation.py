"""
Research Orchestration Platform Incarnation

This module implements the Research Orchestration Platform incarnation of the NeoCoder framework,
providing tools for scientific workflow management, hypothesis tracking, experiment design,
and results publication.
"""

import json
import logging
import uuid
import datetime
from typing import Dict, Any, List, Optional, Union

import mcp.types as types
from pydantic import Field
from neo4j import AsyncDriver, AsyncTransaction, AsyncManagedTransaction

from .base_incarnation import BaseIncarnation

logger = logging.getLogger("mcp_neocoder.research_incarnation")


class ResearchIncarnation(BaseIncarnation):
    """Research Orchestration Platform incarnation of the NeoCoder framework.

    Provides tools for scientific workflow management, hypothesis tracking,
    experiment design, and results publication.
    """

    # Define name as a string identifier
    name = "research_orchestration"
    description = "Research Orchestration Platform for scientific workflows"
    version = "0.1.0"

    # Explicitly define which methods should be registered as tools
    _tool_methods = [
        "register_hypothesis",
        "list_hypotheses",
        "get_hypothesis",
        "update_hypothesis",
        "create_protocol",
        "list_protocols",
        "get_protocol",
        "create_experiment",
        "list_experiments",
        "get_experiment",
        "update_experiment",
        "record_observation",
        "list_observations",
        "compute_statistics",
        "create_publication_draft"
    ]

    def __init__(self, driver: AsyncDriver, database: str = "neo4j"):
        """Initialize the research incarnation."""
        self.driver = driver
        self.database = database
        # Call base class __init__ which will register all tools
        super().__init__(driver, database)

    # No need to manually register tools anymore - the tool registry will discover them automatically

    from typing import LiteralString

    async def _read_query(self, tx: Union["AsyncTransaction", "AsyncManagedTransaction"], query, params: dict) -> str:
        """Execute a read query and return results as JSON string."""
        raw_results = await tx.run(query, params)
        eager_results = await raw_results.to_eager_result()
        return json.dumps([r.data() for r in eager_results.records], default=str)

    async def _write(self, tx, query: LiteralString, params: dict):
        """Execute a write query and return results as JSON string."""
        result = await tx.run(query, params or {})
        summary = await result.consume()
        return summary
    async def initialize_schema(self):
        """Initialize the Neo4j schema for research orchestration."""
        # Define constraints and indexes for research schema
        # Define constraints and indexes for research schema
        # Neo4j 4.x/5.x constraint syntax: CREATE CONSTRAINT name IF NOT EXISTS FOR (n:Label) REQUIRE n.prop IS UNIQUE
        schema_queries = [
            "CREATE CONSTRAINT research_hypothesis_id IF NOT EXISTS FOR (h:Hypothesis) REQUIRE h.id IS UNIQUE",
            "CREATE CONSTRAINT research_experiment_id IF NOT EXISTS FOR (e:Experiment) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT research_protocol_id IF NOT EXISTS FOR (p:Protocol) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT research_observation_id IF NOT EXISTS FOR (o:Observation) REQUIRE o.id IS UNIQUE",
            "CREATE CONSTRAINT research_run_id IF NOT EXISTS FOR (r:Run) REQUIRE r.id IS UNIQUE",

            "CREATE INDEX research_hypothesis_status IF NOT EXISTS FOR (h:Hypothesis) ON (h.status)",
            "CREATE INDEX research_experiment_status IF NOT EXISTS FOR (e:Experiment) ON (e.status)",
            "CREATE INDEX research_protocol_name IF NOT EXISTS FOR (p:Protocol) ON (p.name)"
        ]

        try:
            async with self.driver.session(database=self.database) as session:
                # Execute each constraint/index query individually
                for query in schema_queries:
                    await session.execute_write(lambda tx, query: tx.run(query), query)

                # Create base guidance hub for research if it doesn't exist
                await self.ensure_research_hub_exists()

            logger.info("Research incarnation schema initialized")
        except Exception as e:
            logger.error(f"Error initializing research schema: {e}")
            raise

    async def ensure_research_hub_exists(self):
        """Create the research guidance hub if it doesn't exist."""
        query = """
        MERGE (hub:AiGuidanceHub {id: 'research_hub'})
        ON CREATE SET hub.description = $description
        RETURN hub
        """

        description = """
# Research Orchestration Platform

Welcome to the Research Orchestration Platform powered by the NeoCoder framework.
This system helps you manage scientific workflows with the following capabilities:

## Key Features

1. **Hypothesis Management**
   - Register and track hypotheses
   - Link supporting evidence
   - Calculate Bayesian belief updates

2. **Experiment Design**
   - Create standardized protocols
   - Define expected observations
   - Set success criteria

3. **Data Collection**
   - Record experimental runs
   - Capture raw observations
   - Link to external data sources

4. **Analysis & Publication**
   - Compute statistics on results
   - Generate figures and tables
   - Prepare publication drafts

## Getting Started

- Use `register_hypothesis()` to create a new research hypothesis
- Design experiments with `create_protocol()`
- Record observations using `record_observation()`
- Analyze results with `compute_statistics()`

Each entity in the system has provenance tracking, ensuring reproducibility and transparency.
        """

        params = {"description": description}

        async with self.driver.session(database=self.database) as session:
            await session.execute_write(lambda tx: tx.run(query, params))

    async def get_guidance_hub(self):
        """Get the guidance hub for research incarnation."""
        query = """
        MATCH (hub:AiGuidanceHub {id: 'research_hub'})
        RETURN hub.description AS description
        """

        try:
            async with self.driver.session(database=self.database) as session:
                async def read_query(tx):
                    return await self._read_query(tx, query, {})

                results_json = await session.execute_read(read_query)
                results = json.loads(results_json)

                if results and results[0]:
                    return [types.TextContent(type="text", text=results[0]["description"])]
                else:
                    # If hub doesn't exist, create it
                    await self.ensure_research_hub_exists()
                    # Try again
                    return await self.get_guidance_hub()
        except Exception as e:
            logger.error(f"Error retrieving research guidance hub: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def register_hypothesis(
        self,
        text: str = Field(..., description="The hypothesis statement"),
        description: Optional[str] = Field(None, description="Detailed description and context"),
        prior_probability: float = Field(0.5, description="Prior probability (0-1) of the hypothesis being true"),
        tags: Optional[List[str]] = Field(None, description="Tags for categorizing the hypothesis")
    ) -> List[types.TextContent]:
        """Register a new scientific hypothesis in the knowledge graph."""
        hypothesis_id = str(uuid.uuid4())
        hypothesis_tags = tags or []

        query = """
        CREATE (h:Hypothesis {
            id: $id,
            text: $text,
            status: 'Active',
            created_at: datetime(),
            prior_probability: $prior_probability,
            current_probability: $prior_probability,
            tags: $tags
        })
        """

        params = {
            "id": hypothesis_id,
            "text": text,
            "prior_probability": prior_probability,
            "tags": hypothesis_tags
        }

        if description:
            query = query.replace("tags: $tags", "tags: $tags, description: $description")
            params["description"] = description

        query += """
        WITH h
        MATCH (hub:AiGuidanceHub {id: 'research_hub'})
        CREATE (hub)-[:CONTAINS]->(h)
        RETURN h.id AS id, h.text AS text
        """

        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_write(lambda tx: self._read_query(tx, query, params))
                results = json.loads(results_json)

                if results and len(results) > 0:
                    text_response = "# Hypothesis Registered\n\n"
                    text_response += f"**ID:** {hypothesis_id}\n\n"
                    text_response += f"**Statement:** {text}\n\n"
                    text_response += f"**Prior Probability:** {prior_probability}\n\n"

                    if description:
                        text_response += f"**Description:** {description}\n\n"

                    if hypothesis_tags:
                        text_response += f"**Tags:** {', '.join(hypothesis_tags)}\n\n"

                    text_response += "You can now create experiments to test this hypothesis using `create_protocol()`."

                    return [types.TextContent(type="text", text=text_response)]
                else:
                    return [types.TextContent(type="text", text="Error registering hypothesis")]
        except Exception as e:
            logger.error(f"Error registering hypothesis: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def list_hypotheses(
        self,
        status: Optional[str] = Field(None, description="Filter by status (Active, Confirmed, Rejected)"),
        tag: Optional[str] = Field(None, description="Filter by tag"),
        limit: int = Field(10, description="Maximum number of hypotheses to return")
    ) -> List[types.TextContent]:
        """List scientific hypotheses with optional filtering."""
        query = """
        MATCH (h:Hypothesis)
        WHERE 1=1
        """

        params: Dict[str, Any] = {"limit": limit}

        if status:
            query += " AND h.status = $status"
            params["status"] = status

        if tag:
            query += " AND $tag IN h.tags"
            params["tag"] = tag

        query += """
        RETURN h.id AS id,
               h.text AS text,
               h.status AS status,
               h.created_at AS created_at,
               h.prior_probability AS prior_probability,
               h.current_probability AS current_probability,
               h.tags AS tags
        ORDER BY h.created_at DESC
        LIMIT $limit
        """

        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_read(self._read_query, query, params)
                results = json.loads(results_json)

                if results and len(results) > 0:
                    text_response = "# Hypotheses\n\n"

                    if status:
                        text_response += f"**Status:** {status}\n\n"
                    if tag:
                        text_response += f"**Tag:** {tag}\n\n"

                    text_response += "| ID | Hypothesis | Status | Current Probability | Tags |\n"
                    text_response += "| -- | ---------- | ------ | ------------------- | ---- |\n"

                    for h in results:
                        tags_str = ", ".join(h.get("tags", [])) if h.get("tags") else "-"
                        hypothesis_text = h.get("text", "Unknown")[:50]
                        if len(h.get("text", "")) > 50:
                            hypothesis_text += "..."

                        text_response += f"| {h.get('id', 'unknown')} | {hypothesis_text} | {h.get('status', 'Unknown')} | {h.get('current_probability', 'Unknown')} | {tags_str} |\n"

                    text_response += "\nTo view full details of a hypothesis, use `get_hypothesis(id=\"hypothesis-id\")`"

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
                        return [types.TextContent(type="text", text=f"No hypotheses found{filter_msg}.")]
                    else:
                        return [types.TextContent(type="text", text="No hypotheses found in the database.")]
        except Exception as e:
            logger.error(f"Error listing hypotheses: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def get_hypothesis(
        self,
        id: str = Field(..., description="ID of the hypothesis to retrieve")
    ) -> List[types.TextContent]:
        """Get detailed information about a specific hypothesis."""
        query = """
        MATCH (h:Hypothesis {id: $id})
        OPTIONAL MATCH (h)<-[:TESTS]-(e:Experiment)
        WITH h, count(e) AS experiment_count
        RETURN h.id AS id,
               h.text AS text,
               h.description AS description,
               h.status AS status,
               h.created_at AS created_at,
               h.prior_probability AS prior_probability,
               h.current_probability AS current_probability,
               h.tags AS tags,
               experiment_count
        """

        params = {"id": id}

        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_read(self._read_query, query, params)
                results = json.loads(results_json)

                if results and len(results) > 0:
                    h = results[0]

                    text_response = f"# Hypothesis: {h.get('text', 'Unknown')}\n\n"
                    text_response += f"**ID:** {h.get('id', id)}\n"
                    text_response += f"**Status:** {h.get('status', 'Unknown')}\n"
                    text_response += f"**Created:** {h.get('created_at', 'Unknown')}\n"
                    text_response += f"**Prior Probability:** {h.get('prior_probability', 'Unknown')}\n"
                    text_response += f"**Current Probability:** {h.get('current_probability', 'Unknown')}\n"

                    if h.get("tags"):
                        text_response += f"**Tags:** {', '.join(h.get('tags', []))}\n"

                    if h.get("description"):
                        text_response += f"\n## Description\n\n{h.get('description')}\n"

                    text_response += "\n## Experiments\n\n"
                    text_response += f"This hypothesis has been tested in {h.get('experiment_count', 0)} experiments.\n"

                    if h.get('experiment_count', 0) > 0:
                        text_response += "\nUse `list_experiments(hypothesis_id=\"" + id + "\")` to view related experiments."
                    else:
                        text_response += "\nUse `create_protocol(hypothesis_id=\"" + id + "\")` to design an experiment for this hypothesis."

                    return [types.TextContent(type="text", text=text_response)]
                else:
                    return [types.TextContent(type="text", text=f"No hypothesis found with ID '{id}'")]
        except Exception as e:
            logger.error(f"Error retrieving hypothesis: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def update_hypothesis(
        self,
        id: str = Field(..., description="ID of the hypothesis to update"),
        text: Optional[str] = Field(None, description="Updated hypothesis statement"),
        description: Optional[str] = Field(None, description="Updated description"),
        status: Optional[str] = Field(None, description="Updated status (Active, Confirmed, Rejected)"),
        current_probability: Optional[float] = Field(None, description="Updated probability assessment"),
        tags: Optional[List[str]] = Field(None, description="Updated tags (replaces existing tags)")
    ) -> List[types.TextContent]:
        """Update an existing hypothesis."""
        # Build dynamic SET clause based on provided parameters
        set_clauses = []
        params = {"id": id}

        if text is not None:
            set_clauses.append("h.text = $text")
            params["text"] = text

        if description is not None:
            set_clauses.append("h.description = $description")
            params["description"] = description

        if status is not None:
            set_clauses.append("h.status = $status")
            params["status"] = status

        if current_probability is not None:
            set_clauses.append("h.current_probability = $current_probability")
            params["current_probability"] = str(current_probability)

        if tags is not None:
            set_clauses.append("h.tags = $tags")
            params["tags"] = json.dumps(tags)

        if not set_clauses:
            return [types.TextContent(type="text", text="No updates provided.")]

        # Build the query
        query = f"""
        MATCH (h:Hypothesis {{id: $id}})
        SET {', '.join(set_clauses)}
        RETURN h.id AS id, h.text AS text
        """

        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_write(self._read_query, query, params)
                results = json.loads(results_json)

                if results and len(results) > 0:
                    return [types.TextContent(
                        type="text",
                        text=f"Successfully updated hypothesis '{results[0].get('text', id)}'"
                    )]
                else:
                    return [types.TextContent(type="text", text=f"No hypothesis found with ID '{id}'")]
        except Exception as e:
            logger.error(f"Error updating hypothesis: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def create_protocol(
        self,
        name: str = Field(..., description="Name of the protocol"),
        description: str = Field(..., description="Protocol description"),
        steps: List[str] = Field(..., description="Ordered list of protocol steps"),
        expected_observations: List[str] = Field(..., description="Expected observations if hypothesis is true"),
        materials: Optional[List[str]] = Field(None, description="Required materials and equipment"),
        controls: Optional[List[str]] = Field(None, description="Control conditions")
    ) -> List[types.TextContent]:
        """Create an experimental protocol for scientific experiments."""
        protocol_id = str(uuid.uuid4())

        # Create the protocol node
        query = """
        CREATE (p:Protocol {
            id: $protocol_id,
            name: $name,
            description: $description,
            created_at: datetime(),
            steps: $steps,
            expected_observations: $expected_observations
        })
        """

        params = {
            "protocol_id": protocol_id,
            "name": name,
            "description": description,
            "steps": steps,
            "expected_observations": expected_observations
        }

        if materials:
            query = query.replace("expected_observations: $expected_observations",
                                "expected_observations: $expected_observations, materials: $materials")
            params["materials"] = materials

        if controls:
            query = query.replace("expected_observations: $expected_observations",
                                "expected_observations: $expected_observations, controls: $controls")
            params["controls"] = controls

        query += """
        WITH p
        MATCH (hub:AiGuidanceHub {id: 'research_hub'})
        CREATE (hub)-[:CONTAINS]->(p)
        RETURN p.id AS id, p.name AS name
        """

        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_write(self._read_query, query, params)
                results = json.loads(results_json)

                if results and len(results) > 0:
                    text_response = "# Protocol Created\n\n"
                    text_response += f"**Protocol ID:** {protocol_id}\n"
                    text_response += f"**Name:** {name}\n\n"

                    text_response += f"**Description:**\n{description}\n\n"

                    text_response += "## Protocol Steps\n\n"
                    for i, step in enumerate(steps, 1):
                        text_response += f"{i}. {step}\n"

                    text_response += "\n## Expected Observations\n\n"
                    for i, obs in enumerate(expected_observations, 1):
                        text_response += f"{i}. {obs}\n"

                    if materials:
                        text_response += "\n## Materials\n\n"
                        for i, mat in enumerate(materials, 1):
                            text_response += f"{i}. {mat}\n"

                    if controls:
                        text_response += "\n## Controls\n\n"
                        for i, ctrl in enumerate(controls, 1):
                            text_response += f"{i}. {ctrl}\n"

                    text_response += "\nYou can now create experiments using this protocol with `create_experiment(protocol_id=\"" + protocol_id + "\", hypothesis_id=\"your-hypothesis-id\")`"

                    return [types.TextContent(type="text", text=text_response)]
                else:
                    return [types.TextContent(type="text", text="Error creating protocol")]
        except Exception as e:
            logger.error(f"Error creating protocol: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def list_protocols(
        self,
        limit: int = Field(10, description="Maximum number of protocols to return")
    ) -> List[types.TextContent]:
        """List available experimental protocols."""
        query = """
        MATCH (p:Protocol)
        OPTIONAL MATCH (p)<-[:FOLLOWS]-(e:Experiment)
        WITH p, count(e) AS usage_count
        RETURN p.id AS id,
               p.name AS name,
               p.description AS description,
               p.created_at AS created_at,
               usage_count
        ORDER BY p.created_at DESC
        LIMIT $limit
        """

        params: Dict[str, Any] = {"limit": limit}

        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_read(self._read_query, query, params)
                results = json.loads(results_json)

                if results and len(results) > 0:
                    text_response = "# Available Protocols\n\n"
                    text_response += "| ID | Name | Description | Usage Count |\n"
                    text_response += "| -- | ---- | ----------- | ----------- |\n"

                    for p in results:
                        description = p.get("description", "")[:50]
                        if len(p.get("description", "")) > 50:
                            description += "..."

                        text_response += f"| {p.get('id', 'unknown')} | {p.get('name', 'Unknown')} | {description} | {p.get('usage_count', 0)} |\n"

                    text_response += "\nTo view full details of a protocol, use `get_protocol(id=\"protocol-id\")`"

                    return [types.TextContent(type="text", text=text_response)]
                else:
                    return [types.TextContent(type="text", text="No protocols found in the database.")]
        except Exception as e:
            logger.error(f"Error listing protocols: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def get_protocol(
        self,
        id: str = Field(..., description="ID of the protocol to retrieve")
    ) -> List[types.TextContent]:
        """Get detailed information about a specific protocol."""
        query = """
        MATCH (p:Protocol {id: $id})
        RETURN p.id AS id,
               p.name AS name,
               p.description AS description,
               p.created_at AS created_at,
               p.steps AS steps,
               p.expected_observations AS expected_observations,
               p.materials AS materials,
               p.controls AS controls
        """

        params = {"id": id}

        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_read(self._read_query, query, params)
                results = json.loads(results_json)

                if results and len(results) > 0:
                    p = results[0]

                    text_response = f"# Protocol: {p.get('name', 'Unknown')}\n\n"
                    text_response += f"**ID:** {p.get('id', id)}\n"
                    text_response += f"**Created:** {p.get('created_at', 'Unknown')}\n\n"

                    text_response += f"**Description:**\n{p.get('description', 'No description')}\n\n"

                    text_response += "## Protocol Steps\n\n"
                    steps = p.get("steps", [])
                    for i, step in enumerate(steps, 1):
                        text_response += f"{i}. {step}\n"

                    text_response += "\n## Expected Observations\n\n"
                    observations = p.get("expected_observations", [])
                    for i, obs in enumerate(observations, 1):
                        text_response += f"{i}. {obs}\n"

                    if p.get("materials"):
                        text_response += "\n## Materials\n\n"
                        materials = p.get("materials", [])
                        for i, mat in enumerate(materials, 1):
                            text_response += f"{i}. {mat}\n"

                    if p.get("controls"):
                        text_response += "\n## Controls\n\n"
                        controls = p.get("controls", [])
                        for i, ctrl in enumerate(controls, 1):
                            text_response += f"{i}. {ctrl}\n"

                    text_response += "\n\nUse `create_experiment(protocol_id=\"" + id + "\", hypothesis_id=\"your-hypothesis-id\")` to create an experiment using this protocol."

                    return [types.TextContent(type="text", text=text_response)]
                else:
                    return [types.TextContent(type="text", text=f"No protocol found with ID '{id}'")]
        except Exception as e:
            logger.error(f"Error retrieving protocol: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def create_experiment(
        self,
        name: str = Field(..., description="Name of the experiment"),
        hypothesis_id: str = Field(..., description="ID of the hypothesis to test"),
        protocol_id: str = Field(..., description="ID of the protocol to follow"),
        description: Optional[str] = Field(None, description="Additional experiment details")
    ) -> List[types.TextContent]:
        """Create a new experiment to test a hypothesis using a protocol."""
        experiment_id = str(uuid.uuid4())

        query = """
        MATCH (h:Hypothesis {id: $hypothesis_id})
        MATCH (p:Protocol {id: $protocol_id})
        CREATE (e:Experiment {
            id: $experiment_id,
            name: $name,
            status: 'Planned',
            created_at: datetime()
        })
        CREATE (e)-[:TESTS]->(h)
        CREATE (e)-[:FOLLOWS]->(p)
        """

        params = {
            "experiment_id": experiment_id,
            "name": name,
            "hypothesis_id": hypothesis_id,
            "protocol_id": protocol_id
        }

        if description:
            query = query.replace("created_at: datetime()", "created_at: datetime(), description: $description")
            params["description"] = description

        query += """
        RETURN e.id AS id, e.name AS name, h.text AS hypothesis_text, p.name AS protocol_name
        """

        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_write(self._read_query, query, params)
                results = json.loads(results_json)

                if results and len(results) > 0:
                    result = results[0]

                    text_response = "# Experiment Created\n\n"
                    text_response += f"**Experiment ID:** {experiment_id}\n"
                    text_response += f"**Name:** {name}\n"
                    text_response += "**Status:** Planned\n\n"

                    text_response += f"**Testing Hypothesis:** {result.get('hypothesis_text', 'Unknown')}\n"
                    text_response += f"**Following Protocol:** {result.get('protocol_name', 'Unknown')}\n"

                    if description:
                        text_response += f"\n**Description:**\n{description}\n"

                    text_response += "\nYou can now record observations using `record_observation(experiment_id=\"" + experiment_id + "\")`"

                    return [types.TextContent(type="text", text=text_response)]
                else:
                    return [types.TextContent(type="text", text=f"Error creating experiment. Check if the hypothesis ID '{hypothesis_id}' and protocol ID '{protocol_id}' exist.")]
        except Exception as e:
            logger.error(f"Error creating experiment: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def list_experiments(
        self,
        hypothesis_id: Optional[str] = Field(None, description="Filter by hypothesis ID"),
        protocol_id: Optional[str] = Field(None, description="Filter by protocol ID"),
        status: Optional[str] = Field(None, description="Filter by status (Planned, In Progress, Completed)"),
        limit: int = Field(10, description="Maximum number of experiments to return")
    ) -> List[types.TextContent]:
        """List experiments with optional filtering."""
        query = """
        MATCH (e:Experiment)
        WHERE 1=1
        """


        params: Dict[str, Any] = {"limit": limit}

        if hypothesis_id:
            query += """
            AND (e)-[:TESTS]->(:Hypothesis {id: $hypothesis_id})
            """
            params["hypothesis_id"] = hypothesis_id

        if protocol_id:
            query += """
            AND (e)-[:FOLLOWS]->(:Protocol {id: $protocol_id})
            """
            params["protocol_id"] = protocol_id

        if status:
            query += " AND e.status = $status"
            params["status"] = status

        query += """
        OPTIONAL MATCH (e)-[:TESTS]->(h:Hypothesis)
        OPTIONAL MATCH (e)-[:FOLLOWS]->(p:Protocol)
        OPTIONAL MATCH (e)-[:HAS_OBSERVATION]->(o:Observation)
        WITH e, h, p, count(o) as observation_count
        RETURN e.id AS id,
               e.name AS name,
               e.status AS status,
               e.created_at AS created_at,
               h.id AS hypothesis_id,
               h.text AS hypothesis_text,
               p.id AS protocol_id,
               p.name AS protocol_name,
               observation_count
        ORDER BY e.created_at DESC
        LIMIT $limit
        """

        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_read(self._read_query, query, params)
                results = json.loads(results_json)

                if results and len(results) > 0:
                    text_response = "# Experiments\n\n"

                    filters = []
                    if hypothesis_id:
                        hypothesis_text = results[0].get('hypothesis_text', 'Unknown')
                        filters.append(f"Hypothesis: {hypothesis_text}")
                    if protocol_id:
                        protocol_name = results[0].get('protocol_name', 'Unknown')
                        filters.append(f"Protocol: {protocol_name}")
                    if status:
                        filters.append(f"Status: {status}")

                    if filters:
                        text_response += f"Filtered by: {', '.join(filters)}\n\n"

                    text_response += "| ID | Name | Status | Observations | Hypothesis |\n"
                    text_response += "| -- | ---- | ------ | ------------ | ---------- |\n"

                    for e in results:
                        hypothesis = e.get('hypothesis_text', '')[:30]
                        if len(e.get('hypothesis_text', '')) > 30:
                            hypothesis += "..."

                        text_response += f"| {e.get('id', 'unknown')} | {e.get('name', 'Unknown')} | {e.get('status', 'Unknown')} | {e.get('observation_count', 0)} | {hypothesis} |\n"

                    text_response += "\nTo view full details of an experiment, use `get_experiment(id=\"experiment-id\")`"

                    return [types.TextContent(type="text", text=text_response)]
                else:
                    filter_msg = []
                    if hypothesis_id:
                        filter_msg.append(f"hypothesis ID '{hypothesis_id}'")
                    if protocol_id:
                        filter_msg.append(f"protocol ID '{protocol_id}'")
                    if status:
                        filter_msg.append(f"status '{status}'")

                    if filter_msg:
                        return [types.TextContent(type="text", text=f"No experiments found matching {' and '.join(filter_msg)}.")]
                    else:
                        return [types.TextContent(type="text", text="No experiments found in the database.")]
        except Exception as e:
            logger.error(f"Error listing experiments: {e}")

            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def get_experiment(
        self,
        id: str = Field(..., description="ID of the experiment to retrieve")
    ) -> List[types.TextContent]:
        """Get detailed information about a specific experiment."""
        query = """
        MATCH (e:Experiment {id: $id})
        OPTIONAL MATCH (e)-[:TESTS]->(h:Hypothesis)
        OPTIONAL MATCH (e)-[:FOLLOWS]->(p:Protocol)
        OPTIONAL MATCH (e)-[:HAS_OBSERVATION]->(o:Observation)
        WITH e, h, p, collect(o) as observations
        RETURN e.id AS id,
               e.name AS name,
               e.description AS description,
               e.status AS status,
               e.created_at AS created_at,
               h.id AS hypothesis_id,
               h.text AS hypothesis_text,
               p.id AS protocol_id,
               p.name AS protocol_name,
               p.steps AS protocol_steps,
               size(observations) as observation_count
        """

        params = {"id": id}

        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_read(self._read_query, query, params)
                results = json.loads(results_json)

                if results and len(results) > 0:
                    e = results[0]

                    text_response = f"# Experiment: {e.get('name', 'Unknown')}\n\n"
                    text_response += f"**ID:** {e.get('id', id)}\n"
                    text_response += f"**Status:** {e.get('status', 'Unknown')}\n"
                    text_response += f"**Created:** {e.get('created_at', 'Unknown')}\n\n"

                    if e.get("description"):
                        text_response += f"**Description:**\n{e.get('description')}\n\n"

                    text_response += f"**Testing Hypothesis:** {e.get('hypothesis_text', 'Unknown')}\n"
                    text_response += f"**Following Protocol:** {e.get('protocol_name', 'Unknown')}\n\n"

                    text_response += "## Protocol Steps\n\n"
                    steps = e.get("protocol_steps", [])
                    for i, step in enumerate(steps, 1):
                        text_response += f"{i}. {step}\n"

                    text_response += f"\n## Observations ({e.get('observation_count', 0)})\n\n"
                    if e.get('observation_count', 0) > 0:
                        text_response += "Use `list_observations(experiment_id=\"" + id + "\")` to view recorded observations.\n"
                    else:
                        text_response += "No observations recorded yet. Use `record_observation(experiment_id=\"" + id + "\")` to add observations.\n"

                    return [types.TextContent(type="text", text=text_response)]
                else:
                    return [types.TextContent(type="text", text=f"No experiment found with ID '{id}'")]
        except Exception as e:
            logger.error(f"Error retrieving experiment: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def update_experiment(
        self,
        id: str = Field(..., description="ID of the experiment to update"),
        name: Optional[str] = Field(None, description="Updated experiment name"),
        description: Optional[str] = Field(None, description="Updated description"),
        status: Optional[str] = Field(None, description="Updated status (Planned, In Progress, Completed)")
    ) -> List[types.TextContent]:
        """Update an existing experiment."""
        # Build dynamic SET clause based on provided parameters
        set_clauses = []
        params = {"id": id}

        if name is not None:
            set_clauses.append("e.name = $name")
            params["name"] = name

        if description is not None:
            set_clauses.append("e.description = $description")
            params["description"] = description

        if status is not None:
            set_clauses.append("e.status = $status")
            params["status"] = status

        if not set_clauses:
            return [types.TextContent(type="text", text="No updates provided.")]

        # Build the query
        query = f"""
        MATCH (e:Experiment {{id: $id}})
        SET {', '.join(set_clauses)}
        RETURN e.id AS id, e.name AS name
        """

        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_write(self._read_query, query, params)
                results = json.loads(results_json)

                if results and len(results) > 0:
                    return [types.TextContent(
                        type="text",
                        text=f"Successfully updated experiment '{results[0].get('name', id)}'"
                    )]
                else:
                    return [types.TextContent(type="text", text=f"No experiment found with ID '{id}'")]
        except Exception as e:
            logger.error(f"Error updating experiment: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def record_observation(
        self,
        experiment_id: str = Field(..., description="ID of the experiment"),
        content: str = Field(..., description="The observation content"),
        supports_hypothesis: Optional[bool] = Field(None, description="Whether this observation supports the hypothesis"),
        evidence_strength: Optional[float] = Field(None, description="Strength of evidence (0-1)"),
        metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata about the observation")
    ) -> List[types.TextContent]:
        """Record an experimental observation for a specific experiment."""
        observation_id = str(uuid.uuid4())

        query = """
        MATCH (e:Experiment {id: $experiment_id})-[:TESTS]->(h:Hypothesis)
        CREATE (o:Observation {
            id: $observation_id,
            content: $content,
            timestamp: datetime(),
            supports_hypothesis: $supports_hypothesis
        })
        CREATE (e)-[:HAS_OBSERVATION]->(o)
        """

        params = {
            "experiment_id": experiment_id,
            "observation_id": observation_id,
            "content": content,
            "supports_hypothesis": supports_hypothesis
        }

        if evidence_strength is not None:
            query = query.replace("supports_hypothesis: $supports_hypothesis",
                                "supports_hypothesis: $supports_hypothesis, evidence_strength: $evidence_strength")
            params["evidence_strength"] = evidence_strength

        if metadata:
            metadata_json = json.dumps(metadata)
            query = query.replace("supports_hypothesis: $supports_hypothesis",
                                "supports_hypothesis: $supports_hypothesis, metadata: $metadata")
            params["metadata"] = metadata_json

        # Update experiment status and hypotheses probability if evidence strength is provided
        if evidence_strength is not None:
            query += """
            WITH o, e, h
            SET e.status = 'In Progress'

            // Simplified Bayesian update using evidence strength
            WITH o, e, h, h.current_probability as prior
            WITH o, e, h, prior,
                 CASE
                    WHEN o.supports_hypothesis = true THEN prior + (1 - prior) * o.evidence_strength
                    ELSE prior * (1 - o.evidence_strength)
                 END as posterior
            SET h.current_probability = posterior
            """
        else:
            query += """
            WITH o, e
            SET e.status = 'In Progress'
            """

        query += """
        RETURN o.id AS id, e.id AS experiment_id, h.id AS hypothesis_id, h.text AS hypothesis_text
        """

        try:
            async with self.driver.session(database=self.database) as session:
                async def write_query(tx):
                    raw_result = await tx.run(query, params)
                    return await raw_result.to_eager_result()
                result = await session.execute_write(write_query)

                if result.records:
                    record = result.records[0]

                    text_response = "# Observation Recorded\n\n"
                    text_response += f"**Observation ID:** {observation_id}\n"
                    text_response += f"**Experiment ID:** {record['experiment_id']}\n"
                    text_response += f"**Hypothesis:** {record['hypothesis_text']}\n\n"
                    text_response += f"**Observation:** {content}\n"

                    if supports_hypothesis is not None:
                        text_response += f"**Supports Hypothesis:** {'Yes' if supports_hypothesis else 'No'}\n"

                    if evidence_strength is not None:
                        text_response += f"**Evidence Strength:** {evidence_strength}\n"

                    if metadata:
                        text_response += "\n**Metadata:**\n"
                        for key, value in metadata.items():
                            text_response += f"- **{key}:** {value}\n"

                    return [types.TextContent(type="text", text=text_response)]
                else:
                    return [types.TextContent(type="text", text=f"Error recording observation. Check if experiment ID {experiment_id} exists.")]
        except Exception as e:
            logger.error(f"Error recording observation: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def list_observations(
        self,
        experiment_id: str = Field(..., description="ID of the experiment"),
        limit: int = Field(20, description="Maximum number of observations to return")
    ) -> List[types.TextContent]:
        """List observations for a specific experiment."""
        query = """
        MATCH (e:Experiment {id: $experiment_id})-[:HAS_OBSERVATION]->(o:Observation)
        RETURN o.id AS id,
               o.content AS content,
               o.timestamp AS timestamp,
               o.supports_hypothesis AS supports_hypothesis,
               o.evidence_strength AS evidence_strength,
               o.metadata AS metadata
        ORDER BY o.timestamp DESC
        LIMIT $limit
        """

        params = {
            "experiment_id": experiment_id,
            "limit": limit
        }

        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_read(self._read_query, query, params)
                results = json.loads(results_json)

                if results and len(results) > 0:
                    # Get experiment name first
                    exp_query = """
                    MATCH (e:Experiment {id: $experiment_id})
                    RETURN e.name AS name
                    """

                    exp_result = await session.execute_read(self._read_query, exp_query, {"experiment_id": experiment_id})
                    exp_data = json.loads(exp_result)

                    experiment_name = "Unknown"
                    if exp_data and len(exp_data) > 0:
                        experiment_name = exp_data[0].get("name", "Unknown")

                    text_response = f"# Observations for Experiment: {experiment_name}\n\n"

                    for i, o in enumerate(results, 1):
                        text_response += f"## {i}. {o.get('timestamp', '')[:19]}\n\n"
                        text_response += f"{o.get('content')}\n\n"

                        details = []

                        if o.get("supports_hypothesis") is not None:
                            supports = "Supports" if o.get("supports_hypothesis") else "Contradicts"
                            details.append(f"{supports} hypothesis")

                        if o.get("evidence_strength") is not None:
                            details.append(f"Evidence strength: {o.get('evidence_strength')}")

                        if details:
                            text_response += f"*{', '.join(details)}*\n\n"

                        if o.get("metadata"):
                            try:
                                metadata = json.loads(o.get("metadata"))
                                text_response += "**Metadata:**\n"
                                for key, value in metadata.items():
                                    text_response += f"- **{key}:** {value}\n"
                                text_response += "\n"
                            except Exception:
                                pass

                    return [types.TextContent(type="text", text=text_response)]
                else:
                    return [types.TextContent(type="text", text=f"No observations found for experiment ID '{experiment_id}'.")]
        except Exception as e:
            logger.error(f"Error listing observations: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def compute_statistics(
        self,
        experiment_id: str = Field(..., description="ID of the experiment to analyze"),
        include_visualization: bool = Field(True, description="Include visualization of the data")
    ) -> List[types.TextContent]:
        """Compute statistical analysis of experimental observations."""
        query = """
        MATCH (e:Experiment {id: $experiment_id})-[:HAS_OBSERVATION]->(o:Observation)
        RETURN o.id AS id,
               o.content AS content,
               o.timestamp AS timestamp,
               o.supports_hypothesis AS supports_hypothesis,
               o.evidence_strength AS evidence_strength,
               o.metadata AS metadata
        ORDER BY o.timestamp
        """

        params = {"experiment_id": experiment_id}

        try:
            async with self.driver.session(database=self.database) as session:
                results_json = await session.execute_read(self._read_query, query, params)
                results = json.loads(results_json)

                if results and len(results) > 0:
                    # Get experiment and hypothesis details
                    exp_query = """
                    MATCH (e:Experiment {id: $experiment_id})-[:TESTS]->(h:Hypothesis)
                    RETURN e.name AS experiment_name,
                           h.text AS hypothesis_text,
                           h.prior_probability AS prior_probability,
                           h.current_probability AS current_probability
                    """

                    exp_result = await session.execute_read(self._read_query, exp_query, params)
                    exp_data = json.loads(exp_result)

                    if not exp_data or len(exp_data) == 0:
                        return [types.TextContent(type="text", text=f"Could not find experiment with ID '{experiment_id}'.")]

                    exp_info = exp_data[0]

                    # Calculate basic statistics
                    total_observations = len(results)
                    supporting = sum(1 for o in results if o.get("supports_hypothesis") is True)
                    contradicting = sum(1 for o in results if o.get("supports_hypothesis") is False)
                    neutral = total_observations - supporting - contradicting

                    avg_evidence_strength = 0
                    evidence_strengths = [o.get("evidence_strength") for o in results if o.get("evidence_strength") is not None]
                    if evidence_strengths:
                        avg_evidence_strength = sum(evidence_strengths) / len(evidence_strengths)

                    # Format the response
                    text_response = f"# Statistical Analysis: {exp_info.get('experiment_name', 'Unknown')}\n\n"
                    text_response += f"**Hypothesis:** {exp_info.get('hypothesis_text', 'Unknown')}\n\n"

                    text_response += "## Summary Statistics\n\n"
                    text_response += f"**Total Observations:** {total_observations}\n"
                    text_response += f"**Supporting Hypothesis:** {supporting} ({supporting/total_observations*100:.1f}%)\n"
                    text_response += f"**Contradicting Hypothesis:** {contradicting} ({contradicting/total_observations*100:.1f}%)\n"
                    text_response += f"**Neutral Observations:** {neutral} ({neutral/total_observations*100:.1f}%)\n\n"

                    if evidence_strengths:
                        text_response += f"**Average Evidence Strength:** {avg_evidence_strength:.3f}\n\n"

                    text_response += "## Bayesian Analysis\n\n"
                    text_response += f"**Prior Probability:** {exp_info.get('prior_probability', 'Unknown')}\n"
                    text_response += f"**Current Probability:** {exp_info.get('current_probability', 'Unknown')}\n"

                    if include_visualization:
                        text_response += "\n## Visualization\n\n"
                        text_response += "For visualizations, it's recommended to export the data and use a specialized tool like R, Python (with matplotlib/seaborn/plotly), or a statistics package.\n\n"

                    # Add conclusion
                    text_response += "## Conclusion\n\n"

                    current_prob = float(exp_info.get('current_probability', 0.5))
                    prior_prob = float(exp_info.get('prior_probability', 0.5))

                    if current_prob > 0.8:
                        text_response += "The evidence strongly supports the hypothesis.\n"
                    elif current_prob > 0.6:
                        text_response += "The evidence moderately supports the hypothesis.\n"
                    elif current_prob < 0.2:
                        text_response += "The evidence strongly contradicts the hypothesis.\n"
                    elif current_prob < 0.4:
                        text_response += "The evidence moderately contradicts the hypothesis.\n"
                    else:
                        text_response += "The evidence is inconclusive regarding the hypothesis.\n"

                    if current_prob > prior_prob + 0.1:
                        text_response += "The experiment has substantially increased confidence in the hypothesis.\n"
                    elif current_prob < prior_prob - 0.1:
                        text_response += "The experiment has substantially decreased confidence in the hypothesis.\n"
                    else:
                        text_response += "The experiment has not significantly changed confidence in the hypothesis.\n"

                    return [types.TextContent(type="text", text=text_response)]
                else:
                    return [types.TextContent(type="text", text=f"No observations found for experiment ID '{experiment_id}'.")]
        except Exception as e:
            logger.error(f"Error computing statistics: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    async def create_publication_draft(
        self,
        experiment_id: str = Field(..., description="ID of the experiment to document"),
        title: str = Field(..., description="Publication title"),
        authors: List[str] = Field(..., description="List of author names"),
        include_abstract: bool = Field(True, description="Include an auto-generated abstract"),
        include_figures: bool = Field(True, description="Include figures in the draft")
    ) -> List[types.TextContent]:
        """Create a draft publication document from experimental results."""
        # First, gather all necessary data
        exp_query = """
        MATCH (e:Experiment {id: $experiment_id})
        MATCH (e)-[:TESTS]->(h:Hypothesis)
        MATCH (e)-[:FOLLOWS]->(p:Protocol)
        OPTIONAL MATCH (e)-[:HAS_OBSERVATION]->(o:Observation)
        RETURN e.id AS experiment_id,
               e.name AS experiment_name,
               e.description AS experiment_description,
               e.status AS experiment_status,
               h.id AS hypothesis_id,
               h.text AS hypothesis_text,
               h.description AS hypothesis_description,
               h.prior_probability AS prior_probability,
               h.current_probability AS current_probability,
               p.id AS protocol_id,
               p.name AS protocol_name,
               p.steps AS protocol_steps,
               p.expected_observations AS expected_observations,
               p.materials AS materials,
               collect(o) AS observations
        """

        params = {"experiment_id": experiment_id}

        try:
            async with self.driver.session(database=self.database) as session:
                async def read_query(tx):
                    raw_result = await tx.run(exp_query, params)
                    return await raw_result.to_eager_result()
                result = await session.execute_read(read_query)

                if not result.records:
                    return [types.TextContent(type="text", text=f"Could not find experiment with ID '{experiment_id}'.")]

                record = result.records[0]

                # Extract observations from the record
                observations = []
                if 'observations' in record:
                    for obs in record['observations']:
                        observations.append({
                            'id': obs.get('id'),
                            'content': obs.get('content'),
                            'timestamp': obs.get('timestamp'),
                            'supports_hypothesis': obs.get('supports_hypothesis'),
                            'evidence_strength': obs.get('evidence_strength')
                        })

                # Now, create the publication draft
                current_date = datetime.datetime.now().strftime("%Y-%m-%d")

                publication = f"# {title}\n\n"

                # Authors
                publication += "## Authors\n\n"
                publication += ", ".join(authors) + "\n\n"

                # Date
                publication += f"*{current_date}*\n\n"

                # Abstract
                if include_abstract:
                    publication += "## Abstract\n\n"

                    experiment_name = record.get('experiment_name')
                    hypothesis_text = record.get('hypothesis_text')
                    protocol_name = record.get('protocol_name')

                    # Generate simple abstract
                    abstract = f"This study investigated {hypothesis_text} "
                    abstract += f"through an experiment titled '{experiment_name}' using the protocol '{protocol_name}'. "

                    total_obs = len(observations)
                    supporting = sum(1 for o in observations if o.get('supports_hypothesis') is True)
                    contradicting = sum(1 for o in observations if o.get('supports_hypothesis') is False)

                    if total_obs > 0:
                        abstract += f"A total of {total_obs} observations were recorded. "

                        if supporting > contradicting:
                            abstract += "The results generally supported the hypothesis. "
                        elif contradicting > supporting:
                            abstract += "The results generally contradicted the hypothesis. "
                        else:
                            abstract += "The results were inconclusive regarding the hypothesis. "

                    current_prob = record.get('current_probability')
                    if current_prob is not None:
                        if float(current_prob) > 0.8:
                            abstract += "The evidence strongly supports the original hypothesis."
                        elif float(current_prob) > 0.6:
                            abstract += "The evidence moderately supports the original hypothesis."
                        elif float(current_prob) < 0.2:
                            abstract += "The evidence strongly contradicts the original hypothesis."
                        elif float(current_prob) < 0.4:
                            abstract += "The evidence moderately contradicts the original hypothesis."
                        else:
                            abstract += "The evidence is inconclusive regarding the original hypothesis."

                    publication += abstract + "\n\n"

                # Introduction
                publication += "## Introduction\n\n"
                if record.get('hypothesis_description'):
                    publication += record.get('hypothesis_description') + "\n\n"
                else:
                    publication += f"This study was designed to test the hypothesis: {record.get('hypothesis_text')}\n\n"

                # Methods
                publication += "## Methods\n\n"
                if record.get('experiment_description'):
                    publication += record.get('experiment_description') + "\n\n"

                # Protocol
                publication += "### Protocol\n\n"
                steps = record.get('protocol_steps', [])
                for i, step in enumerate(steps, 1):
                    publication += f"{i}. {step}\n"

                # Materials (if available)
                materials = record.get('materials', [])
                if materials:
                    publication += "\n### Materials\n\n"
                    for material in materials:
                        publication += f"- {material}\n"

                # Results
                publication += "\n## Results\n\n"

                # Calculate basic statistics for results section
                total_observations = len(observations)
                supporting = sum(1 for o in observations if o.get('supports_hypothesis') is True)
                contradicting = sum(1 for o in observations if o.get('supports_hypothesis') is False)
                neutral = total_observations - supporting - contradicting

                publication += f"A total of {total_observations} observations were recorded. "

                publication += f"Of these, {supporting} supported the hypothesis, {contradicting} contradicted it, "
                publication += f"and {neutral} were neutral.\n"

                return [types.TextContent(type="text", text=publication)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error creating publication draft: {str(e)}")]