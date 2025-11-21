"""
Tests for CacheConfig class
"""
import pytest
import os
import tempfile
import json
from unittest.mock import patch
from krista_infinispan.cache_config import CacheConfig


class TestCacheConfig:
    
    def test_load_config_from_file(self, temp_config_file):
        """Test loading configuration from file"""
        config = CacheConfig(config_file=temp_config_file)
        
        assert config.host == "localhost"
        assert config.port == 11222
        assert config.username == "admin"
        assert config.password == "admin"
        assert config.protocol == "rest"
    
    def test_load_config_with_env_variables(self, temp_config_file):
        """Test environment variable override"""
        with patch.dict(os.environ, {
            'INFINISPAN_HOST': 'prod-server.com',
            'INFINISPAN_PORT': '11443',
            'INFINISPAN_USERNAME': 'prod-user'
        }):
            config = CacheConfig(config_file=temp_config_file)
            
            assert config.host == "prod-server.com"
            assert config.port == 11443
            assert config.username == "prod-user"
            assert config.password == "admin"  # Not overridden
    
    def test_get_cache_config(self, cache_config):
        """Test getting specific cache configuration"""
        cache_cfg = cache_config.get_cache_config("test-cache")
        
        assert cache_cfg["enabled"] is True
        assert cache_cfg["memory_size"] == "50MB"
        assert cache_cfg["ttl_hours"] == 2
        assert cache_cfg["locking"]["isolation"] == "READ_COMMITTED"
    
    def test_get_nonexistent_cache_config(self, cache_config):
        """Test getting configuration for non-existent cache"""
        cache_cfg = cache_config.get_cache_config("nonexistent-cache")
        assert cache_cfg is None
    
    def test_config_file_not_found(self):
        """Test handling of missing config file"""
        with pytest.raises(FileNotFoundError):
            CacheConfig(config_file="nonexistent.json")
    
    def test_invalid_json_config(self):
        """Test handling of invalid JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_file = f.name
        
        try:
            with pytest.raises(json.JSONDecodeError):
                CacheConfig(config_file=temp_file)
        finally:
            os.unlink(temp_file)
    
    def test_default_config_values(self, cache_config):
        """Test default configuration values"""
        assert cache_config.host is not None
        assert cache_config.port is not None
        assert cache_config.username is not None
        assert cache_config.password is not None