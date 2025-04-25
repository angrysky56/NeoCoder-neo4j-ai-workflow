#!/bin/bash

# Script to start the NeoCoder server with a specific incarnation
# Usage: ./start_incarnation.sh [incarnation_type]

# Default values
DEFAULT_INCARNATION="coding"
NEO4J_URL=${NEO4J_URL:-"bolt://localhost:7687"}
NEO4J_USERNAME=${NEO4J_USERNAME:-"neo4j"}
NEO4J_PASSWORD=${NEO4J_PASSWORD:-"password"} # Should be set in environment
NEO4J_DATABASE=${NEO4J_DATABASE:-"neo4j"}

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Parse command line argument
INCARNATION=${1:-$DEFAULT_INCARNATION}

# Valid incarnation types
valid_incarnations=("coding" "research_orchestration" "decision_support" "continuous_learning" "complex_system")

# Check if the provided incarnation is valid
is_valid=0
for inc in "${valid_incarnations[@]}"; do
  if [ "$INCARNATION" = "$inc" ]; then
    is_valid=1
    break
  fi
done

if [ $is_valid -eq 0 ]; then
  echo "Error: Invalid incarnation type '$INCARNATION'"
  echo "Valid types are: ${valid_incarnations[*]}"
  exit 1
fi

# Activate virtual environment if it exists
if [ -d "$PROJECT_DIR/venv" ]; then
  echo "Activating virtual environment..."
  source "$PROJECT_DIR/venv/bin/activate"
fi

# Check if Python exists
if ! command -v python3 &> /dev/null; then
  echo "Error: Python 3 not found. Please install Python 3 and try again."
  exit 1
fi

# Export Neo4j environment variables
export NEO4J_URL
export NEO4J_USERNAME
export NEO4J_PASSWORD
export NEO4J_DATABASE
export DEFAULT_INCARNATION="$INCARNATION"

echo "Starting NeoCoder with $INCARNATION incarnation..."
echo "Neo4j URL: $NEO4J_URL"
echo "Neo4j Database: $NEO4J_DATABASE"

# Start the server with the specified incarnation
cd "$PROJECT_DIR" || exit 1
python -m src.mcp_neocoder.server --incarnation "$INCARNATION"
