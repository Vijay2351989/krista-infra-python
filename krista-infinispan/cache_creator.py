"""
Cache Creator - Creates Infinispan caches from configuration.

This module reads cache configurations and creates distributed caches
with proper settings for memory size, TTL, L1 size, and L1 expiration.
"""

import logging
import requests
import time
from typing import Dict, Any
from requests.auth import HTTPDigestAuth
from app.cache.cache_config import CacheConfig

logger = logging.getLogger(__name__)


class CacheCreator:
    """Creates and manages Infinispan caches from configuration."""

    def __init__(
        self,
        config: CacheConfig = None,
        max_retries: int = 3,
        initial_retry_delay: float = 1.0,
        retry_backoff_multiplier: float = 5.0,
        max_retry_delay: float = 30.0
    ):
        """
        Initialize cache creator.

        Args:
            config: CacheConfig instance (optional, will load default if not provided)
            max_retries: Maximum number of retry attempts (default: 3)
            initial_retry_delay: Initial delay between retries in seconds (default: 1.0)
            retry_backoff_multiplier: Multiplier for exponential backoff (default: 2.0)
            max_retry_delay: Maximum delay between retries in seconds (default: 30.0)
        """
        self.config = config or CacheConfig()
        self.base_url = self.config.get_rest_url()
        self.auth = HTTPDigestAuth(self.config.username, self.config.password)
        self.headers = {"Content-Type": "application/json"}

        # Store retry settings
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        self.retry_backoff_multiplier = retry_backoff_multiplier
        self.max_retry_delay = max_retry_delay
    
    def _cache_exists_with_retry(self, url: str) -> requests.Response:
        """Internal method to check cache existence with retry logic."""
        delay = self.initial_retry_delay
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return requests.get(url, auth=self.auth, timeout=10)
            except (requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout,
                    requests.exceptions.RequestException) as e:
                last_exception = e

                if attempt < self.max_retries:
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries + 1} failed for cache_exists {url}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
                    delay = min(delay * self.retry_backoff_multiplier, self.max_retry_delay)
                else:
                    logger.error(
                        f"All {self.max_retries + 1} attempts failed for cache_exists {url}: {e}"
                    )

        raise last_exception

    def _create_cache_with_retry(self, url: str, infinispan_config: dict) -> requests.Response:
        """Internal method to create cache with retry logic."""
        delay = self.initial_retry_delay
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return requests.post(
                    url,
                    json=infinispan_config,
                    auth=self.auth,
                    headers=self.headers,
                    timeout=30
                )
            except (requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout,
                    requests.exceptions.RequestException) as e:
                last_exception = e

                if attempt < self.max_retries:
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries + 1} failed for create_cache {url}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
                    delay = min(delay * self.retry_backoff_multiplier, self.max_retry_delay)
                else:
                    logger.error(
                        f"All {self.max_retries + 1} attempts failed for create_cache {url}: {e}"
                    )

        raise last_exception

    def cache_exists(self, cache_name: str) -> bool:
        """
        Check if a cache exists.
        Retries with exponential backoff on connection errors.
        """
        try:
            url = f"{self.base_url}/caches/{cache_name}"
            response = self._cache_exists_with_retry(url)
            exists = response.status_code == 200
            logger.debug(f"Cache '{cache_name}' exists: {exists} (status: {response.status_code})")
            return exists
        except Exception as e:
            logger.debug(f"Error checking cache existence for '{cache_name}': {e}")
            return False

    def create_cache(self, cache_name: str) -> bool:
        """
        Create a distributed cache by cache name.

        Reads configuration from cache_config.json and creates the cache with proper settings.

        Note: This method assumes the cache is enabled. The caller should check if the cache
        is enabled before calling this method.

        Args:
            cache_name: Name of the cache to create

        Returns:
            True if cache was created successfully or already exists

        Raises:
            ValueError: If cache is not configured
            ConnectionError: If cannot connect to Infinispan server
            Exception: If cache creation fails
        """
        # Check if cache is configured
        cache_config = self.config.get_cache_config(cache_name)
        if not cache_config:
            raise ValueError(f"Cache '{cache_name}' not found in configuration")

        # Note: We don't check if cache is enabled here - that's the caller's responsibility
        # The initializer filters out disabled caches before calling this method

        # Check if cache already exists
        if self.cache_exists(cache_name):
            logger.info(f"Cache '{cache_name}' already exists")
            return True

        # Build cache configuration
        infinispan_config = self._build_cache_config(cache_config)

        # Create cache
        url = f"{self.base_url}/caches/{cache_name}"
        logger.debug(f"Creating cache '{cache_name}' at {url}...")

        try:
            response = self._create_cache_with_retry(url, infinispan_config)
        except requests.exceptions.ConnectionError as e:
            # Cannot connect to server - raise ConnectionError
            raise ConnectionError(
                f"Cannot connect to Infinispan server at {self.config.host}:{self.config.port}: {e}"
            ) from e
        except requests.exceptions.Timeout as e:
            # Connection timeout - raise ConnectionError
            raise ConnectionError(
                f"Connection timeout to Infinispan server at {self.config.host}:{self.config.port}"
            ) from e
        except requests.exceptions.RequestException as e:
            # Other request errors - raise as generic Exception
            raise Exception(f"Request failed while creating cache '{cache_name}': {e}") from e

        # Check response status
        if response.status_code in [200, 201]:
            logger.debug(f"Cache '{cache_name}' created successfully")
            return True
        else:
            raise Exception(
                f"Failed to create cache '{cache_name}': "
                f"HTTP {response.status_code} - {response.text}"
            )
    
    def _build_cache_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build Infinispan distributed cache configuration from settings.

        Args:
            config: Configuration dict with cache settings

        Returns:
            Infinispan cache configuration dict
        """
        # Convert memory size to bytes for Infinispan
        memory_size = config.get('memory_size', '50MB')

        # Convert TTL hours to milliseconds
        ttl_hours = config.get('ttl_hours', 2)
        ttl_ms = ttl_hours * 60 * 60 * 1000

        # Convert L1 expiration to milliseconds
        l1_expiration_ms = self._get_l1_expiration_ms(config)

        # Build the cache configuration
        cache_config = {
            "distributed-cache": {
                "mode": "SYNC",
                "owners": 1,
                "statistics": True,
                "l1-lifespan": l1_expiration_ms,
                "l1-cleanup-interval": l1_expiration_ms,
                "locking": {
                    "isolation": "READ_COMMITTED",
                    "acquire-timeout": 30000
                },
                "transaction": {
                    "mode": "NONE",
                    "auto-commit": True,
                    "locking": "OPTIMISTIC"
                },
                "memory": {
                    "max-size": memory_size,
                    "when-full": "REMOVE",
                    "storage": "HEAP"
                },
                "expiration": {
                    "lifespan": ttl_ms
                },
                "encoding": {
                    "key": {
                        "media-type": "application/x-protostream"
                    },
                    "value": {
                        "media-type": "application/x-protostream"
                    }
                }
            }
        }

        # Add persistence configuration if enabled
        persistence_config = self._build_persistence_config(config)
        if persistence_config:
            cache_config["distributed-cache"]["persistence"] = persistence_config

        return cache_config

    def _build_persistence_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build persistence configuration for file store.

        Args:
            config: Configuration dict with persistence settings

        Returns:
            Persistence configuration dict, or None if persistence is disabled
        """
        persistence_settings = config.get('persistence', {})

        # Check if persistence is enabled
        if not persistence_settings.get('enabled', False):
            return None

        # Get persistence type (currently only file-store supported)
        store_type = persistence_settings.get('type', 'file-store')

        if store_type != 'file-store':
            logger.warning(f"Unsupported persistence type: {store_type}. Only 'file-store' is supported.")
            return None

        # Build file-store configuration with data and index paths
        # Note: Paths must be relative to global persistent location (/opt/infinispan/server/data)
        base_path = persistence_settings.get('path', 'caches')
        file_store_config = {
            "shared": persistence_settings.get('shared', False),
            "data": {
                "path": base_path + "/data"
            },
            "index": {
                "path": base_path + "/index"
            }
        }

        # Add write-behind configuration if enabled (INSIDE file-store for JSON format)
        write_behind = persistence_settings.get('write_behind', {})
        if write_behind.get('enabled', False):
            file_store_config["write-behind"] = {
                "modification-queue-size": write_behind.get('modification_queue_size', 2048),
                "fail-silently": write_behind.get('fail_silently', False)
            }

        # Build the persistence configuration
        persistence_config = {
            "passivation": persistence_settings.get('passivation', False),
            "file-store": file_store_config
        }

        return persistence_config

    def _get_l1_expiration_ms(self, config: Dict[str, Any]) -> int:
        """
        Get L1 expiration in milliseconds from config.

        Supports both l1_expiration_minutes and l1_expiration_hours.
        """
        # Check for minutes first
        if 'l1_expiration_minutes' in config:
            minutes = config['l1_expiration_minutes']
            return minutes * 60 * 1000

        # Check for hours
        if 'l1_expiration_hours' in config:
            hours = config['l1_expiration_hours']
            return hours * 60 * 60 * 1000

        # Default: 30 minutes
        return 30 * 60 * 1000
    



