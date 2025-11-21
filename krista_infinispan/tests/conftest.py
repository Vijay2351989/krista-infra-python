"""
Pytest configuration and fixtures for krista-infinispan tests
"""
import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch
from krista_infinispan.cache_config import CacheConfig


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
    """Mock requests for HTTP calls"""
    with patch('requests.Session') as mock_session:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.text = "OK"
        
        mock_session.return_value.get.return_value = mock_response
        mock_session.return_value.post.return_value = mock_response
        mock_session.return_value.put.return_value = mock_response
        mock_session.return_value.delete.return_value = mock_response
        
        yield mock_session


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
