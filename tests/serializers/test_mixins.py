"""
Tests for configurable related field mixins.

Tests core mixin functionality that provides the foundation
for all configurable related field functionality.
"""

from django.core.exceptions import FieldError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from rest_framework import serializers

from unittest.mock import MagicMock, Mock, patch

from drf_commons.common_tests.base_cases import SerializerTestCase
from drf_commons.common_tests.factories import UserFactory
from drf_commons.common_tests.serializers import (
    MockField,
    create_mock_field,
    create_serialized_mock_field,
)
from drf_commons.serializers.fields.mixins.deferred import DeferredRelatedOperation
from drf_commons.serializers.fields.mixins.relations import RelatedFieldRelationWriteMixin

User = get_user_model()


class ConfigurableRelatedFieldMixinTests(SerializerTestCase):
    """Tests for ConfigurableRelatedFieldMixin."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.queryset = User.objects.all()

    def test_mixin_initialization_with_defaults(self):
        """Test mixin initializes with default configuration."""
        field = create_serialized_mock_field(queryset=self.queryset)
        self.assertEqual(field.input_formats, ["id", "nested"])
        self.assertEqual(field.output_format, "serialized")
        self.assertEqual(field.lookup_field, "pk")
        self.assertTrue(field.create_if_nested)
        self.assertFalse(field.update_if_exists)
        self.assertIsNone(field.custom_output_callable)

    def test_mixin_initialization_with_custom_values(self):
        """Test mixin initializes with custom configuration."""
        def custom_callable(obj, ctx):
            return f"User: {obj.username}"
        field = MockField(
            queryset=self.queryset,
            input_formats=["id", "slug"],
            output_format="custom",
            lookup_field="id",
            create_if_nested=False,
            update_if_exists=True,
            custom_output_callable=custom_callable,
        )
        self.assertEqual(field.input_formats, ["id", "slug"])
        self.assertEqual(field.output_format, "custom")
        self.assertEqual(field.lookup_field, "id")
        self.assertFalse(field.create_if_nested)
        self.assertTrue(field.update_if_exists)
        self.assertEqual(field.custom_output_callable, custom_callable)

    def test_configuration_validation_invalid_input_formats(self):
        """Test validation rejects invalid input formats."""
        with self.assertRaises(ValueError) as cm:
            MockField(
                queryset=self.queryset,
                input_formats=["invalid"],
                output_format="id"
            )
        self.assertIn("Invalid input_formats", str(cm.exception))

    def test_configuration_validation_invalid_output_format(self):
        """Test validation rejects invalid output formats."""
        with self.assertRaises(ValueError) as cm:
            MockField(
                queryset=self.queryset,
                output_format="invalid",
                input_formats=["id"]
            )
        self.assertIn("Invalid output_format", str(cm.exception))

    def test_configuration_validation_serialized_without_serializer_class(self):
        """Test validation requires serializer_class for serialized output."""
        with self.assertRaises(ValueError) as cm:
            MockField(
                queryset=self.queryset,
                output_format="serialized",
                serializer_class=None,
            )
        self.assertIn("serializer_class is required", str(cm.exception))

    def test_configuration_validation_custom_without_callable(self):
        """Test validation requires custom_output_callable for custom output."""
        with self.assertRaises(ValueError) as cm:
            MockField(
                queryset=self.queryset,
                output_format="custom",
                custom_output_callable=None,
                input_formats=["id"]
            )
        self.assertIn("custom_output_callable is required", str(cm.exception))

    def test_configuration_validation_nested_without_serializer_class(self):
        """Test validation requires serializer_class for nested input."""
        with self.assertRaises(ValueError) as cm:
            MockField(
                queryset=self.queryset,
                input_formats=["nested"],
                output_format="id"
            )
        self.assertIn("serializer_class is required", str(cm.exception))

    def test_to_representation_with_none_value(self):
        """Test representation returns None for None value."""
        field = create_mock_field(queryset=self.queryset)
        result = field.to_representation(None)
        self.assertIsNone(result)

    def test_to_representation_with_id_format(self):
        """Test representation returns ID for id format."""
        field = create_mock_field(queryset=self.queryset)
        field.lookup_field = "pk"
        result = field.to_representation(self.user)
        self.assertEqual(result, self.user.pk)

    def test_to_representation_with_str_format(self):
        """Test representation returns string for str format."""
        field = create_mock_field(
            queryset=self.queryset,
            output_format="str"
        )
        result = field.to_representation(self.user)
        self.assertEqual(result, str(self.user))

    def test_to_representation_with_custom_format(self):
        """Test representation uses custom callable for custom format."""
        def custom_callable(obj, ctx):
            return f"User: {obj.username}"
        field = MockField(
            queryset=self.queryset,
            output_format="custom",
            custom_output_callable=custom_callable,
            input_formats=["id"]
        )
        result = field.to_representation(self.user)
        self.assertEqual(result, f"User: {self.user.username}")

    def test_to_internal_value_with_null_and_allow_null_true(self):
        """Test internal value handles null when allow_null is True."""
        field = create_mock_field(queryset=self.queryset, allow_null=True)
        result = field.to_internal_value(None)
        self.assertIsNone(result)

    def test_to_internal_value_with_null_and_allow_null_false(self):
        """Test internal value rejects null when allow_null is False."""
        field = create_mock_field(queryset=self.queryset, allow_null=False)
        field.error_messages = {"null": "This field may not be null."}
        with self.assertRaises(Exception):
            field.to_internal_value(None)

    def test_handle_id_input_with_valid_id(self):
        """Test ID input handling with valid ID."""
        field = create_mock_field(queryset=self.queryset, input_formats=["id"])
        result = field._handle_id_input(self.user.pk)
        self.assertEqual(result, self.user)

    def test_handle_id_input_with_invalid_id(self):
        """Test ID input handling with non-existent ID."""
        field = create_mock_field(queryset=self.queryset, input_formats=["id"])
        field.error_messages = {"does_not_exist": "Object does not exist."}
        with self.assertRaises(Exception):
            field._handle_id_input(99999)

    def test_handle_slug_input_with_username(self):
        """Test slug input handling using username as slug field."""
        user_with_name = UserFactory(username="test-slug")
        field = create_mock_field(
            queryset=self.queryset,
            input_formats=["slug"],
            slug_lookup_field="username",
        )
        result = field._handle_slug_input("test-slug")
        self.assertEqual(result, user_with_name)

    def test_configuration_accepts_valid_input_formats(self):
        """Test configuration accepts all valid input formats."""
        valid_formats = ["id", "nested", "slug", "object"]
        field = create_mock_field(
            queryset=self.queryset, input_formats=valid_formats
        )
        self.assertEqual(field.input_formats, valid_formats)

    def test_configuration_accepts_valid_output_formats(self):
        """Test configuration accepts all valid output formats."""
        valid_formats = ["id", "str", "serialized", "custom"]
        for fmt in valid_formats:
            if fmt == "custom":
                field = create_mock_field(
                    queryset=self.queryset,
                    output_format=fmt,
                    custom_output_callable=lambda x, y: str(x)
                )
            elif fmt == "serialized":

                class TestSerializer(serializers.ModelSerializer):
                    class Meta:
                        model = User
                        fields = ["id"]

                field = MockField(
                    queryset=self.queryset,
                    output_format=fmt,
                    serializer_class=TestSerializer,
                )
            else:
                field = create_mock_field(queryset=self.queryset, output_format=fmt)
            self.assertEqual(field.output_format, fmt)

    def test_to_internal_value_resolves_slug_when_id_and_slug_enabled(self):
        """Non-numeric strings should resolve through slug lookup when enabled."""
        group = Group.objects.create(name="ops-team")
        field = create_mock_field(
            queryset=Group.objects.all(),
            input_formats=["id", "slug"],
            slug_lookup_field="name",
        )

        result = field.to_internal_value("ops-team")

        self.assertEqual(result, group)

    def test_to_internal_value_numeric_string_prefers_id_lookup(self):
        """Numeric strings should resolve through ID lookup when available."""
        group = Group.objects.create(name="group-1")
        field = create_mock_field(
            queryset=Group.objects.all(),
            input_formats=["id", "slug"],
            slug_lookup_field="name",
        )

        result = field.to_internal_value(str(group.pk))

        self.assertEqual(result, group)

    def test_to_internal_value_numeric_string_falls_back_to_slug(self):
        """If numeric ID lookup fails, numeric slug-like names still resolve."""
        group = Group.objects.create(name="404")
        field = create_mock_field(
            queryset=Group.objects.all(),
            input_formats=["id", "slug"],
            slug_lookup_field="name",
        )
        field.error_messages = {
            "does_not_exist": "Object does not exist.",
            "incorrect_type": "Incorrect type.",
        }

        result = field.to_internal_value("404")

        self.assertEqual(result, group)

    def test_handle_slug_input_invalid_lookup_field_raises_validation_error(self):
        field = create_mock_field(
            queryset=self.queryset,
            input_formats=["slug"],
            slug_lookup_field="name",
        )
        with self.assertRaises(serializers.ValidationError):
            field._handle_slug_input("any")

    def test_to_representation_falls_back_to_serializer_when_output_format_unknown(self):
        field = create_serialized_mock_field(queryset=self.queryset)
        field.output_format = "unknown"

        result = field.to_representation(self.user)

        self.assertEqual(result["id"], self.user.pk)

    def test_to_representation_falls_back_to_string_without_serializer(self):
        field = create_mock_field(queryset=self.queryset)
        field.output_format = "unknown"
        field.serializer_class = None

        result = field.to_representation(self.user)

        self.assertEqual(result, str(self.user))

    def test_to_internal_value_with_slug_only_string(self):
        group = Group.objects.create(name="engineering")
        field = create_mock_field(
            queryset=Group.objects.all(),
            input_formats=["slug"],
            slug_lookup_field="name",
        )

        result = field.to_internal_value("engineering")

        self.assertEqual(result, group)

    def test_to_internal_value_with_id_only_string(self):
        group = Group.objects.create(name="ops")
        field = create_mock_field(
            queryset=Group.objects.all(),
            input_formats=["id"],
        )

        result = field.to_internal_value(str(group.pk))

        self.assertEqual(result, group)

    def test_to_internal_value_returns_object_when_object_input_enabled(self):
        field = create_mock_field(queryset=self.queryset, input_formats=["object"])

        result = field.to_internal_value(self.user)

        self.assertEqual(result, self.user)

    def test_to_internal_value_rejects_incorrect_type(self):
        field = create_mock_field(queryset=self.queryset, input_formats=["id"])
        field.error_messages = {"incorrect_type": "Incorrect type."}

        with self.assertRaises(Exception):
            field.to_internal_value(["bad-type"])

    def test_string_id_or_slug_reraises_first_validation_error_when_both_fail(self):
        field = create_mock_field(
            queryset=Group.objects.all(),
            input_formats=["id", "slug"],
            slug_lookup_field="name",
        )

        first_error = serializers.ValidationError("id lookup failed")
        second_error = serializers.ValidationError("slug lookup failed")

        with patch.object(
            field,
            "_get_string_resolution_handlers",
            return_value=(MagicMock(side_effect=first_error), MagicMock(side_effect=second_error)),
        ):
            with self.assertRaises(serializers.ValidationError) as exc:
                field._handle_string_id_or_slug_input("missing")

        self.assertEqual(exc.exception.detail, first_error.detail)

    def test_handle_nested_input_rejects_when_nested_creation_disabled(self):
        field = create_mock_field(
            queryset=self.queryset,
            input_formats=["nested"],
            create_if_nested=False,
        )

        with self.assertRaises(Exception):
            field._handle_nested_input({"username": "nested-user"})

    def test_handle_nested_input_continues_when_existing_object_missing(self):
        field = create_mock_field(
            queryset=self.queryset,
            input_formats=["nested"],
            create_if_nested=True,
            update_if_exists=True,
            lookup_field="username",
        )
        serializer = Mock()
        serializer.is_valid.return_value = True
        field.serializer_class = Mock(return_value=serializer)
        field.queryset.get = Mock(side_effect=field.queryset.model.DoesNotExist)

        result = field._handle_nested_input({"username": "missing-user"})

        self.assertIsInstance(result, DeferredRelatedOperation)
        field.serializer_class.assert_called_once_with(
            None,
            data={"username": "missing-user"},
            partial=False,
            context=field.context,
        )

    def test_handle_nested_input_raises_validation_error_for_invalid_serializer(self):
        field = create_mock_field(
            queryset=self.queryset,
            input_formats=["nested"],
            create_if_nested=True,
            lookup_field="username",
        )
        serializer = Mock()
        serializer.is_valid.return_value = False
        serializer.errors = {"username": ["required"]}
        field.serializer_class = Mock(return_value=serializer)

        with self.assertRaises(serializers.ValidationError) as exc:
            field._handle_nested_input({"username": "invalid"})

        self.assertEqual(exc.exception.detail, {"username": ["required"]})

    def test_handle_id_input_invalid_lookup_field_raises_validation_error(self):
        field = create_mock_field(queryset=self.queryset, input_formats=["id"])
        field.queryset.get = Mock(side_effect=FieldError("bad field"))

        with self.assertRaises(serializers.ValidationError) as exc:
            field._handle_id_input(self.user.pk)

        self.assertIn("Invalid lookup_field", str(exc.exception))

    def test_handle_id_input_invalid_type_raises_field_error(self):
        field = create_mock_field(queryset=self.queryset, input_formats=["id"])
        field.error_messages = {"incorrect_type": "Incorrect type."}
        field.queryset.get = Mock(side_effect=ValueError("invalid"))

        with self.assertRaises(Exception):
            field._handle_id_input("not-an-id")

    def test_handle_slug_input_missing_value_raises_does_not_exist(self):
        field = create_mock_field(
            queryset=self.queryset,
            input_formats=["slug"],
            slug_lookup_field="username",
        )
        field.error_messages = {"does_not_exist": "Object does not exist."}

        with self.assertRaises(Exception):
            field._handle_slug_input("missing-user")


class RelatedFieldRelationWriteMixinTests(SerializerTestCase):
    """Tests for RelatedFieldRelationWriteMixin."""

    def _mixin(self, relation_kind="fk", sync_mode="append", child_link_field=None):
        mixin = RelatedFieldRelationWriteMixin()
        mixin._resolved_relation_write = {
            "relation_kind": relation_kind,
            "sync_mode": sync_mode,
            "child_link_field": child_link_field,
            "write_order": "root_first",
        }
        mixin._get_source_attr = MagicMock(return_value="items")
        mixin._bound_model_field = MagicMock()
        mixin._bound_model_field.field.null = True
        mixin.field_name = "items"
        return mixin

    def test_contains_deferred_related_true_for_deferred_operation(self):
        mixin = RelatedFieldRelationWriteMixin()
        op = DeferredRelatedOperation(field=MagicMock(), serializer=MagicMock())
        self.assertTrue(mixin.contains_deferred_related(op))

    def test_contains_deferred_related_true_for_list_with_deferred(self):
        mixin = RelatedFieldRelationWriteMixin()
        op = DeferredRelatedOperation(field=MagicMock(), serializer=MagicMock())
        self.assertTrue(mixin.contains_deferred_related([op]))

    def test_contains_deferred_related_false_for_plain_value(self):
        mixin = RelatedFieldRelationWriteMixin()
        self.assertFalse(mixin.contains_deferred_related("plain_value"))

    def test_resolve_related_value_resolves_list(self):
        mixin = RelatedFieldRelationWriteMixin()
        op = DeferredRelatedOperation(field=MagicMock(), serializer=MagicMock())
        op_resolved = MagicMock()
        with patch.object(op, "resolve", return_value=op_resolved):
            result = mixin.resolve_related_value([op])
        self.assertEqual(result, [op_resolved])

    def test_apply_root_first_relation_fk_sets_attribute_and_saves(self):
        mixin = self._mixin(relation_kind="fk")
        parent = MagicMock()
        parent.pk = 1
        resolved = MagicMock()
        mixin.apply_root_first_relation(parent, resolved)
        parent.save.assert_called_once()

    def test_apply_root_first_relation_reverse_fk_missing_child_link_raises(self):
        mixin = self._mixin(relation_kind="reverse_fk", child_link_field=None)
        with self.assertRaises(serializers.ValidationError):
            mixin.apply_root_first_relation(MagicMock(), MagicMock())

    def test_apply_root_first_relation_reverse_fk_links_and_saves_children(self):
        mixin = self._mixin(relation_kind="reverse_fk", child_link_field="parent")
        parent = MagicMock()
        parent.pk = 99
        child = MagicMock()
        child.parent_id = None
        mixin.apply_root_first_relation(parent, [child])
        child.save.assert_called_once()

    def test_apply_root_first_relation_m2m_replace_calls_set(self):
        mixin = self._mixin(relation_kind="m2m", sync_mode="replace")
        manager = MagicMock()
        parent = MagicMock(**{"items": manager})
        resolved = [MagicMock(), MagicMock()]
        mixin.apply_root_first_relation(parent, resolved)
        manager.set.assert_called_once_with(resolved)

    def test_apply_root_first_relation_m2m_append_calls_add(self):
        mixin = self._mixin(relation_kind="m2m", sync_mode="append")
        parent = MagicMock()
        manager = MagicMock()
        setattr(parent, "items", manager)
        resolved = [MagicMock()]
        mixin.apply_root_first_relation(parent, resolved)
        manager.add.assert_called_once()

    def test_save_deferred_serializer_raises_when_reverse_fk_missing_child_link(self):
        mixin = self._mixin(relation_kind="reverse_fk", child_link_field=None)
        nested_serializer = MagicMock()
        with self.assertRaises(serializers.ValidationError):
            mixin._save_deferred_serializer(nested_serializer, parent_instance=MagicMock())
