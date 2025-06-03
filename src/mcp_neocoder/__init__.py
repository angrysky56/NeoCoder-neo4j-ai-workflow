"""
MCP Server for Neo4j-Guided AI Coding Workflow with Polymorphic Support

This package implements an MCP server that provides tools for AI assistants to use
a Neo4j graph database as a structured instruction system for coding tasks and other workflows.

The server supports multiple "incarnations" - different operational modes that adapt the system
for specialized use cases while preserving the core Neo4j graph structure.
"""

# Import server components
from .server import create_server, Neo4jWorkflowServer

# Import base incarnation class
from .incarnations.base_incarnation import BaseIncarnation

# Import registries
from .incarnation_registry import registry as incarnation_registry
from .tool_registry import registry as tool_registry

# Dynamically discover and load all incarnations - no hardcoding!
incarnation_registry.discover()

__version__ = "0.1.0"
__all__ = [
    "create_server",
    "Neo4jWorkflowServer",
    "incarnation_registry",
    "tool_registry",
    "BaseIncarnation"
]
