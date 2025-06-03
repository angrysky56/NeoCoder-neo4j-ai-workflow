#!/usr/bin/env python3
"""
Simple script to check the IncarnationType enum and ensure it can be imported correctly.
"""

import sys
import os
from enum import Enum

# Add src to Python path
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, src_dir)

def mock_neo4j_and_mcp():
    """Create mock modules to avoid dependency issues."""
    # Mock neo4j
    class MockAsyncTransaction:
        async def run(self, query, params=None):
            return None
    
    class MockModule:
        AsyncDriver = object
        AsyncGraphDatabase = object
        AsyncTransaction = MockAsyncTransaction
    
    # Add mock modules to sys.modules
    sys.modules['neo4j'] = MockModule
    
    # Mock MCP types
    class MockTypes:
        class TextContent:
            def __init__(self, type="text", text=""):
                self.type = type
                self.text = text
    
    class MockMCP:
        types = MockTypes
    
    sys.modules['mcp'] = MockMCP
    sys.modules['mcp.types'] = MockMCP.types
    sys.modules['mcp.server'] = MockModule
    sys.modules['mcp.server.fastmcp'] = MockModule

def main():
    """Main function to check incarnation types."""
    print("Creating mock modules...")
    mock_neo4j_and_mcp()
    
    print("Importing IncarnationType directly...")
    try:
        from mcp_neocoder.incarnations.base_incarnation import IncarnationType
        
        print("IncarnationType values:")
        for t in IncarnationType:
            print(f"  {t.name} = {t.value}")
            
        return True
    except Exception as e:
        print(f"Error importing IncarnationType: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    main()
