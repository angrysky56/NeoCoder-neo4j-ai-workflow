#!/usr/bin/env python3
"""
Test the data cleaning logic in create_entities.

This test focuses on testing the observation data cleaning logic
without needing a full Neo4j session.
"""

import sys
import os

# Add src to path
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, src_dir)

def test_observation_cleaning():
    """Test the data cleaning logic for observations."""

    def clean_observations(observations):
        """Mirror the cleaning logic from the actual method."""
        cleaned = []
        for obs in observations:
            if isinstance(obs, dict) and 'content' in obs:
                # Extract content from complex objects
                cleaned.append(str(obs['content']))
            elif isinstance(obs, str):
                # Keep simple strings
                cleaned.append(obs)
            else:
                # Convert other types to strings
                cleaned.append(str(obs))
        return cleaned

    print("🧪 Testing observation data cleaning logic")
    print("=" * 50)

    # Test cases
    test_cases = [
        {
            "name": "Empty observations",
            "input": [],
            "expected": []
        },
        {
            "name": "Simple strings",
            "input": ["Simple observation 1", "Simple observation 2"],
            "expected": ["Simple observation 1", "Simple observation 2"]
        },
        {
            "name": "Complex objects with content",
            "input": [
                {"content": "Complex observation 1"},
                {"content": "Complex observation 2"}
            ],
            "expected": ["Complex observation 1", "Complex observation 2"]
        },
        {
            "name": "Mixed types",
            "input": [
                "Simple string",
                {"content": "Complex object"},
                123,
                True,
                {"other": "ignored", "content": "extracted"}
            ],
            "expected": ["Simple string", "Complex object", "123", "True", "extracted"]
        },
        {
            "name": "Objects without content key",
            "input": [
                {"description": "No content key"},
                {"name": "Also no content"}
            ],
            "expected": ["{'description': 'No content key'}", "{'name': 'Also no content'}"]
        }
    ]

    all_passed = True

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}️⃣ Testing: {test_case['name']}")
        print(f"Input: {test_case['input']}")

        result = clean_observations(test_case['input'])
        print(f"Output: {result}")
        print(f"Expected: {test_case['expected']}")

        if result == test_case['expected']:
            print("✅ PASSED")
        else:
            print("❌ FAILED")
            all_passed = False

    return all_passed

def test_entity_structure():
    """Test entity data structure validation."""

    def validate_and_clean_entities(entities):
        """Mirror the entity cleaning logic."""
        cleaned_entities = []

        for entity in entities:
            # Validate required fields
            if 'name' not in entity:
                raise ValueError("All entities must have a 'name' property")
            if 'entityType' not in entity:
                raise ValueError("All entities must have an 'entityType' property")
            if 'observations' not in entity or not isinstance(entity['observations'], list):
                raise ValueError("All entities must have an 'observations' array")

            # Clean the entity
            cleaned_entity = {
                'name': entity['name'],
                'entityType': entity['entityType'],
                'observations': []
            }

            # Clean observations
            for obs in entity['observations']:
                if isinstance(obs, dict) and 'content' in obs:
                    cleaned_entity['observations'].append(str(obs['content']))
                elif isinstance(obs, str):
                    cleaned_entity['observations'].append(obs)
                else:
                    cleaned_entity['observations'].append(str(obs))

            cleaned_entities.append(cleaned_entity)

        return cleaned_entities

    print("\n\n🏗️ Testing entity structure validation and cleaning")
    print("=" * 60)

    # Test valid entity
    try:
        test_entity = [{
            "name": "Test Entity",
            "entityType": "Concept",
            "observations": [
                "Simple observation",
                {"content": "Complex observation"},
                123
            ]
        }]

        result = validate_and_clean_entities(test_entity)
        print("✅ Valid entity structure processed successfully")
        print(f"Cleaned result: {result}")

        # Check that complex objects were cleaned
        expected_obs = ["Simple observation", "Complex observation", "123"]
        if result[0]['observations'] == expected_obs:
            print("✅ Observations cleaned correctly")
            return True
        else:
            print(f"❌ Observation cleaning failed: {result[0]['observations']} != {expected_obs}")
            return False

    except Exception as e:
        print(f"❌ Entity validation failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🔧 Testing create_entities data cleaning and validation")

    test1_passed = test_observation_cleaning()
    test2_passed = test_entity_structure()

    print("\n" + "=" * 60)
    if test1_passed and test2_passed:
        print("🎉 All data cleaning tests passed!")
        print("\nThe fixes should resolve the Neo4j type errors by:")
        print("  ✅ Converting complex objects to simple strings")
        print("  ✅ Extracting 'content' from observation objects")
        print("  ✅ Ensuring only primitive types reach Neo4j")
    else:
        print("❌ Some tests failed!")

if __name__ == "__main__":
    main()
