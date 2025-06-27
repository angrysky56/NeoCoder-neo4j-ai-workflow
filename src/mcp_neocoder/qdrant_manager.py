"""
Qdrant Management Utility for NeoCoder MCP Server

This module ensures that a Qdrant vector database is available for the MCP server.
It will use a running Qdrant instance if available, or attempt to start one via Docker if not.
It will not install the qdrant Python package unless explicitly requested.
"""

import os
import subprocess
import time
import requests
import logging
import shutil

# Qdrant client import
try:
    from qdrant_client import QdrantClient
except ImportError:
    QdrantClient = None

logger = logging.getLogger("mcp_neocoder.qdrant")

QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))
QDRANT_URL = f"http://{QDRANT_HOST}:{QDRANT_PORT}/"

DOCKER_IMAGE = "qdrant/qdrant:latest"
DOCKER_CONTAINER_NAME = "mcp_qdrant"


def is_qdrant_running() -> bool:
    try:
        resp = requests.get(QDRANT_URL + "health")
        if resp.status_code == 200:
            logger.info("Qdrant is running and healthy.")
            return True
        else:
            logger.warning(f"Qdrant health endpoint returned status {resp.status_code}")
            return False
    except Exception as e:
        logger.info(f"Qdrant not running at {QDRANT_URL}: {e}")
        return False


def start_qdrant_docker() -> bool:
    """Attempt to start Qdrant via Docker."""
    try:
        # Check if already running
        result = subprocess.run([
            "docker", "ps", "-q", "-f", f"name={DOCKER_CONTAINER_NAME}"
        ], capture_output=True, text=True)
        if result.stdout.strip():
            logger.info("Qdrant Docker container already running.")
            return True
        # Start new container
        logger.info("Starting Qdrant via Docker...")
        subprocess.run([
            "docker", "run", "-d",
            "--name", DOCKER_CONTAINER_NAME,
            "-p", f"{QDRANT_PORT}:6333",
            DOCKER_IMAGE
        ], check=True)
        # Wait for Qdrant to become healthy
        for _ in range(20):
            if is_qdrant_running():
                return True
            time.sleep(1)
        logger.error("Qdrant did not become healthy after starting Docker container.")
        return False
    except Exception as e:
        logger.error(f"Failed to start Qdrant via Docker: {e}")
        return False


def ensure_qdrant_available() -> bool:
    """Ensure a Qdrant instance is available for the MCP server."""
    if is_qdrant_running():
        return True
    # Try to start via Docker
    if shutil.which("docker"):
        if start_qdrant_docker():
            return True
        else:
            logger.error("Qdrant could not be started via Docker. Please check Docker logs.")
            return False
    else:
        logger.error("Qdrant is not running and Docker is not available. Please start Qdrant manually.")
        return False


def get_qdrant_client():
    """
    Return a QdrantClient instance using environment config.
    Raises ImportError if qdrant-client is not installed.
    Raises RuntimeError if Qdrant is not available.
    """
    if QdrantClient is None:
        raise ImportError("qdrant-client Python package is not installed. Please install it with 'uv pip install qdrant-client' or add to your pyproject.toml.")
    if not is_qdrant_running():
        raise RuntimeError(f"Qdrant is not running at {QDRANT_URL}. Please ensure Qdrant is available.")
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    logger.info(f"Created QdrantClient for {QDRANT_HOST}:{QDRANT_PORT}")
    return client


# Optionally, call ensure_qdrant_available() at server startup
# Example usage:
# if not ensure_qdrant_available():
#     raise RuntimeError("Qdrant is not available. See logs for details.")
