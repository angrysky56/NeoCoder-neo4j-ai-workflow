#!/usr/bin/env python3
"""
Summary of incomplete lambda tx: tx.run calls found in the codebase
"""

issues = [
    {
        "file": "research_incarnation.py",
        "line": 157,
        "context": "ensure_research_hub_exists - creating hub"
    },
    {
        "file": "knowledge_graph_incarnation.py", 
        "line": 147,
        "context": "initialize_schema - executing schema queries"
    },
    {
        "file": "knowledge_graph_incarnation.py",
        "line": 201, 
        "context": "ensure_guidance_hub_exists - creating hub"
    },
    {
        "file": "base_incarnation.py",
        "line": 59,
        "context": "initialize_schema - executing schema queries"
    },
    {
        "file": "base_incarnation.py",
        "line": 94,
        "context": "ensure_hub_exists - creating hub"
    },
    {
        "file": "coding_incarnation.py",
        "line": 296,
        "context": "_create_action_templates - creating templates"
    },
    {
        "file": "coding_incarnation.py",
        "line": 322,
        "context": "_create_sample_projects - creating project"
    },
    {
        "file": "coding_incarnation.py",
        "line": 360,
        "context": "_create_best_practices - creating guide"
    },
    {
        "file": "data_analysis_incarnation.py",
        "line": 641,
        "context": "ensure_guidance_hub_exists - creating hub"
    },
    {
        "file": "data_analysis_incarnation.py",
        "line": 652,
        "context": "get_guidance_hub - reading hub"
    },
    {
        "file": "server.py",
        "line": 1438,
        "context": "_create_default_guidance_hub - creating hub"
    },
    {
        "file": "decision_incarnation.py",
        "line": 82,
        "context": "initialize_schema - executing schema"
    },
    {
        "file": "decision_incarnation.py",
        "line": 142,
        "context": "ensure_decision_hub_exists - creating hub"
    },
    {
        "file": "code_analysis_incarnation.py",
        "line": 482,
        "context": "ensure_hub_exists - creating hub"
    }
]

print(f"Found {len(issues)} incomplete lambda tx: tx.run calls that need fixing")
print("\nThese all need to be fixed to include the actual query and parameters.")
print("\nPattern to fix:")
print("  FROM: await session.execute_write(lambda tx: tx.run)")
print("  TO:   await session.execute_write(lambda tx: tx.run(query, params))")
