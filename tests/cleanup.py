#!/usr/bin/env python3
"""
NeoCoder MCP Server Cleanup Script

This script helps to clean up orphaned or zombie NeoCoder MCP server instances
that might have been left running due to improper shutdown.

Usage:
  python cleanup.py [--force]
  
Options:
  --force    Force kill all running instances (use with caution)
"""

import os
import sys
import argparse
import subprocess
import signal
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("neocoder_cleanup")

def cleanup_instances(force=False):
    """Clean up orphaned or zombie server instances.
    
    Args:
        force: If True, kill all mcp_neocoder processes regardless of their state
    """
    logger.info(f"Looking for orphaned mcp_neocoder instances (force={force})")
    
    # Find all running NeoCoder processes
    try:
        output = subprocess.check_output("ps aux | grep mcp_neocoder | grep -v grep", shell=True, text=True)
        processes = []
        
        for line in output.splitlines():
            parts = line.strip().split()
            if len(parts) < 2:
                continue
                
            try:
                pid = int(parts[1])
                cmd = " ".join(parts[10:])
                processes.append((pid, cmd))
            except:
                continue
        
        if not processes:
            logger.info("No running mcp_neocoder processes found")
            return
            
        logger.info(f"Found {len(processes)} running mcp_neocoder processes:")
        for pid, cmd in processes:
            logger.info(f"  PID {pid}: {cmd}")
        
        # Get current PID
        current_pid = os.getpid()
        
        # Identify which processes to kill
        to_kill = []
        for pid, cmd in processes:
            # Don't kill current process or parent process
            if pid == current_pid or pid == os.getppid():
                logger.info(f"Skipping current process or parent: {pid}")
                continue
                
            # In force mode, kill all other processes
            if force:
                to_kill.append(pid)
                continue
                
            # Ask for confirmation if not in force mode
            if not force:
                response = input(f"Kill process {pid} ({cmd})? [y/N]: ")
                if response.lower() in ('y', 'yes'):
                    to_kill.append(pid)
        
        # Kill processes
        for pid in to_kill:
            try:
                os.kill(pid, signal.SIGTERM)
                logger.info(f"Sent SIGTERM to process {pid}")
            except Exception as e:
                logger.warning(f"Failed to terminate process {pid}: {e}")
        
        # Wait a moment for processes to terminate
        if to_kill:
            logger.info("Waiting for processes to terminate...")
            time.sleep(2)
            
            # Check if any processes are still running
            still_running = []
            for pid in to_kill:
                try:
                    os.kill(pid, 0)  # This will raise an exception if process doesn't exist
                    still_running.append(pid)
                except OSError:
                    logger.info(f"Process {pid} terminated successfully")
            
            # Force kill if needed
            if still_running:
                logger.warning(f"Some processes still running after SIGTERM: {still_running}")
                for pid in still_running:
                    response = "n"
                    if force:
                        response = "y"
                    else:
                        response = input(f"Force kill process {pid} with SIGKILL? [y/N]: ")
                    
                    if response.lower() in ('y', 'yes'):
                        try:
                            os.kill(pid, signal.SIGKILL)
                            logger.info(f"Sent SIGKILL to process {pid}")
                        except Exception as e:
                            logger.warning(f"Failed to kill process {pid}: {e}")
    
    except subprocess.CalledProcessError:
        # No processes found
        logger.info("No running mcp_neocoder processes found")
    except Exception as e:
        logger.error(f"Error cleaning up instances: {e}")

def main():
    """Main function for the cleanup script."""
    parser = argparse.ArgumentParser(description="NeoCoder MCP Server Cleanup Script")
    parser.add_argument("--force", action="store_true", help="Force kill all instances")
    args = parser.parse_args()
    
    logger.info("Starting NeoCoder cleanup script")
    
    try:
        cleanup_instances(force=args.force)
        logger.info("Cleanup complete")
    except KeyboardInterrupt:
        logger.info("Cleanup interrupted by user")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
