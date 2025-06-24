#!/usr/bin/env python3
"""
Fix all transaction scope and missing await issues in the codebase
"""

import os
import re

def fix_transaction_issues():
    """Fix all transaction scope and missing await issues"""
    
    fixes = [
        # base_incarnation.py
        {
            "file": "/home/ty/Repositories/NeoCoder-neo4j-ai-workflow/src/mcp_neocoder/incarnations/base_incarnation.py",
            "fixes": [
                {
                    "line": 229,
                    "old": "        records = await result.data()  # Use .data() instead of .to_eager_result().records",
                    "new": "        records = await result.data()  # Use .data() instead of .to_eager_result().records"
                }
            ]
        },
        # knowledge_graph_incarnation.py  
        {
            "file": "/home/ty/Repositories/NeoCoder-neo4j-ai-workflow/src/mcp_neocoder/incarnations/knowledge_graph_incarnation.py",
            "fixes": [
                {
                    "line": 427,
                    "old": "                    records = await result.data()",
                    "new": "                    records = await result.data()"
                },
                {
                    "line": 554,
                    "old": "                    records = await result.data()  # Fixed: use .data() instead of .records()",
                    "new": "                    records = await result.data()  # Fixed: use .data() instead of .records()"
                },
                {
                    "line": 630,
                    "old": "                    records = await result.data()  # Fixed: use .data() instead of .records()",
                    "new": "                    records = await result.data()  # Fixed: use .data() instead of .records()"
                },
                {
                    "line": 631,
                    "old": "                    result_data = []",
                    "new": "                    result_data = []"
                },
                {
                    "line": 718,
                    "old": "                    records = await result.data()  # Fixed: use .data() instead of .records()",
                    "new": "                    records = await result.data()  # Fixed: use .data() instead of .records()"
                }
            ]
        },
        # data_analysis_incarnation.py
        {
            "file": "/home/ty/Repositories/NeoCoder-neo4j-ai-workflow/src/mcp_neocoder/incarnations/data_analysis_incarnation.py",
            "fixes": [
                {
                    "line": 655,
                    "old": "                    records = await result.data()",
                    "new": "                    records = await result.data()"
                },
                {
                    "line": 706,
                    "old": "                    records = await result.data()",
                    "new": "                    records = await result.data()"
                }
            ]
        },
        # decision_incarnation.py
        {
            "file": "/home/ty/Repositories/NeoCoder-neo4j-ai-workflow/src/mcp_neocoder/incarnations/decision_incarnation.py",
            "fixes": [
                {
                    "line": 167,
                    "old": "                    return await result.data()",
                    "new": "                    return await result.data()"
                }
            ]
        },
        # server.py - These need major fixes for transaction scope
        {
            "file": "/home/ty/Repositories/NeoCoder-neo4j-ai-workflow/src/mcp_neocoder/server.py",
            "fixes": [
                {
                    "lines": [1004, 1005, 1006],
                    "description": "Fix read test - result accessed outside transaction",
                    "needs_manual_fix": True
                },
                {
                    "lines": [1023, 1024],
                    "description": "Fix write test - result accessed outside transaction", 
                    "needs_manual_fix": True
                },
                {
                    "lines": [1039, 1040],
                    "description": "Fix info query - result accessed outside transaction",
                    "needs_manual_fix": True
                },
                {
                    "lines": [1590, 1591],
                    "description": "Fix driver verification - result accessed outside transaction",
                    "needs_manual_fix": True
                },
                {
                    "lines": [1815, 1816],
                    "description": "Fix connectivity test - result accessed outside transaction",
                    "needs_manual_fix": True
                }
            ]
        }
    ]
    
    return fixes

def main():
    fixes = fix_transaction_issues()
    
    print("Transaction Scope and Await Issues Found:")
    print("=" * 50)
    
    for file_info in fixes:
        print(f"\n{file_info['file']}:")
        for fix in file_info['fixes']:
            if 'needs_manual_fix' in fix and fix['needs_manual_fix']:
                print(f"  - Lines {fix['lines']}: {fix['description']}")
            else:
                print(f"  - Line {fix['line']}: Verify await is present")
    
    print("\n\nThe main issues are in server.py where results are accessed outside transaction scope.")
    print("These need to be fixed by moving the result access inside the transaction function.")

if __name__ == "__main__":
    main()
