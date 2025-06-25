#!/usr/bin/env python3
"""
Script to fix all unsafe Neo4j session usages in incarnation files.
Replaces direct driver.session() calls with safe_neo4j_session().
"""

import re
from pathlib import Path

def fix_session_usage_in_file(file_path):
    """Fix unsafe session usage in a single file."""
    with open(file_path, 'r') as f:
        content = f.read()

    original_content = content

    # Determine correct import path based on file location
    if "incarnations" in str(file_path):
        import_statement = 'from ..event_loop_manager import safe_neo4j_session'
    else:
        import_statement = 'from .event_loop_manager import safe_neo4j_session'

    # Check if the safe_neo4j_session import exists
    if import_statement not in content:
        # Find the last import line and add our import after it
        lines = content.split('\n')
        import_line_index = -1

        for i, line in enumerate(lines):
            if line.startswith('from .') or line.startswith('from ..') or line.startswith('import '):
                import_line_index = i

        if import_line_index >= 0:
            lines.insert(import_line_index + 1, import_statement)
            content = '\n'.join(lines)    # Replace unsafe session patterns
    patterns = [
        # async with self.driver.session(database=self.database) as session:
        (r'async with self\.driver\.session\(database=self\.database\) as session:',
         r'async with safe_neo4j_session(self.driver, self.database) as session:'),

        # async with self.driver.session() as session:
        (r'async with self\.driver\.session\(\) as session:',
         r'async with safe_neo4j_session(self.driver, self.database) as session:'),

        # async with driver.session(database=database) as session:
        (r'async with driver\.session\(database=database\) as session:',
         r'async with safe_neo4j_session(driver, database) as session:'),

        # async with driver.session() as session:
        (r'async with driver\.session\(\) as session:',
         r'async with safe_neo4j_session(driver, "neo4j") as session:'),

        # async with driver.session(database=neo4j_database) as session:
        (r'async with driver\.session\(database=neo4j_database\) as session:',
         r'async with safe_neo4j_session(driver, neo4j_database) as session:'),
    ]

    changes_made = 0
    for pattern, replacement in patterns:
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            changes_made += re.subn(pattern, replacement, content)[1]
            content = new_content

    # Write back if changes were made
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Fixed {changes_made} session usages in {file_path}")
        return changes_made
    else:
        print(f"No changes needed in {file_path}")
        return 0

def main():
    """Fix all incarnation files and core mixin files."""
    project_root = Path(__file__).parent

    # Files to process
    files_to_process = []

    # Add all incarnation files
    incarnations_dir = project_root / "src" / "mcp_neocoder" / "incarnations"
    for file_path in incarnations_dir.glob("*.py"):
        if file_path.name != "__init__.py":
            files_to_process.append(file_path)

    # Add core files that use driver.session()
    src_dir = project_root / "src" / "mcp_neocoder"
    core_files = [
        src_dir / "cypher_snippets.py",
        src_dir / "tool_proposals.py",
        src_dir / "server.py",
        src_dir / "init_db.py",
    ]

    for file_path in core_files:
        if file_path.exists():
            files_to_process.append(file_path)

    total_fixes = 0
    files_processed = 0

    for file_path in files_to_process:
        print(f"Processing {file_path}")
        fixes = fix_session_usage_in_file(file_path)
        total_fixes += fixes
        files_processed += 1

    print("\nSummary:")
    print(f"Files processed: {files_processed}")
    print(f"Total session usages fixed: {total_fixes}")

if __name__ == "__main__":
    main()
