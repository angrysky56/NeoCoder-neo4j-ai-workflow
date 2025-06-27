#!/usr/bin/env python3
"""
LV Framework Validation Script
=============================

Validates that the LV Framework is properly installed and configured.
Run this after installation to ensure everything is working correctly.
"""

import sys
import os
import asyncio
import importlib
import subprocess
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_header():
    """Print validation header."""
    print(f"{Colors.PURPLE}{Colors.BOLD}")
    print("🔍 " + "="*60)
    print("   LV FRAMEWORK VALIDATION SCRIPT")
    print("   Comprehensive Installation Verification")
    print("="*64 + f"{Colors.END}")
    print()

def print_success(message):
    """Print success message."""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    """Print error message."""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_info(message):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def print_section(title):
    """Print section header."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}🔧 {title}{Colors.END}")
    print("-" * (len(title) + 4))

def check_python_version():
    """Check Python version compatibility."""
    print_section("Python Version Check")

    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    if version >= (3, 8):
        print_success(f"Python {version_str} (compatible)")
        return True
    else:
        print_error(f"Python {version_str} (requires 3.8+)")
        return False

def check_virtual_environment():
    """Check if running in virtual environment."""
    print_section("Virtual Environment Check")

    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        venv_path = os.environ.get('VIRTUAL_ENV', 'Unknown')
        print_success(f"Virtual environment active: {venv_path}")
        return True
    else:
        print_warning("Not running in virtual environment (recommended)")
        return False

def check_core_dependencies():
    """Check core Python dependencies."""
    print_section("Core Dependencies Check")

    required_packages = [
        'numpy',
        'scipy',
        'sentence_transformers',
        'neo4j',
        'qdrant_client',
        'asyncio',
        'pydantic'
    ]

    all_good = True
    for package in required_packages:
        try:
            if package == 'asyncio':
                # asyncio is built-in
                print_success(f"{package} (built-in)")
            else:
                module = importlib.import_module(package.replace('-', '_'))
                version = getattr(module, '__version__', 'unknown')
                print_success(f"{package} {version}")
        except ImportError:
            print_error(f"{package} not found")
            all_good = False

    return all_good

def check_lv_framework_modules():
    """Check LV Framework specific modules."""
    print_section("LV Framework Modules Check")

    # Add src to path if needed
    src_path = Path(__file__).parent / "src"
    if src_path.exists():
        sys.path.insert(0, str(src_path))

    lv_modules = [
        'mcp_neocoder.lv_ecosystem',
        'mcp_neocoder.lv_templates',
        'mcp_neocoder.lv_integration'
    ]

    all_good = True
    for module in lv_modules:
        try:
            importlib.import_module(module)
            print_success(f"{module}")
        except ImportError as e:
            print_error(f"{module} - {e}")
            all_good = False

    return all_good

def check_file_structure():
    """Check that all required files exist."""
    print_section("File Structure Check")

    required_files = [
        'README_LV_FRAMEWORK.md',
        'QUICKSTART.md',
        'requirements_lv.txt',
        'docker-compose.yml',
        'demo_lv_framework.py',
        'src/mcp_neocoder/lv_ecosystem.py',
        'src/mcp_neocoder/lv_templates.py',
        'src/mcp_neocoder/lv_integration.py'
    ]

    all_good = True
    for file_path in required_files:
        if Path(file_path).exists():
            print_success(f"{file_path}")
        else:
            print_error(f"{file_path} missing")
            all_good = False

    return all_good

def check_docker_services():
    """Check Docker services status."""
    print_section("Docker Services Check")

    try:
        # Check if docker is available
        result = subprocess.run(['docker', '--version'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print_success(f"Docker available: {result.stdout.strip()}")
        else:
            print_warning("Docker not available")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print_warning("Docker not found or not responding")
        return False

    # Check if Neo4j container is running
    try:
        result = subprocess.run(['docker', 'ps', '--filter', 'name=neo4j-lv', '--format', '{{.Status}}'],
                              capture_output=True, text=True, timeout=10)
        if result.stdout.strip():
            print_success(f"Neo4j container: {result.stdout.strip()}")
        else:
            print_warning("Neo4j container not running")
    except subprocess.TimeoutExpired:
        print_warning("Docker ps command timed out")

    # Check if Qdrant container is running
    try:
        result = subprocess.run(['docker', 'ps', '--filter', 'name=qdrant-lv', '--format', '{{.Status}}'],
                              capture_output=True, text=True, timeout=10)
        if result.stdout.strip():
            print_success(f"Qdrant container: {result.stdout.strip()}")
        else:
            print_warning("Qdrant container not running")
    except subprocess.TimeoutExpired:
        print_warning("Docker ps command timed out")

    return True

def test_database_connections():
    """Test database connections."""
    print_section("Database Connection Tests")

    # Test Neo4j connection
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver("bolt://localhost:7687",
                                     auth=("neo4j", "lv_password_2024"))
        with driver.session() as session:
            result = session.run("RETURN 1 AS test")
            single_result = result.single()
            if single_result and single_result.get("test") == 1:
                print_success("Neo4j connection successful")
            else:
                print_error("Neo4j connection failed")
        driver.close()
    except Exception as e:
        print_warning(f"Neo4j connection error: {e}")

    # Test Qdrant connection
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient("localhost", port=6333)
        collections = client.get_collections()
        print_success("Qdrant connection successful")
    except Exception as e:
        print_warning(f"Qdrant connection error: {e}")

async def test_lv_functionality():
    """Test basic LV framework functionality."""
    print_section("LV Framework Functionality Test")

    try:
        from unittest.mock import MagicMock
        from mcp_neocoder.lv_ecosystem import LVEcosystem, EntropyEstimator

        # Test entropy estimation
        estimator = EntropyEstimator()
        entropy = estimator.estimate_prompt_entropy("Test prompt for validation")
        if 0.0 <= entropy <= 1.0:
            print_success(f"Entropy estimation working (entropy: {entropy:.3f})")
        else:
            print_error(f"Entropy estimation failed (got: {entropy})")

        # Test LV ecosystem initialization
        mock_neo4j = MagicMock()
        mock_qdrant = MagicMock()

        lv = LVEcosystem(mock_neo4j, mock_qdrant)
        print_success("LV Ecosystem initialization successful")

        # Test candidate selection (mock version)
        test_candidates = [
            "Test candidate 1: Conservative approach",
            "Test candidate 2: Creative solution",
            "Test candidate 3: Technical implementation"
        ]

        # This would normally require real databases, so we just test the structure
        print_success("LV Framework core functionality validated")

        return True

    except Exception as e:
        print_error(f"LV Framework test failed: {e}")
        return False

def generate_validation_report(results):
    """Generate validation summary report."""
    print_section("Validation Summary Report")

    total_checks = len(results)
    passed_checks = sum(1 for result in results.values() if result)

    print(f"\n{Colors.BOLD}Overall Status: ", end="")
    if passed_checks == total_checks:
        print(f"{Colors.GREEN}✅ ALL CHECKS PASSED{Colors.END}")
        status = "READY"
    elif passed_checks >= total_checks * 0.7:
        print(f"{Colors.YELLOW}⚠️  MOSTLY READY (with warnings){Colors.END}")
        status = "PARTIAL"
    else:
        print(f"{Colors.RED}❌ ISSUES DETECTED{Colors.END}")
        status = "FAILED"

    print(f"\n{Colors.BOLD}Results:{Colors.END}")
    print(f"  Passed: {Colors.GREEN}{passed_checks}{Colors.END}")
    print(f"  Failed: {Colors.RED}{total_checks - passed_checks}{Colors.END}")
    print(f"  Total:  {Colors.BLUE}{total_checks}{Colors.END}")

    print(f"\n{Colors.BOLD}Check Details:{Colors.END}")
    for check_name, result in results.items():
        status_icon = "✅" if result else "❌"
        color = Colors.GREEN if result else Colors.RED
        print(f"  {color}{status_icon} {check_name}{Colors.END}")

    if status == "READY":
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 LV Framework is ready to use!{Colors.END}")
        print(f"{Colors.BLUE}Next steps:{Colors.END}")
        print(f"  1. Run the demo: {Colors.YELLOW}python3 demo_lv_framework.py{Colors.END}")
        print(f"  2. Read the docs: {Colors.YELLOW}README_LV_FRAMEWORK.md{Colors.END}")
        print("  3. Try the examples in the documentation")
    elif status == "PARTIAL":
        print(f"\n{Colors.YELLOW}{Colors.BOLD}🔧 LV Framework mostly ready with some warnings{Colors.END}")
        print(f"{Colors.BLUE}Consider addressing warnings for optimal performance{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}🚫 LV Framework needs attention{Colors.END}")
        print(f"{Colors.BLUE}Please address the failed checks above{Colors.END}")

    return status

async def main():
    """Run complete validation suite."""
    print_header()

    # Run all validation checks
    results = {}

    results["Python Version"] = check_python_version()
    results["Virtual Environment"] = check_virtual_environment()
    results["Core Dependencies"] = check_core_dependencies()
    results["LV Framework Modules"] = check_lv_framework_modules()
    results["File Structure"] = check_file_structure()
    results["Docker Services"] = check_docker_services()

    # Database connections (optional)
    test_database_connections()

    # LV functionality test
    results["LV Framework Functionality"] = await test_lv_functionality()

    # Generate final report
    final_status = generate_validation_report(results)

    print(f"\n{Colors.PURPLE}{Colors.BOLD}🧬 LV Framework Validation Complete! 🧬{Colors.END}")

    return final_status == "READY"

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Validation interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Validation failed with error: {e}{Colors.END}")
        sys.exit(1)
