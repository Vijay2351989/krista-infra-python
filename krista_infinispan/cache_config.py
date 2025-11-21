import json
import os
from typing import Dict, Any, Optional


class CacheConfig:
    """Load cache configuration from cache_config.json file."""

    def __init__(self, config_file: str = "app/config/cache_config.json"):
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load cache configuration from JSON file."""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(
                f"Cache config file '{self.config_file}' not found. "
                "Please create it with the required cache server credentials."
            )

        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            return config
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {self.config_file}: {e}")

    # ===== CONNECTION SETTINGS =====

    @property
    def host(self) -> str:
        """Get cache host from environment variable or config file."""
        return os.getenv('CACHE_HOST', self.config.get('host', 'localhost'))

    @property
    def port(self) -> int:
        """Get cache port from environment variable or config file."""
        port = os.getenv('CACHE_PORT')
        if port:
            return int(port)
        return self.config.get('port', 11222)

    @property
    def username(self) -> str:
        """Get cache username from environment variable or config file."""
        return os.getenv('CACHE_USERNAME', self.config.get('username', 'admin'))

    @property
    def password(self) -> str:
        """Get cache password from environment variable or config file."""
        return os.getenv('CACHE_PASSWORD', self.config.get('password', ''))

    @property
    def protocol(self) -> str:
        """Protocol to use: 'hotrod' or 'rest'"""
        return os.getenv('CACHE_PROTOCOL', self.config.get('protocol', 'hotrod'))

    @property
    def cache_name(self) -> str:
        """Name of the cache to use (legacy - for backward compatibility)."""
        return self.config.get('cache_name', 'default')

    def get_hotrod_connection_string(self) -> str:
        """Get HotRod connection string for Infinispan."""
        return f"{self.host}:{self.port}"

    def get_rest_url(self) -> str:
        """Get REST API base URL for Infinispan."""
        return f"http://{self.host}:{self.port}/rest/v2"

    def get_credentials(self) -> Dict[str, str]:
        """Get credentials as dictionary."""
        return {
            'username': self.username,
            'password': self.password
        }

    # ===== CACHE DEFINITIONS =====

    def get_cache_names(self) -> list:
        """Get list of all configured cache names."""
        caches = self.config.get('caches', {})
        return list(caches.keys())

    def get_cache_config(self, cache_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific cache."""
        caches = self.config.get('caches', {})
        return caches.get(cache_name)

    def is_cache_enabled(self, cache_name: str) -> bool:
        """Check if a cache is enabled."""
        cache_config = self.get_cache_config(cache_name)
        if cache_config is None:
            return False
        return cache_config.get('enabled', False)

    def get_cache_memory_size(self, cache_name: str) -> str:
        """Get memory size for a cache."""
        cache_config = self.get_cache_config(cache_name)
        if cache_config is None:
            return "50MB"
        return cache_config.get('memory_size', '50MB')

    def get_cache_ttl_hours(self, cache_name: str) -> int:
        """Get TTL in hours for a cache."""
        cache_config = self.get_cache_config(cache_name)
        if cache_config is None:
            return 2
        return cache_config.get('ttl_hours', 2)

    def get_cache_l1_size(self, cache_name: str) -> str:
        """Get L1 cache size for a cache."""
        cache_config = self.get_cache_config(cache_name)
        if cache_config is None:
            return "5MB"
        return cache_config.get('l1_size', '5MB')

    def get_cache_l1_expiration_minutes(self, cache_name: str) -> Optional[int]:
        """Get L1 expiration in minutes for a cache."""
        cache_config = self.get_cache_config(cache_name)
        if cache_config is None:
            return None
        return cache_config.get('l1_expiration_minutes')

    def get_cache_l1_expiration_hours(self, cache_name: str) -> Optional[int]:
        """Get L1 expiration in hours for a cache."""
        cache_config = self.get_cache_config(cache_name)
        if cache_config is None:
            return None
        return cache_config.get('l1_expiration_hours')

    def get_cache_description(self, cache_name: str) -> str:
        """Get description for a cache."""
        cache_config = self.get_cache_config(cache_name)
        if cache_config is None:
            return ""
        return cache_config.get('description', '')

    def get_all_caches_config(self) -> Dict[str, Any]:
        """Get configuration for all caches."""
        return self.config.get('caches', {})

