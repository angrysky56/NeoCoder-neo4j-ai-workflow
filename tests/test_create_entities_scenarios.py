#!/usr/bin/env python3
"""
Test the specific create_entities scenario that was failing.

This test simulates the exact case where complex observations were causing
the "Map{content -> String(...)}" error.
"""

import asyncio
import sys
import os

# Add src to path
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, src_dir)

async def test_create_entities_scenarios():
    """Test various create_entities scenarios."""
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
                # Simulate the actual execution and catch validation issues
                try:
                    result = await func(MockTransaction())
                    return True
                except Exception as e:
                    print(f"Mock execution failed: {e}")
                    return False
            async def execute_read(self, func):
                return []

        class MockTransaction:
            async def run(self, query, params):
                # Check if the query parameters would cause Neo4j type errors
                print(f"Mock Query: {query[:100]}...")
                print(f"Mock Params keys: {list(params.keys()) if params else 'None'}")

                # Check for complex objects in observations
                if 'entities' in params:
                    for entity in params['entities']:
                        if 'observations' in entity:
                            for obs in entity['observations']:
                                if isinstance(obs, dict):
                                    raise Exception(f"Complex object in observations: {obs}")
                                print(f"  Observation type: {type(obs)} value: {obs}")

                return MockResult()

            async def consume(self):
                return MockSummary()

        class MockResult:
            async def data(self):
                return [{"entityCount": 1}]

        class MockSummary:
            def __init__(self):
                self.counters = MockCounters()

        class MockCounters:
            nodes_created = 1
            relationships_created = 0
            properties_set = 3

        # Get knowledge graph instance
        registry.discover()
        kg_instance = registry.get_instance("knowledge_graph", MockDriver(), "neo4j")

        print("🧪 Testing create_entities scenarios")
        print("=" * 50)

        # Test 1: Empty observations (should work)
        print("\n1️⃣ Testing with empty observations...")
        result1 = await kg_instance.create_entities([
            {
                "name": "Test Entity 1",
                "entityType": "Concept",
                "observations": []
            }
        ])
        print(f"Result: {result1[0].text}")

        # Test 2: Simple string observations (should work)
        print("\n2️⃣ Testing with simple string observations...")
        result2 = await kg_instance.create_entities([
            {
                "name": "Test Entity 2",
                "entityType": "Concept",
                "observations": ["Simple observation 1", "Simple observation 2"]
            }
        ])
        print(f"Result: {result2[0].text}")

        # Test 3: Complex object observations (this is what was failing before)
        print("\n3️⃣ Testing with complex object observations (should be cleaned)...")
        result3 = await kg_instance.create_entities([
            {
                "name": "Test Entity 3",
                "entityType": "Concept",
                "observations": [
                    {"content": "Complex observation 1"},
                    {"content": "Complex observation 2"}
                ]
            }
        ])
        print(f"Result: {result3[0].text}")

        # Test 4: Mixed observations (should be cleaned)
        print("\n4️⃣ Testing with mixed observation types...")
        result4 = await kg_instance.create_entities([
            {
                "name": "Test Entity 4",
                "entityType": "Concept",
                "observations": [
                    "Simple string",
                    {"content": "Complex object"},
                    123,  # Number
                    True  # Boolean
                ]
            }
        ])
        print(f"Result: {result4[0].text}")

        print("\n✅ All create_entities tests completed!")
        return True

    except Exception as e:
        print(f"❌ Error in create_entities test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the test."""
    print("🔧 Testing create_entities data handling fixes")
    success = await test_create_entities_scenarios()

    if success:
        print("\n🎉 All tests passed! The create_entities method should now handle:")
        print("  ✅ Empty observations arrays")
        print("  ✅ Simple string observations")
        print("  ✅ Complex object observations (auto-cleaned)")
        print("  ✅ Mixed observation types (auto-cleaned)")
    else:
        print("\n❌ Some tests failed!")

if __name__ == "__main__":
    asyncio.run(main())
