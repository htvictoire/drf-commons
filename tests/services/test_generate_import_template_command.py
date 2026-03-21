from argparse import ArgumentParser
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from openpyxl import load_workbook

from drf_commons.common_tests.base_cases import DrfCommonTestCase
from drf_commons.management.commands import generate_import_template as root_command
from drf_commons.services.management.commands.generate_import_template import (
    Command,
    Command as ServiceCommand,
)


class GenerateImportTemplateCommandTests(DrfCommonTestCase):
    def test_root_command_reexports_service_command(self):
        self.assertIs(root_command.Command, ServiceCommand)
        self.assertEqual(root_command.__all__, ["Command"])

    def test_add_arguments_parses_expected_options(self):
        parser = ArgumentParser()
        command = Command()

        command.add_arguments(parser)
        parsed = parser.parse_args(
            [
                "tests.integration.test_viewset_integration.ImportExportUserViewSet",
                "--filename",
                "custom.xlsx",
                "--format",
                "csv",
                "--include-examples",
                "--order-by",
                "alphabetic",
            ]
        )

        self.assertEqual(
            parsed.viewset_path,
            "tests.integration.test_viewset_integration.ImportExportUserViewSet",
        )
        self.assertEqual(parsed.filename, "custom.xlsx")
        self.assertEqual(parsed.format, "csv")
        self.assertTrue(parsed.include_examples)
        self.assertEqual(parsed.order_by, "alphabetic")

    def test_load_viewset_class_requires_dotted_path(self):
        command = Command()

        with self.assertRaises(CommandError) as exc:
            command.load_viewset_class("InvalidPath")

        self.assertIn("Invalid viewset path format", str(exc.exception))

    def test_load_viewset_class_tries_fallback_modules_until_match(self):
        command = Command()

        empty_module = ModuleType("example.accounts.views")
        target_module = ModuleType("example.accounts.viewsets")

        class StudentViewSet:
            pass

        target_module.StudentViewSet = StudentViewSet

        with patch(
            "drf_commons.services.management.commands.generate_import_template.importlib.import_module",
            side_effect=[ImportError("no module"), empty_module, target_module],
        ) as mock_import:
            viewset_class = command.load_viewset_class(
                "example.accounts.StudentViewSet"
            )

        self.assertIs(viewset_class, StudentViewSet)
        self.assertEqual(
            [call.args[0] for call in mock_import.call_args_list],
            [
                "example.accounts.views.student",
                "example.accounts.views",
                "example.accounts.viewsets",
            ],
        )

    def test_load_viewset_class_raises_when_class_not_found(self):
        command = Command()

        with patch(
            "drf_commons.services.management.commands.generate_import_template.importlib.import_module",
            side_effect=[
                ImportError("missing"),
                ModuleType("example.accounts.views"),
                ModuleType("example.accounts.viewsets"),
                ModuleType("example.accounts"),
            ],
        ):
            with self.assertRaises(CommandError) as exc:
                command.load_viewset_class("example.accounts.StudentViewSet")

        self.assertIn("ViewSet class 'StudentViewSet' not found", str(exc.exception))

    def test_validate_viewset_rejects_invalid_configs(self):
        command = Command()
        scenarios = [
            (
                type("MissingConfigViewSet", (), {}),
                "does not have 'import_file_config' attribute",
            ),
            (
                type("EmptyConfigViewSet", (), {"import_file_config": None}),
                "has empty 'import_file_config'",
            ),
            (
                type("StringConfigViewSet", (), {"import_file_config": "bad"}),
                "must be a dictionary",
            ),
            (
                type(
                    "MissingModelsViewSet",
                    (),
                    {"import_file_config": {"order": ["users"]}},
                ),
                "missing required key: 'models'",
            ),
        ]

        for viewset_class, expected_message in scenarios:
            with self.subTest(expected_message=expected_message):
                with self.assertRaises(CommandError) as exc:
                    command.validate_viewset(viewset_class, "demo.ViewSet")

                self.assertIn(expected_message, str(exc.exception))

    def test_extract_columns_from_config_handles_all_column_types(self):
        stdout = StringIO()
        command = Command(stdout=stdout)
        config = {
            "order": ["users", "profiles"],
            "models": {
                "users": {
                    "model": "auth.User",
                    "required_fields": ["username", "email"],
                    "direct_columns": {
                        "username": "Username",
                        "email": "Email",
                    },
                    "transformed_columns": {
                        "full_name": {"column": "Full Name"},
                    },
                    "lookup_fields": {
                        "group": {"column": "Group"},
                    },
                    "computed_fields": {
                        "slug": {"mode": "if_empty", "column": "Slug"},
                        "code": {"mode": "always"},
                    },
                },
                "profiles": {
                    "model": "profiles.Profile",
                    "required_fields": ["bio"],
                    "direct_columns": {"bio": "Bio"},
                    "lookup_fields": {"group": {"column": "Group"}},
                },
            },
        }

        columns, required_status = command.extract_columns_from_config(config)

        self.assertEqual(
            columns,
            ["Username", "Email", "Full Name", "Group", "Slug", "Bio"],
        )
        self.assertEqual(
            required_status,
            {
                "Username": True,
                "Email": True,
                "Full Name": False,
                "Group": False,
                "Slug": False,
                "Bio": True,
            },
        )
        output = stdout.getvalue()
        self.assertIn("Processing step 'users'", output)
        self.assertIn("Added column: 'Group' (lookup, optional)", output)
        self.assertIn("Skipped field: 'code'", output)

    def test_is_field_required_prefers_computed_then_required_fields(self):
        command = Command()
        model_config = {
            "required_fields": ["username"],
            "computed_fields": {"slug": {"mode": "if_empty", "column": "Slug"}},
        }

        self.assertFalse(command._is_field_required("auth.User", "slug", model_config))
        self.assertTrue(command._is_field_required("auth.User", "username", model_config))
        self.assertFalse(command._is_field_required("auth.User", "email", model_config))

    def test_generate_filename_strips_viewset_suffix_when_supported(self):
        command = Command()

        class StudentViewset:
            __name__ = "StudentViewset"

        self.assertEqual(
            command.generate_filename(StudentViewset, "csv"),
            "student_import_template.csv",
        )

    def test_create_template_file_creates_csv_with_examples(self):
        command = Command()

        with TemporaryDirectory() as tmpdir, override_settings(BASE_DIR=tmpdir):
            path = command.create_template_file(
                ["Last Name", "Email"],
                {"Last Name": False, "Email": True},
                "users.csv",
                "csv",
                include_examples=True,
                order_by="alphabetic",
            )

            content = Path(path).read_text(encoding="utf-8").splitlines()

        self.assertTrue(path.endswith("users.csv"))
        self.assertEqual(content[0], "Email,Last Name")
        self.assertEqual(len(content), 4)
        self.assertIn("Example email 1", content[1])

    def test_create_template_file_creates_xlsx_with_legend_and_colors(self):
        command = Command()

        with TemporaryDirectory() as tmpdir, override_settings(BASE_DIR=tmpdir):
            path = command.create_template_file(
                ["Optional Field", "Required Field"],
                {"Optional Field": False, "Required Field": True},
                "users.xlsx",
                "xlsx",
                include_examples=True,
                order_by="required-first",
            )
            workbook = load_workbook(path)
            sheet = workbook.active

        self.assertEqual(sheet.title, "Import Template")
        self.assertEqual(sheet["A1"].value, "LEGEND:")
        self.assertEqual(sheet["A5"].value, "Required Field")
        self.assertEqual(sheet["B5"].value, "Optional Field")
        self.assertIn("Example required_field 1", sheet["A6"].value)
        self.assertTrue(sheet["A5"].fill.start_color.rgb.endswith("DC3545"))
        self.assertTrue(sheet["B5"].fill.start_color.rgb.endswith("28A745"))
        self.assertGreaterEqual(sheet.column_dimensions["A"].width, 12)

    def test_handle_uses_import_template_name_and_writes_file(self):
        stdout = StringIO()
        viewset_path = "tests.integration.test_viewset_integration.ImportExportUserViewSet"

        with TemporaryDirectory() as tmpdir, override_settings(BASE_DIR=tmpdir):
            call_command(
                "generate_import_template",
                viewset_path,
                format="csv",
                include_examples=True,
                order_by="config",
                stdout=stdout,
            )
            expected_file = (
                Path(tmpdir)
                / "static"
                / "import-templates"
                / "user_import_template.csv"
            )
            file_exists = expected_file.exists()

        output = stdout.getvalue()
        self.assertTrue(file_exists)
        self.assertIn("Template created successfully", output)
        self.assertIn("Template contains 4 columns", output)
        self.assertIn("Column order: config", output)
        self.assertIn("username (optional)", output)

    def test_handle_uses_generated_filename_and_required_first_display_order(self):
        stdout = StringIO()
        command = Command(stdout=stdout)

        class DemoViewset:
            import_file_config = {"order": ["main"], "models": {"main": {}}}

        with patch.object(command, "load_viewset_class", return_value=DemoViewset), patch.object(
            command, "validate_viewset"
        ), patch.object(
            command,
            "extract_columns_from_config",
            return_value=(
                ["optional_column", "required_column"],
                {"optional_column": False, "required_column": True},
            ),
        ), patch.object(
            command,
            "generate_filename",
            return_value="generated_template.xlsx",
        ) as mock_generate, patch.object(
            command,
            "create_template_file",
            return_value="/tmp/generated_template.xlsx",
        ) as mock_create:
            command.handle(
                viewset_path="demo.DemoViewset",
                filename=None,
                format="xlsx",
                include_examples=False,
                order_by="required-first",
            )

        mock_generate.assert_called_once_with(DemoViewset, "xlsx")
        mock_create.assert_called_once()
        output = stdout.getvalue()
        required_index = output.index("required_column (required)")
        optional_index = output.index("optional_column (optional)")
        self.assertLess(required_index, optional_index)

    def test_handle_uses_alphabetic_display_order_and_normalizes_extension(self):
        stdout = StringIO()
        command = Command(stdout=stdout)

        class DemoViewset:
            import_template_name = "demo_template.xlsx"
            import_file_config = {"order": ["main"], "models": {"main": {}}}

        with patch.object(command, "load_viewset_class", return_value=DemoViewset), patch.object(
            command, "validate_viewset"
        ), patch.object(
            command,
            "extract_columns_from_config",
            return_value=(
                ["zebra", "alpha"],
                {"zebra": True, "alpha": False},
            ),
        ), patch.object(
            command,
            "create_template_file",
            return_value="/tmp/demo_template.csv",
        ) as mock_create:
            command.handle(
                viewset_path="demo.DemoViewset",
                filename="custom.xlsx",
                format="csv",
                include_examples=False,
                order_by="alphabetic",
            )

        created_filename = mock_create.call_args.args[2]
        self.assertEqual(created_filename, "custom.csv")
        output = stdout.getvalue()
        self.assertLess(output.index("alpha (optional)"), output.index("zebra (required)"))

    def test_handle_wraps_no_columns_and_create_errors(self):
        command = Command(stdout=StringIO())

        class DemoViewset:
            import_file_config = {"order": ["main"], "models": {"main": {}}}

        with patch.object(command, "load_viewset_class", return_value=DemoViewset), patch.object(
            command, "validate_viewset"
        ), patch.object(
            command,
            "extract_columns_from_config",
            return_value=([], {}),
        ):
            with self.assertRaises(CommandError) as exc:
                command.handle(
                    viewset_path="demo.DemoViewset",
                    filename=None,
                    format="xlsx",
                    include_examples=False,
                    order_by="config",
                )

        self.assertIn("No columns found in import_file_config", str(exc.exception))

        with patch.object(command, "load_viewset_class", return_value=DemoViewset), patch.object(
            command, "validate_viewset"
        ), patch.object(
            command,
            "extract_columns_from_config",
            return_value=(["alpha"], {"alpha": True}),
        ), patch.object(
            command,
            "generate_filename",
            return_value="broken.xlsx",
        ), patch.object(
            command,
            "create_template_file",
            side_effect=OSError("disk full"),
        ):
            with self.assertRaises(CommandError) as wrapped_exc:
                command.handle(
                    viewset_path="demo.DemoViewset",
                    filename=None,
                    format="xlsx",
                    include_examples=False,
                    order_by="config",
                )

        self.assertIn("Failed to generate template: disk full", str(wrapped_exc.exception))
