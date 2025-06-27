#!/usr/bin/env python3
"""
Test script to verify LV tools integration
Run this after restarting Claude Desktop
"""

print("""
🧬 LV Framework Integration Test Commands
========================================

After restarting Claude Desktop, try these commands to test the LV tools:

1. Test entropy estimation:
   ```
   User: Switch to knowledge graph incarnation
   Claude: [switches incarnation]
   
   User: Estimate the entropy of "What is 2+2?"
   Claude: [Should show low entropy ~0.1-0.2, precision mode]
   
   User: Estimate the entropy of "Generate creative solutions for sustainable AI development"
   Claude: [Should show high entropy ~0.7-0.9, creativity mode]
   ```

2. Test LV framework:
   ```
   User: Test the LV framework with basic functionality
   Claude: [Should run basic LV test and show results]
   ```

3. Enhance a template:
   ```
   User: Use LV to enhance the FEATURE template for "create an innovative caching system"
   Claude: [Should show entropy analysis and enhanced execution]
   ```

4. Check dashboard:
   ```
   User: Show me the LV ecosystem dashboard
   Claude: [Should display performance metrics and status]
   ```

Integration Notes:
- The LV tools are now part of the knowledge graph incarnation
- They'll automatically appear when you switch to that incarnation
- Each tool has proper type hints and docstrings for MCP
- The tools handle initialization of LV components automatically

Troubleshooting:
- If tools don't appear, check Claude Desktop logs
- Ensure Neo4j is running (the tools need database connection)
- The sentence-transformers dependency might need to be installed
""")
