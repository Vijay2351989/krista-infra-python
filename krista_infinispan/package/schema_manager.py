"""
Schema Manager - Register Protobuf schemas with Infinispan for ProtoStream encoding.

This module handles the registration of Protobuf schemas required for
application/x-protostream encoding in Infinispan.
"""

import logging
import requests
import time
from requests.auth import HTTPDigestAuth
from .cache_config import CacheConfig

logger = logging.getLogger(__name__)


class SchemaManager:
    """Manage Protobuf schema registration in Infinispan."""

    def __init__(
        self,
        config: CacheConfig = None,
        max_retries: int = 3,
        initial_retry_delay: float = 1.0,
        retry_backoff_multiplier: float = 5.0,
        max_retry_delay: float = 30.0
    ):
        """
        Initialize schema manager.

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

        # Store retry settings
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        self.retry_backoff_multiplier = retry_backoff_multiplier
        self.max_retry_delay = max_retry_delay

    def _register_schema_with_retry(self, url: str, schema_content: str) -> requests.Response:
        """Internal method to register schema with retry logic."""
        delay = self.initial_retry_delay
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return requests.post(
                    url,
                    data=schema_content,
                    auth=self.auth,
                    headers={"Content-Type": "text/plain"},
                    timeout=10
                )
            except (requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout,
                    requests.exceptions.RequestException) as e:
                last_exception = e

                if attempt < self.max_retries:
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries + 1} failed for register_schema {url}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
                    delay = min(delay * self.retry_backoff_multiplier, self.max_retry_delay)
                else:
                    logger.error(
                        f"All {self.max_retries + 1} attempts failed for register_schema {url}: {e}"
                    )

        raise last_exception

    def register_schema(self, schema_name: str, schema_content: str) -> bool:
        """
        Register a Protobuf schema with Infinispan.
        Retries with exponential backoff on connection errors.

        Args:
            schema_name: Name of the schema (e.g., "cache_entry.proto")
            schema_content: The Protobuf schema definition as a string

        Returns:
            True if registration was successful, False otherwise
        """
        try:
            url = f"{self.base_url}/schemas/{schema_name}"
            logger.info(f"Registering Protobuf schema '{schema_name}'...")

            # Register the schema
            response = self._register_schema_with_retry(url, schema_content)

            if response.status_code in [200, 201, 204]:
                logger.info(f"✓ Successfully registered schema '{schema_name}'")
                return True
            else:
                logger.error(f"✗ Failed to register schema '{schema_name}': {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"✗ Error registering schema '{schema_name}': {e}")
            return False

    def _get_schema_with_retry(self, url: str) -> requests.Response:
        """Internal method to get schema with retry logic."""
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
                        f"Attempt {attempt + 1}/{self.max_retries + 1} failed for get_schema {url}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
                    delay = min(delay * self.retry_backoff_multiplier, self.max_retry_delay)
                else:
                    logger.error(
                        f"All {self.max_retries + 1} attempts failed for get_schema {url}: {e}"
                    )

        raise last_exception

    def get_schema(self, schema_name: str) -> str:
        """
        Get a registered Protobuf schema from Infinispan.
        Retries with exponential backoff on connection errors.

        Args:
            schema_name: Name of the schema

        Returns:
            Schema content as string, or None if not found
        """
        try:
            url = f"{self.base_url}/schemas/{schema_name}"
            response = self._get_schema_with_retry(url)

            if response.status_code == 200:
                return response.text
            elif response.status_code == 404:
                logger.debug(f"Schema '{schema_name}' not found")
                return None
            else:
                logger.error(f"Error getting schema '{schema_name}': {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error getting schema '{schema_name}': {e}")
            return None

    def schema_exists(self, schema_name: str) -> bool:
        """
        Check if a schema is already registered.

        Args:
            schema_name: Name of the schema

        Returns:
            True if schema exists, False otherwise
        """
        return self.get_schema(schema_name) is not None

    def register_cache_entry_schema(self) -> bool:
        """
        Register the default CacheEntry schema.

        Returns:
            True if registration was successful, False otherwise
        """
        schema_content = """syntax = "proto3";

package cache;

/**
 * Generic cache entry that stores base64-encoded JSON data
 */
message CacheEntry {
    // The actual value stored as a base64-encoded JSON string
    string value = 1;

    // Optional metadata
    int64 created_at = 2;
    int64 updated_at = 3;
}
"""

        schema_name = "cache_entry.proto"

        # Check if schema already exists
        if self.schema_exists(schema_name):
            logger.info(f"Schema '{schema_name}' already registered")
            return True

        return self.register_schema(schema_name, schema_content)

