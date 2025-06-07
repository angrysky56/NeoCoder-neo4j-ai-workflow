#!/usr/bin/env python3
"""
Guidance Hub Refresh Utility for NeoCoder Data Analysis

This script refreshes the guidance hub content in Neo4j for the data analysis incarnation.

Author: NeoCoder Data Analysis Team
Created: 2025
"""

import sys
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def refresh_data_analysis_hub():
    """Refresh the data analysis guidance hub content."""
    try:
        # Import the data analysis incarnation
        from src.mcp_neocoder.incarnations.data_analysis_incarnation import DataAnalysisIncarnation
        
        # Create a mock driver connection (you might need to adjust this based on your setup)
        import asyncio
        from neo4j import AsyncGraphDatabase
        
        async def update_hub():
            # Database connection details (adjust as needed)
            uri = "bolt://localhost:7687"
            username = "neo4j"
            password = "00000000"
            database = "neo4j"
            
            driver = AsyncGraphDatabase.driver(uri, auth=(username, password))
            
            try:
                # Create incarnation instance
                incarnation = DataAnalysisIncarnation(driver=driver, database=database)
                
                # Force update the guidance hub
                await incarnation.ensure_guidance_hub_exists()
                
                logger.info("✅ Data analysis guidance hub refreshed successfully!")
                
            except Exception as e:
                logger.error(f"❌ Error refreshing guidance hub: {e}")
                
            finally:
                await driver.close()
        
        # Run the async function
        asyncio.run(update_hub())
        
    except Exception as e:
        logger.error(f"❌ Error importing or running refresh: {e}")
        return False
    
    return True

def main():
    """Main function."""
    print("🔄 Refreshing Data Analysis Guidance Hub...")
    
    success = refresh_data_analysis_hub()
    
    if success:
        print("✅ Hub refresh completed!")
        print("💡 Try running get_guidance_hub() again in your NeoCoder session")
        return 0
    else:
        print("❌ Hub refresh failed - check logs for details")
        return 1

if __name__ == '__main__':
    exit(main())
