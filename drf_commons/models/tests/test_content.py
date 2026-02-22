"""
Tests for content-related mixins.
"""

from unittest.mock import Mock, patch

from django.db import models
from django.utils.text import slugify

from drf_commons.common_tests.base_cases import ModelTestCase

from ..content import MetaMixin, SlugMixin, VersionConflictError, VersionMixin


class SlugModelForTesting(SlugMixin):
    """Test model using SlugMixin."""

    class Meta:
        app_label = "drf_commons"

    title = models.CharField(max_length=100)

    def get_slug_source(self):
        return self.title


class MetaModelForTesting(MetaMixin):
    """Test model using MetaMixin."""

    class Meta:
        app_label = "drf_commons"

    name = models.CharField(max_length=100)


class VersionModelForTesting(VersionMixin):
    """Test model using VersionMixin."""

    class Meta:
        app_label = "drf_commons"

    name = models.CharField(max_length=100)


class SlugMixinTests(ModelTestCase):
    """Tests for SlugMixin."""

    def test_mixin_fields_exist(self):
        """Test that SlugMixin adds slug field."""
        model = SlugModelForTesting()

        self.assertTrue(hasattr(model, "slug"))

    def test_slug_field_properties(self):
        """Test slug field properties."""
        field = SlugModelForTesting._meta.get_field("slug")

        self.assertIsInstance(field, models.SlugField)
        self.assertEqual(field.max_length, 255)
        self.assertTrue(field.unique)
        self.assertTrue(field.blank)

    def test_get_slug_source_not_implemented(self):
        """Test get_slug_source raises NotImplementedError in base class."""

        class BadSlugModel(SlugMixin):
            class Meta:
                app_label = "drf_commons"

        model = BadSlugModel()

        with self.assertRaises(NotImplementedError):
            model.get_slug_source()

    def test_get_slug_source_implementation(self):
        """Test get_slug_source returns title."""
        model = SlugModelForTesting(title="Test Title")

        result = model.get_slug_source()

        self.assertEqual(result, "Test Title")

    @patch.object(SlugModelForTesting.objects, "filter")
    def test_generate_slug_basic(self, mock_filter):
        """Test generate_slug creates basic slug."""
        mock_queryset = Mock()
        mock_queryset.exclude.return_value.exists.return_value = False
        mock_filter.return_value = mock_queryset

        model = SlugModelForTesting(title="Test Title")

        slug = model.generate_slug()

        self.assertEqual(slug, "test-title")

    def test_generate_slug_with_conflicts(self):
        """Test generate_slug handles conflicts with counter."""
        SlugModelForTesting.objects.create(title="Other Title", slug="test-title")
        SlugModelForTesting.objects.create(title="Another Title", slug="test-title-1")

        model = SlugModelForTesting(title="Test Title")
        slug = model.generate_slug()

        self.assertEqual(slug, "test-title-2")

    def test_generate_slug_excludes_current_instance(self):
        """Test generate_slug excludes current instance from conflict check."""
        existing = SlugModelForTesting.objects.create(title="Other Title", slug="test-title")

        # Create a new instance with the same title and set its pk to the existing one
        model = SlugModelForTesting(title="Test Title", pk=existing.pk)

        # Should generate the same slug since it excludes itself
        slug = model.generate_slug()

        self.assertEqual(slug, "test-title")

    def test_save_generates_slug_when_empty(self):
        """Test save generates slug when not provided."""
        model = SlugModelForTesting(title="Test Title")

        with patch.object(
            model, "generate_slug", return_value="test-slug"
        ) as mock_generate:
            with patch("django.db.models.Model.save") as mock_super_save:
                model.save()

                mock_generate.assert_called_once()
                self.assertEqual(model.slug, "test-slug")
                mock_super_save.assert_called_once()

    def test_save_preserves_existing_slug(self):
        """Test save preserves existing slug."""
        model = SlugModelForTesting(title="Test Title", slug="existing-slug")

        with patch.object(model, "generate_slug") as mock_generate:
            with patch("django.db.models.Model.save"):
                model.save()

                mock_generate.assert_not_called()
                self.assertEqual(model.slug, "existing-slug")

    def test_slug_generation_with_special_characters(self):
        """Test slug generation handles special characters."""
        model = SlugModelForTesting(title="Test & Title with Spëcial Chars!")

        with patch.object(SlugModelForTesting.objects, "filter") as mock_filter:
            mock_queryset = Mock()
            mock_queryset.exclude.return_value.exists.return_value = False
            mock_filter.return_value = mock_queryset

            slug = model.generate_slug()

            self.assertEqual(slug, slugify("Test & Title with Spëcial Chars!"))

    def test_slug_generation_with_empty_source(self):
        """Test slug generation handles empty source."""
        model = SlugModelForTesting(title="")

        with patch.object(SlugModelForTesting.objects, "filter") as mock_filter:
            mock_queryset = Mock()
            mock_queryset.exclude.return_value.exists.return_value = False
            mock_filter.return_value = mock_queryset

            slug = model.generate_slug()

            self.assertEqual(slug, "")

    def test_help_text_is_descriptive(self):
        """Test that slug field has descriptive help text."""
        field = SlugModelForTesting._meta.get_field("slug")

        self.assertIn("URL-friendly", field.help_text)


class MetaMixinTests(ModelTestCase):
    """Tests for MetaMixin."""

    def test_mixin_fields_exist(self):
        """Test that MetaMixin adds metadata fields."""
        model = MetaModelForTesting()

        self.assertTrue(hasattr(model, "metadata"))
        self.assertTrue(hasattr(model, "tags"))
        self.assertTrue(hasattr(model, "notes"))

    def test_metadata_field_properties(self):
        """Test metadata field properties."""
        field = MetaModelForTesting._meta.get_field("metadata")

        self.assertIsInstance(field, models.JSONField)
        self.assertEqual(field.default, dict)
        self.assertTrue(field.blank)

    def test_tags_field_properties(self):
        """Test tags field properties."""
        field = MetaModelForTesting._meta.get_field("tags")

        self.assertIsInstance(field, models.CharField)
        self.assertEqual(field.max_length, 500)
        self.assertTrue(field.blank)

    def test_notes_field_properties(self):
        """Test notes field properties."""
        field = MetaModelForTesting._meta.get_field("notes")

        self.assertIsInstance(field, models.TextField)
        self.assertTrue(field.blank)

    def test_get_tags_list_empty(self):
        """Test get_tags_list returns empty list for no tags."""
        model = MetaModelForTesting(tags="")

        result = model.get_tags_list()

        self.assertEqual(result, [])

    def test_get_tags_list_none(self):
        """Test get_tags_list returns empty list for None tags."""
        model = MetaModelForTesting()

        result = model.get_tags_list()

        self.assertEqual(result, [])

    def test_get_tags_list_single_tag(self):
        """Test get_tags_list returns single tag."""
        model = MetaModelForTesting(tags="tag1")

        result = model.get_tags_list()

        self.assertEqual(result, ["tag1"])

    def test_get_tags_list_multiple_tags(self):
        """Test get_tags_list returns multiple tags."""
        model = MetaModelForTesting(tags="tag1, tag2, tag3")

        result = model.get_tags_list()

        self.assertEqual(result, ["tag1", "tag2", "tag3"])

    def test_get_tags_list_strips_whitespace(self):
        """Test get_tags_list strips whitespace from tags."""
        model = MetaModelForTesting(tags="  tag1  ,  tag2  ,  tag3  ")

        result = model.get_tags_list()

        self.assertEqual(result, ["tag1", "tag2", "tag3"])

    def test_get_tags_list_ignores_empty_tags(self):
        """Test get_tags_list ignores empty tags."""
        model = MetaModelForTesting(tags="tag1, , tag2, ,tag3")

        result = model.get_tags_list()

        self.assertEqual(result, ["tag1", "tag2", "tag3"])

    def test_add_tag_to_empty_tags(self):
        """Test add_tag adds first tag."""
        model = MetaModelForTesting(tags="")

        model.add_tag("new_tag")

        self.assertEqual(model.tags, "new_tag")

    def test_add_tag_to_existing_tags(self):
        """Test add_tag adds to existing tags."""
        model = MetaModelForTesting(tags="existing_tag")

        model.add_tag("new_tag")

        self.assertEqual(model.tags, "existing_tag, new_tag")

    def test_add_tag_duplicate(self):
        """Test add_tag ignores duplicate tags."""
        model = MetaModelForTesting(tags="existing_tag")

        model.add_tag("existing_tag")

        self.assertEqual(model.tags, "existing_tag")

    def test_remove_tag_existing(self):
        """Test remove_tag removes existing tag."""
        model = MetaModelForTesting(tags="tag1, tag2, tag3")

        model.remove_tag("tag2")

        self.assertEqual(model.tags, "tag1, tag3")

    def test_remove_tag_nonexistent(self):
        """Test remove_tag ignores nonexistent tag."""
        model = MetaModelForTesting(tags="tag1, tag2")

        model.remove_tag("nonexistent")

        self.assertEqual(model.tags, "tag1, tag2")

    def test_remove_tag_single(self):
        """Test remove_tag removes single tag."""
        model = MetaModelForTesting(tags="single_tag")

        model.remove_tag("single_tag")

        self.assertEqual(model.tags, "")

    def test_get_metadata_value_existing(self):
        """Test get_metadata_value returns existing value."""
        model = MetaModelForTesting(metadata={"key": "value"})

        result = model.get_metadata_value("key")

        self.assertEqual(result, "value")

    def test_get_metadata_value_nonexistent_no_default(self):
        """Test get_metadata_value returns None for nonexistent key."""
        model = MetaModelForTesting(metadata={})

        result = model.get_metadata_value("nonexistent")

        self.assertIsNone(result)

    def test_get_metadata_value_nonexistent_with_default(self):
        """Test get_metadata_value returns default for nonexistent key."""
        model = MetaModelForTesting(metadata={})

        result = model.get_metadata_value("nonexistent", "default_value")

        self.assertEqual(result, "default_value")

    def test_set_metadata_value_new(self):
        """Test set_metadata_value sets new value."""
        model = MetaModelForTesting(metadata={})

        model.set_metadata_value("key", "value")

        self.assertEqual(model.metadata["key"], "value")

    def test_set_metadata_value_existing(self):
        """Test set_metadata_value overwrites existing value."""
        model = MetaModelForTesting(metadata={"key": "old_value"})

        model.set_metadata_value("key", "new_value")

        self.assertEqual(model.metadata["key"], "new_value")

    def test_set_metadata_value_complex(self):
        """Test set_metadata_value handles complex values."""
        model = MetaModelForTesting(metadata={})
        complex_value = {"nested": {"data": [1, 2, 3]}}

        model.set_metadata_value("complex", complex_value)

        self.assertEqual(model.metadata["complex"], complex_value)

    def test_help_text_is_descriptive(self):
        """Test that metadata fields have descriptive help text."""
        metadata_field = MetaModelForTesting._meta.get_field("metadata")
        tags_field = MetaModelForTesting._meta.get_field("tags")
        notes_field = MetaModelForTesting._meta.get_field("notes")

        self.assertIn("metadata", metadata_field.help_text.lower())
        self.assertIn("tags", tags_field.help_text.lower())
        self.assertIn("notes", notes_field.help_text.lower())


class VersionMixinTests(ModelTestCase):
    """Tests for VersionMixin."""

    def test_mixin_fields_exist(self):
        """Test that VersionMixin adds version fields."""
        model = VersionModelForTesting()

        self.assertTrue(hasattr(model, "version"))
        self.assertTrue(hasattr(model, "revision_notes"))

    def test_version_field_properties(self):
        """Test version field properties."""
        field = VersionModelForTesting._meta.get_field("version")

        self.assertIsInstance(field, models.PositiveIntegerField)
        self.assertEqual(field.default, 1)

    def test_revision_notes_field_properties(self):
        """Test revision_notes field properties."""
        field = VersionModelForTesting._meta.get_field("revision_notes")

        self.assertIsInstance(field, models.TextField)
        self.assertTrue(field.blank)

    def test_default_version_is_one(self):
        """Test that default version is 1."""
        model = VersionModelForTesting()

        self.assertEqual(model.version, 1)

    def test_increment_version_without_notes(self):
        """Test increment_version increases version."""
        model = VersionModelForTesting()
        original_version = model.version

        model.increment_version()

        self.assertEqual(model.version, original_version + 1)

    def test_increment_version_with_notes(self):
        """Test increment_version increases version and sets notes."""
        model = VersionModelForTesting()
        original_version = model.version

        model.increment_version("Updated with new features")

        self.assertEqual(model.version, original_version + 1)
        self.assertEqual(model.revision_notes, "Updated with new features")

    def test_increment_version_empty_notes(self):
        """Test increment_version with empty notes doesn't change revision_notes."""
        model = VersionModelForTesting(revision_notes="Old notes")
        original_version = model.version

        model.increment_version("")

        self.assertEqual(model.version, original_version + 1)
        self.assertEqual(model.revision_notes, "Old notes")

    def test_save_increments_version_for_updates(self):
        """Test save increments version for existing records."""
        original = VersionModelForTesting.objects.create(name="test", version=1)

        # Create a new instance with the same pk and version
        model = VersionModelForTesting(pk=original.pk, version=1, name="updated test")

        with patch("django.db.models.Model.save") as mock_super_save:
            model.save()

            self.assertEqual(model.version, 2)
            mock_super_save.assert_not_called()
            original.refresh_from_db()
            self.assertEqual(original.version, 2)
            self.assertEqual(original.name, "updated test")

    def test_save_does_not_increment_version_for_creates(self):
        """Test save does not increment version for new records."""
        model = VersionModelForTesting(name="test")

        with patch("django.db.models.Model.save") as mock_super_save:
            model.save()

            self.assertEqual(model.version, 1)
            mock_super_save.assert_called_once()

    def test_save_raises_version_conflict_when_version_changed(self):
        """Test save raises conflict when provided version is stale."""
        original = VersionModelForTesting.objects.create(name="test", version=1)

        # Create a new instance with the same pk but different version (simulating concurrent update)
        model = VersionModelForTesting(pk=original.pk, version=2, name="updated test")

        with self.assertRaises(VersionConflictError):
            model.save()

    def test_save_with_skip_version_increment(self):
        """Test save with skip_version_increment kwarg."""
        model = VersionModelForTesting(pk=1, version=1, name="test")

        with patch.object(VersionModelForTesting.objects, "get") as mock_get:
            with patch("django.db.models.Model.save"):
                model.save(skip_version_increment=True)

                mock_get.assert_not_called()
                self.assertEqual(model.version, 1)

    def test_save_removes_skip_version_increment_kwarg(self):
        """Test save removes skip_version_increment from kwargs before calling super."""
        model = VersionModelForTesting(name="test")

        with patch("django.db.models.Model.save") as mock_super_save:
            model.save(skip_version_increment=True, other_kwarg="value")

            mock_super_save.assert_called_once_with(other_kwarg="value")

    def test_help_text_is_descriptive(self):
        """Test that version fields have descriptive help text."""
        version_field = VersionModelForTesting._meta.get_field("version")
        notes_field = VersionModelForTesting._meta.get_field("revision_notes")

        self.assertIn("version", version_field.help_text.lower())
        self.assertIn("version", notes_field.help_text.lower())
