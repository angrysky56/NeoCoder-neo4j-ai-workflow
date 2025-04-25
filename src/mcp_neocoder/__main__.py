#!/usr/bin/env python3
"""
Main entry point for NeoCoder package.
"""

import argparse
import asyncio
import os
import logging

from .server import main as server_main
from .init_db import main as init_db_main

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mcp_neocoder")


def main():
    """Main entry point for the NeoCoder package."""
    import signal
    import sys
    
    # Define signal handlers before anything else
    def signal_handler(sig, frame):
        """Handle termination signals gracefully."""
        logger.info(f"Received signal {sig}, shutting down NeoCoder...")
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check for existing instances and clean up if needed
    try:
        from .server import cleanup_zombie_instances
        cleanup_zombie_instances()
    except Exception as e:
        logger.warning(f"Failed to clean up zombie instances: {e}")
    
    parser = argparse.ArgumentParser(description="NeoCoder Neo4j-Guided AI Coding Workflow")

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Server command
    server_parser = subparsers.add_parser("server", help="Run the MCP server")
    server_parser.add_argument("--db-url", default=None, help="Neo4j connection URL")
    server_parser.add_argument("--username", default=None, help="Neo4j username")
    server_parser.add_argument("--password", default=None, help="Neo4j password")
    server_parser.add_argument("--database", default=None, help="Neo4j database name")
    server_parser.add_argument("--force-clean", action="store_true", 
                             help="Force clean up of other running instances")

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize the Neo4j database")
    init_parser.add_argument("--db-url", default=None, help="Neo4j connection URL")
    init_parser.add_argument("--username", default=None, help="Neo4j username")
    init_parser.add_argument("--password", default=None, help="Neo4j password")
    init_parser.add_argument("--database", default=None, help="Neo4j database name")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up orphaned server instances")
    cleanup_parser.add_argument("--force", action="store_true", help="Force kill all instances")

    args = parser.parse_args()

    # Log the environment variables for debugging
    logger.info(f"NEO4J_URL from environment: {os.environ.get('NEO4J_URL', 'Not set')}")
    logger.info(f"NEO4J_USERNAME from environment: {os.environ.get('NEO4J_USERNAME', 'Not set')}")
    logger.info(f"NEO4J_PASSWORD from environment: {'Set' if os.environ.get('NEO4J_PASSWORD') else 'Not set'}")
    logger.info(f"NEO4J_DATABASE from environment: {os.environ.get('NEO4J_DATABASE', 'Not set')}")

    # Set environment variables for database connection
    if hasattr(args, 'db_url') and args.db_url:
        os.environ["NEO4J_URL"] = args.db_url
    if hasattr(args, 'username') and args.username:
        os.environ["NEO4J_USERNAME"] = args.username
    if hasattr(args, 'password') and args.password:
        os.environ["NEO4J_PASSWORD"] = args.password
    if hasattr(args, 'database') and args.database:
        os.environ["NEO4J_DATABASE"] = args.database

    # Execute the appropriate command
    if args.command == "server":
        logger.info("Starting NeoCoder MCP Server")
        if hasattr(args, 'force_clean') and args.force_clean:
            try:
                from .server import cleanup_zombie_instances
                cleanup_zombie_instances(force=True)
            except Exception as e:
                logger.warning(f"Failed to force clean instances: {e}")
        server_main()
    elif args.command == "init":
        logger.info("Initializing Neo4j database")
        init_db_main()
    elif args.command == "cleanup":
        logger.info("Cleaning up server instances")
        from .server import cleanup_zombie_instances
        cleanup_zombie_instances(force=args.force)
        logger.info("Cleanup complete")
    else:
        # Default to server if no command provided
        logger.info("No command specified, starting NeoCoder MCP Server")
        server_main()


if __name__ == "__main__":
    main()
