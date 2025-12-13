"""
Main DataProcessor class that orchestrates data processing operations.
"""

import logging
from typing import Any, Dict, List

from django.db.models import Model

import pandas as pd

from .field_processor import FieldProcessor
from .lookup_manager import LookupManager
from .object_manager import ObjectManager

logger = logging.getLogger(__name__)


class DataProcessor:
    """Handles data processing, transformations, and model operations."""

    def __init__(self, config: Dict[str, Any], transforms: Dict[str, callable]):
        self.config = config
        self.transforms = transforms

        # Initialize managers
        self.lookup_manager = LookupManager(config)
        self.field_processor = FieldProcessor(transforms)
        self.object_manager = ObjectManager(transforms)

    def collect_lookup_values(self, df: pd.DataFrame) -> Dict[str, set]:
        """Scan configurations and gather unique source values for lookups."""
        return self.lookup_manager.collect_lookup_values(df)

    def prefetch_lookups(
        self, lookup_values: Dict[str, set]
    ) -> Dict[str, Dict[Any, Model]]:
        """Prefetch lookup objects to avoid N+1 queries."""
        return self.lookup_manager.prefetch_lookups(lookup_values)

    def resolve_lookup(
        self, lookup_spec: Dict[str, Any], value, lookup_caches: Dict[str, Dict]
    ):
        """Return existing object from cache or None."""
        return self.lookup_manager.resolve_lookup(lookup_spec, value, lookup_caches)

    def apply_transform(self, transform_name: str, value):
        """Apply named transform function to value."""
        return self.field_processor.apply_transform(transform_name, value)

    def prepare_kwargs_for_row(
        self,
        row,
        model_config: Dict[str, Any],
        created_objs_for_row: Dict[str, Model],
        lookup_caches: Dict[str, Dict],
    ) -> Dict[str, Any]:
        """Prepare kwargs for model creation from row data."""
        kwargs = {}

        # Process computed fields FIRST - they may be needed for lookups and unique_by
        self.field_processor.process_computed_fields(
            row, model_config, created_objs_for_row, kwargs
        )

        # Process direct columns (simple field -> column mapping)
        self.field_processor.process_direct_columns(row, model_config, kwargs)

        # Process transformed columns (field -> {column, transform})
        self.field_processor.process_transformed_columns(row, model_config, kwargs)

        # Process constant fields (field -> constant_value)
        self.field_processor.process_constant_fields(model_config, kwargs)

        # Process reference fields (field -> reference_key from previous step)
        self.field_processor.process_reference_fields(
            model_config, created_objs_for_row, kwargs
        )

        # Process lookup fields (field -> {column, model, lookup_field, create_if_missing})
        self.field_processor.process_lookup_fields(
            row, model_config, lookup_caches, self.lookup_manager, kwargs
        )

        # Validate required fields AFTER all field processing is complete
        self.field_processor.validate_required_fields(kwargs, model_config)

        return kwargs

    def prefetch_existing_objects(
        self,
        model_cls,
        unique_by: List[str],
        model_config: Dict[str, Any],
        df: pd.DataFrame,
    ):
        """Prefetch existing objects from DB based on unique keys."""
        return self.object_manager.prefetch_existing_objects(
            model_cls, unique_by, model_config, df
        )

    def find_existing_obj(
        self, existing_map: Dict, unique_by: List[str], kwargs: Dict[str, Any]
    ):
        """Find existing object based on unique_by fields."""
        return self.object_manager.find_existing_obj(existing_map, unique_by, kwargs)
