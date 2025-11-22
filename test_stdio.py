import subprocess
import json
import os
import sys

# Set environment variables
env = os.environ.copy()
env["NEO4J_URL"] = "bolt://localhost:7687"
env["NEO4J_USERNAME"] = "neo4j"
env["NEO4J_PASSWORD"] = "00000000"
env["NEO4J_DATABASE"] = "neo4j"
env["LOG_LEVEL"] = "DEBUG"


def main():
    print("Starting server process...")
    process = subprocess.Popen(["uv", "run", "mcp_neocoder", "server"], cwd="/home/ty/Repositories/NeoCoder-neo4j-ai-workflow", stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=sys.stderr, env=env, text=True)

    # JSON-RPC request for check_connection
    request = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "check_connection", "arguments": {}}}

    # Also need to initialize first?
    init_request = {"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test-client", "version": "1.0"}}}

    try:
        print("Sending initialize request...")
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()

        print("Reading initialize response...")
        response = process.stdout.readline()
        print(f"Initialize Response: {response}")

        # Send initialized notification
        process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        process.stdin.flush()

        print("Sending check_connection request...")
        process.stdin.write(json.dumps(request) + "\n")
        process.stdin.flush()

        print("Reading check_connection response...")
        response = process.stdout.readline()
        print(f"Check Connection Response: {response}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        process.terminate()


if __name__ == "__main__":
    main()
