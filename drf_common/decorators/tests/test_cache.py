"""
Tests for cache decorators.
"""

from unittest.mock import Mock, patch

from drf_common.common_tests.base_cases import DrfCommonTestCase

from ..cache import cache_debug


class CacheDebugTests(DrfCommonTestCase):
    """Tests for cache_debug decorator."""

    @patch("decorators.cache.Categories")
    @patch("decorators.cache.time")
    def test_cache_debug_basic(self, mock_time, mock_categories):
        """Test basic cache debug logging."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_time.time.side_effect = [1000.0, 1000.3]  # 0.3s execution

        @cache_debug()
        def test_function(arg1, arg2, kwarg1=None):
            return "cached_result"

        result = test_function("value1", "value2", kwarg1="kwvalue")

        # Verify logger was created with correct name and category
        mock_categories.get_logger.assert_called_with(
            "cache.test_function", mock_categories.CACHE
        )

        # Verify cache key was generated and logged
        calls = [str(call) for call in mock_logger.debug.call_args_list]
        cache_key_logged = any(
            "Cache operation for test_function with key: test_function_" in call
            for call in calls
        )
        self.assertTrue(cache_key_logged, f"Expected cache key log not found in: {calls}")
        mock_logger.debug.assert_any_call("Cache operation completed in 0.3000s")

        self.assertEqual(result, "cached_result")

    @patch("decorators.cache.Categories")
    @patch("decorators.cache.time")
    def test_cache_debug_with_custom_key_func(self, mock_time, mock_categories):
        """Test cache debug with custom cache key function."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_time.time.side_effect = [1000.0, 1000.1]

        def custom_key_func(arg1, arg2, kwarg1=None):
            return f"custom_key_{arg1}_{arg2}_{kwarg1}"

        @cache_debug(cache_key_func=custom_key_func)
        def test_function(arg1, arg2, kwarg1=None):
            return "cached_result"

        result = test_function("val1", "val2", kwarg1="kw1")

        # Verify custom cache key was used
        mock_logger.debug.assert_any_call(
            "Cache operation for test_function with key: custom_key_val1_val2_kw1"
        )
        mock_logger.debug.assert_any_call("Cache operation completed in 0.1000s")

        self.assertEqual(result, "cached_result")

    @patch("decorators.cache.Categories")
    @patch("decorators.cache.time")
    def test_cache_debug_no_arguments(self, mock_time, mock_categories):
        """Test cache debug with function that has no arguments."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_time.time.side_effect = [1000.0, 1000.05]

        @cache_debug()
        def test_function():
            return "no_args_result"

        result = test_function()

        # Verify hash-based key was generated for function with no args
        expected_key_pattern = "test_function_"  # Should contain function name
        debug_calls = [str(call) for call in mock_logger.debug.call_args_list]
        key_call_found = any(expected_key_pattern in call for call in debug_calls)
        self.assertTrue(key_call_found)

        mock_logger.debug.assert_any_call("Cache operation completed in 0.0500s")
        self.assertEqual(result, "no_args_result")

    @patch("decorators.cache.Categories")
    @patch("decorators.cache.time")
    def test_cache_debug_with_complex_arguments(self, mock_time, mock_categories):
        """Test cache debug with complex argument types."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_time.time.side_effect = [1000.0, 1000.2]

        @cache_debug()
        def test_function(data_dict, data_list, number):
            return "complex_result"

        result = test_function({"key": "value"}, [1, 2, 3], 42)

        # Should handle complex args without error
        self.assertEqual(result, "complex_result")

        # Verify logging occurred
        self.assertEqual(len(mock_logger.debug.call_args_list), 2)
        mock_logger.debug.assert_any_call("Cache operation completed in 0.2000s")

    @patch("decorators.cache.Categories")
    @patch("decorators.cache.time")
    def test_cache_debug_preserves_exceptions(self, mock_time, mock_categories):
        """Test that cache debug preserves exceptions from decorated function."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_time.time.side_effect = [1000.0, 1000.1]

        @cache_debug()
        def test_function():
            raise ValueError("Cache function error")

        with self.assertRaises(ValueError) as cm:
            test_function()

        self.assertEqual(str(cm.exception), "Cache function error")

        # Should still log cache operation start and completion timing
        mock_logger.debug.assert_any_call("Cache operation completed in 0.1000s")

    @patch("decorators.cache.Categories")
    @patch("decorators.cache.time")
    def test_cache_debug_custom_key_func_with_exception(
        self, mock_time, mock_categories
    ):
        """Test cache debug when custom key function raises exception."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_time.time.side_effect = [1000.0, 1000.1]

        def failing_key_func(*args, **kwargs):
            raise RuntimeError("Key generation failed")

        @cache_debug(cache_key_func=failing_key_func)
        def test_function(arg1):
            return "result"

        # Should raise the exception from key function
        with self.assertRaises(RuntimeError) as cm:
            test_function("value")

        self.assertEqual(str(cm.exception), "Key generation failed")

    @patch("decorators.cache.Categories")
    @patch("decorators.cache.time")
    def test_cache_debug_return_value_preservation(self, mock_time, mock_categories):
        """Test that cache debug preserves all types of return values."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_time.time.side_effect = [1000.0, 1000.1]

        @cache_debug()
        def test_function(return_type):
            if return_type == "dict":
                return {"key": "value", "nested": {"inner": True}}
            elif return_type == "list":
                return [1, 2, {"nested": "data"}]
            elif return_type == "none":
                return None
            elif return_type == "bool":
                return False
            else:
                return "string_result"

        # Test different return types
        dict_result = test_function("dict")
        self.assertEqual(dict_result, {"key": "value", "nested": {"inner": True}})

        # Reset time mock for next call
        mock_time.time.side_effect = [2000.0, 2000.1]
        list_result = test_function("list")
        self.assertEqual(list_result, [1, 2, {"nested": "data"}])

        mock_time.time.side_effect = [3000.0, 3000.1]
        none_result = test_function("none")
        self.assertIsNone(none_result)

        mock_time.time.side_effect = [4000.0, 4000.1]
        bool_result = test_function("bool")
        self.assertFalse(bool_result)

        mock_time.time.side_effect = [5000.0, 5000.1]
        string_result = test_function("string")
        self.assertEqual(string_result, "string_result")

    @patch("decorators.cache.Categories")
    @patch("decorators.cache.time")
    def test_cache_debug_key_generation_consistency(self, mock_time, mock_categories):
        """Test that cache key generation is consistent for same inputs."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_time.time.side_effect = [1000.0, 1000.1, 2000.0, 2000.1]

        @cache_debug()
        def test_function(arg1, kwarg1=None):
            return "result"

        # Call twice with same arguments
        test_function("value", kwarg1="kw")
        test_function("value", kwarg1="kw")

        # Extract the cache keys from drf_common.debug calls
        debug_calls = [
            call[0][0]
            for call in mock_logger.debug.call_args_list
            if "Cache operation for" in call[0][0]
        ]

        # Should have two identical cache key logs
        self.assertEqual(len(debug_calls), 2)
        self.assertEqual(debug_calls[0], debug_calls[1])
