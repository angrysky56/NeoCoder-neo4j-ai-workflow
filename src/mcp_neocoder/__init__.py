"""
MCP Server for Neo4j-Guided AI Coding Workflow

This package implements an MCP server that provides tools for AI assistants to use 
a Neo4j graph database as a structured instruction system for coding tasks.
"""

from .server import create_server, Neo4jWorkflowServer

__version__ = "0.1.0"
__all__ = ["create_server", "Neo4jWorkflowServer"]
