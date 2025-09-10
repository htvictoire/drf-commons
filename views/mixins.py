"""
Basic building blocks for generic class based views.

We don't bind behaviour to http method handlers yet,
which allows mixin classes to be composed in interesting ways.
"""
from typing import List, Dict, Any
from django.db import transaction
from django.http import HttpResponse
from django.conf import settings as django_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from common.response.utils import success_response, error_response
import os
from django.utils.text import slugify
from common.services.export_file import ExportService


class CreateModelMixin:
    """
    Create a model instance.
    """
    many_on_create = False
    return_data_on_create = False
    def create(self, request, *args, **kwargs):
        
        if self.many_on_create:
            serializer = self.get_serializer(data=request.data, many=True)
        else:
            serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        if self.return_data_on_create:
            return success_response(
                data=serializer.data,
                message="Object created successfully",
                status_code=status.HTTP_201_CREATED,
            )
        return success_response(
            message="Object created successfully",
            status_code=status.HTTP_201_CREATED,
        )
    def perform_create(self, serializer):
        serializer.save()



class ListModelMixin:
    """
    List a queryset.
    """
    append_indexes = True
    
    def _add_indexes_to_results(self, results):
        """Add sequential index to each item in results."""
        if not self.append_indexes:
            return results
        
        results_with_index = []
        for idx, item in enumerate(results, 1):
            item['index'] = idx
            results_with_index.append(item)
        return results_with_index
    
    def list(self, request, *args, **kwargs):
        paginated = request.query_params.get('paginated', 'true').lower() in ['true', '1', 'yes']
        queryset = self.filter_queryset(self.get_queryset())
        if not paginated:
            serializer = self.get_serializer(queryset, many=True)
            results = self._add_indexes_to_results(serializer.data)
            return success_response(
                data= {
                    'next': None,
                    'previous': None,
                    'count': queryset.count(),
                    'results': results,
                },
                message="Objects retrieved successfully",
            )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            if 'results' in paginated_response.data:
                paginated_response.data['results'] = self._add_indexes_to_results(paginated_response.data['results'])
            return success_response(
                data=paginated_response.data,
                message="Objects retrieved successfully",
            )

        serializer = self.get_serializer(queryset, many=True)
        results = self._add_indexes_to_results(serializer.data)
        return success_response(
            data= {
                    'next': None,
                    'previous': None,
                    'count': queryset.count(),
                    'results': results,
                },
            message="Objects retrieved successfully",
        )


class RetrieveModelMixin:
    """
    Retrieve a model instance.
    """
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(
            data=serializer.data,
            message="Object retrieved successfully",
        )


class UpdateModelMixin:
    """
    Update a model instance.
    """
    return_data_on_update = False
    many_on_update = False    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        if self.return_data_on_update:
            return success_response(
                data=serializer.data,
                message="Object updated successfully",
            )
        return success_response(
            message="Object updated successfully",
        )

    def perform_update(self, serializer):
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class DestroyModelMixin:
    """
    Destroy a model instance.
    """
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return success_response(
            message="Object deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT,
        )
    def soft_destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_soft_destroy(instance)
        return success_response(
            message="Object soft-deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT,
        )
    def perform_destroy(self, instance):
        instance.delete()
    def perform_soft_destroy(self, instance):
        """
        Override this method to implement soft delete logic.
        For example, set an 'is_active' field to False instead of deleting the instance.
        """
        instance.is_active = False
        instance.save()


class BulkCreateModelMixin:
    """
    Bulk create model instances.
    """
    bulk_batch_size = 1000
    
    def validate_bulk_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate bulk operation data."""
        if not data:
            raise ValidationError("Data cannot be empty.")
        
        if not isinstance(data, list):
            raise ValidationError("Data must be a list of objects.")
        
        if len(data) > self.bulk_batch_size:
            raise ValidationError(f"Batch size cannot exceed {self.bulk_batch_size} items.")
        
        return data
    
    @action(detail=False, methods=['post'], url_path='bulk-create')
    def bulk_create(self, request: Request) -> Response:
        """Create multiple objects in a single request."""
        objects_data = request.data.get('objects', [])
        
        try:
            validated_data = self.validate_bulk_data(objects_data)
            created_objects = []
            errors = []
            
            with transaction.atomic():
                for obj_data in validated_data:
                    try:
                        serializer = self.get_serializer(data=obj_data)
                        if serializer.is_valid():
                            self.perform_create(serializer)
                            created_objects.append(serializer.instance)
                        else:
                            errors.append({'data': obj_data, 'errors': serializer.errors})
                    except Exception as e:
                        errors.append({'data': obj_data, 'errors': {'detail': str(e)}})
            
            response_data = {
                'created_count': len(created_objects),
                'error_count': len(errors),
                'created_objects': self.get_serializer(created_objects, many=True).data,
            }
            
            if errors:
                response_data['errors'] = errors
            
            return success_response(
                data=response_data,
                message=f"Bulk create completed. {len(created_objects)} objects created.",
                status_code=status.HTTP_201_CREATED
            )
            
        except ValidationError as e:
            return error_response(
                errors=e.detail, 
                message="Bulk create validation failed",
                status_code=status.HTTP_400_BAD_REQUEST
            )


class BulkUpdateModelMixin(UpdateModelMixin):
    """
    Bulk update model instances.
    """
    bulk_batch_size = 1000
    
    def validate_bulk_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate bulk operation data."""
        if not data:
            raise ValidationError("Data cannot be empty.")
        
        if not isinstance(data, list):
            raise ValidationError("Data must be a list of objects.")
        
        if len(data) > self.bulk_batch_size:
            raise ValidationError(f"Batch size cannot exceed {self.bulk_batch_size} items.")
        
        return data
    
    @action(detail=False, methods=['patch'], url_path='bulk-update')
    def bulk_update(self, request: Request) -> Response:
        """Update multiple objects in a single request."""
        objects_data = request.data.get('objects', [])
        
        try:
            validated_data = self.validate_bulk_data(objects_data)
            updated_objects = []
            errors = []
            
            with transaction.atomic():
                for obj_data in validated_data:
                    try:
                        obj_id = obj_data.get('id')
                        if not obj_id:
                            errors.append({'data': obj_data, 'errors': {'id': ['This field is required.']}})
                            continue
                        
                        try:
                            instance = self.get_queryset().get(pk=obj_id)
                        except self.queryset.model.DoesNotExist:
                            errors.append({'data': obj_data, 'errors': {'id': ['Object not found.']}})
                            continue
                        
                        serializer = self.get_serializer(instance, data=obj_data, partial=True)
                        if serializer.is_valid():
                            self.perform_update(serializer)
                            updated_objects.append(serializer.instance)
                        else:
                            errors.append({'data': obj_data, 'errors': serializer.errors})
                            
                    except Exception as e:
                        errors.append({'data': obj_data, 'errors': {'detail': str(e)}})
            
            response_data = {
                'updated_count': len(updated_objects),
                'error_count': len(errors),
                'updated_objects': self.get_serializer(updated_objects, many=True).data,
            }
            
            if errors:
                response_data['errors'] = errors
            
            return success_response(
                data=response_data,
                message=f"Bulk update completed. {len(updated_objects)} objects updated.",
                status_code=status.HTTP_200_OK
            )
            
        except ValidationError as e:
            return error_response(
                errors=e.detail,
                message="Bulk update validation failed",
                status_code=status.HTTP_400_BAD_REQUEST
            )


class BulkDeleteModelMixin:
    """
    Bulk delete model instances.
    """
    bulk_batch_size = 1000
    
    @action(detail=False, methods=['delete'])
    def bulk_delete(self, request: Request) -> Response:
        """Delete multiple objects in a single request."""
        ids = request.data.get('ids', [])
        
        try:
            if not isinstance(ids, list):
                raise ValidationError("IDs must be provided as a list.")
            
            if not ids:
                raise ValidationError("IDs list cannot be empty.")
            
            if len(ids) > self.bulk_batch_size:
                raise ValidationError(f"Cannot delete more than {self.bulk_batch_size} items at once.")
            
            with transaction.atomic():
                queryset = self.get_queryset().filter(pk__in=ids)
                found_objects = list(queryset)
                found_ids = [str(obj.pk) for obj in found_objects]
                missing_ids = set(ids) - set(found_ids)
                
                deleted_count = 0
                if found_objects:
                    deleted_info = queryset.delete()
                    deleted_count = deleted_info[0]
            
            response_data = {
                'deleted_count': deleted_count,
                'requested_count': len(ids),
            }
            
            if missing_ids:
                response_data['missing_ids'] = list(missing_ids)
            
            return success_response(
                data=response_data,
                message=f"Bulk delete completed. {deleted_count} objects deleted.",
                status_code=status.HTTP_200_OK
            )
            
        except ValidationError as e:
            return error_response(
                errors=e.detail,
                message="Bulk delete validation failed",
                status_code=status.HTTP_400_BAD_REQUEST
            )


class FileImportMixin:
    """
    Mixin for importing data from files.
    
    Viewsets using this mixin must define:
    - import_file_config: Dict containing FileImportService configuration
    - import_template_name: Name of the template file in static/import-templates/
    - import_transforms: Optional dict of transform functions (default: {})
    """
    
    import_file_config = None     # Must be defined by subclass
    import_template_name = None   # Must be defined by subclass
    import_transforms = {}        # Optional transform functions
    
    @action(detail=False, methods=['post'], url_path='import-from-file')
    def import_file(self, request, *args, **kwargs):
        """
        Import data from uploaded file.
        
        Expected form data:
        - file: uploaded file (CSV, XLS, XLSX)
        - append_data: true (append to existing data) OR
        - replace_data: true (replace all existing data)
        """
        from common.services.import_from_file import FileImportService, ImportValidationError
        
        if not self.import_file_config:
            return error_response(
                message="Import configuration not defined for this resource",
                status_code=status.HTTP_501_NOT_IMPLEMENTED
            )
        
        if not self.import_template_name:
            return error_response(
                message="Import template not defined for this resource",
                status_code=status.HTTP_501_NOT_IMPLEMENTED
            )
        
        # Validate form data
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return error_response(
                message="No file provided",
                errors={'file': ['This field is required.']},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Check operation mode
        append_data = request.data.get('append_data', '').lower() == 'true'
        replace_data = request.data.get('replace_data', '').lower() == 'true'
        
        if not (append_data or replace_data):
            return error_response(
                message="Must specify either 'append_data=true' or 'replace_data=true'",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        if append_data and replace_data:
            return error_response(
                message="Cannot specify both 'append_data' and 'replace_data'",
                status_code=status.HTTP_400_BAD_REQUEST
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
            progress_data = {'processed': 0, 'total': 0}
            
            def progress_callback(processed: int, total: int):
                progress_data.update({'processed': processed, 'total': total})
            
            # Create and run import service
            service = FileImportService(
                self.import_file_config,
                transforms=self.import_transforms,
                progress_callback=progress_callback
            )
            
            result = service.import_file(uploaded_file)
            
            # Format response data
            response_data = {
                'import_summary': result['summary'],
                'operation': 'replace' if replace_data else 'append',
            }
            
            if replace_data:
                response_data['deleted_count'] = deleted_count
            
            # Include row details if there were failures
            failed_rows = [row for row in result['rows'] if row['status'] == 'failed']
            if failed_rows:
                response_data['failed_rows'] = failed_rows[:10]  # Limit to first 10 failures
                if len(failed_rows) > 10:
                    response_data['additional_failures'] = len(failed_rows) - 10
            
            # Determine status based on results
            summary = result['summary']
            if summary.get('failed', 0) == 0:
                message = f"Import completed successfully. Created: {summary.get('created', 0)}, Updated: {summary.get('updated', 0)}"
                status_code = status.HTTP_201_CREATED
            elif summary.get('created', 0) + summary.get('updated', 0) > 0:
                message = f"Import completed with errors. Created: {summary.get('created', 0)}, Updated: {summary.get('updated', 0)}, Failed: {summary.get('failed', 0)}"
                status_code = status.HTTP_207_MULTI_STATUS
            else:
                message = f"Import failed. No records were processed successfully. Failed: {summary.get('failed', 0)}"
                status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
            
            return success_response(
                data=response_data,
                message=message,
                status_code=status_code
            )
            
        except ImportValidationError as e:
            error_message = str(e)
            
            # Determine if this is a header validation error
            if 'columns' in error_message.lower() or 'template' in error_message.lower():
                # Generate template download URL (remove 'import-from-file/' and add 'download-import-template/')
                base_path = request.path.replace('import-from-file/', '')
                template_url = request.build_absolute_uri(
                    f"{base_path}download-import-template/"
                )
                
                return error_response(
                    message="Import validation failed - missing or incorrect columns",
                    errors={'validation': [error_message]},
                    data={'template_download_url': template_url},
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
                )
            else:
                # Other validation errors (config issues, transforms, etc.)
                return error_response(
                    message="Import configuration validation failed",
                    errors={'validation': [error_message]},
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
                )
        except Exception as e:
            return error_response(
                message="Import failed due to unexpected error",
                errors={'import': [str(e)]},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='download-import-template')
    def download_import_template(self, request, *args, **kwargs):
        """
        Download the Excel template file for this import.
        
        Returns the template file directly for download with a timestamped filename.
        """
        if not self.import_template_name:
            return error_response(
                message="Import template not defined for this resource",
                status_code=status.HTTP_501_NOT_IMPLEMENTED
            )
        
        # Construct the path to the template file
        template_path = os.path.join(
            django_settings.BASE_DIR, 
            'static', 
            'import-templates', 
            self.import_template_name
        )
        
        # Check if template file exists, generate if missing
        if not os.path.exists(template_path):
            try:
                self._generate_template_file()
                # Verify it was created successfully
                if not os.path.exists(template_path):
                    return error_response(
                        message="Failed to generate template file",
                        errors={'template': [f"Could not create template '{self.import_template_name}'"]},
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            except Exception as e:
                return error_response(
                    message="Template generation failed",
                    errors={'template': [f"Error generating template: {str(e)}"]},
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        try:
            # Read the template file
            with open(template_path, 'rb') as template_file:
                file_content = template_file.read()
            
            # Generate timestamped filename
            timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
            base_name, ext = os.path.splitext(self.import_template_name)
            download_filename = f"{base_name}_{timestamp}{ext}"
            
            # Determine content type based on file extension
            content_type_mapping = {
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.xls': 'application/vnd.ms-excel',
                '.csv': 'text/csv'
            }
            
            file_ext = os.path.splitext(self.import_template_name)[1].lower()
            content_type = content_type_mapping.get(file_ext, 'application/octet-stream')
            
            # Create response with file content
            response = HttpResponse(file_content, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{download_filename}"'
            response['Content-Length'] = len(file_content)
            
            return response
            
        except Exception as e:
            return error_response(
                message="Failed to read template file",
                errors={'template': [str(e)]},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _generate_template_file(self):
        """Generate template file using Django's management command."""
        from django.core.management import call_command
        from io import StringIO
        
        # Get app label from the model in queryset
        if hasattr(self, 'queryset') and self.queryset is not None:
            app_label = self.queryset.model._meta.app_label
        elif hasattr(self, 'model') and self.model is not None:
            app_label = self.model._meta.app_label
        else:
            # Fallback: try to extract from module path
            module_parts = self.__class__.__module__.split('.')
            app_label = module_parts[0]
        
        viewset_name = self.__class__.__name__
        viewset_path = f"{app_label}.{viewset_name}"
        
        # Capture command output
        out = StringIO()
        
        try:
            # Call the management command directly
            call_command(
                'generate_import_template',
                viewset_path,
                filename=self.import_template_name,
                order_by='required-first',
                stdout=out
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
    
    @action(detail=False, methods=['post'], url_path='export-as-file')
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
            file_type = request.data.get('file_type', 'xlsx').lower()
            includes_str = request.data.get('includes', '')
            column_config = request.data.get('column_config', {})
            provided_data = request.data.get('data')
            file_titles = request.data.get('file_titles', [])
            
            # Validate file type
            if file_type not in ['pdf', 'xlsx', 'csv']:
                return Response(
                    {'error': 'Invalid file type. Must be pdf, xlsx, or csv.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Parse includes
            if isinstance(includes_str, str):
                includes = [field.strip() for field in includes_str.split(',') if field.strip()]
            elif isinstance(includes_str, list):
                includes = includes_str
            else:
                includes = []
            
            if not includes:
                return Response(
                    {'error': 'No fields specified for export.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate that data is provided
            if not provided_data:
                return Response(
                    {'error': 'No data provided for export.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Initialize export service
            export_service = ExportService()
            
            # Process export data
            processed_data = export_service.process_export_data(
                provided_data, includes, column_config, file_titles
            )
            
            # Generate filename
            model_name = getattr(self.queryset.model, '_meta', None) if hasattr(self, 'queryset') else None
            if model_name:
                base_filename = slugify(model_name.verbose_name_plural or model_name.model_name)
            else:
                base_filename = 'export'
            
            filename = f"{base_filename}.{file_type}"
            
            # Generate file based on type
            if file_type == 'csv':
                return export_service.export_csv(
                    processed_data['table_data'], 
                    processed_data['remaining_includes'], 
                    column_config, 
                    filename, 
                    processed_data['export_headers'], 
                    processed_data['document_titles']
                )
            elif file_type == 'xlsx':
                return export_service.export_xlsx(
                    processed_data['table_data'], 
                    processed_data['remaining_includes'], 
                    column_config, 
                    filename, 
                    processed_data['export_headers'], 
                    processed_data['document_titles']
                )
            elif file_type == 'pdf':
                return export_service.export_pdf(
                    processed_data['table_data'], 
                    processed_data['remaining_includes'], 
                    column_config, 
                    filename, 
                    processed_data['export_headers'], 
                    processed_data['document_titles']
                )
                
        except Exception as e:
            return Response(
                {'error': f'Export failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )