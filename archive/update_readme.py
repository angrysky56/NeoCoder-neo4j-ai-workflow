#!/usr/bin/env python3
"""
README Update Script

This script replaces the Cypher snippet section in the README.md file with a clean version
that doesn't include citation markers that cause rendering issues on GitHub.
"""

import os
import re
import shutil
from pathlib import Path

# Define paths
repo_root = Path('/home/ty/Repositories/ai_workspace/NeoCoder-neo4j-ai-workflow')
readme_path = repo_root / 'README.md'
clean_snippets_path = repo_root / 'docs/clean_cypher_snippets.md'
backup_path = repo_root / 'README.md.bak'


def update_readme():
    """Update the README.md file with clean Cypher snippets."""
    # Read the current README
    with open(readme_path, 'r') as f:
        readme_content = f.read()

    # Create a backup
    shutil.copy(readme_path, backup_path)
    print(f"Created backup at {backup_path}")

    # Read the clean snippets
    with open(clean_snippets_path, 'r') as f:
        clean_snippets = f.read()

    # Define the section to replace
    # This pattern looks for the Cypher snippet section starting with "## The 'Cypher Snippet Toolkit'"
    # and ending just before the "## License" section
    start_marker = "## The 'Cypher Snippet Toolkit' tools operate on the graph structure defined below. Run these Cyphers to enable these tools if not auto-installed or done by your AI assistant"
    end_marker = "## License"

    # Use regex to do the replacement
    pattern = re.compile(
        f"{re.escape(start_marker)}(.*?){re.escape(end_marker)}",
        re.DOTALL
    )

    # Prepare replacement text
    replacement = f"## The 'Cypher Snippet Toolkit' tools operate on the graph structure defined below\n\n{clean_snippets}\n\n## License"

    # Replace the section
    updated_content = pattern.sub(replacement, readme_content)

    # Write the updated content back to the README
    with open(readme_path, 'w') as f:
        f.write(updated_content)

    print(f"Successfully updated {readme_path}")
    print("The Cypher snippet section has been replaced with a clean version.")
    print("The original content is preserved in docs/cypher_snippets_reference.md")


if __name__ == "__main__":
    # Check if files exist
    if not readme_path.exists():
        print(f"Error: README.md not found at {readme_path}")
        exit(1)

    if not clean_snippets_path.exists():
        print(f"Error: Clean snippets file not found at {clean_snippets_path}")
        exit(1)

    # Update the README
    update_readme()
