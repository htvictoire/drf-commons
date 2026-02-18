"""
Mixins for file import and export functionality.
"""

import os
import logging
from io import StringIO
from uuid import uuid4

from django.conf import settings as django_settings
from django.core.management import call_command
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from django.utils.text import slugify

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.request import Request

from drf_commons.common_conf.settings import IMPORT_FAILED_ROWS_DISPLAY_LIMIT
from drf_commons.response.utils import error_response, success_response
from drf_commons.services.export_file import ExportService

from .utils import get_model_name

logger = logging.getLogger(__name__)


class FileImportMixin:
    """
    Mixin for importing data from files.

    Viewsets using this mixin must define:
    - import_file_config: Dict containing FileImportService configuration
    - import_template_name: Name of the template file in static/import-templates/
    - import_transforms: Optional dict of transform functions (default: None)
    """

    import_file_config = None  # Must be defined by subclass
    import_template_name = None  # Must be defined by subclass
    import_transforms = None  # Optional transform functions

    @staticmethod
    def parse_bool(value, field_name: str) -> bool:
        """Parse a request boolean flag from bool/int/str representations."""
        if value is None:
            return False

        if isinstance(value, bool):
            return value

        if isinstance(value, int):
            if value in (0, 1):
                return bool(value)
            raise ValueError(
                f"'{field_name}' must be a boolean value (true/false, 1/0, yes/no, on/off)."
            )

        if isinstance(value, str):
            normalized = value.strip().lower()
            truthy = {"true", "1", "yes", "y", "on"}
            falsy = {"false", "0", "no", "n", "off", ""}

            if normalized in truthy:
                return True
            if normalized in falsy:
                return False

        raise ValueError(
            f"'{field_name}' must be a boolean value (true/false, 1/0, yes/no, on/off)."
        )

    def get_import_transforms(self):
        """Return a per-request transform mapping."""
        return dict(self.import_transforms or {})

    @action(detail=False, methods=["post"], url_path="import-from-file")
    def import_file(self, request, *args, **kwargs):
        """
        Import data from uploaded file.

        Expected form data:
        - file: uploaded file (CSV, XLS, XLSX)
        - append_data: boolean-like value resolving to true (append to existing data) OR
        - replace_data: boolean-like value resolving to true (replace all existing data)
        """

        from drf_commons.services.import_from_file import (
            FileImportService,
            ImportValidationError,
        )

        if not self.import_file_config:
            raise NotImplementedError(
                "import_file_config must be defined in the ViewSet"
            )

        if not self.import_template_name:
            raise NotImplementedError(
                "import_template_name must be defined in the ViewSet"
            )

        # Validate form data
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return error_response(
                message="No file provided",
                errors={"file": ["This field is required."]},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Check operation mode
        try:
            append_data = self.parse_bool(request.data.get("append_data"), "append_data")
            replace_data = self.parse_bool(
                request.data.get("replace_data"), "replace_data"
            )
        except ValueError as exc:
            return error_response(
                message="Invalid import mode flag",
                errors={"mode": [str(exc)]},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if not (append_data or replace_data):
            return error_response(
                message="Must specify exactly one of append_data or replace_data as true",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if append_data and replace_data:
            return error_response(
                message="Cannot specify both 'append_data' and 'replace_data'",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            deleted_count = 0
            # Setup progress tracking
            progress_data = {"processed": 0, "total": 0}

            def progress_callback(processed: int, total: int):
                progress_data.update({"processed": processed, "total": total})

            # Create and run import service
            service = FileImportService(
                self.import_file_config,
                transforms=self.get_import_transforms(),
                progress_callback=progress_callback,
            )

            if replace_data:
                with transaction.atomic():
                    count = self.get_queryset().count()
                    if count > 0:
                        deleted_info = self.get_queryset().delete()
                        deleted_count = deleted_info[0]

                    result = service.import_file(uploaded_file)
                    summary = result["summary"]

                    # Replace mode is strict all-or-nothing.
                    # Any failed rows trigger transaction rollback.
                    if summary.get("failed", 0) > 0:
                        response_data = {
                            "import_summary": summary,
                            "operation": "replace",
                            "deleted_count": 0,
                        }
                        failed_rows = [
                            row for row in result["rows"] if row["status"] == "failed"
                        ]
                        if failed_rows:
                            response_data["failed_rows"] = failed_rows[
                                :IMPORT_FAILED_ROWS_DISPLAY_LIMIT
                            ]
                            if len(failed_rows) > IMPORT_FAILED_ROWS_DISPLAY_LIMIT:
                                response_data["additional_failures"] = (
                                    len(failed_rows)
                                    - IMPORT_FAILED_ROWS_DISPLAY_LIMIT
                                )

                        transaction.set_rollback(True)
                        return error_response(
                            message=(
                                "Replace import failed validation and was rolled back. "
                                f"Failed rows: {summary.get('failed', 0)}"
                            ),
                            errors={
                                "import": [
                                    "replace_data requires zero failed rows; no changes were committed."
                                ]
                            },
                            data=response_data,
                            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        )
            else:
                result = service.import_file(uploaded_file)

            # Format response data
            response_data = {
                "import_summary": result["summary"],
                "operation": "replace" if replace_data else "append",
            }

            if replace_data:
                response_data["deleted_count"] = deleted_count
            else:
                response_data["deleted_count"] = 0

            # Include row details if there were failures
            failed_rows = [row for row in result["rows"] if row["status"] == "failed"]
            if failed_rows:
                response_data["failed_rows"] = failed_rows[
                    :IMPORT_FAILED_ROWS_DISPLAY_LIMIT
                ]
                if len(failed_rows) > IMPORT_FAILED_ROWS_DISPLAY_LIMIT:
                    response_data["additional_failures"] = (
                        len(failed_rows) - IMPORT_FAILED_ROWS_DISPLAY_LIMIT
                    )

            # Determine status based on results
            summary = result["summary"]
            if summary.get("failed", 0) == 0:
                message = f"Import completed successfully. Created: {summary.get('created', 0)}, Updated: {summary.get('updated', 0)}"
                status_code = status.HTTP_201_CREATED
            elif (
                not replace_data
                and summary.get("created", 0) + summary.get("updated", 0) > 0
            ):
                message = f"Import completed with errors. Created: {summary.get('created', 0)}, Updated: {summary.get('updated', 0)}, Failed: {summary.get('failed', 0)}"
                status_code = status.HTTP_207_MULTI_STATUS
            else:
                message = f"Import failed. No records were processed successfully. Failed: {summary.get('failed', 0)}"
                status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

            return success_response(
                data=response_data, message=message, status_code=status_code
            )

        except ImportValidationError as e:
            error_message = str(e)

            # Determine if this is a header validation error
            if (
                "columns" in error_message.lower()
                or "template" in error_message.lower()
            ):
                # Generate template download URL (remove 'import-from-file/' and add 'download-import-template/')
                base_path = request.path.replace("import-from-file/", "")
                template_url = request.build_absolute_uri(
                    f"{base_path}download-import-template/"
                )

                return error_response(
                    message="Import validation failed - missing or incorrect columns",
                    errors={"validation": [error_message]},
                    data={"template_download_url": template_url},
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )
            else:
                # Other validation errors (config issues, transforms, etc.)
                return error_response(
                    message="Import configuration validation failed",
                    errors={"validation": [error_message]},
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

    @action(detail=False, methods=["get"], url_path="download-import-template")
    def download_import_template(self, request, *args, **kwargs):
        """
        Download the Excel template file for this import.

        Returns the template file directly for download with a timestamped filename.
        """
        if not self.import_template_name:
            raise NotImplementedError(
                "import_template_name must be defined in the ViewSet"
            )

        # Construct the path to the template file
        template_path = os.path.join(
            django_settings.BASE_DIR,
            "static",
            "import-templates",
            self.import_template_name,
        )

        # Check if template file exists, generate if missing
        if not os.path.exists(template_path):
            try:
                self._generate_template_file()
                # Verify it was created successfully
                if not os.path.exists(template_path):
                    return error_response(
                        message="Failed to generate template file",
                        errors={
                            "template": [
                                f"Could not create template '{self.import_template_name}'"
                            ]
                        },
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )
            except Exception as e:
                return error_response(
                    message="Template generation failed",
                    errors={"template": [f"Error generating template: {str(e)}"]},
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        try:
            # Read the template file
            with open(template_path, "rb") as template_file:
                file_content = template_file.read()

            # Generate timestamped filename
            timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
            base_name, ext = os.path.splitext(self.import_template_name)
            download_filename = f"{base_name}_{timestamp}{ext}"

            # Determine content type based on file extension
            content_type_mapping = {
                ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ".xls": "application/vnd.ms-excel",
                ".csv": "text/csv",
            }

            file_ext = os.path.splitext(self.import_template_name)[1].lower()
            content_type = content_type_mapping.get(
                file_ext, "application/octet-stream"
            )

            # Create response with file content
            response = HttpResponse(file_content, content_type=content_type)
            response["Content-Disposition"] = (
                f'attachment; filename="{download_filename}"'
            )
            response["Content-Length"] = len(file_content)

            return response

        except Exception as e:
            return error_response(
                message="Failed to read template file",
                errors={"template": [str(e)]},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _generate_template_file(self):
        """Generate template file using Django's management command."""

        # Get app label from the model in queryset
        if hasattr(self, "queryset") and self.queryset is not None:
            app_label = self.queryset.model._meta.app_label
        elif hasattr(self, "model") and self.model is not None:
            app_label = self.model._meta.app_label
        else:
            # Fallback: try to extract from module path
            module_parts = self.__class__.__module__.split(".")
            app_label = module_parts[0]

        viewset_name = self.__class__.__name__
        viewset_path = f"{app_label}.{viewset_name}"

        # Capture command output
        out = StringIO()

        try:
            # Call the management command directly
            call_command(
                "generate_import_template",
                viewset_path,
                filename=self.import_template_name,
                order_by="required-first",
                stdout=out,
            )
        except Exception as e:
            raise Exception(f"Template generation failed: {str(e)}")


class FileExportMixin:
    """
    Mixin that adds export functionality to ViewSets.

    The frontend export dialog sends:
    - file_type: "pdf", "xlsx", or "csv"
    - includes: list of field names or comma-separated field names
    - column_config: mapping of field names to display labels
    - data: optional pre-filtered data array
    """

    @staticmethod
    def _normalize_includes(includes_raw):
        """
        Normalize includes payload into a deduplicated ordered list of field names.

        Accepts:
        - list/tuple of strings
        - comma-separated string
        """
        if isinstance(includes_raw, str):
            candidates = includes_raw.split(",")
        elif isinstance(includes_raw, (list, tuple)):
            candidates = includes_raw
        else:
            raise TypeError(
                "Includes must be a list of field names or a comma-separated string."
            )

        includes = []
        seen = set()

        for value in candidates:
            if not isinstance(value, str):
                raise TypeError("Each include value must be a string.")
            field_name = value.strip()
            if not field_name or field_name in seen:
                continue
            seen.add(field_name)
            includes.append(field_name)

        if not includes:
            raise ValueError("No valid fields specified for export.")

        return includes

    @action(detail=False, methods=["post"], url_path="export-as-file")
    def export_data(self, request: Request) -> HttpResponse:
        """
        Export data based on frontend dialog parameters.

        Expected request data:
        - file_type: "pdf", "xlsx", or "csv"
        - includes: list of field names or comma-separated string
        - column_config: dict mapping field names to display labels
        - data: array of data to export (required)
        """
        try:
            # Parse request parameters
            file_type = str(request.data.get("file_type", "xlsx")).lower().strip()
            includes_raw = request.data.get("includes", [])
            column_config = request.data.get("column_config", {})
            provided_data = request.data.get("data")
            file_titles = request.data.get("file_titles", [])

            # Validate file type
            if file_type not in ["pdf", "xlsx", "csv"]:
                return error_response(
                    message="Invalid file type. Must be pdf, xlsx, or csv.",
                    errors={
                        "file_type": "Invalid file type. Must be pdf, xlsx, or csv."
                    },
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            try:
                includes = self._normalize_includes(includes_raw)
            except (TypeError, ValueError) as exc:
                return error_response(
                    message="Invalid includes payload.",
                    errors={"includes": [str(exc)]},
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            # Validate that data is provided
            if not provided_data:
                return error_response(
                    message="No data provided for export.",
                    errors={"data": "No data provided for export."},
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            # Initialize export service
            export_service = ExportService()

            # Process export data
            processed_data = export_service.process_export_data(
                provided_data, includes, column_config, file_titles
            )

            # Generate filename
            base_filename = slugify(get_model_name(self).lower())

            filename = f"{base_filename}.{file_type}"

            # Generate file based on type
            if file_type == "csv":
                return export_service.export_csv(
                    processed_data["table_data"],
                    processed_data["remaining_includes"],
                    column_config,
                    filename,
                    processed_data["export_headers"],
                    processed_data["document_titles"],
                )
            elif file_type == "xlsx":
                return export_service.export_xlsx(
                    processed_data["table_data"],
                    processed_data["remaining_includes"],
                    column_config,
                    filename,
                    processed_data["export_headers"],
                    processed_data["document_titles"],
                )
            elif file_type == "pdf":
                return export_service.export_pdf(
                    processed_data["table_data"],
                    processed_data["remaining_includes"],
                    column_config,
                    filename,
                    processed_data["export_headers"],
                    processed_data["document_titles"],
                )

        except Exception:
            error_id = uuid4().hex
            logger.exception(
                "File export failed",
                extra={
                    "error_id": error_id,
                    "viewset": self.__class__.__name__,
                },
            )
            return error_response(
                message="Data export failed",
                errors={
                    "export": [
                        "Unexpected error during export. Please contact support with the provided error id."
                    ]
                },
                error_id=error_id,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
