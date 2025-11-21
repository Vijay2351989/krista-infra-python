"""
Tests for CacheCreator class
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from krista_infinispan.cache_creator import CacheCreator


class TestCacheCreator:
    
    @pytest.fixture
    def cache_creator(self, cache_config):
        """CacheCreator instance for testing"""
        return CacheCreator(config=cache_config)
    
    def test_create_cache_success(self, cache_creator, mock_requests):
        """Test successful cache creation"""
        mock_requests.return_value.post.return_value.status_code = 200
        
        result = cache_creator.create_cache("test-cache")
        
        assert result is True
        mock_requests.return_value.post.assert_called_once()
    
    def test_create_cache_with_custom_config(self, cache_creator, mock_requests):
        """Test cache creation with custom configuration"""
        mock_requests.return_value.post.return_value.status_code = 200
        
        custom_config = {
            "memory_size": "100MB",
            "ttl_hours": 4,
            "locking": {"isolation": "REPEATABLE_READ"}
        }
        
        result = cache_creator.create_cache("custom-cache", custom_config)
        
        assert result is True
        mock_requests.return_value.post.assert_called_once()
    
    def test_create_cache_failure(self, cache_creator, mock_requests):
        """Test cache creation failure"""
        mock_requests.return_value.post.return_value.status_code = 500
        mock_requests.return_value.post.return_value.text = "Internal Server Error"
        
        result = cache_creator.create_cache("test-cache")
        
        assert result is False
    
    def test_cache_exists_true(self, cache_creator, mock_requests):
        """Test cache existence check - cache exists"""
        mock_requests.return_value.get.return_value.status_code = 200
        
        result = cache_creator.cache_exists("test-cache")
        
        assert result is True
    
    def test_cache_exists_false(self, cache_creator, mock_requests):
        """Test cache existence check - cache doesn't exist"""
        mock_requests.return_value.get.return_value.status_code = 404
        
        result = cache_creator.cache_exists("test-cache")
        
        assert result is False
    
    def test_build_cache_config(self, cache_creator):
        """Test building cache configuration XML"""
        cache_config = {
            "memory_size": "100MB",
            "ttl_hours": 2,
            "locking": {"isolation": "READ_COMMITTED"},
            "encoding": {
                "key": {"media_type": "application/x-protostream"},
                "value": {"media_type": "application/x-protostream"}
            }
        }
        
        xml_config = cache_creator._build_cache_config(cache_config)
        
        assert xml_config is not None
        assert isinstance(xml_config, str)
        assert "100MB" in xml_config
        assert "READ_COMMITTED" in xml_config
    
    def test_ensure_cache_exists_creates_new(self, cache_creator, mock_requests):
        """Test ensure_cache_exists creates cache when it doesn't exist"""
        # First call (check existence) returns 404, second call (create) returns 200
        mock_requests.return_value.get.return_value.status_code = 404
        mock_requests.return_value.post.return_value.status_code = 200
        
        result = cache_creator.ensure_cache_exists("new-cache")
        
        assert result is True
        mock_requests.return_value.get.assert_called_once()
        mock_requests.return_value.post.assert_called_once()
    
    def test_ensure_cache_exists_already_exists(self, cache_creator, mock_requests):
        """Test ensure_cache_exists when cache already exists"""
        mock_requests.return_value.get.return_value.status_code = 200
        
        result = cache_creator.ensure_cache_exists("existing-cache")
        
        assert result is True
        mock_requests.return_value.get.assert_called_once()
        mock_requests.return_value.post.assert_not_called()