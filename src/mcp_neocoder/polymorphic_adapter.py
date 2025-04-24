"""
Polymorphic Adapter for NeoCoder Neo4j AI Workflow

This module extends the NeoCoder framework to support multiple incarnations beyond code workflows,
including research orchestration, decision support, continuous learning, and complex systems simulation.

The adapter follows a plugin architecture where different incarnations can be registered and
dynamically loaded based on configuration.
"""

import json
import logging
import uuid
from typing import Dict, Any, List, Optional, Type, Union
from enum import Enum

import mcp.types as types
from pydantic import Field
from neo4j import AsyncTransaction

logger = logging.getLogger("mcp_neocoder.polymorphic_adapter")


class IncarnationType(str, Enum):
    """Supported incarnation types for the NeoCoder framework."""
    CODING = "coding"                       # Original coding workflow
    RESEARCH = "research_orchestration"     # Research lab notebook
    DECISION = "decision_support"           # Decision-making system
    LEARNING = "continuous_learning"        # Learning environment
    SIMULATION = "complex_system"           # Complex system simulator


class BaseIncarnation:
    """Base class for all incarnation implementations."""
    
    incarnation_type: IncarnationType
    description: str
    version: str
    
    def __init__(self, driver, database):
        """Initialize the incarnation with database connection."""
        self.driver = driver
        self.database = database
    
    async def initialize_schema(self):
        """Initialize the Neo4j schema for this incarnation."""
        raise NotImplementedError("Each incarnation must implement schema initialization")
    
    async def get_guidance_hub(self):
        """Get the guidance hub content for this incarnation."""
        raise NotImplementedError("Each incarnation must implement guidance hub")
    
    async def register_tools(self, server):
        """Register incarnation-specific tools with the server."""
        raise NotImplementedError("Each incarnation must register its tools")
    
    async def _read_query(self, tx: AsyncTransaction, query: str, params: dict) -> str:
        """Execute a read query and return results as JSON string."""
        raise NotImplementedError("_read_query must be implemented by the parent class")

    async def _write(self, tx: AsyncTransaction, query: str, params: dict):
        """Execute a write query and return results as JSON string."""
        raise NotImplementedError("_write must be implemented by the parent class")


class PolymorphicAdapterMixin:
    """Mixin to add polymorphic capabilities to the Neo4jWorkflowServer."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the polymorphic adapter."""
        self.incarnation_registry = {}
        self.current_incarnation = None
        super().__init__(*args, **kwargs)
    
    def register_incarnation(self, incarnation_class: Type[BaseIncarnation], incarnation_type: IncarnationType):
        """Register a new incarnation type."""
        self.incarnation_registry[incarnation_type] = incarnation_class
        
    async def set_incarnation(self, incarnation_type: IncarnationType):
        """Set the current incarnation type."""
        if incarnation_type not in self.incarnation_registry:
            raise ValueError(f"Unknown incarnation type: {incarnation_type}")
        
        # Create instance of the incarnation
        incarnation_class = self.incarnation_registry[incarnation_type]
        self.current_incarnation = incarnation_class(self.driver, self.database)
        
        # Initialize schema for this incarnation
        await self.current_incarnation.initialize_schema()
        
        # Register incarnation-specific tools
        await self.current_incarnation.register_tools(self)
        
        logger.info(f"Switched to incarnation: {incarnation_type}")
        return self.current_incarnation
    
    async def get_current_incarnation_type(self) -> Optional[IncarnationType]:
        """Get the currently active incarnation type."""
        if not self.current_incarnation:
            return None
        return self.current_incarnation.incarnation_type
    
    async def list_available_incarnations(self) -> List[Dict[str, Any]]:
        """List all available incarnations with metadata."""
        return [
            {
                "type": inc_type.value,
                "description": inc_class.__doc__ or "No description available",
            }
            for inc_type, inc_class in self.incarnation_registry.items()
        ]


class ResearchIncarnation(BaseIncarnation):
    """Research Orchestration Platform incarnation of the NeoCoder framework.
    
    Provides tools for scientific workflow management, hypothesis tracking,
    experiment design, and results publication.
    """
    
    incarnation_type = IncarnationType.RESEARCH
    description = "Research Orchestration Platform for scientific workflows"
    version = "0.1.0"
    
    async def initialize_schema(self):
        """Initialize the Neo4j schema for research orchestration."""
        # Define constraints and indexes for research schema
        schema_query = """
        // Create constraints for unique IDs
        CREATE CONSTRAINT IF NOT EXISTS FOR (h:Hypothesis) REQUIRE h.id IS UNIQUE;
        CREATE CONSTRAINT IF NOT EXISTS FOR (e:Experiment) REQUIRE e.id IS UNIQUE;
        CREATE CONSTRAINT IF NOT EXISTS FOR (p:Protocol) REQUIRE p.id IS UNIQUE;
        CREATE CONSTRAINT IF NOT EXISTS FOR (o:Observation) REQUIRE o.id IS UNIQUE;
        CREATE CONSTRAINT IF NOT EXISTS FOR (r:Run) REQUIRE r.id IS UNIQUE;
        
        // Create indexes for performance
        CREATE INDEX IF NOT EXISTS FOR (h:Hypothesis) ON (h.status);
        CREATE INDEX IF NOT EXISTS FOR (e:Experiment) ON (e.status);
        CREATE INDEX IF NOT EXISTS FOR (p:Protocol) ON (p.name);
        """
        
        try:
            async with self.driver.session(database=self.database) as session:
                await session.execute_write(lambda tx: tx.run(schema_query))
                
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
- Record observations using `add_observation()`
- Analyze results with `compute_statistics()`

Each entity in the system has provenance tracking, ensuring reproducibility and transparency.
        """
        
        params = {"description": description}
        
        async with self.driver.session(database=self.database) as session:
            await session.execute_write(lambda tx: tx.run(query, params))
    
    async def register_tools(self, server):
        """Register research incarnation-specific tools with the server."""
        server.mcp.add_tool(self.register_hypothesis)
        server.mcp.add_tool(self.list_hypotheses)
        server.mcp.add_tool(self.create_protocol)
        server.mcp.add_tool(self.record_observation)
        server.mcp.add_tool(self.list_experiments)
        
        logger.info("Research incarnation tools registered")
    
    async def get_guidance_hub(self):
        """Get the guidance hub for research incarnation."""
        query = """
        MATCH (hub:AiGuidanceHub {id: 'research_hub'})
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
                results_json = await session.execute_write(self._read_query, query, params)
                results = json.loads(results_json)
                
                if results and len(results) > 0:
                    text_response = f"# Hypothesis Registered\n\n"
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
        
        params = {"limit": limit}
        
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
                    
                    for h in results:
                        text_response += f"## {h.get('text', 'Unnamed Hypothesis')}\n\n"
                        text_response += f"**ID:** {h.get('id', 'unknown')}\n"
                        text_response += f"**Status:** {h.get('status', 'Unknown')}\n"
                        text_response += f"**Created:** {h.get('created_at', 'Unknown')}\n"
                        text_response += f"**Current Probability:** {h.get('current_probability', 'Unknown')}\n"
                        
                        if h.get('tags'):
                            text_response += f"**Tags:** {', '.join(h.get('tags', []))}\n"
                        
                        text_response += "\n"
                    
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
    
    async def create_protocol(
        self,
        name: str = Field(..., description="Name of the protocol"),
        hypothesis_id: str = Field(..., description="ID of the hypothesis to test"),
        steps: List[str] = Field(..., description="Ordered list of protocol steps"),
        expected_observations: List[str] = Field(..., description="Expected observations if hypothesis is true"),
        materials: Optional[List[str]] = Field(None, description="Required materials and equipment"),
        controls: Optional[List[str]] = Field(None, description="Control conditions")
    ) -> List[types.TextContent]:
        """Create an experimental protocol to test a hypothesis."""
        protocol_id = str(uuid.uuid4())
        experiment_id = str(uuid.uuid4())
        
        # Create the protocol node
        protocol_query = """
        MATCH (h:Hypothesis {id: $hypothesis_id})
        CREATE (p:Protocol {
            id: $protocol_id,
            name: $name,
            created_at: datetime(),
            steps: $steps,
            expected_observations: $expected_observations
        })
        """
        
        protocol_params = {
            "protocol_id": protocol_id,
            "hypothesis_id": hypothesis_id,
            "name": name,
            "steps": steps,
            "expected_observations": expected_observations
        }
        
        if materials:
            protocol_query = protocol_query.replace("expected_observations: $expected_observations", 
                                                  "expected_observations: $expected_observations, materials: $materials")
            protocol_params["materials"] = materials
        
        if controls:
            protocol_query = protocol_query.replace("expected_observations: $expected_observations", 
                                                  "expected_observations: $expected_observations, controls: $controls")
            protocol_params["controls"] = controls
        
        # Create the experiment node
        experiment_query = """
        MATCH (p:Protocol {id: $protocol_id})
        MATCH (h:Hypothesis {id: $hypothesis_id})
        CREATE (e:Experiment {
            id: $experiment_id,
            name: $experiment_name,
            status: 'Planned',
            created_at: datetime()
        })
        CREATE (e)-[:TESTS]->(h)
        CREATE (e)-[:FOLLOWS]->(p)
        RETURN e.id AS experiment_id, p.id AS protocol_id, h.text AS hypothesis_text
        """
        
        experiment_params = {
            "protocol_id": protocol_id,
            "hypothesis_id": hypothesis_id,
            "experiment_id": experiment_id,
            "experiment_name": f"Experiment for {name}"
        }
        
        try:
            async with self.driver.session(database=self.database) as session:
                # Create protocol
                await session.execute_write(lambda tx: tx.run(protocol_query, protocol_params))
                
                # Create experiment
                results = await session.execute_write(
                    lambda tx: tx.run(experiment_query, experiment_params).to_eager_result()
                )
                
                if results.records:
                    record = results.records[0]
                    text_response = "# Protocol Created\n\n"
                    text_response += f"**Protocol ID:** {protocol_id}\n"
                    text_response += f"**Name:** {name}\n"
                    text_response += f"**Experiment ID:** {record['experiment_id']}\n"
                    text_response += f"**Testing Hypothesis:** {record['hypothesis_text']}\n\n"
                    
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
                    
                    text_response += "\nYou can now record observations using `record_observation(experiment_id=\"" + record['experiment_id'] + "\")`"
                    
                    return [types.TextContent(type="text", text=text_response)]
                else:
                    return [types.TextContent(type="text", text="Error creating protocol and experiment")]
        except Exception as e:
            logger.error(f"Error creating protocol: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]
    
    async def record_observation(
        self,
        experiment_id: str = Field(..., description="ID of the experiment"),
        content: str = Field(..., description="The observation content"),
        supports_hypothesis: bool = Field(None, description="Whether this observation supports the hypothesis"),
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
                results = await session.execute_write(
                    lambda tx: tx.run(query, params).to_eager_result()
                )
                
                if results.records:
                    record = results.records[0]
                    
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
    
    async def list_experiments(
        self,
        hypothesis_id: Optional[str] = Field(None, description="Filter by hypothesis ID"),
        status: Optional[str] = Field(None, description="Filter by status (Planned, In Progress, Completed)"),
        limit: int = Field(10, description="Maximum number of experiments to return")
    ) -> List[types.TextContent]:
        """List experiments with optional filtering."""
        query = """
        MATCH (e:Experiment)-[:TESTS]->(h:Hypothesis)
        WHERE 1=1
        """
        
        params = {"limit": limit}
        
        if hypothesis_id:
            query += " AND h.id = $hypothesis_id"
            params["hypothesis_id"] = hypothesis_id
        
        if status:
            query += " AND e.status = $status"
            params["status"] = status
        
        query += """
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
                    
                    if hypothesis_id:
                        text_response += f"**Hypothesis:** {results[0].get('hypothesis_text', 'Unknown')}\n\n"
                    if status:
                        text_response += f"**Status:** {status}\n\n"
                    
                    for e in results:
                        text_response += f"## {e.get('name', 'Unnamed Experiment')}\n\n"
                        text_response += f"**ID:** {e.get('id', 'unknown')}\n"
                        text_response += f"**Status:** {e.get('status', 'Unknown')}\n"
                        text_response += f"**Created:** {e.get('created_at', 'Unknown')}\n"
                        
                        if not hypothesis_id:
                            text_response += f"**Hypothesis:** {e.get('hypothesis_text', 'Unknown')}\n"
                        
                        text_response += f"**Protocol:** {e.get('protocol_name', 'Unknown')}\n"
                        text_response += f"**Observations:** {e.get('observation_count', 0)}\n\n"
                    
                    return [types.TextContent(type="text", text=text_response)]
                else:
                    filter_msg = ""
                    if hypothesis_id:
                        filter_msg += f" for hypothesis '{hypothesis_id}'"
                    if status:
                        if filter_msg:
                            filter_msg += " and"
                        filter_msg += f" with status '{status}'"
                    
                    if filter_msg:
                        return [types.TextContent(type="text", text=f"No experiments found{filter_msg}.")]
                    else:
                        return [types.TextContent(type="text", text="No experiments found in the database.")]
        except Exception as e:
            logger.error(f"Error listing experiments: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]


class DecisionIncarnation(BaseIncarnation):
    """Decision Support System incarnation of the NeoCoder framework.
    
    Provides tools for tracking decisions, alternatives, metrics, and evidence
    to support transparent, data-driven decision-making processes.
    """
    
    incarnation_type = IncarnationType.DECISION
    description = "Decision Support System for data-driven decision making"
    version = "0.1.0"
    
    async def initialize_schema(self):
        """Initialize the Neo4j schema for decision support system."""
        # Define constraints and indexes for decision schema
        schema_query = """
        // Create constraints for unique IDs
        CREATE CONSTRAINT IF NOT EXISTS FOR (d:Decision) REQUIRE d.id IS UNIQUE;
        CREATE CONSTRAINT IF NOT EXISTS FOR (a:Alternative) REQUIRE a.id IS UNIQUE;
        CREATE CONSTRAINT IF NOT EXISTS FOR (m:Metric) REQUIRE m.id IS UNIQUE;
        CREATE CONSTRAINT IF NOT EXISTS FOR (e:Evidence) REQUIRE e.id IS UNIQUE;
        
        // Create indexes for performance
        CREATE INDEX IF NOT EXISTS FOR (d:Decision) ON (d.status);
        CREATE INDEX IF NOT EXISTS FOR (a:Alternative) ON (a.name);
        """
        
        try:
            async with self.driver.session(database=self.database) as session:
                await session.execute_write(lambda tx: tx.run(schema_query))
                
                # Create base guidance hub for decisions if it doesn't exist
                await self.ensure_decision_hub_exists()
                
            logger.info("Decision incarnation schema initialized")
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

Welcome to the Decision Support System powered by the NeoCoder framework.
This system helps you make better decisions with the following capabilities:

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
        # Here we would register decision-specific tools
        # Implementation would be similar to the research incarnation
        pass
    
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


# Module for switching between incarnations
async def switch_incarnation(
    server,
    incarnation_type: IncarnationType
) -> List[types.TextContent]:
    """Switch the server to a different incarnation."""
    try:
        await server.set_incarnation(incarnation_type)
        return [types.TextContent(
            type="text",
            text=f"Successfully switched to '{incarnation_type.value}' incarnation"
        )]
    except Exception as e:
        logger.error(f"Error switching incarnation: {e}")
        return [types.TextContent(type="text", text=f"Error: {e}")]


async def get_current_incarnation(server) -> List[types.TextContent]:
    """Get the currently active incarnation type."""
    try:
        current = await server.get_current_incarnation_type()
        if current:
            return [types.TextContent(
                type="text",
                text=f"Currently using '{current.value}' incarnation"
            )]
        else:
            return [types.TextContent(
                type="text",
                text="No incarnation is currently active"
            )]
    except Exception as e:
        logger.error(f"Error getting current incarnation: {e}")
        return [types.TextContent(type="text", text=f"Error: {e}")]


async def list_incarnations(server) -> List[types.TextContent]:
    """List all available incarnations."""
    try:
        incarnations = await server.list_available_incarnations()
        
        if incarnations:
            text = "# Available Incarnations\n\n"
            text += "| Type | Description |\n"
            text += "| ---- | ----------- |\n"
            
            for inc in incarnations:
                text += f"| {inc['type']} | {inc['description']} |\n"
            
            current = await server.get_current_incarnation_type()
            if current:
                text += f"\nCurrently using: **{current.value}**"
            
            return [types.TextContent(type="text", text=text)]
        else:
            return [types.TextContent(type="text", text="No incarnations are registered")]
    except Exception as e:
        logger.error(f"Error listing incarnations: {e}")
        return [types.TextContent(type="text", text=f"Error: {e}")]
