"""
Content-related mixins for model functionality.

This module contains mixins that provide content-related features
like slug generation, metadata storage, and version tracking.
"""

from typing import Any, List

from django.db import models
from django.utils.text import slugify


class SlugMixin(models.Model):
    """
    Mixin that provides automatic slug generation functionality.
    
    Automatically generates a URL-friendly slug from a specified source field.
    The slug is unique and can be used in URLs for SEO-friendly routing.
    
    Attributes:
        slug: URL-friendly string generated from source field
    """
    
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        help_text="URL-friendly version of the title/name"
    )
    
    class Meta:
        abstract = True
    
    def get_slug_source(self) -> str:
        """
        Get the source field value for slug generation.
        
        Override this method in subclasses to specify which field
        should be used as the source for slug generation.
        
        Returns:
            String value to generate slug from
            
        Raises:
            NotImplementedError: If not implemented in subclass
        """
        raise NotImplementedError("Subclasses must implement get_slug_source()")
    
    def generate_slug(self) -> str:
        """
        Generate a unique slug from the source field.
        
        Returns:
            Generated unique slug string
        """
        base_slug = slugify(self.get_slug_source())
        slug = base_slug
        counter = 1
        
        # Ensure uniqueness by appending counter if needed
        while self.__class__.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
            
        return slug
    
    def save(self, *args, **kwargs) -> None:
        """
        Override save to automatically generate slug if not provided.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        if not self.slug:
            self.slug = self.generate_slug()
        super().save(*args, **kwargs)


class MetaMixin(models.Model):
    """
    Mixin that provides metadata fields for storing additional information.
    
    Useful for storing configuration, settings, or any additional data
    that doesn't warrant separate fields.
    
    Attributes:
        metadata: JSON field for storing arbitrary metadata
        tags: Comma-separated tags for categorization
        notes: Text field for additional notes or comments
    """
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata stored as JSON"
    )
    tags = models.CharField(
        max_length=500,
        blank=True,
        help_text="Comma-separated tags for categorization"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes or comments"
    )
    
    class Meta:
        abstract = True
    
    def get_tags_list(self) -> List[str]:
        """
        Get tags as a list of strings.
        
        Returns:
            List of tag strings, empty list if no tags
        """
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
    
    def add_tag(self, tag: str) -> None:
        """
        Add a tag to the existing tags.
        
        Args:
            tag: Tag string to add
        """
        current_tags = self.get_tags_list()
        if tag not in current_tags:
            current_tags.append(tag)
            self.tags = ', '.join(current_tags)
    
    def remove_tag(self, tag: str) -> None:
        """
        Remove a tag from the existing tags.
        
        Args:
            tag: Tag string to remove
        """
        current_tags = self.get_tags_list()
        if tag in current_tags:
            current_tags.remove(tag)
            self.tags = ', '.join(current_tags)
    
    def get_metadata_value(self, key: str, default: Any = None) -> Any:
        """
        Get a specific value from metadata.
        
        Args:
            key: Metadata key to retrieve
            default: Default value if key doesn't exist
            
        Returns:
            Value from metadata or default
        """
        return self.metadata.get(key, default)
    
    def set_metadata_value(self, key: str, value: Any) -> None:
        """
        Set a specific value in metadata.
        
        Args:
            key: Metadata key to set
            value: Value to set
        """
        self.metadata[key] = value


class VersionMixin(models.Model):
    """
    Mixin that provides version tracking functionality.
    
    Tracks version numbers and revision information for model instances.
    Useful for maintaining history and implementing optimistic locking.
    
    Attributes:
        version: Current version number of the record
        revision_notes: Notes about changes in current version
    """
    
    version = models.PositiveIntegerField(
        default=1,
        help_text="Current version number of this record"
    )
    revision_notes = models.TextField(
        blank=True,
        help_text="Notes about changes made in this version"
    )
    
    class Meta:
        abstract = True
    
    def increment_version(self, notes: str = "") -> None:
        """
        Increment the version number and optionally add revision notes.
        
        Args:
            notes: Optional notes about the changes made
        """
        self.version += 1
        if notes:
            self.revision_notes = notes
    
    def save(self, *args, **kwargs) -> None:
        """
        Override save to handle version incrementing for existing records.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        if self.pk and not kwargs.get('skip_version_increment', False):
            # Only increment version for updates, not creates
            original = self.__class__.objects.get(pk=self.pk)
            if original.version == self.version:
                self.increment_version()
        
        # Remove our custom kwarg before calling super
        kwargs.pop('skip_version_increment', None)
        super().save(*args, **kwargs)