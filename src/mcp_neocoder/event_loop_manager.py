"""
Event Loop Manager for NeoCoder

This module provides tools to manage asyncio event loops consistently across the application,
particularly for Neo4j async operations that need to run in the same event loop context.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional
from neo4j import AsyncDriver

logger = logging.getLogger("mcp_neocoder")

# Global reference to the main event loop used for Neo4j operations
_MAIN_LOOP: Optional[asyncio.AbstractEventLoop] = None

def initialize_main_loop() -> asyncio.AbstractEventLoop:
    """Initialize and store the main event loop for the application."""
    global _MAIN_LOOP

    try:
        # Try to get the current running event loop
        loop = asyncio.get_running_loop()
        logger.debug("Found running event loop")
    except RuntimeError:
        # No running event loop, try to get the event loop for this thread
        try:
            loop = asyncio.get_event_loop()
            logger.debug("Found event loop for current thread")
        except RuntimeError:
            # No event loop exists in this thread, create a new one
            logger.info("No event loop found in thread, creating a new one")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

    # Store as main loop if not already set or if we want to update it
    if _MAIN_LOOP is None:
        logger.info("Initializing main event loop for Neo4j operations")
        _MAIN_LOOP = loop
    elif _MAIN_LOOP is not loop:
        logger.warning("Main loop changed, updating reference")
        _MAIN_LOOP = loop

    return loop

def get_main_loop() -> Optional[asyncio.AbstractEventLoop]:
    """Get the main event loop used for Neo4j operations."""
    global _MAIN_LOOP
    return _MAIN_LOOP

async def _handle_session_creation(driver: AsyncDriver, database: str, **kwargs):
    """
    Helper function to handle session creation, dealing with both coroutines and context managers.

    Args:
        driver: Neo4j AsyncDriver
        database: Database name
        **kwargs: Additional arguments to pass to session()

    Returns:
        Async context manager for the session
    """
    session_result = driver.session(database=database, **kwargs)

    # Check if session() returned a coroutine (common with AsyncMock)
    if asyncio.iscoroutine(session_result):
        # If it's a coroutine, await it first to get the actual session
        logger.debug("Driver.session() returned coroutine, awaiting...")
        actual_session = await session_result

        # Now check if the result has async context manager methods
        if hasattr(actual_session, '__aenter__') and hasattr(actual_session, '__aexit__'):
            return actual_session
        else:
            # Create a simple context manager wrapper for non-context manager objects
            class SessionWrapper:
                def __init__(self, session):
                    self.session = session

                async def __aenter__(self):
                    return self.session

                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    # Try to close if possible
                    if hasattr(self.session, 'close') and callable(self.session.close):
                        if asyncio.iscoroutinefunction(self.session.close):
                            await self.session.close()
                        else:
                            self.session.close()

            return SessionWrapper(actual_session)
    else:
        # Normal async context manager case
        return session_result


@asynccontextmanager
async def safe_neo4j_session(driver: AsyncDriver, database: str):
    """
    Create a Neo4j session safely, ensuring event loop consistency and proper tracking.

    This context manager helps avoid "attached to different loop" errors
    by ensuring consistent event loop usage with Neo4j operations.
    """
    # Import tracking functions
    from .process_manager import track_session, untrack_session

    session_cm = None
    try:
        # Create session using the helper function that handles coroutines/context managers
        session_cm = await _handle_session_creation(driver, database)

        # Track the session for cleanup
        track_session(session_cm)

        async with session_cm as session:
            yield session

    except Exception as e:
        logger.error(f"Error in Neo4j session: {e}")
        # Add more detailed error context to help with debugging event loop issues
        if "attached to a different loop" in str(e):
            logger.error("Event loop mismatch detected. This is likely due to asyncio objects being used across different event loops.")
            logger.error("Recommendation: Ensure all Neo4j operations use the same event loop context.")
        elif "Event loop is running" in str(e):
            logger.error("Cannot create new event loop when one is already running.")
        elif "asynchronous context manager protocol" in str(e):
            logger.error("Driver.session() returned an object that doesn't support async context manager protocol.")
        raise
    finally:
        # Always untrack the session
        if session_cm:
            untrack_session(session_cm)

async def run_in_main_loop(coro):
    """
    Run a coroutine in the main event loop.

    Args:
        coro: An awaitable or coroutine object to be executed.

    This is useful for operations that must run in the same loop context
    as the Neo4j driver initialization.
    """
    global _MAIN_LOOP
    
    # Ensure we have a main loop reference
    main_loop = get_main_loop()
    if main_loop is None:
        main_loop = initialize_main_loop()
    
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running event loop - we can't execute async code here
        logger.error("No running event loop in current thread. Cannot execute coroutine.")
        raise RuntimeError("No running event loop in current thread. Please call this function from within an async context.")

    # Check if we're already in the main loop
    if current_loop is main_loop:
        # Already in the main loop, just await directly
        logger.debug("Already in main loop, executing directly")
        return await coro
    else:
        # We're in a different event loop - this is the problematic case
        logger.warning("Running coroutine from different event loop than main loop")
        
        # IMPORTANT: Instead of trying to run in main loop, just run in current loop
        # This prevents the "Future attached to different loop" error
        # The assumption is that if we're already in a running loop, it should work
        logger.info("Executing coroutine in current running loop to avoid loop conflicts")
        return await coro
