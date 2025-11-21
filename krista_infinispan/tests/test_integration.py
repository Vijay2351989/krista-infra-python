"""
Integration tests for krista-infinispan
"""
import pytest
import json
import tempfile
import os
from unittest.mock import patch, Mock
from krista_infinispan import CacheOperations, CacheCreator
from krista_infinispan.cache_config import CacheConfig


class TestIntegration:
    
    @pytest.fixture
    def full_config(self):
        """Full configuration for integration testing"""
        return {
            "host": "localhost",
            "port": 11222,
            "username": "admin",
            "password": "admin",
            "protocol": "rest",
            "caches": {
                "integration-test": {
                    "enabled": True,
                    "memory_size": "100MB",
                    "ttl_hours": 4,
                    "l1_size": "10MB",
                    "l1_expiration_minutes": 60,
                    "description": "Integration test cache",
                    "locking": {
                        "isolation": "REPEATABLE_READ",
                        "acquire_timeout": 20000,
                        "concurrency_level": 2000
                    },
                    "transaction": {
                        "mode": "FULL_XA",
                        "locking": "PESSIMISTIC",
                        "auto_commit": False,
                        "recovery_enabled": True
                    },
                    "encoding": {
                        "key": {"media_type": "application/x-protostream"},
                        "value": {"media_type": "application/x-protostream"}
                    },
                    "persistence": {
                        "enabled": True,
                        "type": "file-store",
                        "path": "integration-test-data",
                        "passivation": True,
                        "write_behind": {
                            "enabled": True,
                            "modification_queue_size": 4096,
                            "fail_silently": False
                        }
                    }
                }
            }
        }
    
    def test_end_to_end_workflow(self, full_config):
        """Test complete workflow: config -> create cache -> operations"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(full_config, f)
            config_file = f.name
        
        try:
            with patch('requests.Session') as mock_session:
                # Mock all HTTP responses
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {}
                mock_session.return_value.get.return_value = mock_response
                mock_session.return_value.post.return_value = mock_response
                mock_session.return_value.put.return_value = mock_response
                mock_session.return_value.delete.return_value = mock_response
                mock_session.return_value.head.return_value = mock_response
                
                # Step 1: Load configuration
                config = CacheConfig(config_file=config_file)
                assert config.host == "localhost"
                
                # Step 2: Create cache
                creator = CacheCreator(config=config)
                result = creator.create_cache("integration-test")
                assert result is True
                
                # Step 3: Perform cache operations
                cache_ops = CacheOperations(config=config, cache_name="integration-test")
                
                # Test various data types
                test_data = {
                    "user_session": {
                        "user_id": 12345,
                        "username": "testuser",
                        "permissions": ["read", "write"],
                        "metadata": {"login_time": "2024-01-01T10:00:00Z"}
                    }
                }
                
                # Put data
                put_result = cache_ops.put("session:12345", test_data["user_session"])
                assert put_result is True
                
                # Mock get response with serialized data
                import base64
                encoded_data = base64.b64encode(
                    json.dumps(test_data["user_session"]).encode()
                ).decode()
                mock_get_response = Mock()
                mock_get_response.status_code = 200
                mock_get_response.json.return_value = {
                    "_type": "cache.CacheEntry",
                    "value": encoded_data
                }
                mock_session.return_value.get.return_value = mock_get_response
                
                # Get data
                retrieved_data = cache_ops.get("session:12345")
                assert retrieved_data == test_data["user_session"]
                
                # Check existence
                exists_result = cache_ops.exists("session:12345")
                assert exists_result is True
                
                # Delete data
                delete_result = cache_ops.delete("session:12345")
                assert delete_result is True
                
        finally:
            if os.path.exists(config_file):
                os.unlink(config_file)
    
    def test_multiple_cache_configurations(self, full_config):
        """Test working with multiple cache configurations"""
        # Add another cache configuration
        full_config["caches"]["user-sessions"] = {
            "enabled": True,
            "memory_size": "200MB",
            "ttl_hours": 24,
            "persistence": {"enabled": False}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(full_config, f)
            config_file = f.name
        
        try:
            with patch('requests.Session') as mock_session:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_session.return_value.get.return_value = mock_response
                mock_session.return_value.post.return_value = mock_response
                
                config = CacheConfig(config_file=config_file)
                creator = CacheCreator(config=config)
                
                # Create both caches
                result1 = creator.create_cache("integration-test")
                result2 = creator.create_cache("user-sessions")
                
                assert result1 is True
                assert result2 is True
                
                # Verify different configurations were used
                assert mock_session.return_value.post.call_count == 2
                
        finally:
            if os.path.exists(config_file):
                os.unlink(config_file)
    
    def test_error_handling_integration(self, full_config):
        """Test error handling in integration scenario"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(full_config, f)
            config_file = f.name
        
        try:
            with patch('requests.Session') as mock_session:
                # Simulate server errors
                mock_session.return_value.post.return_value.status_code = 500
                mock_session.return_value.get.return_value.status_code = 503
                
                config = CacheConfig(config_file=config_file)
                creator = CacheCreator(config=config)
                cache_ops = CacheOperations(
                    config=config, 
                    cache_name="integration-test",
                    max_retries=1,
                    initial_retry_delay=0.1
                )
                
                # Cache creation should fail
                result = creator.create_cache("integration-test")
                assert result is False
                
                # Cache operations should fail
                put_result = cache_ops.put("key", "value")
                assert put_result is False
                
                get_result = cache_ops.get("key")
                assert get_result is None
                
        finally:
            if os.path.exists(config_file):
                os.unlink(config_file)