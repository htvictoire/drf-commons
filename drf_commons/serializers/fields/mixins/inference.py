"""Relation inference from model metadata for configurable related fields."""

from django.core.exceptions import FieldDoesNotExist


class RelatedFieldInferenceMixin:
    """Relation-type inference and write-order resolution."""

    def _resolve_relation_write(self, field_name, parent):
        """Resolve relation write config using serializer model metadata."""
        resolved = {
            "relation_kind": "generic",
            "write_order": "dependency_first",
            "child_link_field": None,
            "sync_mode": "append",
        }

        relation_kind_override = self.relation_write.get("relation_kind", "auto")
        write_order_override = self.relation_write.get("write_order", "auto")
        child_link_override = self.relation_write.get("child_link_field")
        sync_mode = self.relation_write.get("sync_mode", "append")
        resolved["sync_mode"] = sync_mode

        source = field_name if self.source in (None, "*") else self.source
        inferred_kind = "generic"
        inferred_child_link = None
        self._bound_model_field = None

        model = getattr(getattr(parent, "Meta", None), "model", None)
        if model and "." not in source:
            try:
                model_field = model._meta.get_field(source)
                self._bound_model_field = model_field
                inferred_kind, inferred_child_link = self._infer_relation_kind(
                    model_field
                )
            except FieldDoesNotExist:
                inferred_kind = "generic"

        if relation_kind_override != "auto":
            resolved["relation_kind"] = relation_kind_override
        else:
            resolved["relation_kind"] = inferred_kind

        if child_link_override:
            resolved["child_link_field"] = child_link_override
        else:
            resolved["child_link_field"] = inferred_child_link

        if write_order_override != "auto":
            resolved["write_order"] = write_order_override
        else:
            resolved["write_order"] = self._default_write_order(
                resolved["relation_kind"]
            )

        return resolved

    def _infer_relation_kind(self, model_field):
        """Infer relation type from Django model field metadata."""
        if getattr(model_field, "one_to_many", False) and getattr(
            model_field, "auto_created", False
        ):
            return "reverse_fk", model_field.field.name

        if getattr(model_field, "many_to_many", False) and getattr(
            model_field, "auto_created", False
        ):
            return "reverse_m2m", None

        if getattr(model_field, "many_to_one", False) or getattr(
            model_field, "one_to_one", False
        ):
            return "fk", None

        if getattr(model_field, "many_to_many", False):
            return "m2m", None

        return "generic", None

    def _default_write_order(self, relation_kind):
        if relation_kind in {"reverse_fk", "reverse_m2m"}:
            return "root_first"
        return "dependency_first"

    def _get_source_attr(self):
        """Return top-level source attribute used by serializer field."""
        if self.source and self.source != "*":
            return self.source
        return self.field_name
