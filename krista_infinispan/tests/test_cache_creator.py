"""
Tests for CacheCreator class
"""
import pytest
import requests
from unittest.mock import Mock, patch
from krista_infinispan.cache_creator import CacheCreator


class TestCacheCreator:
    
    @pytest.fixture
    def cache_creator(self, cache_config):
        """CacheCreator instance for testing"""
        return CacheCreator(config=cache_config)
    
    def test_create_cache_success(self, cache_creator, mock_requests):
        """Test successful cache creation"""
        # First call: cache_exists() returns False (404 - cache doesn't exist)
        get_response = Mock()
        get_response.status_code = 404
        mock_requests['get'].return_value = get_response
        
        # Second call: create_cache() returns success (200)
        post_response = Mock()
        post_response.status_code = 200
        mock_requests['post'].return_value = post_response
        
        result = cache_creator.create_cache("test-cache")
        
        assert result is True
        mock_requests['get'].assert_called_once()  # Check cache exists
        mock_requests['post'].assert_called_once() 
    
    
    def test_create_cache_failure(self, cache_creator, mock_requests):
        """Test cache creation failure"""
        # First call: cache_exists() returns False (404 - cache doesn't exist)
        get_response = Mock()
        get_response.status_code = 404
        mock_requests['get'].return_value = get_response
        
        # Second call: create_cache() returns success (200)
        post_response = Mock()
        post_response.status_code = 500
        post_response.text = "Internal Server Error"
        mock_requests['post'].return_value = post_response
        
        with pytest.raises(Exception):
          cache_creator.create_cache("test-cache")
    
        mock_requests['get'].assert_called_once()
        mock_requests['post'].assert_called_once()
    
    def test_cache_exists_true(self, cache_creator, mock_requests):
        """Test cache existence check - cache exists"""
        
        result = cache_creator.cache_exists("test-cache")
        
        assert result is True
        mock_requests['get'].assert_called_once()
    
    def test_create_cache_with_retry_success_first_attempt(self, cache_creator, mock_requests):
        """Test _create_cache_with_retry succeeds on first attempt"""
        url = "http://test.com/caches/test-cache"
        config = {"distributed-cache": {"mode": "SYNC"}}
        
        # Mock successful response
        success_response = Mock()
        success_response.status_code = 201
        mock_requests['post'].return_value = success_response
        
        result = cache_creator._create_cache_with_retry(url, config)
        
        assert result == success_response
        assert mock_requests['post'].call_count == 1
        mock_requests['post'].assert_called_with(
            url,
            json=config,
            auth=cache_creator.auth,
            headers=cache_creator.headers,
            timeout=30
        )

    def test_create_cache_with_retry_success_after_retries(self, cache_creator, mock_requests):
        """Test _create_cache_with_retry succeeds after some failures"""
        url = "http://test.com/caches/test-cache"
        config = {"distributed-cache": {"mode": "SYNC"}}
        
        # Mock: fail twice, then succeed
        success_response = Mock()
        success_response.status_code = 201
        
        mock_requests['post'].side_effect = [
            requests.exceptions.ConnectionError("Connection failed"),
            requests.exceptions.Timeout("Request timeout"),
            success_response
        ]
        
        with patch('time.sleep') as mock_sleep:
            result = cache_creator._create_cache_with_retry(url, config)
        
        assert result == success_response
        assert mock_requests['post'].call_count == 3
        assert mock_sleep.call_count == 2  # Two retries

    def test_create_cache_with_retry_all_attempts_fail(self, cache_creator, mock_requests):
        """Test _create_cache_with_retry fails after max retries"""
        url = "http://test.com/caches/test-cache"
        config = {"distributed-cache": {"mode": "SYNC"}}
        
        # Mock: all attempts fail
        mock_requests['post'].side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        with patch('time.sleep') as mock_sleep:
            with pytest.raises(requests.exceptions.ConnectionError, match="Connection failed"):
                cache_creator._create_cache_with_retry(url, config)
        
        # Should try max_retries + 1 times (default: 3 + 1 = 4)
        assert mock_requests['post'].call_count == 4
        assert mock_sleep.call_count == 3  # Three retry delays

    def test_create_cache_with_retry_exponential_backoff(self, cache_creator, mock_requests):
        """Test _create_cache_with_retry uses exponential backoff"""
        url = "http://test.com/caches/test-cache"
        config = {"distributed-cache": {"mode": "SYNC"}}
        
        # Mock: all attempts fail
        mock_requests['post'].side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        with patch('time.sleep') as mock_sleep:
            with pytest.raises(requests.exceptions.ConnectionError):
                cache_creator._create_cache_with_retry(url, config)
        
        # Check exponential backoff delays
        expected_delays = [1.0, 5.0, 25.0]  # 1.0 * 5^0, 1.0 * 5^1, 1.0 * 5^2
        actual_delays = [call[0][0] for call in mock_sleep.call_args_list]
        assert actual_delays == expected_delays

    def test_create_cache_with_retry_max_delay_cap(self, cache_creator, mock_requests):
        """Test _create_cache_with_retry respects max delay cap"""
        # Create cache creator with small max delay
        cache_creator.max_retry_delay = 10.0
        cache_creator.retry_backoff_multiplier = 5.0
        
        url = "http://test.com/caches/test-cache"
        config = {"distributed-cache": {"mode": "SYNC"}}
        
        mock_requests['post'].side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        with patch('time.sleep') as mock_sleep:
            with pytest.raises(requests.exceptions.ConnectionError):
                cache_creator._create_cache_with_retry(url, config)
        
        # Check that delay is capped at max_retry_delay
        actual_delays = [call[0][0] for call in mock_sleep.call_args_list]
        assert all(delay <= 10.0 for delay in actual_delays)
