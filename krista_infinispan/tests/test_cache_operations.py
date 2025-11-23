"""
Tests for CacheOperations class
"""
import pytest
import json
import base64
from unittest.mock import Mock, patch, MagicMock
from krista_infinispan.package.cache_operations import CacheOperations


class TestCacheOperations:
    
    @pytest.fixture
    def cache_operations(self, cache_config):
        """CacheOperations instance for testing"""
        return CacheOperations(config=cache_config)
    
    def test_put_and_get_string(self, cache_operations, mock_requests, sample_data, test_cache_name):
        """Test putting and getting string data"""
        # Mock successful put
        mock_requests['put'].return_value.status_code = 200
        
        # Mock successful get with encoded data
        encoded_data = base64.b64encode(json.dumps(sample_data["string_data"]).encode()).decode()
        mock_response_data = {
            "_type": "cache.CacheEntry",
            "value": encoded_data
        }
        get_response = Mock()
        get_response.status_code = 200
        get_response.json.return_value = mock_response_data
        get_response.text = json.dumps(mock_response_data)
        mock_requests['get'].return_value = get_response
        
        # Test put
        result = cache_operations.put(test_cache_name, "test_key", sample_data["string_data"])
        assert result is True
        
        # Test get
        retrieved_data = cache_operations.get(test_cache_name, "test_key")
        assert retrieved_data == sample_data["string_data"]

    def test_put_and_get_dict(self, cache_operations, mock_requests, sample_data, test_cache_name):
        """Test putting and getting dictionary data"""
        mock_requests['put'].return_value.status_code = 200
        
        encoded_data = base64.b64encode(json.dumps(sample_data["dict_data"]).encode()).decode()
        mock_response_data = {
            "_type": "cache.CacheEntry",
            "value": encoded_data
        }
        get_response = Mock()
        get_response.status_code = 200
        get_response.json.return_value = mock_response_data
        get_response.text = json.dumps(mock_response_data)
        mock_requests['get'].return_value = get_response
        
        result = cache_operations.put(test_cache_name, "dict_key", sample_data["dict_data"])
        assert result is True
        
        retrieved_data = cache_operations.get(test_cache_name, "dict_key")
        assert retrieved_data == sample_data["dict_data"]
        assert retrieved_data["name"] == "John"
        assert retrieved_data["age"] == 30

    def test_put_and_get_list(self, cache_operations, mock_requests, sample_data, test_cache_name):
        """Test putting and getting list data"""
        mock_requests['put'].return_value.status_code = 200
        
        encoded_data = base64.b64encode(json.dumps(sample_data["list_data"]).encode()).decode()
        mock_response_data = {
            "_type": "cache.CacheEntry",
            "value": encoded_data
        }
        get_response = Mock()
        get_response.status_code = 200
        get_response.json.return_value = mock_response_data
        get_response.text = json.dumps(mock_response_data)
        mock_requests['get'].return_value = get_response
        
        result = cache_operations.put(test_cache_name, "list_key", sample_data["list_data"])
        assert result is True
        
        retrieved_data = cache_operations.get(test_cache_name, "list_key")
        assert retrieved_data == sample_data["list_data"]

    def test_get_nonexistent_key(self, cache_operations, mock_requests, test_cache_name):
        """Test getting a key that doesn't exist"""
        not_found_response = Mock()
        not_found_response.status_code = 404
        mock_requests['get'].return_value = not_found_response
        
        result = cache_operations.get(test_cache_name, "nonexistent_key")
        assert result is None

    def test_delete_existing_key(self, cache_operations, mock_requests, test_cache_name):
        """Test deleting an existing key"""
        mock_requests['delete'].return_value.status_code = 200
        result = cache_operations.delete(test_cache_name, "existing_key")
        assert result is True
        mock_requests['delete'].assert_called_once()

    def test_delete_nonexistent_key(self, cache_operations, mock_requests, test_cache_name):
        """Test deleting a key that doesn't exist"""
        
        not_found_response = Mock()
        not_found_response.status_code = 404
        mock_requests['delete'].return_value = not_found_response
        
        result = cache_operations.delete(test_cache_name, "nonexistent_key")
        assert result is True

    def test_put_failure(self, cache_operations, mock_requests, test_cache_name):
        """Test put operation failure"""
        error_response = Mock()
        error_response.status_code = 500
        error_response.text = "Internal Server Error"
        mock_requests['put'].return_value = error_response
        
        result = cache_operations.put(test_cache_name, "test_key", "test_value")
        assert result is False

    def test_get_with_invalid_json_response(self, cache_operations, mock_requests, test_cache_name):
        """Test get operation with invalid JSON response"""
        invalid_json_response = Mock()
        invalid_json_response.status_code = 200
        invalid_json_response.json.side_effect = ValueError("Invalid JSON")
        mock_requests['get'].return_value = invalid_json_response
        
        result = cache_operations.get(test_cache_name, "test_key")
        assert result is None
