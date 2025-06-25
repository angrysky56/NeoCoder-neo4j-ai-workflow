#!/usr/bin/env python3
"""
Validation script to check for unsafe Neo4j session usages.
This helps ensure we catch any unsafe patterns in the codebase.
"""

import re
from pathlib import Path

def check_file_for_unsafe_patterns(file_path):
    """Check a file for unsafe session patterns."""
    with open(file_path, 'r') as f:
        content = f.read()

    unsafe_patterns = [
        r'self\.driver\.session\(',
        r'driver\.session\(',
        r'asyncio\.run_coroutine_threadsafe.*session',
    ]

    issues = []
    lines = content.split('\n')

    for i, line in enumerate(lines, 1):
        for pattern in unsafe_patterns:
            if re.search(pattern, line):
                # Skip if this line already uses safe_neo4j_session
                if 'safe_neo4j_session' in line:
                    continue
                # Skip if this is in a comment showing example
                if line.strip().startswith('#'):
                    continue
                # Skip if this is in event_loop_manager.py (expected usage inside the safe wrapper)
                if 'event_loop_manager.py' in str(file_path):
                    continue

                issues.append({
                    'line': i,
                    'content': line.strip(),
                    'pattern': pattern,
                    'file': file_path
                })

    return issues

def main():
    """Check all Python files for unsafe session patterns."""
    project_root = Path(__file__).parent
    src_dir = project_root / "src" / "mcp_neocoder"

    all_issues = []
    files_checked = 0

    # Check all Python files in the mcp_neocoder directory
    for file_path in src_dir.rglob("*.py"):
        # Skip __pycache__ and test files
        if "__pycache__" in str(file_path) or file_path.name.startswith("test_"):
            continue

        issues = check_file_for_unsafe_patterns(file_path)
        all_issues.extend(issues)
        files_checked += 1

    print(f"Checked {files_checked} Python files")

    if all_issues:
        print(f"\n⚠️  Found {len(all_issues)} potential unsafe session usages:")
        for issue in all_issues:
            print(f"  {issue['file']}:{issue['line']} - {issue['content']}")
        print("\n🔧 These should be replaced with safe_neo4j_session()")
        return 1
    else:
        print("✅ No unsafe session patterns found!")
        return 0

if __name__ == "__main__":
    exit(main())
