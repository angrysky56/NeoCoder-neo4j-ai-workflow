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
        # Try to get the current event loop
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # No event loop exists in this thread, create a new one
        logger.info("No event loop found in thread, creating a new one")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Store as main loop if not already set
    if _MAIN_LOOP is None:
        logger.info("Initializing main event loop for Neo4j operations")
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
            logger.error("This is likely due to an event loop mismatch issue. Check event loop initialization and usage.")
        elif "Event loop is running" in str(e):
            logger.error("Cannot create new event loop when one is already running.")
        elif "asynchronous context manager protocol" in str(e):
            logger.error("Driver.session() returned an object that doesn't support async context manager protocol. This is likely a mocking issue or driver problem.")
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
    main_loop = get_main_loop()
    if main_loop is None:
        # Initialize if not done yet
        main_loop = initialize_main_loop()
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        logger.error("No running event loop in current thread. Refusing to create a new event loop to avoid conflicts. Please ensure this function is called from within an existing event loop context.")
        raise RuntimeError("No running event loop in current thread. Please call this function from within an existing event loop.")
        # Not running in an event loop - create one
        current_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(current_loop)

    if current_loop is main_loop:
        # Already in the main loop, just await
        logger.debug("Already in main loop, executing directly")
        return await coro
    else:
        # Need to run in the main loop
        if main_loop.is_running():
            # Handle the complex case where the main loop is already running
            logger.warning("Main loop is already running in another thread, using run_coroutine_threadsafe")
            try:
                # Be very careful with timeout - this is a common source of hangs
                future = asyncio.run_coroutine_threadsafe(coro, main_loop)
                result = future.result(timeout=30)  # Increased timeout for complex operations
                logger.info("Successfully executed in main loop via run_coroutine_threadsafe")
                return result
            except asyncio.TimeoutError:
                logger.error("Timeout while waiting for coroutine result from main loop")
                logger.warning("Fallback: Running in current loop after timeout")
                # WARNING: Awaiting the coroutine here may cause 'attached to a different loop' errors.
                raise RuntimeError(
                    "Failed to execute coroutine in the main event loop due to timeout. "
                    "Attempting to await the coroutine in the current loop may cause 'attached to a different loop' errors. "
                    "Please check event loop usage and ensure coroutines are bound to the correct loop."
                )
            except Exception as e:
                logger.error(f"Error running in main loop: {e}")
                logger.warning("Falling back to current loop as last resort")
                return await coro
                return await coro
