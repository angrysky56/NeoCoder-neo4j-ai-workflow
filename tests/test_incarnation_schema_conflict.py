#!/usr/bin/env python3
"""
Test to reproduce the schema conflict bug when switching incarnations.

This test demonstrates the issue where existing indexes conflict with
constraint creation during incarnation switching.
"""

import asyncio
import pytest
from neo4j import AsyncGraphDatabase
from src.mcp_neocoder.incarnation_registry import registry

async def test_incarnation_switch_schema_conflict():
    """
    Test that reproduces the schema conflict when switching to coding incarnation.
    
    This test should FAIL initially, demonstrating the bug.
    After the fix, it should PASS.
    """
    # Use the same connection settings as the main system
    driver = AsyncGraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "00000000")
    )
    
    try:
        # Get coding incarnation instance
        coding_incarnation = registry.get_instance("coding", driver, "neo4j")
        assert coding_incarnation is not None, "Could not get coding incarnation"
        
        # This should work without throwing schema conflict errors
        await coding_incarnation.initialize_schema()
        
        print("✅ Incarnation schema initialization succeeded")
        
    except Exception as e:
        print(f"❌ Schema conflict error: {e}")
        # Re-raise the exception to make the test fail
        raise e
        
    finally:
        await driver.close()

async def test_index_constraint_conflict_detection():
    """
    Test that checks for the specific index/constraint conflict on File.path.
    """
    driver = AsyncGraphDatabase.driver(
        "bolt://localhost:7687", 
        auth=("neo4j", "00000000")
    )
    
    try:
        async with driver.session(database="neo4j") as session:
            # Check if File.path index exists
            result = await session.run(
                "SHOW INDEXES WHERE labelsOrTypes = ['File'] AND properties = ['path']"
            )
            indexes = [record async for record in result]
            
            # Check if File.path constraint exists  
            result = await session.run(
                "SHOW CONSTRAINTS WHERE labelsOrTypes = ['File'] AND properties = ['path']"
            )
            constraints = [record async for record in result]
            
            print(f"Found {len(indexes)} indexes on File.path")
            print(f"Found {len(constraints)} constraints on File.path")
            
            # The bug is that we have an index but are trying to create a constraint
            if len(indexes) > 0 and len(constraints) == 0:
                print("❌ Detected: INDEX exists but no CONSTRAINT - this causes the conflict")
                return False
            else:
                print("✅ No conflict detected")
                return True
                
    finally:
        await driver.close()

if __name__ == "__main__":
    print("Testing incarnation schema conflict...")
    
    # Test 1: Check for the specific index/constraint conflict
    result = asyncio.run(test_index_constraint_conflict_detection())
    if not result:
        print("❌ Conflict detected - proceeding to test incarnation switch...")
        
        # Test 2: Try to reproduce the actual error
        try:
            asyncio.run(test_incarnation_switch_schema_conflict())
            print("❌ TEST SHOULD HAVE FAILED - Bug may already be fixed")
        except Exception as e:
            print(f"✅ TEST FAILED AS EXPECTED - Bug reproduced: {e}")
    else:
        print("❌ No conflict detected - trying incarnation switch anyway...")
        asyncio.run(test_incarnation_switch_schema_conflict())
