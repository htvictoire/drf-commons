from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from drf_commons.common_tests.base_cases import DrfCommonTestCase
from drf_commons.debug.logging import get_logging_config
from drf_commons.debug.logging.config import build_logging_config
from drf_commons.debug.logging.directories import create_log_directories
from drf_commons.debug.logging.formatters import get_formatters


class LoggingConfigTests(DrfCommonTestCase):
    def test_get_formatters_returns_expected_specs(self):
        formatters = get_formatters()

        self.assertEqual(set(formatters.keys()), {"verbose", "minimal"})
        self.assertEqual(formatters["verbose"]["style"], "{")
        self.assertIn("{message}", formatters["minimal"]["format"])

    def test_create_log_directories_creates_expected_tree(self):
        with TemporaryDirectory() as tmpdir:
            logs_dir = Path(tmpdir) / "logs"

            create_log_directories(logs_dir, ["api", "users"])

            self.assertTrue(logs_dir.exists())
            self.assertTrue((logs_dir / "api").exists())
            self.assertTrue((logs_dir / "users").exists())
            self.assertTrue((logs_dir / "errors").exists())

    def test_build_logging_config_assembles_expected_structure(self):
        with patch(
            "drf_commons.debug.logging.config.Categories.get_enabled",
            return_value=["api", "users"],
        ), patch(
            "drf_commons.debug.logging.config.create_log_directories"
        ) as mock_create_dirs, patch(
            "drf_commons.debug.logging.config.build_handlers",
            return_value={"console": {}, "main": {}, "errors": {}},
        ) as mock_build_handlers, patch(
            "drf_commons.debug.logging.config.build_loggers",
            return_value={"django": {"handlers": ["console"]}},
        ) as mock_build_loggers, patch(
            "drf_commons.debug.logging.config.get_formatters",
            return_value={"minimal": {}},
        ), patch(
            "drf_commons.debug.logging.config.filter_available_handlers",
            return_value=["console", "main"],
        ) as mock_filter:
            config = build_logging_config("/tmp/project", debug_mode=True)

        mock_create_dirs.assert_called_once()
        mock_build_handlers.assert_called_once()
        mock_build_loggers.assert_called_once_with(["api", "users"], True)
        mock_filter.assert_called_once_with(
            ["console", "main", "errors"],
            {"console": {}, "main": {}, "errors": {}},
        )
        self.assertEqual(config["version"], 1)
        self.assertEqual(config["formatters"], {"minimal": {}})
        self.assertEqual(config["root"]["handlers"], ["console", "main"])

    def test_get_logging_config_delegates_to_builder(self):
        with patch(
            "drf_commons.debug.logging.build_logging_config",
            return_value={"root": {"handlers": []}},
        ) as mock_builder:
            config = get_logging_config("/tmp/project", debug=True)

        mock_builder.assert_called_once_with("/tmp/project", True)
        self.assertEqual(config, {"root": {"handlers": []}})
