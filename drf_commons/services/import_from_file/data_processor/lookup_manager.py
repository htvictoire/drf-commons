"""
Lookup management for data processing operations.
"""

import logging
from typing import Any, Dict, Optional

from django.apps import apps
from django.db.models import Model

try:
    import pandas as pd
except ImportError as e:
    raise ImportError(
        "File import service requires pandas. "
        "Install it with: pip install drf-commons[import]"
    ) from e

logger = logging.getLogger(__name__)


class LookupManager:
    """Handles lookup operations for data processing."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def collect_lookup_values(self, df: pd.DataFrame) -> Dict[str, set]:
        """Scan configurations and gather unique source values for lookups."""
        lookup_values = {}
        for step_key in self.config["order"]:
            model_config = self.config["models"][step_key]

            if "lookup_fields" in model_config:
                for field_name, lookup_spec in model_config["lookup_fields"].items():
                    col = lookup_spec["column"]
                    if col and col in df.columns:
                        vals = set(df[col].dropna().unique().tolist())
                        # Use full model path to avoid conflicts between apps
                        model_path = lookup_spec["model"]
                        if "." not in model_path:
                            raise ValueError(
                                f"Model path '{model_path}' must be fully qualified (app_label.ModelName)"
                            )
                        key = f"{model_path}__{lookup_spec['lookup_field']}"
                        lookup_values.setdefault(key, set()).update(vals)
        return lookup_values

    def prefetch_lookups(
        self, lookup_values: Dict[str, set]
    ) -> Dict[str, Dict[Any, Model]]:
        """Prefetch lookup objects to avoid N+1 queries."""
        caches = {}
        for key, values in lookup_values.items():
            model_path, field = key.split("__", 1)
            model = self._get_model(model_path)

            # Check if the field is a database field or a property/attribute
            if self._is_model_field(model, field):
                # Database field - use ORM filtering
                q = {f"{field}__in": list(values)}
                qs = model.objects.filter(**q)
                map_ = {getattr(obj, field): obj for obj in qs}
            else:
                # Property/attribute - fetch all objects and filter in Python
                qs = model.objects.all()
                map_ = {}
                for obj in qs:
                    try:
                        attr_value = getattr(obj, field)
                        if attr_value in values:
                            map_[attr_value] = obj
                    except AttributeError:
                        # Attribute doesn't exist on this object
                        continue

            caches[key] = map_
        return caches

    def resolve_lookup(
        self, lookup_spec: Dict[str, Any], value, lookup_caches: Dict[str, Dict]
    ) -> Optional[Model]:
        """Return existing object from cache or None."""
        model_path = lookup_spec["model"]
        if "." not in model_path:
            raise ValueError(
                f"Model path '{model_path}' must be fully qualified (app_label.ModelName)"
            )
        field = lookup_spec["lookup_field"]
        key = f"{model_path}__{field}"
        cache = lookup_caches.get(key, {})
        return cache.get(value)

    def _get_model(self, model_path: str):
        """Get Django model from app.Model path."""
        return apps.get_model(model_path)

    def _is_model_field(self, model_cls, field_name: str) -> bool:
        """Check if field_name is a database field on the model."""
        try:
            model_cls._meta.get_field(field_name)
            return True
        except Exception:
            # Field doesn't exist in model's database fields
            return False
