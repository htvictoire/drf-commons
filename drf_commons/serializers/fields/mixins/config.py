"""Configuration validation for configurable related fields."""


class RelatedFieldConfigMixin:
    """Configuration validation behavior shared by configurable related fields."""

    def _validate_configuration(self):
        """Validate field configuration."""
        valid_input_formats = ["id", "nested", "slug", "object"]
        valid_output_formats = ["id", "str", "serialized", "custom"]
        valid_relation_kinds = [
            "auto",
            "generic",
            "fk",
            "m2m",
            "reverse_fk",
            "reverse_m2m",
        ]
        valid_write_orders = ["auto", "dependency_first", "root_first"]
        valid_sync_modes = ["append", "replace", "sync"]

        if not all(fmt in valid_input_formats for fmt in self.input_formats):
            raise ValueError(
                f"Invalid input_formats. Must be subset of {valid_input_formats}"
            )

        if self.output_format not in valid_output_formats:
            raise ValueError(
                f"Invalid output_format. Must be one of {valid_output_formats}"
            )

        if self.output_format == "serialized" and not self.serializer_class:
            raise ValueError(
                "serializer_class is required when output_format='serialized'"
            )

        if self.output_format == "custom" and not self.custom_output_callable:
            raise ValueError(
                "custom_output_callable is required when output_format='custom'"
            )

        if "nested" in self.input_formats and not self.serializer_class:
            raise ValueError(
                "serializer_class is required when 'nested' is in input_formats"
            )

        relation_kind = self.relation_write.get("relation_kind", "auto")
        if relation_kind not in valid_relation_kinds:
            raise ValueError(
                f"Invalid relation_write.relation_kind. Must be one of {valid_relation_kinds}"
            )

        write_order = self.relation_write.get("write_order", "auto")
        if write_order not in valid_write_orders:
            raise ValueError(
                f"Invalid relation_write.write_order. Must be one of {valid_write_orders}"
            )

        sync_mode = self.relation_write.get("sync_mode", "append")
        if sync_mode not in valid_sync_modes:
            raise ValueError(
                f"Invalid relation_write.sync_mode. Must be one of {valid_sync_modes}"
            )
