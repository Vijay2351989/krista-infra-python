"""Python module for Krista Infinispan integration."""
"""Knowledge Agent Cache - Infinispan integration package."""

from .cache_operations import CacheOperations
from .cache_creator import CacheCreator
from .cache_config import CacheConfig
from .schema_manager import SchemaManager

__version__ = "1.0.7"
__all__ = ["CacheOperations", "CacheCreator", "CacheConfig", "SchemaManager"]

