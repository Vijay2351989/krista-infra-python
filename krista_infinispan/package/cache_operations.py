"""
Cache Operations - Put and get operations for Infinispan cache.

This module provides simple methods to put and get data from the cache.
It automatically ensures the cache exists before performing operations.

Values are automatically serialized to JSON and base64-encoded before storage.
"""

import logging
import requests
import json
import base64
import time
from typing import Any, Optional
from requests.auth import HTTPDigestAuth
from .cache_config import CacheConfig
from .cache_creator import CacheCreator

logger = logging.getLogger(__name__)


class CacheOperations:
    """Perform put and get operations on Infinispan cache."""

    def __init__(
        self,
        config: CacheConfig = None,
        max_retries: int = 3,
        initial_retry_delay: float = 1.0,
        retry_backoff_multiplier: float = 5.0,
        max_retry_delay: float = 30.0
    ):
        """
        Initialize cache operations.

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
        self.cache_creator = CacheCreator(
            self.config,
            max_retries=max_retries,
            initial_retry_delay=initial_retry_delay,
            retry_backoff_multiplier=retry_backoff_multiplier,
            max_retry_delay=max_retry_delay
        )

        # Store retry settings
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        self.retry_backoff_multiplier = retry_backoff_multiplier
        self.max_retry_delay = max_retry_delay

    def _encode_value(self, value: Any) -> str:
        """
        Encode a Python value to base64-encoded JSON string.

        This is the FIRST step - encoding the actual value before wrapping in ProtoStream.

        Args:
            value: Python object to encode

        Returns:
            Base64-encoded JSON string
        """
        try:
            # Convert to JSON
            if isinstance(value, str):
                json_str = value
            else:
                json_str = json.dumps(value)

            # Encode to base64
            encoded = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
            return encoded

        except Exception as e:
            logger.error(f"Failed to encode value: {e}")
            raise

    def _decode_value(self, encoded_str: str) -> Any:
        """
        Decode a base64-encoded JSON string back to a Python value.

        This is the LAST step - decoding the actual value after unwrapping from ProtoStream.

        Args:
            encoded_str: Base64-encoded JSON string

        Returns:
            Decoded Python object
        """
        try:
            # Decode from base64
            decoded_bytes = base64.b64decode(encoded_str.encode('utf-8'))
            json_str = decoded_bytes.decode('utf-8')

            # Parse JSON
            try:
                return json.loads(json_str)
            except (json.JSONDecodeError, TypeError):
                # If not valid JSON, return as string
                return json_str

        except Exception as e:
            logger.error(f"Failed to decode value: {e}")
            raise

    def _serialize_value(self, value: Any) -> str:
        """
        Serialize a Python value to ProtoStream JSON format.

        This is a TWO-STEP process:
        1. Encode the value to base64-encoded JSON
        2. Wrap the encoded value in the ProtoStream envelope

        Args:
            value: Python object to serialize

        Returns:
            JSON string in ProtoStream format with base64-encoded value
        """
        # Step 1: Encode the value to base64
        encoded_value = self._encode_value(value)

        # Step 2: Wrap in ProtoStream format with correct _type
        # The _type must match the fully qualified Protobuf message name
        # from our registered schema: package.MessageName = cache.CacheEntry
        protostream_value = {
            "_type": "cache.CacheEntry",
            "value": encoded_value
        }

        return json.dumps(protostream_value)

    def _deserialize_value(self, protostream_json: str) -> Any:
        """
        Deserialize a ProtoStream JSON string back to a Python value.

        This is a TWO-STEP process (reverse of serialization):
        1. Unwrap the ProtoStream envelope
        2. Decode the base64-encoded value

        Args:
            protostream_json: JSON string in ProtoStream format

        Returns:
            Deserialized Python object
        """
        try:
            # Step 1: Parse the ProtoStream envelope
            protostream_obj = json.loads(protostream_json)

            # Extract the value field
            if isinstance(protostream_obj, dict) and "value" in protostream_obj:
                encoded_value = protostream_obj["value"]

                # Step 2: Decode the base64-encoded value
                return self._decode_value(encoded_value)
            else:
                # If not in expected format, return as-is
                logger.warning(f"Unexpected ProtoStream format: {protostream_json}")
                return protostream_obj

        except json.JSONDecodeError as e:
            logger.error(f"Failed to deserialize value: {e}")
            # Return raw string if deserialization fails
            return protostream_json

    def _put_with_retry(self, url: str, json_value: str, headers: dict) -> requests.Response:
        """Internal method to put value with retry logic."""
        delay = self.initial_retry_delay
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return requests.put(
                    url,
                    data=json_value,
                    auth=self.auth,
                    headers=headers,
                    timeout=10
                )
            except (requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout,
                    requests.exceptions.RequestException) as e:
                last_exception = e

                if attempt < self.max_retries:
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries + 1} failed for PUT {url}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
                    delay = min(delay * self.retry_backoff_multiplier, self.max_retry_delay)
                else:
                    logger.error(
                        f"All {self.max_retries + 1} attempts failed for PUT {url}: {e}"
                    )

        raise last_exception

    def put(self, cache_name: str, key: str, value: Any) -> bool:
        """
        Put a key-value pair into the cache.

        Automatically creates the cache if it doesn't exist.
        The value is base64-encoded, then wrapped in ProtoStream.
        Retries with exponential backoff on connection errors.

        Args:
            cache_name: Name of the cache
            key: Cache key
            value: Value to store (any JSON-serializable Python object)

        Returns:
            True if operation was successful, False otherwise
        """
        try:
            # Ensure cache exists
            if not self._ensure_cache_exists(cache_name):
                logger.error(f"Failed to ensure cache '{cache_name}' exists")
                return False

            # Serialize value to ProtoStream JSON format (with base64 encoding)
            json_value = self._serialize_value(value)

            # Put value in cache
            url = f"{self.base_url}/caches/{cache_name}/{key}"
            logger.debug(f"Putting key '{key}' into cache '{cache_name}' with value: {json_value}")

            # Use JSON with ProtoStream encoding
            # The cache is configured with application/x-protostream
            # But we send JSON and Infinispan converts it automatically
            headers = {"Content-Type": "application/json"}

            response = self._put_with_retry(url, json_value, headers)

            if response.status_code in [200, 201, 204]:
                logger.info(f"✓ Successfully put key '{key}' into cache '{cache_name}'")
                logger.debug(f"Response status: {response.status_code}")
                return True
            else:
                logger.error(f"✗ Failed to put key '{key}': {response.status_code} - {response.text}")
                logger.error(f"Request URL: {url}")
                logger.error(f"Request Data: {value}")
                logger.error(f"Request Headers: {headers}")
                return False

        except Exception as e:
            logger.error(f"✗ Error putting key '{key}' into cache: {e}")
            return False

    def _get_with_retry(self, url: str) -> requests.Response:
        """Internal method to get value with retry logic."""
        delay = self.initial_retry_delay
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return requests.get(
                    url,
                    auth=self.auth,
                    timeout=10
                )
            except (requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout,
                    requests.exceptions.RequestException) as e:
                last_exception = e

                if attempt < self.max_retries:
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries + 1} failed for GET {url}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
                    delay = min(delay * self.retry_backoff_multiplier, self.max_retry_delay)
                else:
                    logger.error(
                        f"All {self.max_retries + 1} attempts failed for GET {url}: {e}"
                    )

        raise last_exception

    def get(self, cache_name: str, key: str, deserialize: bool = True) -> Optional[Any]:
        """
        Get a value from the cache by key.

        Does NOT create cache if it doesn't exist. Returns None if cache doesn't exist.
        The value is automatically deserialized from ProtoStream format by default.
        Retries with exponential backoff on connection errors.

        Args:
            cache_name: Name of the cache
            key: Cache key
            deserialize: If True (default), deserialize the value to Python object.
                        If False, return raw ProtoStream JSON string.

        Returns:
            Deserialized Python object (if deserialize=True),
            or raw JSON string (if deserialize=False),
            or None if key not found, cache doesn't exist, or error occurred
        """
        try:
            # Check if cache exists (do NOT create it)
            if not self._cache_exists(cache_name):
                logger.warning(f"Cache '{cache_name}' does not exist. Cannot retrieve key '{key}'")
                return None

            # Get value from cache
            url = f"{self.base_url}/caches/{cache_name}/{key}"
            logger.debug(f"Getting key '{key}' from cache '{cache_name}'")

            response = self._get_with_retry(url)

            if response.status_code == 200:
                logger.debug(f"✓ Successfully retrieved key '{key}' from cache '{cache_name}'")

                # Deserialize if requested
                if deserialize:
                    return self._deserialize_value(response.text)
                else:
                    # Return raw ProtoStream JSON
                    return response.text

            elif response.status_code == 404:
                logger.debug(f"Key '{key}' not found in cache '{cache_name}'")
                return None
            else:
                logger.error(f"✗ Failed to get key '{key}': {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"✗ Error getting key '{key}' from cache: {e}")
            return None

    def _delete_with_retry(self, url: str) -> requests.Response:
        """Internal method to delete value with retry logic."""
        delay = self.initial_retry_delay
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return requests.delete(
                    url,
                    auth=self.auth,
                    timeout=10
                )
            except (requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout,
                    requests.exceptions.RequestException) as e:
                last_exception = e

                if attempt < self.max_retries:
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries + 1} failed for DELETE {url}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
                    delay = min(delay * self.retry_backoff_multiplier, self.max_retry_delay)
                else:
                    logger.error(
                        f"All {self.max_retries + 1} attempts failed for DELETE {url}: {e}"
                    )

        raise last_exception

    def delete(self, cache_name: str, key: str) -> bool:
        """
        Delete a key from the cache.

        Does NOT create cache if it doesn't exist. Returns False if cache doesn't exist.
        Retries with exponential backoff on connection errors.

        Args:
            cache_name: Name of the cache
            key: Cache key

        Returns:
            True if operation was successful, False if cache doesn't exist or error occurred
        """
        try:
            # Check if cache exists (do NOT create it)
            if not self._cache_exists(cache_name):
                logger.warning(f"Cache '{cache_name}' does not exist. Cannot delete key '{key}'")
                return False

            # Delete key from cache
            url = f"{self.base_url}/caches/{cache_name}/{key}"
            logger.debug(f"Deleting key '{key}' from cache '{cache_name}'")

            response = self._delete_with_retry(url)

            if response.status_code in [200, 204]:
                logger.debug(f"✓ Successfully deleted key '{key}' from cache '{cache_name}'")
                return True
            elif response.status_code == 404:
                logger.debug(f"Key '{key}' not found in cache '{cache_name}'")
                return True  # Key doesn't exist, so deletion is successful
            else:
                logger.error(f"✗ Failed to delete key '{key}': {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"✗ Error deleting key '{key}' from cache: {e}")
            return False

    def _cache_exists(self, cache_name: str) -> bool:
        """
        Check if a cache exists. Does NOT create it.

        Args:
            cache_name: Name of the cache

        Returns:
            True if cache exists, False otherwise
        """
        try:
            return self.cache_creator.cache_exists(cache_name)
        except Exception as e:
            logger.error(f"✗ Error checking if cache '{cache_name}' exists: {e}")
            return False

    def _ensure_cache_exists(self, cache_name: str) -> bool:
        """
        Ensure the cache exists. Creates it if it doesn't.

        Used by put() operation to automatically create cache if needed.

        Args:
            cache_name: Name of the cache

        Returns:
            True if cache exists or was created successfully, False otherwise
        """
        try:
            # Check if cache exists
            if self.cache_creator.cache_exists(cache_name):
                logger.debug(f"Cache '{cache_name}' already exists")
                return True

            # Cache doesn't exist, create it
            logger.info(f"Cache '{cache_name}' does not exist, creating it...")
            success = self.cache_creator.create_cache(cache_name)

            if success:
                logger.info(f"✓ Cache '{cache_name}' created successfully")
                return True
            else:
                logger.error(f"✗ Failed to create cache '{cache_name}'")
                return False

        except Exception as e:
            logger.error(f"✗ Error ensuring cache exists: {e}")
            return False

