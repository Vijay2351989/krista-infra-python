"""
Pytest configuration and fixtures for krista-infinispan tests
"""
import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch
from package.cache_config import CacheConfig


@pytest.fixture
def sample_cache_config():
    """Sample cache configuration for testing"""
    return {
        "host": "localhost",
        "port": 11222,
        "username": "admin",
        "password": "admin",
        "protocol": "rest",
        "caches": {
            "test-cache": {
                "enabled": True,
                "memory_size": "50MB",
                "ttl_hours": 2,
                "l1_size": "5MB",
                "l1_expiration_minutes": 30,
                "description": "Test cache",
                "locking": {
                    "isolation": "READ_COMMITTED",
                    "acquire_timeout": 15000
                },
                "transaction": {
                    "mode": "NON_XA",
                    "locking": "OPTIMISTIC"
                },
                "encoding": {
                    "key": {"media_type": "application/x-protostream"},
                    "value": {"media_type": "application/x-protostream"}
                },
                "persistence": {
                    "enabled": True,
                    "type": "file-store",
                    "path": "test-cache-data"
                }
            }
        }
    }


@pytest.fixture
def temp_config_file(sample_cache_config):
    """Create temporary config file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_cache_config, f)
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.fixture
def cache_config(sample_cache_config):
    """CacheConfig instance for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_cache_config, f)
        temp_file = f.name
    
    config = CacheConfig(config_file=temp_file)
    yield config
    
    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)

@pytest.fixture
def mock_requests():
    """Simple requests mock that actually works"""
    with patch('requests.get') as mock_get, \
         patch('requests.post') as mock_post, \
         patch('requests.put') as mock_put, \
         patch('requests.delete') as mock_delete:
        
        # Create a simple response mock
        response = Mock()
        response.status_code = 200
        response.json.return_value = {}
        response.text = "OK"
        
        # All methods return the same response by default
        mock_get.return_value = response
        mock_post.return_value = response
        mock_put.return_value = response
        mock_delete.return_value = response
        
        # Return the mocks directly
        yield {
            'get': mock_get,
            'post': mock_post,
            'put': mock_put,
            'delete': mock_delete,
            'response': response
        }


@pytest.fixture
def sample_data():
    """Sample data for cache operations testing"""
    return {
        "string_data": "Hello World",
        "dict_data": {"name": "John", "age": 30, "active": True},
        "list_data": [1, 2, 3, 4, 5],
        "number_data": 42,
        "boolean_data": True,
        "nested_data": {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"}
            ],
            "metadata": {"created": "2024-01-01", "version": 1}
        }
    }

@pytest.fixture
def test_cache_name():
    """Test cache name for testing"""
    return "test-cache"