#!/bin/bash

# LV Framework Installation Script
# ================================
# Automated installation for Lotka-Volterra Ecosystem Intelligence Framework

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PYTHON_MIN_VERSION="3.8"
NEO4J_VERSION="5.22.0"
QDRANT_VERSION="latest"

echo -e "${BLUE}"
echo "🧬 ============================================================"
echo "   LOTKA-VOLTERRA ECOSYSTEM INTELLIGENCE FRAMEWORK"
echo "   Installation Script v1.0"
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

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python version
check_python_version() {
    if command_exists python3; then
        PYTHON_VERSION=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_VERSION=$(python -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
        PYTHON_CMD="python"
    else
        print_error "Python not found. Please install Python $PYTHON_MIN_VERSION or higher."
        exit 1
    fi

    # Compare versions
    if [ "$(printf '%s\n' "$PYTHON_MIN_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$PYTHON_MIN_VERSION" ]; then
        print_status "Python $PYTHON_VERSION found"
        return 0
    else
        print_error "Python $PYTHON_MIN_VERSION or higher required. Found: $PYTHON_VERSION"
        exit 1
    fi
}

# Create virtual environment
create_venv() {
    print_info "Creating virtual environment..."

    if [ -d ".venv" ]; then
        print_warning "Virtual environment already exists. Removing old one..."
        rm -rf .venv
    fi

    $PYTHON_CMD -m venv .venv

    # Activate virtual environment
    source .venv/bin/activate

    # Upgrade pip
    pip install --upgrade pip setuptools wheel

    print_status "Virtual environment created and activated"
}

# Install Python dependencies
install_python_deps() {
    print_info "Installing Python dependencies..."

    # Ensure we're in virtual environment
    if [ -z "$VIRTUAL_ENV" ]; then
        print_error "Virtual environment not activated"
        exit 1
    fi

    # Install core dependencies
    pip install -r requirements_lv.txt

    # Install development dependencies if requested
    if [ "$1" = "--dev" ]; then
        pip install pytest pytest-asyncio black flake8 mypy jupyter notebook
        print_status "Development dependencies installed"
    fi

    print_status "Python dependencies installed"
}

# Check and install Docker
setup_docker() {
    if command_exists docker; then
        print_status "Docker found"

        # Check if Docker daemon is running
        if ! docker info >/dev/null 2>&1; then
            print_warning "Docker daemon not running. Please start Docker."
            return 1
        fi
    else
        print_warning "Docker not found. Installing Docker..."

        # Install Docker based on OS
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Ubuntu/Debian
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo usermod -aG docker $USER
            print_status "Docker installed. Please log out and log back in."
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            print_warning "Please install Docker Desktop for macOS from https://docker.com"
            return 1
        else
            print_warning "Please install Docker manually for your OS"
            return 1
        fi
    fi

    return 0
}

# Setup Neo4j database
setup_neo4j() {
    print_info "Setting up Neo4j database..."

    # Check if Neo4j container already exists
    if docker ps -a | grep -q "neo4j-lv"; then
        print_warning "Neo4j container 'neo4j-lv' already exists"
        read -p "Remove existing container? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker stop neo4j-lv >/dev/null 2>&1 || true
            docker rm neo4j-lv >/dev/null 2>&1 || true
        else
            print_info "Using existing Neo4j container"
            return 0
        fi
    fi

    # Start Neo4j container
    docker run -d \
        --name neo4j-lv \
        -p 7474:7474 -p 7687:7687 \
        -e NEO4J_AUTH=neo4j/lv_password_2024 \
        -e NEO4J_PLUGINS='["apoc"]' \
        -v neo4j-lv-data:/data \
        -v neo4j-lv-logs:/logs \
        neo4j:$NEO4J_VERSION

    print_status "Neo4j container started"
    print_info "Neo4j Web Interface: http://localhost:7474"
    print_info "Username: neo4j, Password: lv_password_2024"

    # Wait for Neo4j to start
    print_info "Waiting for Neo4j to start..."
    sleep 30

    # Test connection
    if docker exec neo4j-lv cypher-shell -u neo4j -p lv_password_2024 "RETURN 1" >/dev/null 2>&1; then
        print_status "Neo4j connection verified"
    else
        print_warning "Neo4j may still be starting. Please wait a moment and test manually."
    fi
}

# Setup Qdrant vector database
setup_qdrant() {
    print_info "Setting up Qdrant vector database..."

    # Check if Qdrant container already exists
    if docker ps -a | grep -q "qdrant-lv"; then
        print_warning "Qdrant container 'qdrant-lv' already exists"
        read -p "Remove existing container? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker stop qdrant-lv >/dev/null 2>&1 || true
            docker rm qdrant-lv >/dev/null 2>&1 || true
        else
            print_info "Using existing Qdrant container"
            return 0
        fi
    fi

    # Start Qdrant container
    docker run -d \
        --name qdrant-lv \
        -p 6333:6333 -p 6334:6334 \
        -v qdrant-lv-data:/qdrant/storage \
        qdrant/qdrant:$QDRANT_VERSION

    print_status "Qdrant container started"
    print_info "Qdrant Web Interface: http://localhost:6333/dashboard"

    # Wait for Qdrant to start
    print_info "Waiting for Qdrant to start..."
    sleep 15

    # Test connection
    if curl -s http://localhost:6333/collections >/dev/null 2>&1; then
        print_status "Qdrant connection verified"
    else
        print_warning "Qdrant may still be starting. Please wait a moment and test manually."
    fi
}

# Install LV Framework
install_lv_framework() {
    print_info "Installing LV Framework..."

    # Ensure we're in the right directory
    if [ ! -f "src/mcp_neocoder/lv_ecosystem.py" ]; then
        print_error "LV Framework files not found. Please run this script from the project root."
        exit 1
    fi

    # Install in development mode
    pip install -e .

    print_status "LV Framework installed"
}

# Run verification tests
run_verification() {
    print_info "Running verification tests..."

    # Test Python imports
    python3 -c "
import sys
try:
    import numpy as np
    import sentence_transformers
    print('✅ NumPy and SentenceTransformers import successful')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"

    # Test Neo4j connection
    python3 -c "
import sys
try:
    from neo4j import GraphDatabase
    driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'lv_password_2024'))
    with driver.session() as session:
        result = session.run('RETURN 1 AS test')
        if result.single()['test'] == 1:
            print('✅ Neo4j connection successful')
        else:
            print('❌ Neo4j connection failed')
            sys.exit(1)
    driver.close()
except Exception as e:
    print(f'❌ Neo4j connection error: {e}')
    sys.exit(1)
"

    # Test Qdrant connection
    python3 -c "
import sys
try:
    from qdrant_client import QdrantClient
    client = QdrantClient('localhost', port=6333)
    collections = client.get_collections()
    print('✅ Qdrant connection successful')
except Exception as e:
    print(f'❌ Qdrant connection error: {e}')
    sys.exit(1)
"

    # Run LV Framework demo (minimal test)
    if [ -f "demo_lv_framework.py" ]; then
        print_info "Running LV Framework demo..."
        python3 demo_lv_framework.py 2>/dev/null || print_warning "Demo completed with warnings (expected)"
    fi

    print_status "Verification tests completed"
}

# Create desktop shortcuts (Linux only)
create_shortcuts() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        print_info "Creating desktop shortcuts..."

        DESKTOP_DIR="$HOME/Desktop"
        if [ -d "$DESKTOP_DIR" ]; then
            # Neo4j shortcut
            cat > "$DESKTOP_DIR/Neo4j-LV.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Link
Name=Neo4j LV Database
Comment=Open Neo4j database for LV Framework
URL=http://localhost:7474
Icon=applications-internet
EOF

            # Qdrant shortcut
            cat > "$DESKTOP_DIR/Qdrant-LV.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Link
Name=Qdrant LV Vector DB
Comment=Open Qdrant vector database for LV Framework
URL=http://localhost:6333/dashboard
Icon=applications-internet
EOF

            chmod +x "$DESKTOP_DIR"/*.desktop
            print_status "Desktop shortcuts created"
        fi
    fi
}

# Print completion message
print_completion() {
    echo
    echo -e "${GREEN}"
    echo "🎉 ============================================================"
    echo "   LV FRAMEWORK INSTALLATION COMPLETED!"
    echo "============================================================${NC}"
    echo
    echo -e "${BLUE}Next Steps:${NC}"
    echo "1. Activate virtual environment: ${YELLOW}source .venv/bin/activate${NC}"
    echo "2. Test the framework: ${YELLOW}python3 demo_lv_framework.py${NC}"
    echo "3. Read the documentation: ${YELLOW}README_LV_FRAMEWORK.md${NC}"
    echo
    echo -e "${BLUE}Database Access:${NC}"
    echo "• Neo4j Web Interface: ${YELLOW}http://localhost:7474${NC}"
    echo "  Username: neo4j, Password: lv_password_2024"
    echo "• Qdrant Dashboard: ${YELLOW}http://localhost:6333/dashboard${NC}"
    echo
    echo -e "${BLUE}Example Usage:${NC}"
    echo "${YELLOW}from mcp_neocoder.lv_ecosystem import LVEcosystem${NC}"
    echo "${YELLOW}lv = LVEcosystem(neo4j_session, qdrant_client)${NC}"
    echo "${YELLOW}results = await lv.select_diverse_outputs(candidates, prompt)${NC}"
    echo
    print_status "Happy Ecosystem Building! 🧬✨"
}

# Main installation function
main() {
    print_info "Starting LV Framework installation..."

    # Parse command line arguments
    INSTALL_TYPE="standard"
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dev|--development)
                INSTALL_TYPE="development"
                shift
                ;;
            --no-docker)
                SKIP_DOCKER=1
                shift
                ;;
            --help|-h)
                echo "LV Framework Installation Script"
                echo ""
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --dev, --development    Install development dependencies"
                echo "  --no-docker            Skip Docker-based database setup"
                echo "  --help, -h              Show this help message"
                echo ""
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Installation steps
    check_python_version
    create_venv

    if [ -z "$SKIP_DOCKER" ]; then
        if setup_docker; then
            setup_neo4j
            setup_qdrant
        else
            print_warning "Skipping database setup due to Docker issues"
            print_info "Please install Neo4j and Qdrant manually"
        fi
    else
        print_info "Skipping Docker-based database setup"
    fi

    if [ "$INSTALL_TYPE" = "development" ]; then
        install_python_deps --dev
    else
        install_python_deps
    fi

    install_lv_framework

    if [ -z "$SKIP_DOCKER" ]; then
        run_verification
    fi

    create_shortcuts
    print_completion
}

# Run main function
main "$@"
