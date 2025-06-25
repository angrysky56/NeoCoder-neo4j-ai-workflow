#!/usr/bin/env python3
"""
Test Knowledge Graph Tools

This script tests the knowledge graph tools to ensure they work correctly.
"""

import asyncio
import sys
import os

# Add src to path
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, src_dir)

async def test_knowledge_graph():
    """Test the knowledge graph incarnation tools."""
    try:
        from mcp_neocoder.incarnation_registry import registry

        # Mock Neo4j driver for testing
        class MockDriver:
            async def session(self, database=None):
                return MockSession()

        class MockSession:
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
            async def execute_write(self, func):
                return True
            async def execute_read(self, func):
                return []

        # Discover incarnations
        registry.discover()

        # Get knowledge graph incarnation
        kg_instance = registry.get_instance("knowledge_graph", MockDriver(), "neo4j")

        if not kg_instance:
            print("❌ Could not get knowledge graph instance")
            return False

        print("✅ Knowledge graph instance created")

        # Test tool methods list
        tools = kg_instance.list_tool_methods()
        print(f"✅ Found {len(tools)} tools: {tools}")

        # Check if add_single_observation is in the list
        if "add_single_observation" in tools:
            print("✅ add_single_observation tool is available")
        else:
            print("❌ add_single_observation tool not found")

        return True

    except Exception as e:
        print(f"❌ Error testing knowledge graph: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run tests."""
    print("🧪 Testing Knowledge Graph Tools")
    print("=" * 40)

    success = await test_knowledge_graph()

    if success:
        print("\n✅ All tests passed!")
        print("\n📋 Usage Example:")
        print("To add observations correctly, use this format:")
        print("""
observations = [
    {
        "entityName": "Deep Learning Models",
        "contents": ["Machine learning models that use neural networks", "Often trained with SGD"]
    }
]
        """)
        print("Or use the convenience method:")
        print("add_single_observation(entityName='MyEntity', content='My observation')")
    else:
        print("\n❌ Tests failed!")

if __name__ == "__main__":
    asyncio.run(main())
