"""Public configurable related field mixin composed from focused sub-mixins."""

from .config import RelatedFieldConfigMixin
from .conversion import RelatedFieldConversionMixin
from .inference import RelatedFieldInferenceMixin
from .relations import RelatedFieldRelationWriteMixin


class ConfigurableRelatedFieldMixin(
    RelatedFieldConfigMixin,
    RelatedFieldConversionMixin,
    RelatedFieldRelationWriteMixin,
    RelatedFieldInferenceMixin,
):
    """
    Base mixin providing core functionality for configurable related fields.
    """

    def __init__(
        self,
        serializer_class=None,
        input_formats=None,
        output_format="serialized",
        lookup_field="pk",
        slug_lookup_field=None,
        create_if_nested=True,
        update_if_exists=False,
        custom_output_callable=None,
        relation_write=None,
        **kwargs,
    ):
        """
        Initialize the configurable related field.

        Args:
            serializer_class: Serializer class for nested operations
            input_formats: List of accepted input formats ['id', 'nested', 'slug', 'object']
            output_format: Output format - 'id', 'str', 'serialized', 'custom'
            lookup_field: Field to use for lookups (default: 'pk')
            slug_lookup_field: Field to use for slug-string lookups (default: lookup_field)
            create_if_nested: Whether to create objects from nested data
            update_if_exists: Whether to update existing objects with nested data
            custom_output_callable: Custom function for output formatting
        """
        self.serializer_class = serializer_class
        self.input_formats = input_formats or ["id", "nested"]
        self.output_format = output_format
        self.lookup_field = lookup_field
        self.slug_lookup_field = slug_lookup_field or lookup_field
        self.create_if_nested = create_if_nested
        self.update_if_exists = update_if_exists
        self.custom_output_callable = custom_output_callable
        self.relation_write = relation_write or {}

        self._resolved_relation_write = {
            "relation_kind": "generic",
            "write_order": "dependency_first",
            "child_link_field": None,
            "sync_mode": "append",
        }
        self._bound_model_field = None

        # Let DRF handle its own parameters (allow_null, required, etc.).
        super().__init__(**kwargs)

        # Validate custom configuration after initialization.
        self._validate_configuration()

    def bind(self, field_name, parent):
        """Bind field and resolve relation write configuration from model metadata."""
        super().bind(field_name, parent)
        self._resolved_relation_write = self._resolve_relation_write(field_name, parent)
