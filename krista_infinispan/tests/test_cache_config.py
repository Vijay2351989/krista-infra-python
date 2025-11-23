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

        def test_config_with_ssl(self, temp_config_file):
            """Test SSL configuration"""
            with patch.dict(os.environ, {
                'INFINISPAN_USE_SSL': 'true',
                'INFINISPAN_PORT': '11443'
            }):
                config = CacheConfig(config_file=temp_config_file)
                
                assert config.port == 11443

        def test_missing_config_file(self):
            """Test behavior with missing config file"""
            with pytest.raises(FileNotFoundError):
                CacheConfig(config_file="nonexistent.yaml")

        def test_invalid_yaml_config(self, tmp_path):
            """Test behavior with invalid YAML"""
            invalid_config = tmp_path / "invalid.yaml"
            invalid_config.write_text("invalid: yaml: content: [")
            
            with pytest.raises(ValueError):
                CacheConfig(config_file=str(invalid_config))
