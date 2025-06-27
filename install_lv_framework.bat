@echo off
REM LV Framework Windows Installation Script

setlocal enabledelayedexpansion

:: Configuration
set PYTHON_MIN_VERSION=3.8
set NEO4J_VERSION=5.0
set QDRANT_VERSION=latest

:: Parse command line arguments
set INSTALL_TYPE=standard
set SKIP_DOCKER=
:parse_args
if "%~1"=="" goto :start_install
if "%~1"=="--dev" set INSTALL_TYPE=development
if "%~1"=="--development" set INSTALL_TYPE=development
if "%~1"=="--no-docker" set SKIP_DOCKER=1
if "%~1"=="--help" goto :show_help
if "%~1"=="-h" goto :show_help
shift
goto :parse_args

:show_help
echo LV Framework Windows Installation Script
echo.
echo Usage: install_lv_framework.bat [OPTIONS]
echo.
echo Options:
echo   --dev, --development    Install development dependencies
echo   --no-docker            Skip Docker-based database setup
echo   --help, -h             Show this help message
echo.
pause
exit /b 0

:start_install
echo ============================================================
echo    LOTKA-VOLTERRA ECOSYSTEM INTELLIGENCE FRAMEWORK
echo    Windows Installation Script v1.0
echo ============================================================
echo.

:: Check Python version
python --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    set PYTHON_CMD=python
    goto :check_version
)
python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('python3 --version 2^>^&1') do set PYTHON_VERSION=%%i
    set PYTHON_CMD=python3
    goto :check_version
)
py --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('py --version 2^>^&1') do set PYTHON_VERSION=%%i
    set PYTHON_CMD=py
    goto :check_version
)
echo Python not found. Please install Python %PYTHON_MIN_VERSION% or higher.
pause
exit /b 1

:check_version
echo Found Python %PYTHON_VERSION%
:: (No strict version check, assuming user has recent Python)

:: Create virtual environment
if exist ".venv" (
    echo Virtual environment already exists. Removing old one...
    rmdir /s /q .venv
)
%PYTHON_CMD% -m venv .venv
if errorlevel 1 (
    echo Failed to create virtual environment.
    pause
    exit /b 1
)
call .venv\Scripts\activate.bat

:: Upgrade pip
python -m pip install --upgrade pip setuptools wheel

:: Install Python dependencies
if "%INSTALL_TYPE%"=="development" (
    pip install -r requirements_lv.txt
    pip install pytest pytest-asyncio black flake8 mypy jupyter notebook
) else (
    pip install -r requirements_lv.txt
)
if errorlevel 1 (
    echo Failed to install Python dependencies.
    pause
    exit /b 1
)
echo Python dependencies installed.

:: Docker setup
if not defined SKIP_DOCKER (
    where docker >nul 2>&1
    if errorlevel 1 (
        echo Docker not found. Please install Docker Desktop from https://docker.com/products/docker-desktop
        set SKIP_DOCKER=1
    ) else (
        docker info >nul 2>&1
        if errorlevel 1 (
            echo Docker Desktop not running. Please start Docker Desktop.
            pause
        )
    )
)

:: Setup Neo4j
if not defined SKIP_DOCKER (
    echo Setting up Neo4j database...
    docker ps -a | findstr "neo4j-lv" >nul
    if %errorlevel% equ 0 (
        echo Neo4j container 'neo4j-lv' already exists
        set /p "choice=Remove existing container? (y/N): "
        if /i "!choice!"=="y" (
            docker stop neo4j-lv >nul 2>&1
            docker rm neo4j-lv >nul 2>&1
        ) else (
            echo Using existing Neo4j container
            goto :setup_qdrant
        )
    )
    docker run -d ^
        --name neo4j-lv ^
        -p 7474:7474 -p 7687:7687 ^
        -e NEO4J_AUTH=neo4j/lv_password_2024 ^
        -e NEO4J_PLUGINS=["apoc"] ^
        -v neo4j-lv-data:/data ^
        -v neo4j-lv-logs:/logs ^
        neo4j:%NEO4J_VERSION%
    echo Waiting for Neo4j to start...
    timeout /t 30 /nobreak >nul
    echo Neo4j setup completed.
)

:setup_qdrant
if not defined SKIP_DOCKER (
    echo Setting up Qdrant vector database...
    docker ps -a | findstr "qdrant-lv" >nul
    if %errorlevel% equ 0 (
        echo Qdrant container 'qdrant-lv' already exists
        set /p "choice=Remove existing container? (y/N): "
        if /i "!choice!"=="y" (
            docker stop qdrant-lv >nul 2>&1
            docker rm qdrant-lv >nul 2>&1
        ) else (
            echo Using existing Qdrant container
            goto :install_lv_framework
        )
    )
    docker run -d ^
        --name qdrant-lv ^
        -p 6333:6333 -p 6334:6334 ^
        -v qdrant-lv-data:/qdrant/storage ^
        qdrant/qdrant:%QDRANT_VERSION%
    echo Waiting for Qdrant to start...
    timeout /t 15 /nobreak >nul
    echo Qdrant setup completed.
)

:install_lv_framework
:: Ensure we're in the right directory
if not exist "src\mcp_neocoder\lv_ecosystem.py" (
    echo LV Framework files not found. Please run this script from the project root.
    pause
    exit /b 1
)
pip install -e .
if errorlevel 1 (
    echo LV Framework installation failed.
    pause
    exit /b 1
)
echo LV Framework installed.

:: Verification
if not defined SKIP_DOCKER (
    echo Running verification tests...
    python -c "import sys; import numpy as np; import sentence_transformers; print('NumPy and SentenceTransformers import successful')" || (
        echo Python import test failed.
        goto :skip_verification
    )
    python -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'lv_password_2024')); \
with driver.session() as session: result = session.run('RETURN 1 AS test'); \
print('Neo4j connection successful' if result.single()['test'] == 1 else 'Neo4j connection failed'); driver.close()" || (
        echo Neo4j connection test failed.
    )
    python -c "from qdrant_client import QdrantClient; client = QdrantClient('localhost', port=6333); \
collections = client.get_collections(); print('Qdrant connection successful')" || (
        echo Qdrant connection test failed.
    )
)
:skip_verification

:: Create desktop shortcuts
set DESKTOP=%USERPROFILE%\Desktop
echo [InternetShortcut] > "%DESKTOP%\Neo4j-LV.url"
echo URL=http://localhost:7474 >> "%DESKTOP%\Neo4j-LV.url"
echo [InternetShortcut] > "%DESKTOP%\Qdrant-LV.url"
echo URL=http://localhost:6333/dashboard >> "%DESKTOP%\Qdrant-LV.url"
echo Desktop shortcuts created.

:: Print completion message
echo ============================================================
echo    LV FRAMEWORK INSTALLATION COMPLETED!
echo ============================================================
echo.
echo Next Steps:
echo 1. Activate virtual environment: .venv\Scripts\activate.bat
echo 2. Test the framework: python demo_lv_framework.py
echo 3. Read the documentation: README_LV_FRAMEWORK.md
echo.
echo Database Access:
echo • Neo4j Web Interface: http://localhost:7474
echo   Username: neo4j, Password: lv_password_2024
echo • Qdrant Dashboard: http://localhost:6333/dashboard
echo.
echo Example Usage:
echo from mcp_neocoder.lv_ecosystem import LVEcosystem
echo lv = LVEcosystem(neo4j_session, qdrant_client)
echo results = await lv.select_diverse_outputs(candidates, prompt)
echo.
echo Happy Ecosystem Building! 🧬✨
echo.
pause
exit /b 0
