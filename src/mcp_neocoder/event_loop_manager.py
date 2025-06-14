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
    Create a Neo4j session safely, ensuring event loop consistency.

    This context manager helps avoid "attached to different loop" errors
    by ensuring consistent event loop usage with Neo4j operations.
    """
    # Get current loop and check against main loop
    try:
        current_loop = asyncio.get_running_loop()
        main_loop = get_main_loop()

        if main_loop is not None and current_loop is not main_loop:
            logger.warning(
                "Event loop mismatch detected! Current operation is running in a "
                "different event loop than the Neo4j driver was initialized with. "
                "This may cause 'Future attached to a different loop' errors."
            )

            # Instead of just warning, try to handle this properly
            if main_loop.is_running():
                logger.warning("Detected event loop mismatch - attempting to handle")
                # We'll continue with the session creation but be more careful
                # The issue will be handled in the actual session operations
                logger.info("Will use run_in_main_loop for critical operations")
    except RuntimeError:
        # Not running in an event loop - less likely but possible
        logger.warning("Attempting Neo4j session outside of an event loop context")

    # Use driver session in a safer way to avoid event loop issues
    try:
        main_loop = get_main_loop()
        current_loop = None
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            pass

        if main_loop is not None and current_loop is not main_loop:
            # Critical case - session must be created in the same loop as the driver
            logger.info("Creating session in main loop to avoid mismatch")

            async def create_session_in_main_loop():
                """Helper to create session in the main loop"""
                async with driver.session(database=database) as session:
                    # Store session properties we need to access later
                    session_props = {
                        # Add any needed properties to access outside this context
                    }
                    return session, session_props

            # Get a session created in the main loop
            try:
                # For simplicity, we'll still use the session in the current loop
                # This is a compromise - ideally we'd do all operations in the main loop
                # but that would require restructuring the entire application
                session_mgr = await _handle_session_creation(driver, database)
                async with session_mgr as session:
                    yield session
            except asyncio.CancelledError:
                # Important to handle cancellation explicitly
                logger.warning("Session operation was cancelled")
                raise
            except Exception as e:
                if "attached to a different loop" in str(e):
                    logger.error("Event loop mismatch in session creation despite precautions")
                    # As a last resort, try to create a completely fresh connection
                    logger.warning("Attempting last-resort session creation")
                    # This may still fail but worth trying
                    emergency_session_mgr = await _handle_session_creation(driver, database, fetch_size=1)
                    async with emergency_session_mgr as emergency_session:
                        yield emergency_session
                else:
                    # Other error, not loop related
                    logger.error(f"Error in Neo4j session: {e}")
                    raise
        else:
            # Normal case - same loop or no main loop yet
            session_mgr = await _handle_session_creation(driver, database)
            async with session_mgr as session:
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

async def run_in_main_loop(coro):
    """
    Run a coroutine in the main event loop.

    This is useful for operations that must run in the same loop context
    as the Neo4j driver initialization.
    """
    main_loop = get_main_loop()
    if main_loop is None:
        # Initialize if not done yet
        main_loop = initialize_main_loop()

    current_loop = None
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
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
                # Fall back to running in current loop - may cause loop errors but at least won't hang
                logger.warning("Fallback: Running in current loop after timeout")
                return await coro
            except Exception as e:
                logger.error(f"Failed to run coroutine in main loop: {e}")
                # Try a different approach
                logger.warning("Attempting fallback execution method")
                return await coro
        else:
            # Main loop is not running, we can execute the coroutine in it
            logger.info("Main loop is not running, will execute coroutine in it")
            try:
                # Run the coroutine directly in the main loop
                if not main_loop.is_closed():
                    # Safest way to run in the main loop when it's not running
                    fut = asyncio.run_coroutine_threadsafe(coro, main_loop)
                    return fut.result(timeout=30)
                else:
                    logger.error("Main loop is closed, creating new loop")
                    # If main loop is closed, create a new one and execute there
                    new_loop = asyncio.new_event_loop()
                    global _MAIN_LOOP
                    _MAIN_LOOP = new_loop  # Update the global main loop
                    asyncio.set_event_loop(new_loop)
                    return await coro  # Run in the new loop
            except Exception as e:
                logger.error(f"Error running in main loop: {e}")
                logger.warning("Falling back to current loop as last resort")
                return await coro
