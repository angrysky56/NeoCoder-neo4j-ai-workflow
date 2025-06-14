"""
Test to demonstrate and verify the event loop manager async context manager bug fix.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from src.mcp_neocoder.event_loop_manager import safe_neo4j_session, initialize_main_loop


@pytest.mark.asyncio
async def test_safe_neo4j_session_with_async_mock():
    """
    Test that reproduces the 'coroutine object does not support async context manager' error.
    This test should FAIL initially, demonstrating the bug.
    """
    # Create a mock driver that returns a coroutine when .session() is called
    mock_driver = AsyncMock()
    
    # The bug: AsyncMock.session() returns a coroutine, not an async context manager
    # This simulates the exact error we're seeing in production
    
    try:
        async with safe_neo4j_session(mock_driver, "neo4j") as session:
            # This should work after the fix
            assert session is not None
        
        # If we reach here, the test passed (which means the bug is fixed)
        assert True, "safe_neo4j_session handled async mock correctly"
        
    except TypeError as e:
        if "asynchronous context manager protocol" in str(e):
            # This is the expected error before the fix - test should fail initially
            pytest.fail(f"Bug reproduced: {e}")
        else:
            # Different error, re-raise
            raise


@pytest.mark.asyncio 
async def test_safe_neo4j_session_with_proper_context_manager():
    """
    Test that safe_neo4j_session works with a properly implemented async context manager.
    This test should PASS both before and after the fix.
    """
    
    class MockAsyncSession:
        async def __aenter__(self):
            return self
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
            
        async def run(self, query):
            return MagicMock()
    
    class MockDriver:
        def session(self, database=None):
            return MockAsyncSession()
    
    mock_driver = MockDriver()
    
    # This should work both before and after the fix
    async with safe_neo4j_session(mock_driver, "neo4j") as session:
        assert session is not None
        

@pytest.mark.asyncio
async def test_event_loop_mismatch_handling():
    """
    Test that event loop mismatch is handled gracefully.
    """
    # Initialize a main loop
    main_loop = initialize_main_loop()
    
    # Create a mock driver
    mock_driver = AsyncMock()
    
    # The session creation should not crash even with loop mismatches
    try:
        async with safe_neo4j_session(mock_driver, "neo4j") as session:
            # Should work after the fix
            pass
    except Exception as e:
        # Should not have async context manager errors after fix
        assert "asynchronous context manager protocol" not in str(e), f"Async context manager bug still present: {e}"
