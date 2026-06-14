"""
Vibe-Audit Framework (VAF) v3.0

DevSecOps framework for validating AI-generated and AI-assisted code before production.
"""

__version__ = "3.0.0"
__author__ = "VAF Contributors"
__license__ = "MIT"

# Expose top-level API
from vaf.config import VAFConfig, load_config

__all__ = ["VAFConfig", "__version__", "load_config"]
