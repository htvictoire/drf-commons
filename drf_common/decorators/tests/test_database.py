"""
Tests for database decorators.
"""

from unittest.mock import Mock, patch

from drf_common.common_tests.base_cases import DrfCommonTestCase

from ..database import log_db_query


class LogDbQueryTests(DrfCommonTestCase):
    """Tests for log_db_query decorator."""

    @patch("decorators.database.Categories")
    @patch("decorators.database.connection")
    @patch("decorators.database.time")
    def test_db_query_logging_basic(self, mock_time, mock_connection, mock_categories):
        """Test basic database query logging."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_time.time.side_effect = [1000.0, 1000.5]  # 0.5s execution

        # Mock connection.queries
        mock_connection.queries = [
            {"sql": "SELECT * FROM table1", "time": "0.001"},
            {"sql": "SELECT * FROM table2", "time": "0.002"},
        ]

        @log_db_query("Test Operation")
        def test_function():
            # Simulate adding one more query during execution
            mock_connection.queries.append(
                {"sql": "INSERT INTO table3 VALUES (1)", "time": "0.003"}
            )
            return "result"

        # Mock len() calls to simulate query count changes
        with patch("decorators.database.len") as mock_len:
            mock_len.side_effect = [2, 3]  # 2 initial, 3 after execution
            result = test_function()

        # Verify logger was created with correct name and category
        mock_categories.get_logger.assert_called_with(
            "database.queries", mock_categories.DATABASE
        )

        # Verify info log with query count and timing
        mock_logger.info.assert_called_with(
            "Test Operation test_function: 1 queries in 0.5000s"
        )

        # Verify debug log for the new query
        mock_logger.debug.assert_called_with(
            "SQL: INSERT INTO table3 VALUES (1) (Time: 0.003s)"
        )

        self.assertEqual(result, "result")

    @patch("decorators.database.Categories")
    @patch("decorators.database.connection")
    @patch("decorators.database.time")
    def test_db_query_logging_no_queries(
        self, mock_time, mock_connection, mock_categories
    ):
        """Test database query logging when no queries are executed."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_time.time.side_effect = [1000.0, 1000.2]  # 0.2s execution

        mock_connection.queries = []

        @log_db_query("No Query Operation")
        def test_function():
            return "result"

        with patch("decorators.database.len") as mock_len:
            mock_len.side_effect = [0, 0]  # No queries before or after
            result = test_function()

        # Should log 0 queries
        mock_logger.info.assert_called_with(
            "No Query Operation test_function: 0 queries in 0.2000s"
        )

        # No debug logs for queries
        mock_logger.debug.assert_not_called()

        self.assertEqual(result, "result")

    @patch("decorators.database.Categories")
    @patch("decorators.database.connection")
    @patch("decorators.database.time")
    def test_db_query_logging_multiple_queries(
        self, mock_time, mock_connection, mock_categories
    ):
        """Test database query logging with multiple queries."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_time.time.side_effect = [1000.0, 1000.8]

        # Start with 1 query, end with 4 queries (3 new queries)
        mock_connection.queries = [
            {"sql": "SELECT * FROM existing", "time": "0.001"},
        ]

        @log_db_query("Multi Query")
        def test_function():
            # Simulate adding 3 more queries during execution
            mock_connection.queries.extend(
                [
                    {"sql": "SELECT * FROM users WHERE id = 1", "time": "0.002"},
                    {
                        "sql": "UPDATE users SET name = %s WHERE id = %s",
                        "time": "0.005",
                    },
                    {"sql": "INSERT INTO logs (message) VALUES (%s)", "time": "0.001"},
                ]
            )
            return "result"

        with patch("decorators.database.len") as mock_len:
            mock_len.side_effect = [1, 4]  # 1 initial, 4 after execution
            test_function()

        # Verify info log shows 3 new queries
        mock_logger.info.assert_called_with(
            "Multi Query test_function: 3 queries in 0.8000s"
        )

        # Verify all 3 new queries were logged
        expected_debug_calls = [
            "SQL: SELECT * FROM users WHERE id = 1 (Time: 0.002s)",
            "SQL: UPDATE users SET name = %s WHERE id = %s (Time: 0.005s)",
            "SQL: INSERT INTO logs (message) VALUES (%s) (Time: 0.001s)",
        ]

        actual_debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
        for expected_call in expected_debug_calls:
            self.assertIn(expected_call, actual_debug_calls)

    @patch("decorators.database.Categories")
    @patch("decorators.database.connection")
    @patch("decorators.database.time")
    def test_db_query_logging_with_exception(
        self, mock_time, mock_connection, mock_categories
    ):
        """Test database query logging when function raises exception."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_time.time.side_effect = [1000.0, 1000.3]

        mock_connection.queries = []

        @log_db_query("Error Operation")
        def test_function():
            raise ValueError("Database error")

        with patch("decorators.database.len") as mock_len:
            mock_len.side_effect = [0, 0]

            with self.assertRaises(ValueError):
                test_function()

        # Should log error with timing
        mock_logger.error.assert_called_with(
            "Error Operation test_function failed after 0.3000s: Database error"
        )

    @patch("decorators.database.Categories")
    @patch("decorators.database.connection")
    @patch("decorators.database.time")
    def test_db_query_logging_empty_query_type(
        self, mock_time, mock_connection, mock_categories
    ):
        """Test database query logging with empty query type."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_time.time.side_effect = [1000.0, 1000.1]

        mock_connection.queries = []

        @log_db_query("")  # Empty query type
        def test_function():
            return "result"

        with patch("decorators.database.len") as mock_len:
            mock_len.side_effect = [0, 0]
            test_function()

        # Should log with empty prefix
        mock_logger.info.assert_called_with(" test_function: 0 queries in 0.1000s")

    @patch("decorators.database.Categories")
    @patch("decorators.database.connection")
    @patch("decorators.database.time")
    def test_db_query_logging_default_query_type(
        self, mock_time, mock_connection, mock_categories
    ):
        """Test database query logging with default empty query type."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_time.time.side_effect = [1000.0, 1000.1]

        mock_connection.queries = []

        @log_db_query()  # No query type specified
        def test_function():
            return "result"

        with patch("decorators.database.len") as mock_len:
            mock_len.side_effect = [0, 0]
            test_function()

        # Should log with empty prefix (default behavior)
        mock_logger.info.assert_called_with(" test_function: 0 queries in 0.1000s")

    @patch("decorators.database.Categories")
    @patch("decorators.database.connection")
    @patch("decorators.database.time")
    def test_db_query_logging_preserves_return_value(
        self, mock_time, mock_connection, mock_categories
    ):
        """Test that decorator preserves function return value."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_time.time.side_effect = [1000.0, 1000.1]

        mock_connection.queries = []

        @log_db_query("Test")
        def test_function():
            return {"key": "value", "number": 42}

        with patch("decorators.database.len") as mock_len:
            mock_len.side_effect = [0, 0]
            result = test_function()

        self.assertEqual(result, {"key": "value", "number": 42})
