#!/usr/bin/env python3
"""
Test the fixed create_entities method
"""

import asyncio
import sys
import os

# Add src to path
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, src_dir)

async def test_create_entities_fix():
    """Test the create_entities method with various input formats."""
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
                # Simulate the function call to test parameter processing
                await func({"entities": []})
                return True

        # Get knowledge graph incarnation
        registry.discover()
        kg_instance = registry.get_instance("knowledge_graph", MockDriver(), "neo4j")

        print("🧪 Testing create_entities with different input formats...")

        # Test 1: Simple string observations (should work)
        test1_entities = [
            {
                "name": "Test Entity 1",
                "entityType": "Test",
                "observations": ["Simple string observation"]
            }
        ]

        print("\n📝 Test 1: Simple string observations")
        result1 = await kg_instance.create_entities(test1_entities)
        print(f"Result: {result1[0].text}")

        # Test 2: Complex object observations (should be cleaned)
        test2_entities = [
            {
                "name": "Test Entity 2",
                "entityType": "Test",
                "observations": [{"content": "Complex object observation"}]
            }
        ]

        print("\n📝 Test 2: Complex object observations (should be auto-cleaned)")
        result2 = await kg_instance.create_entities(test2_entities)
        print(f"Result: {result2[0].text}")

        # Test 3: Empty observations (should work)
        test3_entities = [
            {
                "name": "Test Entity 3",
                "entityType": "Test",
                "observations": []
            }
        ]

        print("\n📝 Test 3: Empty observations")
        result3 = await kg_instance.create_entities(test3_entities)
        print(f"Result: {result3[0].text}")

        # Test 4: Mixed observation types (should be cleaned)
        test4_entities = [
            {
                "name": "Test Entity 4",
                "entityType": "Test",
                "observations": [
                    "Simple string",
                    {"content": "Complex object"},
                    123,  # Number
                    None  # Should be skipped
                ]
            }
        ]

        print("\n📝 Test 4: Mixed observation types (should be auto-cleaned)")
        result4 = await kg_instance.create_entities(test4_entities)
        print(f"Result: {result4[0].text}")

        print("\n✅ All tests completed!")
        return True

    except Exception as e:
        print(f"❌ Error testing create_entities: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_create_entities_fix())
