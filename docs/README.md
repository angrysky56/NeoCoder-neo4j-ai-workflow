# NeoCoder Documentation

This directory contains additional documentation and reference materials for the NeoCoder Neo4j AI workflow project.

## Contents

### Cypher Snippets Reference

- **cypher_snippets_reference.md**: Complete reference guide for the Cypher snippet toolkit with original formatting and citation markers.
- **clean_cypher_snippets.md**: Clean version of the Cypher snippet documentation for use in the main README.

## Purpose

The main purpose of this docs directory is to store detailed reference materials that might be too verbose for the main README or that contain specialized formatting that might cause rendering issues in GitHub's Markdown viewer.

## Usage

To update the main README with clean Cypher snippets (without citation markers that cause rendering issues), run:

```bash
python scripts/update_readme.py
```

This script will:
1. Create a backup of the current README.md
2. Replace the Cypher snippets section with the clean version
3. Preserve a reference to the full documentation

## Citation Markers

The original Cypher snippet documentation contains `citeturnXsearchY` markers which are citation references from the original source material. These markers can cause rendering issues in GitHub's Markdown viewer (displaying as Chinese/Japanese characters), so we've created clean versions without these markers for better readability.

The original markers are preserved in the reference document for completeness.
