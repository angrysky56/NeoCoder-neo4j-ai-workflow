#!/bin/bash

# LV Framework Development Setup Script
# ====================================
# Complete development environment setup for LV Framework contributors

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${PURPLE}"
echo "🛠️  ============================================================"
echo "   LV FRAMEWORK DEVELOPMENT ENVIRONMENT SETUP"
echo "   For Contributors and Advanced Users"
echo "============================================================${NC}"
echo

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_dev() {
    echo -e "${PURPLE}🔧 $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for Python 3.11
check_python_dev_version() {
    print_info "Checking for Python 3.11..."
    if ! command_exists python3.11; then
        print_error "Python 3.11 is required for the development environment."
        print_error "Please install Python 3.11 and ensure 'python3.11' is in your PATH."
        exit 1
    fi
    print_status "Python 3.11 found."
}

# Setup development environment
setup_dev_environment() {
    print_dev "Setting up development environment..."

    # Create development virtual environment
    if [ -d ".venv-dev" ]; then
        print_warning "Development environment exists. Removing..."
        rm -rf .venv-dev
    fi

    python3.11 -m venv .venv-dev
    source .venv-dev/bin/activate

    # Upgrade pip and install development tools
    pip install --upgrade pip setuptools wheel

    print_status "Development virtual environment created"
}

# Install development dependencies
install_dev_dependencies() {
    print_dev "Installing development dependencies..."

    # Check for uv and install if not present
    if ! command_exists uv; then
        print_warning "uv not found. Installing uv..."
        pip install uv
    fi

    # Install core dependencies from pyproject.toml in editable mode
    # This is the standard for uv projects
    print_info "Installing project in editable mode with dev, docs, and gpu extras..."
    uv pip install -e ".[dev,docs,gpu]"

    # Fallback for projects that might still use requirements.txt
    if [ -f "requirements.txt" ]; then
        print_info "Found requirements.txt, installing..."
        uv pip install -r requirements.txt
    fi

    print_status "Development dependencies installed"
}

# Setup pre-commit hooks
setup_pre_commit() {
    print_dev "Setting up pre-commit hooks..."

    # Create pre-commit configuration if it doesn't exist
    if [ -f ".pre-commit-config.yaml" ]; then
        print_warning ".pre-commit-config.yaml already exists. Skipping creation."
    else
        cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: debug-statements

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3
        args: [--line-length=88]

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: [--profile=black]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203,W503]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--ignore-missing-imports]

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: [-r, src/]
        exclude: tests/
EOF
        print_status ".pre-commit-config.yaml created."
    fi

    # Install pre-commit hooks
    pre-commit install

    print_status "Pre-commit hooks configured"
}

# Setup pytest configuration
setup_pytest() {
    print_dev "Setting up pytest configuration..."

    # Add pytest configuration to pyproject.toml if it doesn't exist
    if [ -f "pyproject.toml" ] && grep -q "\[tool.pytest.ini_options\]" "pyproject.toml"; then
        print_warning "pytest configuration already exists in pyproject.toml. Skipping."
    else
        # Appends to pyproject.toml, creating it if it doesn't exist.
        cat >> pyproject.toml << 'EOF'

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --cov=src/mcp_neocoder --cov-report=term-missing --cov-report=html"
testpaths = ["tests"]
asyncio_mode = "auto"
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
    "gpu: marks tests that require GPU",
]

[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["mcp_neocoder"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[[tool.mypy.overrides]]
module = [
    "neo4j.*",
    "qdrant_client.*",
    "sentence_transformers.*",
    "numpy.*",
    "scipy.*",
]
ignore_missing_imports = true
EOF
        print_status "Pytest configuration added to pyproject.toml."
    fi
}

# Create test structure
create_test_structure() {
    print_dev "Creating test structure..."

    # Create test directories
    mkdir -p tests/{unit,integration,performance}

    # Create __init__.py files
    touch tests/__init__.py
    touch tests/unit/__init__.py
    touch tests/integration/__init__.py
    touch tests/performance/__init__.py

    # Create conftest.py for shared fixtures if it doesn't exist
    if [ -f "tests/conftest.py" ]; then
        print_warning "tests/conftest.py already exists. Skipping creation."
    else
        cat > tests/conftest.py << 'EOF'
"""Shared pytest fixtures for LV Framework tests."""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
import numpy as np


@pytest.fixture
def mock_neo4j_session():
    """Mock Neo4j session for testing."""
    session = MagicMock()
    session.run = MagicMock(return_value=MagicMock())
    return session


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client for testing."""
    client = MagicMock()
    client.search = AsyncMock(return_value=[])
    client.get_collections = MagicMock(return_value=[])
    return client


@pytest.fixture
def sample_candidates():
    """Sample candidate outputs for testing."""
    return [
        "Conservative analysis with high precision",
        "Creative approach with novel insights",
        "Technical implementation with code examples",
        "Balanced perspective combining methods"
    ]


@pytest.fixture
def sample_alpha_matrix():
    """Sample alpha matrix for testing."""
    return np.array([
        [-1.5, -0.7, 0.3, 0.2],
        [-0.7, -1.2, 0.0, 0.1],
        [0.3, 0.0, -0.9, -0.4],
        [0.2, 0.1, -0.4, -1.1]
    ])


@pytest.fixture
def sample_growth_rates():
    """Sample growth rates for testing."""
    return np.array([0.8, 0.6, 0.9, 0.7])


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
EOF
        print_status "tests/conftest.py created."
    fi

    # Create basic unit tests if they don't exist
    if [ -f "tests/unit/test_lv_ecosystem.py" ]; then
        print_warning "tests/unit/test_lv_ecosystem.py already exists. Skipping creation."
    else
        cat > tests/unit/test_lv_ecosystem.py << 'EOF'
"""Unit tests for LV Ecosystem core functionality."""

import pytest
import numpy as np
from unittest.mock import MagicMock, AsyncMock, patch

from mcp_neocoder.lv_ecosystem import LVEcosystem, EntropyEstimator, LVCandidate


class TestEntropyEstimator:
    """Test entropy estimation functionality."""

    def test_entropy_estimator_initialization(self):
        """Test entropy estimator can be initialized."""
        estimator = EntropyEstimator()
        assert estimator is not None

    def test_low_entropy_prompt(self):
        """Test low entropy detection for factual prompts."""
        estimator = EntropyEstimator()
        entropy = estimator.estimate_prompt_entropy("What is the capital of France?")
        assert 0.0 <= entropy <= 1.0
        # Factual questions should have lower entropy
        assert entropy < 0.5

    def test_high_entropy_prompt(self):
        """Test high entropy detection for creative prompts."""
        estimator = EntropyEstimator()
        entropy = estimator.estimate_prompt_entropy(
            "Imagine creative solutions for climate change using multiple approaches"
        )
        assert 0.0 <= entropy <= 1.0
        # Creative questions should have higher entropy
        assert entropy > 0.3


class TestLVCandidate:
    """Test LV candidate data structure."""

    def test_candidate_creation(self):
        """Test candidate creation with basic parameters."""
        candidate = LVCandidate(content="Test candidate content")
        assert candidate.content == "Test candidate content"
        assert candidate.quality_score == 0.0
        assert candidate.novelty_score == 0.0
        assert candidate.content_hash is not None

    def test_candidate_with_scores(self):
        """Test candidate creation with quality scores."""
        candidate = LVCandidate(
            content="Test content",
            quality_score=0.8,
            novelty_score=0.6
        )
        assert candidate.quality_score == 0.8
        assert candidate.novelty_score == 0.6


class TestLVEcosystem:
    """Test LV ecosystem core functionality."""

    @pytest.fixture
    def lv_ecosystem(self, mock_neo4j_session, mock_qdrant_client):
        """Create LV ecosystem for testing."""
        with patch('mcp_neocoder.lv_ecosystem.SentenceTransformer'):
            return LVEcosystem(mock_neo4j_session, mock_qdrant_client)

    def test_ecosystem_initialization(self, lv_ecosystem):
        """Test LV ecosystem can be initialized."""
        assert lv_ecosystem is not None
        assert lv_ecosystem.max_iterations == 10
        assert lv_ecosystem.damping_factor == 0.15

    @pytest.mark.asyncio
    async def test_select_diverse_outputs(self, lv_ecosystem, sample_candidates):
        """Test diverse output selection."""
        with patch.object(lv_ecosystem, '_calculate_growth_rates',
                         return_value=np.array([0.8, 0.6, 0.9, 0.7])):
            with patch.object(lv_ecosystem, '_build_alpha_matrix',
                             return_value=np.eye(4) * -1.0):
                results = await lv_ecosystem.select_diverse_outputs(
                    candidates=sample_candidates,
                    prompt="Test prompt",
                    context={'test': True}
                )

                assert 'selected_outputs' in results
                assert 'entropy' in results
                assert 'diversity_metrics' in results
                assert len(results['selected_outputs']) > 0
EOF
        print_status "tests/unit/test_lv_ecosystem.py created."
    fi

    # Create integration tests if they don't exist
    if [ -f "tests/integration/test_neocoder_integration.py" ]; then
        print_warning "tests/integration/test_neocoder_integration.py already exists. Skipping creation."
    else
        cat > tests/integration/test_neocoder_integration.py << 'EOF'
"""Integration tests for NeoCoder-LV integration."""

import pytest
from unittest.mock import MagicMock, AsyncMock

from mcp_neocoder.lv_integration import NeoCoder_LV_Integration


class TestNeoCoder_LV_Integration:
    """Test NeoCoder integration functionality."""

    @pytest.fixture
    def lv_integration(self, mock_neo4j_session, mock_qdrant_client):
        """Create LV integration for testing."""
        return NeoCoder_LV_Integration(mock_neo4j_session, mock_qdrant_client)

    @pytest.mark.asyncio
    async def test_enhance_existing_template(self, lv_integration):
        """Test template enhancement functionality."""
        context = {
            'prompt': 'Test enhancement prompt',
            'template_type': 'KNOWLEDGE_EXTRACT'
        }

        # Mock the enhancement process
        with patch.object(lv_integration, '_apply_lv_enhancement') as mock_enhance:
            mock_enhance.return_value = {'enhanced': True, 'entropy': 0.7}

            results = await lv_integration.enhance_existing_template(
                'KNOWLEDGE_EXTRACT', context
            )

            assert 'enhanced' in results or 'entropy' in results
EOF
        print_status "tests/integration/test_neocoder_integration.py created."
    fi

    print_status "Test structure created"
}

# Setup development tools configuration
setup_dev_tools() {
    print_dev "Setting up development tools configuration..."

    # Create Makefile for common tasks if it doesn't exist
    if [ -f "Makefile" ]; then
        print_warning "Makefile already exists. Skipping creation."
    else
        cat > Makefile << 'EOF'
.PHONY: help install test lint format clean docs dev-setup
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "LV Framework Development Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install the package in development mode
	pip install -e .[dev]

test: ## Run all tests
	pytest -v

test-unit: ## Run unit tests only
	pytest tests/unit/ -v

test-integration: ## Run integration tests only
	pytest tests/integration/ -v

test-cov: ## Run tests with coverage
	pytest --cov=src/mcp_neocoder --cov-report=html --cov-report=term-missing

lint: ## Run linting checks
	flake8 src/ tests/
	mypy src/
	bandit -r src/

format: ## Format code
	black src/ tests/
	isort src/ tests/

check: ## Run all quality checks
	$(MAKE) format
	$(MAKE) lint
	$(MAKE) test

clean: ## Clean up build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

docs: ## Build documentation
	cd docs && make html

dev-setup: ## Setup complete development environment
	$(MAKE) install
	pre-commit install
	$(MAKE) test

benchmark: ## Run performance benchmarks
	pytest tests/performance/ --benchmark-only

profile: ## Profile the code
	python -m cProfile -o profile_stats.prof demo_lv_framework.py
	python -c "import pstats; pstats.Stats('profile_stats.prof').sort_stats('cumtime').print_stats(20)"

docker-dev: ## Start development environment with Docker
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

docker-test: ## Run tests in Docker
	docker-compose exec app pytest

notebook: ## Start Jupyter notebook server
	jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root
EOF
        print_status "Makefile created."
    fi

    # Create VS Code settings if they don't exist
    mkdir -p .vscode
    if [ -f ".vscode/settings.json" ]; then
        print_warning ".vscode/settings.json already exists. Skipping creation."
    else
        cat > .vscode/settings.json << 'EOF'
{
    "python.defaultInterpreterPath": "./.venv-dev/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackPath": "./.venv-dev/bin/black",
    "python.sortImports.path": "./.venv-dev/bin/isort",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestPath": "./.venv-dev/bin/pytest",
    "python.testing.pytestArgs": [
        "tests"
    ],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    },
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        ".pytest_cache": true,
        ".coverage": true,
        "htmlcov": true
    }
}
EOF
        print_status ".vscode/settings.json created."
    fi

    # Create launch configuration for debugging if it doesn't exist
    if [ -f ".vscode/launch.json" ]; then
        print_warning ".vscode/launch.json already exists. Skipping creation."
    else
        cat > .vscode/launch.json << 'EOF'
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug LV Framework Demo",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/demo_lv_framework.py",
            "console": "integratedTerminal",
            "env": {
                "PYTHONPATH": "${workspaceFolder}/src"
            }
        },
        {
            "name": "Debug Tests",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": [
                "tests/",
                "-v"
            ],
            "console": "integratedTerminal",
            "env": {
                "PYTHONPATH": "${workspaceFolder}/src"
            }
        }
    ]
}
EOF
        print_status ".vscode/launch.json created."
    fi

    print_status "Development tools configured"
}

# Setup documentation
setup_documentation() {
    print_dev "Setting up documentation environment..."

    mkdir -p docs/{source,build}

    # Create Sphinx configuration if it doesn't exist
    if [ -f "docs/source/conf.py" ]; then
        print_warning "docs/source/conf.py already exists. Skipping creation."
    else
        cat > docs/source/conf.py << 'EOF'
"""Sphinx configuration for LV Framework documentation."""

import os
import sys
sys.path.insert(0, os.path.abspath('../../src'))

# Project information
project = 'LV Framework'
copyright = '2024, NeoCoder Team'
author = 'NeoCoder Team'
release = '1.0.0'

# Extensions
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'myst_parser',
    'sphinx_autodoc_typehints'
]

# Templates and themes
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False

# Autodoc settings
autodoc_member_order = 'bysource'
autodoc_typehints = 'description'

# Intersphinx settings
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'scipy': ('https://docs.scipy.org/doc/scipy/', None),
}
EOF
        print_status "docs/source/conf.py created."
    fi

    # Create main documentation file if it doesn't exist
    if [ -f "docs/source/index.md" ]; then
        print_warning "docs/source/index.md already exists. Skipping creation."
    else
        cat > docs/source/index.md << 'EOF'
# LV Framework Documentation

Welcome to the Lotka-Volterra Ecosystem Intelligence Framework documentation.

## Overview

The LV Framework applies ecological dynamics to AI output selection, maintaining sustainable diversity while preserving quality.

## Contents

```{toctree}
:maxdepth: 2
:caption: User Guide

installation
quickstart
concepts
examples
```

```{toctree}
:maxdepth: 2
:caption: API Reference

api/ecosystem
api/templates
api/integration
```

```{toctree}
:maxdepth: 2
:caption: Developer Guide

development
contributing
testing
```

## Indices and tables

* {ref}`genindex`
* {ref}`modindex`
* {ref}`search`
EOF
        print_status "docs/source/index.md created."
    fi

    print_status "Documentation environment setup"
}

# Create development shortcuts
create_dev_shortcuts() {
    print_dev "Creating development shortcuts..."

    # Create activation script if it doesn't exist
    if [ -f "activate_dev.sh" ]; then
        print_warning "activate_dev.sh already exists. Skipping creation."
    else
        cat > activate_dev.sh << 'EOF'
#!/bin/bash
# LV Framework Development Environment Activation

echo "🧬 Activating LV Framework Development Environment"
source .venv-dev/bin/activate

echo "Development environment activated!"
echo "Available commands:"
echo "  make help     - Show all available commands"
echo "  make test     - Run tests"
echo "  make format   - Format code"
echo "  make lint     - Run linting"
echo "  make docs     - Build documentation"
echo ""
echo "Happy coding! 🚀"
EOF
        chmod +x activate_dev.sh
        print_status "activate_dev.sh created."
    fi

    # Create quick test script if it doesn't exist
    if [ -f "quick_test.sh" ]; then
        print_warning "quick_test.sh already exists. Skipping creation."
    else
        cat > quick_test.sh << 'EOF'
#!/bin/bash
# Quick LV Framework Test Runner

source .venv-dev/bin/activate
echo "Running quick LV Framework tests..."
pytest tests/unit/ -v --tb=short
echo "Quick tests completed!"
EOF
        chmod +x quick_test.sh
        print_status "quick_test.sh created."
    fi

    print_status "Development shortcuts created"
}

# Print completion message
print_dev_completion() {
    echo
    echo -e "${PURPLE}"
    echo "🎉 ============================================================"
    echo "   LV FRAMEWORK DEVELOPMENT ENVIRONMENT READY!"
    echo "============================================================${NC}"
    echo
    echo -e "${BLUE}Development Environment Features:${NC}"
    echo "✅ Virtual environment (.venv-dev)"
    echo "✅ All development dependencies"
    echo "✅ Pre-commit hooks with code quality checks"
    echo "✅ Pytest configuration with coverage"
    echo "✅ Black, isort, flake8, mypy configuration"
    echo "✅ VS Code settings and debugging config"
    echo "✅ Comprehensive test structure"
    echo "✅ Documentation setup with Sphinx"
    echo "✅ Makefile with development commands"
    echo
    echo -e "${BLUE}Quick Start Commands:${NC}"
    echo "${YELLOW}./activate_dev.sh${NC}     - Activate development environment"
    echo "${YELLOW}make help${NC}              - Show all available commands"
    echo "${YELLOW}make test${NC}              - Run all tests"
    echo "${YELLOW}make check${NC}             - Run all quality checks"
    echo "${YELLOW}./quick_test.sh${NC}        - Run quick unit tests"
    echo
    echo -e "${BLUE}Development Workflow:${NC}"
    echo "1. ${YELLOW}./activate_dev.sh${NC} - Activate environment"
    echo "2. ${YELLOW}make format${NC} - Format your code"
    echo "3. ${YELLOW}make test${NC} - Run tests"
    echo "4. ${YELLOW}git commit${NC} - Pre-commit hooks will run automatically"
    echo
    print_status "Happy LV Framework Development! 🧬✨"
}

# Main function
main() {
    print_dev "Starting LV Framework development setup..."

    check_python_dev_version
    setup_dev_environment
    install_dev_dependencies
    setup_pre_commit
    setup_pytest
    create_test_structure
    setup_dev_tools
    setup_documentation
    create_dev_shortcuts
    print_dev_completion
}

# Run main function
main "$@"
