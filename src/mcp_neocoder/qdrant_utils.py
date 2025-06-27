"""
qdrant_utils.py - Qdrant client utility for NeoCoder

This module provides a helper to get a Qdrant client instance.
You must have the `qdrant-client` Python package installed.
"""

from typing import Optional

try:
    from qdrant_client import QdrantClient
except ImportError:
    QdrantClient = None

def get_qdrant_client(host: Optional[str] = None, port: Optional[int] = None, api_key: Optional[str] = None):
    """
    Returns a QdrantClient instance using environment variables or defaults.
    Raises ImportError if qdrant-client is not installed.
    """
    import os
    if QdrantClient is None:
        raise ImportError("qdrant-client package is not installed. Please install it with 'pip install qdrant-client'.")

    host = host or os.environ.get("QDRANT_HOST", "localhost")
    port = port or int(os.environ.get("QDRANT_PORT", "6333"))
    api_key = api_key or os.environ.get("QDRANT_API_KEY")

    # If using cloud, you may need to set api_key and https
    kwargs = {"host": host, "port": port}
    if api_key:
        kwargs["api_key"] = api_key
    if os.environ.get("QDRANT_HTTPS", "false").lower() in ("1", "true", "yes"):  # optional
        kwargs["https"] = True

    return QdrantClient(**kwargs)
