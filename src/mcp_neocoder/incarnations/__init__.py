"""
Incarnations Package for NeoCoder Framework

This package contains different incarnations of the NeoCoder framework, each providing
a different functionality. Incarnations are loaded dynamically from this directory.

New incarnations can be added by creating a new file in this directory following
the naming convention {name}_incarnation.py. The class should set the incarnation_type attribute.
"""

import importlib
import logging
from pathlib import Path

logger = logging.getLogger("mcp_neocoder.incarnations")

# Only import the base incarnation
from .base_incarnation import BaseIncarnation

# The incarnation discovery is handled by the incarnation_registry
# This file simply provides the BaseIncarnation import
