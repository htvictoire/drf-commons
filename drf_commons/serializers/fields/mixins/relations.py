"""Deferred relation resolution and write-application behavior."""

from rest_framework import serializers

from .deferred import DeferredRelatedOperation


class RelatedFieldRelationWriteMixin:
    """Deferred relation write orchestration."""

    def contains_deferred_related(self, value):
        """Return True when value contains deferred nested write operations."""
        if isinstance(value, DeferredRelatedOperation):
            return True
        if isinstance(value, list):
            return any(self.contains_deferred_related(item) for item in value)
        return False

    def resolve_related_value(self, value, parent_instance=None):
        """Resolve deferred operations into saved model instances."""
        if isinstance(value, DeferredRelatedOperation):
            return value.resolve(parent_instance=parent_instance)
        if isinstance(value, list):
            return [
                self.resolve_related_value(item, parent_instance=parent_instance)
                for item in value
            ]
        return value

    def get_relation_write_order(self):
        """Get resolved write order for this field."""
        return self._resolved_relation_write["write_order"]

    def apply_root_first_relation(self, parent_instance, resolved_value):
        """Apply root-first relation writes after parent save."""
        relation_kind = self._resolved_relation_write["relation_kind"]
        source_attr = self._get_source_attr()
        sync_mode = self._resolved_relation_write["sync_mode"]

        if relation_kind == "reverse_fk":
            child_link_field = self._resolved_relation_write.get("child_link_field")
            if not child_link_field:
                raise serializers.ValidationError(
                    f"Field '{self.field_name}' requires relation_write.child_link_field for reverse_fk operations."
                )

            values = (
                resolved_value if isinstance(resolved_value, list) else [resolved_value]
            )

            for obj in values:
                current_parent_id = getattr(obj, f"{child_link_field}_id", None)
                if current_parent_id != parent_instance.pk:
                    setattr(obj, child_link_field, parent_instance)
                    obj.save()

            if sync_mode in {"replace", "sync"}:
                if not self._bound_model_field or not getattr(
                    self._bound_model_field.field, "null", False
                ):
                    raise serializers.ValidationError(
                        "sync_mode='replace'/'sync' for reverse_fk requires a nullable child foreign key."
                    )

                provided_ids = [obj.pk for obj in values if getattr(obj, "pk", None)]
                manager = getattr(parent_instance, source_attr)
                manager.exclude(pk__in=provided_ids).update(**{child_link_field: None})
            return

        if relation_kind in {"reverse_m2m", "m2m"}:
            values = (
                resolved_value if isinstance(resolved_value, list) else [resolved_value]
            )
            manager = getattr(parent_instance, source_attr)
            if sync_mode in {"replace", "sync"}:
                manager.set(values)
            elif values:
                manager.add(*values)
            return

        setattr(parent_instance, source_attr, resolved_value)
        parent_instance.save()

    def _save_deferred_serializer(self, nested_serializer, parent_instance=None):
        """Persist nested serializer at save-time."""
        save_kwargs = {}
        if (
            parent_instance is not None
            and self._resolved_relation_write["relation_kind"] == "reverse_fk"
        ):
            child_link_field = self._resolved_relation_write.get("child_link_field")
            if not child_link_field:
                raise serializers.ValidationError(
                    f"Field '{self.field_name}' requires relation_write.child_link_field for reverse_fk operations."
                )
            save_kwargs[child_link_field] = parent_instance
        return nested_serializer.save(**save_kwargs)
