"""
Main file import service orchestrating all components.
"""

import logging
from typing import Dict, Any, List, Optional, Callable
import pandas as pd
from django.db import transaction
from django.apps import apps
from common_conf import settings

from .config_validator import ConfigValidator
from .file_reader import FileReader
from .data_processor import DataProcessor
from .bulk_operations import BulkOperations
from .config_helpers import ConfigHelpers
from .exceptions import ImportErrorRow

logger = logging.getLogger(__name__)


class FileImportService:
    """
    File import service supporting multiple models and field types.
    
    This service orchestrates file reading, validation, data processing,
    and bulk database operations for importing data from CSV/Excel files.
    """
    
    # Expose class methods from helpers
    create_simple_config = staticmethod(ConfigHelpers.create_simple_config)
    validate_transforms = staticmethod(ConfigHelpers.validate_transforms_needed)

    def __init__(self, config: Dict[str, Any], *,
                 batch_size: int = settings.IMPORT_BATCH_SIZE,
                 transforms: Optional[Dict[str, callable]] = None,
                 progress_callback: Optional[Callable[[int, int], None]] = None):
        """
        Initialize the import service.
        
        Args:
            config: Import configuration dictionary
            batch_size: Batch size for bulk operations
            transforms: Transform functions for data processing
            progress_callback: Optional callback for progress tracking
        """
        self.config = config
        self.batch_size = batch_size
        self.transforms = transforms or {}
        self.progress_callback = progress_callback
        
        # Initialize components
        self.validator = ConfigValidator(config, self.transforms)
        self.file_reader = FileReader(config)
        self.data_processor = DataProcessor(config, self.transforms)
        self.bulk_ops = BulkOperations(batch_size)
        
        # Validate configuration
        self.validator.validate()

    def import_file(self, file_obj, progress_callback: Optional[Callable[[int, int], None]] = None) -> Dict[str, Any]:
        """Main entry point for file import."""
        df = self.file_reader.read_file(file_obj)
        callback = progress_callback or self.progress_callback
        chunk_size = self.config.get("chunk_size", len(df))
        
        if chunk_size >= len(df):
            return self._import_chunk(df, 0, callback, total_file_rows=len(df))
        else:
            return self._import_in_chunks(df, chunk_size, callback)

    def get_template_columns(self) -> List[str]:
        """Get the list of columns required for this import configuration."""
        return sorted(self.validator.get_all_columns())

    def _import_in_chunks(self, df: pd.DataFrame, chunk_size: int, callback: Optional[Callable]) -> Dict[str, Any]:
        """Process large files in chunks."""
        total_rows = len(df)
        all_results = []
        summary_totals = {"created": 0, "updated": 0, "failed": 0, "pending": 0}
        
        for start_idx in range(0, total_rows, chunk_size):
            end_idx = min(start_idx + chunk_size, total_rows)
            chunk_df = df.iloc[start_idx:end_idx].copy().reset_index(drop=True)
            
            try:
                chunk_result = self._import_chunk(chunk_df, start_idx, callback, total_file_rows=total_rows)
                all_results.extend(chunk_result["rows"])
                
                for key in summary_totals:
                    if key in chunk_result["summary"]:
                        summary_totals[key] += chunk_result["summary"][key]
                        
            except Exception as e:
                logger.error("Failed to process chunk %d-%d: %s", start_idx, end_idx, e)
                chunk_size_actual = end_idx - start_idx
                failed_rows = [{"status": "failed", "errors": [str(e)]} for _ in range(chunk_size_actual)]
                all_results.extend(failed_rows)
                summary_totals["failed"] += chunk_size_actual
        
        summary_totals["total_rows"] = total_rows
        return {"rows": all_results, "summary": summary_totals}

    @transaction.atomic
    def _import_chunk(self, df: pd.DataFrame, start_row_offset: int, callback: Optional[Callable], total_file_rows: int = None) -> Dict[str, Any]:
        """Process a single chunk of data."""
        # Validate headers only on first chunk
        if start_row_offset == 0:
            required_columns = self.validator.get_all_columns()
            self.file_reader.validate_headers(df.columns.tolist(), required_columns)
        
        total_rows = len(df)
        results_per_row = [
            {"status": "pending", "errors": [], "row_number": start_row_offset + i + 1} 
            for i in range(total_rows)
        ]

        # Prefetch lookup candidates
        lookup_values = self.data_processor.collect_lookup_values(df)
        lookup_caches = self.data_processor.prefetch_lookups(lookup_values)

        # Per-row container for created instances
        created_objs: List[Dict[str, Any]] = [dict() for _ in range(total_rows)]

        # Process models in configured order
        for step_key in self.config["order"]:
            with transaction.atomic():  # Per-model atomic transaction
                model_config = self.config["models"][step_key]
                model_cls = self._get_model(model_config["model"])
                unique_by = model_config.get("unique_by")
                update_if_exists = model_config.get("update_if_exists", False)

                # Prefetch existing objects for updates if needed
                existing_map = {}
                if unique_by:
                    existing_map = self.data_processor.prefetch_existing_objects(
                        model_cls, unique_by, model_config, df
                    )

                to_create = []
                to_update = []
                update_fields = set()

                for idx, row in df.iterrows():
                    try:
                        kwargs = self.data_processor.prepare_kwargs_for_row(
                            row, model_config, created_objs[idx], lookup_caches
                        )
                        existing_obj = None
                        if unique_by:
                            existing_obj = self.data_processor.find_existing_obj(
                                existing_map, unique_by, kwargs
                            )

                        if existing_obj and update_if_exists:
                            self.bulk_ops.apply_updates(existing_obj, kwargs)
                            to_update.append(existing_obj)
                            update_fields.update(kwargs.keys())
                            created_objs[idx][step_key] = existing_obj
                            results_per_row[idx]["status"] = "updated"
                        else:
                            inst = model_cls(**kwargs)
                            to_create.append((idx, inst))
                            results_per_row[idx]["status"] = "created"

                    except ImportErrorRow as e:
                        # Handle specific import errors with detailed context
                        row_num = start_row_offset + idx + 1
                        if e.field_name:
                            error_msg = f"Row {row_num}, Field '{e.field_name}': {str(e)}"
                        else:
                            error_msg = f"Row {row_num}: {str(e)}"
                        logger.error("Import error at row %s: %s", row_num, e)
                        results_per_row[idx]["status"] = "failed"
                        results_per_row[idx]["errors"].append(error_msg)
                    except Exception as e:
                        # Handle unexpected errors separately to avoid overwriting ImportErrorRow
                        row_num = start_row_offset + idx + 1
                        error_msg = f"Row {row_num}: Unexpected error - {str(e)}"
                        logger.error("Unexpected error preparing row %s: %s", row_num, e)
                        results_per_row[idx]["status"] = "failed"
                        results_per_row[idx]["errors"].append(error_msg)
                    
                    # Progress callback
                    if callback and (idx + 1) % 100 == 0:
                        callback(start_row_offset + idx + 1, total_file_rows)

                # Check if this step is referenced by later steps (needs individual saves for consistency)
                is_referenced = self._is_step_referenced_later(step_key)
                
                # Perform saves and capture any errors
                save_errors = {}
                if is_referenced:
                    # Use individual saves to maintain object consistency for references
                    save_errors = self.bulk_ops.individual_create_instances(model_cls, to_create, created_objs, step_key)
                else:
                    # Safe to use bulk operations for final step objects
                    save_errors = self.bulk_ops.bulk_create_instances(model_cls, to_create, created_objs, step_key)
                
                # Update row status for failed saves
                for row_idx, error_msg in save_errors.items():
                    results_per_row[row_idx]["status"] = "failed"
                    results_per_row[row_idx]["errors"].append(f"Row {start_row_offset + row_idx + 1}, Field '{step_key}': {error_msg}")
                
                self.bulk_ops.bulk_update_instances(model_cls, to_update, update_fields)

        # Final progress callback
        if callback:
            callback(start_row_offset + total_rows, total_file_rows)
            
        summary = self._build_summary(results_per_row, total_rows)
        return {"rows": results_per_row, "summary": summary}

    def _build_summary(self, results_per_row: List[Dict], total_rows: int) -> Dict[str, int]:
        """Build summary statistics from row results."""
        counts = {"created": 0, "updated": 0, "failed": 0, "pending": 0}
        for r in results_per_row:
            counts[r["status"]] = counts.get(r["status"], 0) + 1
        summary = {"total_rows": total_rows}
        summary.update(counts)
        return summary

    def _is_step_referenced_later(self, step_key: str) -> bool:
        """Check if a step is referenced by any later steps in the processing order."""
        current_index = self.config["order"].index(step_key)
        later_steps = self.config["order"][current_index + 1:]
        
        for later_step in later_steps:
            later_config = self.config["models"][later_step]
            if "reference_fields" in later_config:
                if step_key in later_config["reference_fields"].values():
                    return True
        return False

    def _get_model(self, model_path: str):
        """Get Django model from app.Model path."""
        return apps.get_model(model_path)