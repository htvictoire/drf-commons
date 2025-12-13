"""
Tests for CRUD operation mixins.

Tests basic CRUD mixins functionality.
"""

from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model


from drf_commons.common_tests.base_cases import ViewTestCase
from drf_commons.common_tests.factories import UserFactory

from ..crud import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)

User = get_user_model()


class CreateModelMixinTests(ViewTestCase):
    """Tests for CreateModelMixin."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    def test_create_mixin_default_attributes(self):
        """Test CreateModelMixin default attributes."""
        mixin = CreateModelMixin()
        self.assertFalse(mixin.return_data_on_create)

    def test_create_mixin_has_create_method(self):
        """Test CreateModelMixin has create method."""
        mixin = CreateModelMixin()
        self.assertTrue(hasattr(mixin, "create"))

    def test_create_mixin_has_perform_create_method(self):
        """Test CreateModelMixin has perform_create method."""
        mixin = CreateModelMixin()
        self.assertTrue(hasattr(mixin, "perform_create"))

    def test_on_create_message_method(self):
        """Test on_create_message method."""
        mixin = CreateModelMixin()
        # Mock the get_model_name function
        with patch("views.mixins.crud.get_model_name", return_value="TestModel"):
            message = mixin.on_create_message()
            self.assertEqual(message, "TestModel created successfully")

    def test_perform_create_calls_serializer_save(self):
        """Test perform_create calls serializer.save()."""
        mixin = CreateModelMixin()
        mock_serializer = Mock()

        mixin.perform_create(mock_serializer)

        mock_serializer.save.assert_called_once()


class ListModelMixinTests(ViewTestCase):
    """Tests for ListModelMixin."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    def test_list_mixin_default_attributes(self):
        """Test ListModelMixin default attributes."""
        mixin = ListModelMixin()
        self.assertTrue(mixin.append_indexes)

    def test_list_mixin_has_list_method(self):
        """Test ListModelMixin has list method."""
        mixin = ListModelMixin()
        self.assertTrue(hasattr(mixin, "list"))


class RetrieveModelMixinTests(ViewTestCase):
    """Tests for RetrieveModelMixin."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    def test_retrieve_mixin_has_retrieve_method(self):
        """Test RetrieveModelMixin has retrieve method."""
        mixin = RetrieveModelMixin()
        self.assertTrue(hasattr(mixin, "retrieve"))


class UpdateModelMixinTests(ViewTestCase):
    """Tests for UpdateModelMixin."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    def test_update_mixin_has_update_method(self):
        """Test UpdateModelMixin has update method."""
        mixin = UpdateModelMixin()
        self.assertTrue(hasattr(mixin, "update"))

    def test_update_mixin_has_partial_update_method(self):
        """Test UpdateModelMixin has partial_update method."""
        mixin = UpdateModelMixin()
        self.assertTrue(hasattr(mixin, "partial_update"))

    def test_update_mixin_has_perform_update_method(self):
        """Test UpdateModelMixin has perform_update method."""
        mixin = UpdateModelMixin()
        self.assertTrue(hasattr(mixin, "perform_update"))


class DestroyModelMixinTests(ViewTestCase):
    """Tests for DestroyModelMixin."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    def test_destroy_mixin_has_destroy_method(self):
        """Test DestroyModelMixin has destroy method."""
        mixin = DestroyModelMixin()
        self.assertTrue(hasattr(mixin, "destroy"))

    def test_destroy_mixin_has_perform_destroy_method(self):
        """Test DestroyModelMixin has perform_destroy method."""
        mixin = DestroyModelMixin()
        self.assertTrue(hasattr(mixin, "perform_destroy"))
