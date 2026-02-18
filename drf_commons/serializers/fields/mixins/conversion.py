"""Input and output conversion behavior for configurable related fields."""

from rest_framework import serializers

from .deferred import DeferredRelatedOperation


class RelatedFieldConversionMixin:
    """Representation and internal-value conversion behavior."""

    def to_representation(self, value):
        """Convert the internal value to the desired output format."""
        if value is None:
            return None

        if self.output_format == "id":
            return getattr(value, self.lookup_field)

        if self.output_format == "str":
            return str(value)

        if self.output_format == "serialized":
            serializer = self.serializer_class(value, context=self.context)
            return serializer.data

        if self.output_format == "custom":
            return self.custom_output_callable(value, self.context)

        if self.serializer_class:
            serializer = self.serializer_class(value, context=self.context)
            return serializer.data
        return str(value)

    def to_internal_value(self, data):
        """Convert input data to internal value."""
        if data is None or data == "":
            if not self.allow_null:
                self.fail("null")
            return None

        if isinstance(data, dict) and "nested" in self.input_formats:
            return self._handle_nested_input(data)

        if isinstance(data, int) and "id" in self.input_formats:
            return self._handle_id_input(data)

        if isinstance(data, str):
            if "slug" in self.input_formats and "id" in self.input_formats:
                return self._handle_string_id_or_slug_input(data)
            if "slug" in self.input_formats:
                return self._handle_slug_input(data)
            if "id" in self.input_formats:
                return self._handle_id_input(data)

        if hasattr(data, "_meta") and "object" in self.input_formats:
            return data

        self.fail("incorrect_type", data_type=type(data).__name__)

    def _handle_string_id_or_slug_input(self, data):
        """Resolve string input when both ID and slug formats are enabled."""
        first_handler, second_handler = self._get_string_resolution_handlers(data)

        try:
            return first_handler(data)
        except serializers.ValidationError as first_error:
            try:
                return second_handler(data)
            except serializers.ValidationError:
                raise first_error

    @staticmethod
    def _is_numeric_string(value):
        """Return True when value is a plain decimal string."""
        return value.isdigit()

    def _get_string_resolution_handlers(self, data):
        """Choose resolution priority for mixed string input."""
        if self._is_numeric_string(data):
            return self._handle_id_input, self._handle_slug_input
        return self._handle_slug_input, self._handle_id_input

    def _handle_nested_input(self, data):
        """Validate nested data and defer create/update until serializer save."""
        if not self.create_if_nested:
            self.fail("invalid")

        lookup_value = data.get(self.lookup_field)
        instance = None

        if lookup_value and self.update_if_exists:
            try:
                instance = self.queryset.get(**{self.lookup_field: lookup_value})
            except self.queryset.model.DoesNotExist:
                instance = None

        nested_serializer = self.serializer_class(
            instance, data=data, partial=instance is not None, context=self.context
        )
        if not nested_serializer.is_valid():
            raise serializers.ValidationError(nested_serializer.errors)

        return DeferredRelatedOperation(field=self, serializer=nested_serializer)

    def _handle_id_input(self, data):
        """Handle ID-based lookup."""
        try:
            return self.queryset.get(**{self.lookup_field: data})
        except self.queryset.model.DoesNotExist:
            self.fail("does_not_exist", pk_value=data)
        except (ValueError, TypeError):
            self.fail("incorrect_type", data_type=type(data).__name__)

    def _handle_slug_input(self, data):
        """Handle slug-based lookup."""
        slug_field = "slug" if hasattr(self.queryset.model, "slug") else "name"
        try:
            return self.queryset.get(**{slug_field: data})
        except self.queryset.model.DoesNotExist:
            self.fail("does_not_exist", pk_value=data)
