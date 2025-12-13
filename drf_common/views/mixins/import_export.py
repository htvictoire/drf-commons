"""
Mixins for file import and export functionality.
"""

import os
from io import StringIO

from django.conf import settings as django_settings
from django.core.management import call_command
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from django.utils.text import slugify

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.request import Request

from drf_common.common_conf.settings import IMPORT_FAILED_ROWS_DISPLAY_LIMIT
from drf_common.response.utils import error_response, success_response
from drf_common.services.export_file import ExportService
from drf_common.services.import_from_file import FileImportService, ImportValidationError
from .utils import get_model_name


class FileImportMixin:
    """
    Mixin for importing data from files.

    Viewsets using this mixin must define:
    - import_file_config: Dict containing FileImportService configuration
    - import_template_name: Name of the template file in static/import-templates/
    - import_transforms: Optional dict of transform functions (default: {})
    """

    import_file_config = None  # Must be defined by subclass
    import_template_name = None  # Must be defined by subclass
    import_transforms = {}  # Optional transform functions

    @action(detail=False, methods=["post"], url_path="import-from-file")
    def import_file(self, request, *args, **kwargs):
        """
        Import data from uploaded file.

        Expected form data:
        - file: uploaded file (CSV, XLS, XLSX)
        - append_data: true (append to existing data) OR
        - replace_data: true (replace all existing data)
        """

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
        append_data = request.data.get("append_data", "").lower() == "true"
        replace_data = request.data.get("replace_data", "").lower() == "true"

        if not (append_data or replace_data):
            return error_response(
                message="Must specify either 'append_data=true' or 'replace_data=true'",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if append_data and replace_data:
            return error_response(
                message="Cannot specify both 'append_data' and 'replace_data'",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            deleted_count = 0
            # Handle replace_data by clearing existing records
            if replace_data:
                with transaction.atomic():
                    count = self.get_queryset().count()
                    if count > 0:
                        deleted_info = self.get_queryset().delete()
                        deleted_count = deleted_info[0]

            # Setup progress tracking
            progress_data = {"processed": 0, "total": 0}

            def progress_callback(processed: int, total: int):
                progress_data.update({"processed": processed, "total": total})

            # Create and run import service
            service = FileImportService(
                self.import_file_config,
                transforms=self.import_transforms,
                progress_callback=progress_callback,
            )

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
            elif summary.get("created", 0) + summary.get("updated", 0) > 0:
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
    - includes: comma-separated list of field names to include
    - column_config: mapping of field names to display labels
    - data: optional pre-filtered data array
    """

    @action(detail=False, methods=["post"], url_path="export-as-file")
    def export_data(self, request: Request) -> HttpResponse:
        """
        Export data based on frontend dialog parameters.

        Expected request data:
        - file_type: "pdf", "xlsx", or "csv"
        - includes: comma-separated string of field names
        - column_config: dict mapping field names to display labels
        - data: array of data to export (required)
        """
        try:
            # Parse request parameters
            file_type = request.data.get("file_type", "xlsx").lower()
            includes = request.data.get("includes", "")
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
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not includes:
                return error_response(
                    message="No fields specified for export.",
                    errors={"includes": "No fields specified for export."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate that data is provided
            if not provided_data:
                return error_response(
                    message="No data provided for export.",
                    errors={"data": "No data provided for export."},
                    status=status.HTTP_400_BAD_REQUEST,
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

        except Exception as e:
            return error_response(
                message="Data export failed",
                errors={"export": [str(e)]},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
