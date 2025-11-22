import asyncio
import os
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mcp_neocoder")

# Set environment variables
os.environ["NEO4J_URL"] = "bolt://localhost:7687"
os.environ["NEO4J_USERNAME"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "00000000"
os.environ["NEO4J_DATABASE"] = "neo4j"


async def main():
    try:
        print("Importing server...")
        from src.mcp_neocoder.server import create_server

        print("Creating server...")
        server = create_server(os.environ["NEO4J_URL"], os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"], os.environ["NEO4J_DATABASE"])

        print("Calling check_connection...")
        result = await server.check_connection()
        print(f"Result: {result}")

    except Exception as e:
        print(f"Caught exception: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
