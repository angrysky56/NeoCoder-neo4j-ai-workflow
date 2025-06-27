"""
Process and Resource Management for NeoCoder MCP Server

This module implements essential cleanup patterns to prevent process leaks
and ensure proper resource management as outlined in MCP best practices.
"""

import asyncio
import atexit
import logging
import os
import signal
import subprocess
import sys
import threading
import time
from typing import Dict, List, Optional, Set, Any
from neo4j import AsyncDriver

logger = logging.getLogger("mcp_neocoder")

# Timeout configurations for different scenarios
TIMEOUTS = {
    "tool_operation": 900.0,  # 15 minutes for tool operations (generous)
    "shutdown_task_cancel": 10.0,  # 10 seconds for task cancellation during shutdown
    "shutdown_process_terminate": 15.0,  # 15 seconds for process termination
    "shutdown_process_kill": 5.0,  # 5 seconds after SIGKILL
    "shutdown_cleanup_total": 30.0,  # 30 seconds total for full cleanup
    "subprocess_default": 600.0,  # 10 minutes default for subprocesses
}

# Global tracking dictionaries for cleanup
running_processes: Dict[str, subprocess.Popen] = {}
background_tasks: Set[asyncio.Task] = set()
active_drivers: Set[AsyncDriver] = set()
active_sessions: Set[Any] = set()
tool_operations: Set[asyncio.Task] = set()  # Track legitimate tool operations separately
cleanup_lock = threading.Lock()
_cleanup_registered = False
_shutdown_in_progress = False


def track_tool_operation(task: asyncio.Task) -> None:
    """Track a tool operation task separately from background tasks.

    Tool operations get more generous timeouts and special handling during shutdown.

    Args:
        task: The asyncio task performing a tool operation
    """
    with cleanup_lock:
        tool_operations.add(task)
        # Also add to background_tasks for general tracking
        background_tasks.add(task)
        task.add_done_callback(lambda t: _cleanup_tool_operation(t))
        logger.debug(f"Tracking tool operation, total: {len(tool_operations)}")


def _cleanup_tool_operation(task: asyncio.Task) -> None:
    """Internal cleanup function for completed tool operations."""
    with cleanup_lock:
        tool_operations.discard(task)
        background_tasks.discard(task)


def track_background_task(task: asyncio.Task) -> None:
    """Track a background task for cleanup.

    Args:
        task: The asyncio task to track
    """
    with cleanup_lock:
        background_tasks.add(task)
        task.add_done_callback(lambda t: background_tasks.discard(t))


def track_process(process_id: str, process: subprocess.Popen) -> None:
    """Track a subprocess for cleanup.

    Args:
        process_id: Unique identifier for the process
        process: The subprocess.Popen object
    """
    with cleanup_lock:
        running_processes[process_id] = process
        logger.info(f"Tracking process {process_id} (PID: {process.pid})")


def untrack_process(process_id: str) -> None:
    """Remove a process from tracking.

    Args:
        process_id: The process identifier to untrack
    """
    with cleanup_lock:
        if process_id in running_processes:
            del running_processes[process_id]
            logger.info(f"Untracked process {process_id}")


def track_driver(driver: AsyncDriver) -> None:
    """Track a Neo4j driver for cleanup.

    Args:
        driver: The Neo4j AsyncDriver to track
    """
    with cleanup_lock:
        active_drivers.add(driver)
        logger.debug(f"Tracking Neo4j driver, total: {len(active_drivers)}")


def untrack_driver(driver: AsyncDriver) -> None:
    """Remove a driver from tracking.

    Args:
        driver: The driver to untrack
    """
    with cleanup_lock:
        active_drivers.discard(driver)
        logger.debug(f"Untracked Neo4j driver, remaining: {len(active_drivers)}")


def track_session(session: Any) -> None:
    """Track a Neo4j session for cleanup.

    Args:
        session: The Neo4j session to track
    """
    with cleanup_lock:
        active_sessions.add(session)
        logger.debug(f"Tracking Neo4j session, total: {len(active_sessions)}")


def untrack_session(session: Any) -> None:
    """Remove a session from tracking.

    Args:
        session: The session to untrack
    """
    with cleanup_lock:
        active_sessions.discard(session)
        logger.debug(f"Untracked Neo4j session, remaining: {len(active_sessions)}")


async def cleanup_processes() -> None:
    """Clean up all running processes, background tasks, Neo4j sessions, and Neo4j drivers.

    This function ensures that all tracked subprocesses, asyncio tasks, Neo4j sessions, and drivers
    are properly terminated or closed to prevent resource leaks during shutdown.
    """
    global _shutdown_in_progress
    _shutdown_in_progress = True

    logger.info("Starting process cleanup...")

    # Handle tool operations with more grace
    with cleanup_lock:
        tool_tasks = list(tool_operations)
        tool_count = len(tool_tasks)
    if tool_count > 0:
        logger.info(f"Waiting for {tool_count} tool operations to complete...")

        for task in tool_tasks:
            if not task.done():
                try:
                    # Wait longer for tool operations (they might be doing important work)
                    await asyncio.wait_for(task, timeout=TIMEOUTS["shutdown_task_cancel"])
                    logger.info("Tool operation completed gracefully during shutdown")
                except asyncio.TimeoutError:
                    logger.warning(f"Tool operation didn't complete in {TIMEOUTS['shutdown_task_cancel']}s, cancelling")
                    task.cancel()
                    try:
                        await asyncio.wait_for(task, timeout=2.0)
                    except (asyncio.CancelledError, asyncio.TimeoutError):
                        pass
                except Exception as e:
                    logger.error(f"Error waiting for tool operation: {e}")

        with cleanup_lock:
            for task in tool_tasks:
                tool_operations.discard(task)

    # Cancel remaining background tasks (non-tool operations)
    with cleanup_lock:
        remaining_tasks = background_tasks - tool_operations
        task_list = list(remaining_tasks)
        task_count = len(task_list)
    if task_count > 0:
        logger.info(f"Cancelling {task_count} background tasks")
        for task in task_list:
            if not task.done():
                task.cancel()
                try:
                    await asyncio.wait_for(task, timeout=2.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
        with cleanup_lock:
            for task in task_list:
                background_tasks.discard(task)
            background_tasks.clear()

    # Terminate all processes (with longer timeout for graceful shutdown)
    with cleanup_lock:
        processes = list(running_processes.items())
        process_count = len(processes)
    if process_count > 0:
        logger.info(f"Terminating {process_count} running processes")
        for job_id, process in processes:
            if process and process.poll() is None:
                logger.info(f"Terminating process {job_id} (PID: {process.pid})")
                try:
                    process.terminate()
                    try:
                        process.wait(timeout=TIMEOUTS["shutdown_process_terminate"])
                        logger.info(f"Process {job_id} terminated gracefully")
                    except subprocess.TimeoutExpired:
                        logger.warning(f"Process {job_id} did not terminate, killing")
                        process.kill()
                        process.wait(timeout=TIMEOUTS["shutdown_process_kill"])
                except Exception as e:
                    logger.error(f"Error terminating process {job_id}: {e}")
        with cleanup_lock:
            running_processes.clear()
    # Close Neo4j sessions
    with cleanup_lock:
        sessions = list(active_sessions)
        session_count = len(sessions)
    if session_count > 0:
        logger.info(f"Closing {session_count} Neo4j sessions")
        for session in sessions:
            try:
                if hasattr(session, 'close'):
                    if asyncio.iscoroutinefunction(session.close):
                        try:
                            await session.close()
                        except Exception as e:
                            # Ignore errors if session is already closed
                            if "closed" in str(e).lower():
                                logger.debug(f"Session already closed: {e}")
                            else:
                                logger.error(f"Error closing session: {e}")
                    else:
                        try:
                            session.close()
                        except Exception as e:
                            if "closed" in str(e).lower():
                                logger.debug(f"Session already closed: {e}")
                            else:
                                logger.error(f"Error closing session: {e}")
            except Exception as e:
                logger.error(f"Unexpected error closing session: {e}")
        with cleanup_lock:
            active_sessions.clear()

    with cleanup_lock:
        drivers = list(active_drivers)
        driver_count = len(drivers)
    if driver_count > 0:
        logger.info(f"Closing {driver_count} Neo4j drivers")
        for driver in drivers:
            try:
                await driver.close()
                logger.debug("Neo4j driver closed successfully")
            except Exception as e:
                logger.error(f"Error closing Neo4j driver: {e}")
        with cleanup_lock:
            active_drivers.clear()

    logger.info("Process cleanup completed")


def cleanup_processes_sync() -> None:
    """Synchronous wrapper for cleanup_processes."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # If loop is running, we can't use run_until_complete.
        # Submit the coroutine to the running loop from this (main) thread.
        future = asyncio.run_coroutine_threadsafe(cleanup_processes(), loop)
        try:
            # Use longer timeout during shutdown to allow tool operations to complete
            future.result(timeout=TIMEOUTS["shutdown_cleanup_total"])
            logger.info("Synchronous cleanup completed via running loop.")
        except Exception as e:
            logger.error(f"Error waiting for cleanup future: {e}")
    else:
        # No running loop, or it's closed. Use asyncio.run() to create a new one.
        try:
            logger.info("No running event loop, creating new one for cleanup.")
            asyncio.run(cleanup_processes())
            logger.info("Synchronous cleanup completed via new loop.")
        except Exception as e:
            logger.error(f"Error in synchronous cleanup with new loop: {e}")


def signal_handler(signum: int, frame: Any) -> None:
    """Handle shutdown signals gracefully.

    Args:
        signum: Signal number
        frame: Current stack frame
    """
    logger.info(f"Received signal {signum}, initiating graceful shutdown")
    try:
        cleanup_processes_sync()
    except Exception as e:
        logger.error(f"Error during signal cleanup: {e}")
    finally:
        sys.exit(0)


def register_cleanup_handlers() -> None:
    """Register cleanup handlers for signals and exit."""
    global _cleanup_registered

    if _cleanup_registered:
        logger.debug("Cleanup handlers already registered")
        return

    try:
        # Register signal handlers
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        logger.info("Registered signal handlers for SIGTERM and SIGINT")

        # Register atexit handler
        atexit.register(cleanup_processes_sync)
        logger.info("Registered atexit cleanup handler")

        _cleanup_registered = True

    except Exception as e:
        logger.error(f"Failed to register cleanup handlers: {e}")


def cleanup_zombie_instances() -> int:
    """Clean up any orphaned server processes.

    Returns:
        Number of processes cleaned up
    """
    import psutil

    logger.info("Scanning for zombie NeoCoder MCP server instances...")
    cleaned_count = 0

    try:
        current_pid = os.getpid()

        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            info = None  # Ensure info is always defined
            try:
                info = proc.info
                if not info['cmdline']:
                    continue

                # Look for mcp_neocoder processes
                cmdline_str = ' '.join(info['cmdline']).lower()
                if ('mcp_neocoder' in cmdline_str or
                    'neocoder' in cmdline_str) and info['pid'] != current_pid:

                    # Check if it's actually a zombie or orphaned process
                    try:
                        proc_obj = psutil.Process(info['pid'])
                        if proc_obj.status() in [psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD]:
                            logger.info(f"Found zombie process: PID {info['pid']}")
                            proc_obj.terminate()
                            cleaned_count += 1
                        elif not proc_obj.is_running():
                            logger.info(f"Found dead process: PID {info['pid']}")
                            cleaned_count += 1
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # Process already cleaned up or no permission
                        pass

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Process no longer exists or no permission
                continue
            except Exception as e:
                pid = info.get('pid', 'unknown') if info else 'unknown'
                logger.debug(f"Error checking process {pid}: {e}")
                continue

    except Exception as e:
        logger.error(f"Error during zombie cleanup: {e}")

    if cleaned_count > 0:
        logger.info(f"Cleaned up {cleaned_count} zombie processes")
    else:
        logger.info("No zombie processes found")

    return cleaned_count


async def safe_subprocess_run(cmd: List[str], timeout: Optional[float] = None,
                            process_id: Optional[str] = None,
                            is_tool_operation: bool = False) -> subprocess.CompletedProcess:
    """Run a subprocess safely with proper cleanup tracking.

    Args:
        cmd: Command to run as list of strings
        timeout: Timeout in seconds (defaults based on operation type)
        process_id: Optional identifier for tracking
        is_tool_operation: If True, uses longer timeout for tool operations

    Returns:
        CompletedProcess object

    Raises:
        asyncio.TimeoutError: If process times out
        subprocess.SubprocessError: If process fails
    """
    # Choose appropriate timeout based on operation type
    if timeout is None:
        timeout = TIMEOUTS["tool_operation"] if is_tool_operation else TIMEOUTS["subprocess_default"]

    proc_id = process_id or f"proc_{int(time.time())}"

    # Check if shutdown is in progress
    if _shutdown_in_progress and is_tool_operation:
        logger.warning(f"Tool operation {proc_id} starting during shutdown - may be interrupted")

    try:
        # Start the process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Track the process
        track_process(proc_id, process)

        try:
            # Wait for completion with timeout
            stdout, stderr = process.communicate(timeout=timeout)
            return_code = process.returncode

            # Create result object
            result = subprocess.CompletedProcess(
                args=cmd,
                returncode=return_code,
                stdout=stdout,
                stderr=stderr
            )

            if return_code != 0:
                logger.warning(f"Process {proc_id} exited with code {return_code}")
                logger.warning(f"stderr: {stderr}")

            return result

        except subprocess.TimeoutExpired:
            operation_type = "tool operation" if is_tool_operation else "subprocess"
            logger.error(f"{operation_type.title()} {proc_id} timed out after {timeout}s")
            process.kill()
            process.wait()
            raise asyncio.TimeoutError(f"{operation_type.title()} timed out after {timeout}s")

    finally:
        # Always untrack the process
        untrack_process(proc_id)


def get_cleanup_status() -> Dict[str, Any]:
    """Get current cleanup status for monitoring.

    Returns:
        Dictionary with cleanup status information
    """
    with cleanup_lock:
        return {
            "running_processes": len(running_processes),
            "background_tasks": len(background_tasks),
            "tool_operations": len(tool_operations),
            "active_drivers": len(active_drivers),
            "active_sessions": len(active_sessions),
            "cleanup_registered": _cleanup_registered,
            "shutdown_in_progress": _shutdown_in_progress,
            "process_ids": list(running_processes.keys()),
            "timeouts": TIMEOUTS
        }
