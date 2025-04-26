"""
Incarnations Package for NeoCoder Framework

This package contains different incarnations of the NeoCoder framework, each providing
a different functionality. Incarnations are loaded dynamically from this directory.

Available incarnations:
- coding: Original coding workflow
- research_orchestration: Scientific workflow management
- decision_support: Decision analysis system
- continuous_learning: Adaptive learning environment
- complex_system: Complex system simulator

New incarnations can be added by creating a new file in this directory following
the naming convention {name}_incarnation.py. The class must inherit from BaseIncarnation
and set the incarnation_type attribute.
"""

from pathlib import Path
import importlib.util
import sys
import logging
import inspect
from typing import Dict, Type, List, Optional, Set, Any

logger = logging.getLogger("mcp_neocoder.incarnations")

# Export the polymorphic_adapter module to make BaseIncarnation available
from .polymorphic_adapter import BaseIncarnation, IncarnationType

# Dictionary to track loaded incarnation modules
INCARNATION_MODULES = {}

def discover_incarnations():
    """Discover and load all incarnation modules in this directory."""
    incarnations_dir = Path(__file__).parent
    incarnation_classes = {}

    for file_path in incarnations_dir.glob("*.py"):
        # Skip __init__.py and other special files
        if file_path.name.startswith("__") or file_path.name == "polymorphic_adapter.py":
            continue

        module_name = file_path.stem
        module_path = str(file_path)

        try:
            # Dynamically load the module
            spec = importlib.util.spec_from_file_location(f"mcp_neocoder.incarnations.{module_name}", module_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)

            # Add to available incarnations
            INCARNATION_MODULES[module_name] = module

            # Find all classes that inherit from BaseIncarnation
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and
                    issubclass(obj, BaseIncarnation) and
                    obj is not BaseIncarnation and
                    hasattr(obj, 'incarnation_type')):
                    incarnation_type = obj.incarnation_type
                    incarnation_classes[incarnation_type] = obj
                    logger.info(f"Discovered incarnation: {incarnation_type.value} ({obj.__name__})")

            logger.info(f"Loaded incarnation module: {module_name}")
        except Exception as e:
            logger.error(f"Error loading incarnation module {module_name}: {e}")

    logger.info(f"Discovered {len(INCARNATION_MODULES)} incarnation modules with {len(incarnation_classes)} incarnation classes")
    return incarnation_classes

# Auto-discover incarnations when the package is imported
# Register all discovered incarnation classes in this central registry
INCARNATION_CLASSES = discover_incarnations()

# This is complete bullshit Claude and we discussed not doing this many times, it prevents modularity and efficient adding of new incarnations and tools. Find a way to import the incarnations from their folder properly.
# We need to explicitly import all incarnation modules to ensure their tools are registered
# This ensures that the modules are loaded and their classes are properly initialized
# Even if they're dynamically discovered above, we need to ensure they're properly imported
try:
    from .data_analysis_incarnation import DataAnalysisIncarnation
    from .research_incarnation import ResearchOrchestration
    from .decision_incarnation import DecisionSupport
    from .knowledge_graph_incarnation import KnowledgeGraphIncarnation

    # Register any other incarnation classes here
    # Dynamically import all potential incarnation modules
    for module_name in INCARNATION_MODULES:
        if module_name not in ['data_analysis_incarnation', 'research_incarnation', 'decision_incarnation', 'knowledge_graph_incarnation']:
            logger.info(f"Ensuring import of additional module: {module_name}")
            if module_name.endswith('_incarnation'):
                try:
                    # Import the module dynamically if we haven't already
                    if f".{module_name}" not in sys.modules:
                        importlib.import_module(f".{module_name}", package="mcp_neocoder.incarnations")
                        logger.info(f"Successfully imported additional module: {module_name}")
                except Exception as e:
                    logger.error(f"Failed to import additional incarnation module {module_name}: {e}")

    # Log all successfully registered incarnation classes
    logger.info(f"Registered incarnation classes: {[cls.__name__ for cls in INCARNATION_CLASSES.values()]}")

except Exception as e:
    logger.error(f"Error importing incarnation modules: {e}")
