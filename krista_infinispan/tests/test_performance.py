# """
# Performance and load tests for krista-infinispan
# """
# import pytest
# import time
# import threading
# from unittest.mock import patch, Mock
# from krista_infinispan import CacheOperations


# class TestPerformance:
    
#     @pytest.fixture
#     def fast_cache_ops(self, cache_config):
#         """CacheOperations with minimal retry delays for testing"""
#         return CacheOperations(
#             config=cache_config,
#             cache_name="perf-test",
#             max_retries=1,
#             initial_retry_delay=0.01,
#             max_retry_delay=0.1
#         )
    
#     def test_bulk_operations_performance(self, fast_cache_ops):
#         """Test performance of bulk cache operations"""
#         with patch('requests.Session') as mock_session:
#             mock_response = Mock()
#             mock_response.status_code = 200
#             mock_session.return_value.put.return_value = mock_response
            
#             # Test bulk puts
#             start_time = time.time()
            
#             for i in range(100):
#                 result = fast_cache_ops.put(f"key_{i}", f"value_{i}")
#                 assert result is True
            
#             end_time = time.time()
#             duration = end_time - start_time
            
#             # Should complete 100 operations reasonably quickly
#             assert duration < 5.0  # 5 seconds max
#             assert mock_session.return_value.put.call_count == 100
    
#     def test_concurrent_operations(self, fast_cache_ops):
#         """Test concurrent cache operations"""
#         with patch('requests.Session') as mock_session:
#             mock_response = Mock()
#             mock_response.status_code = 200
#             mock_session.return_value.put.return_value = mock_response
            
#             results = []
#             threads = []
            
#             def worker(thread_id):
#                 for i in range(10):
#                     result = fast_cache_ops.put(f"thread_{thread_id}_key_{i}", f"value_{i}")
#                     results.append(result)
            
#             # Create 5 threads, each doing 10 operations
#             for thread_id in range(5):
#                 thread = threading.Thread(target=worker, args=(thread_id,))
#                 threads.append(thread)
#                 thread.start()
            
#             # Wait for all threads to complete
#             for thread in threads:
#                 thread.join()
            
#             # All operations should succeed
#             assert len(results) == 50
#             assert all(results)
#             assert mock_session.return_value.put.call_count == 50
    
#     def test_retry_performance(self, cache_config):
#         """Test retry logic performance"""
#         cache_ops = CacheOperations(
#             config=cache_config,
#             cache_name="retry-test",
#             max_retries=3,
#             initial_retry_delay=0.01,
#             retry_backoff_multiplier=2.0
#         )
        
#         with patch('requests.Session') as mock_session:
#             # Simulate failures then success
#             mock_session.return_value.put.side_effect = [
#                 Mock(status_code=500),  # First attempt fails
#                 Mock(status_code=500),  # Second attempt fails
#                 Mock(status_code=200)   # Third attempt succeeds
#             ]
            
#             start_time = time.time()
#             result = cache_ops.put("test_key", "test_value")
#             end_time = time.time()
            
#             assert result is True
#             assert mock_session.return_value.put.call_count == 3
            
#             # Should complete with retries in reasonable time
#             # 0.01 + 0.02 + operation time should be < 1 second
#             assert end_time - start_time < 1.0
    
#     def test_large_data_serialization(self, fast_cache_ops):
#         """Test serialization performance with large data"""
#         with patch('requests.Session') as mock_session:
#             mock_response = Mock()
#             mock_response.status_code = 200
#             mock_session.return_value.put.return_value = mock_response
            
#             # Create large data structure
#             large_data = {
#                 "users": [
#                     {"id": i, "name": f"user_{i}", "data": "x" * 1000}
#                     for i in range(1000)
#                 ]
#             }
            
#             start_time = time.time()
#             result = fast_cache_ops.put("large_data", large_data)
#             end_time = time.time()
            
#             assert result is True
            
#             # Serialization should complete in reasonable time
#             assert end_time - start_time < 2.0
    
#     def test_memory_usage_bulk_operations(self, fast_cache_ops):
#         """Test memory usage doesn't grow excessively during bulk operations"""
#         import gc
        
#         with patch('requests.Session') as mock_session:
#             mock_response = Mock()
#             mock_response.status_code = 200
#             mock_session.return_value.put.return_value = mock_response
            
#             # Force garbage collection before test
#             gc.collect()
            
#             # Perform many operations
#             for i in range(1000):
#                 data = {"iteration": i, "data": "test" * 100}
#                 result = fast_cache_ops.put(f"bulk_key_{i}", data)
#                 assert result is True
                
#                 # Periodically force garbage collection
#                 if i % 100 == 0:
#                     gc.collect()
            
#             # Test should complete without memory issues
#             assert mock_session.return_value.put.call_count == 1000