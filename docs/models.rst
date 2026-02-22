Model Mixins
============

drf-commons provides a comprehensive suite of Django model mixins. Each mixin
addresses a specific concern and can be composed freely with others.

Base Mixins
-----------

BaseModelMixin
~~~~~~~~~~~~~~

.. code-block:: python

   from drf_commons.models import BaseModelMixin

The canonical base model for drf-commons projects. Composes:

* :class:`~drf_commons.models.mixins.JsonModelMixin`
* :class:`~drf_commons.models.base.UserActionMixin`
* :class:`~drf_commons.models.base.TimeStampMixin`
* :class:`~drf_commons.models.base.SoftDeleteMixin`
* ``models.Model``

**Fields provided**:

.. list-table::
   :widths: 20 15 65
   :header-rows: 1

   * - Field
     - Type
     - Description
   * - ``id``
     - ``UUIDField``
     - Primary key, auto-generated, non-editable
   * - ``created_at``
     - ``DateTimeField``
     - Set on creation, never modified (``auto_now_add=True``)
   * - ``updated_at``
     - ``DateTimeField``
     - Updated on every save (``auto_now=True``)
   * - ``created_by``
     - ``ForeignKey(User)``
     - Populated from context user on first save
   * - ``updated_by``
     - ``ForeignKey(User)``
     - Populated from context user on every save
   * - ``is_active``
     - ``BooleanField``
     - Soft delete flag; ``True`` means record is live
   * - ``deleted_at``
     - ``DateTimeField``
     - Timestamp of soft deletion; ``null`` when active

**Usage**:

.. code-block:: python

   from django.db import models
   from drf_commons.models import BaseModelMixin

   class Invoice(BaseModelMixin):
       number = models.CharField(max_length=64, unique=True)
       total = models.DecimalField(max_digits=12, decimal_places=2)

       class Meta:
           ordering = ["-created_at"]

TimeStampMixin
~~~~~~~~~~~~~~

.. code-block:: python

   from drf_commons.models.base import TimeStampMixin

Adds ``created_at`` and ``updated_at`` fields with automatic population.
Use when you need timestamping without the full ``BaseModelMixin`` stack.

UserActionMixin
~~~~~~~~~~~~~~~

.. code-block:: python

   from drf_commons.models.base import UserActionMixin

Adds ``created_by`` and ``updated_by`` ForeignKey fields. Overrides
``save()`` to auto-populate these fields from the current context user.

The implementation:

* Sets ``created_by`` **only** on the first save (``pk is None`` check)
* Always updates ``updated_by`` on every save
* Calls ``get_current_authenticated_user()`` — raises if no authenticated user

.. important::

   ``UserActionMixin`` requires ``CurrentUserMiddleware`` to be installed.
   The application will raise ``ImproperlyConfigured`` at startup if this
   middleware is missing.

SoftDeleteMixin
~~~~~~~~~~~~~~~

.. code-block:: python

   from drf_commons.models.base import SoftDeleteMixin

Adds non-destructive deletion with restore capability.

**Fields**: ``is_active`` (BooleanField), ``deleted_at`` (DateTimeField)

**Methods**:

.. code-block:: python

   instance.soft_delete()   # is_active=False, deleted_at=timezone.now()
   instance.restore()       # is_active=True, deleted_at=None

**Property**:

.. code-block:: python

   instance.is_deleted      # returns not self.is_active

JsonModelMixin
~~~~~~~~~~~~~~

.. code-block:: python

   from drf_commons.models.mixins import JsonModelMixin

Provides ``get_json()`` for flexible model-to-JSON serialization.

**Signature**:

.. code-block:: python

   instance.get_json(
       fields: list = None,          # Explicit field inclusion list
       exclude_fields: list = None,  # Explicit field exclusion list
       exclude_audit: bool = False,  # Exclude audit fields
   ) -> str

**Examples**:

.. code-block:: python

   # All fields
   article.get_json()

   # Specific fields only
   article.get_json(fields=["id", "title", "published"])

   # Exclude audit trail fields
   article.get_json(exclude_audit=True)

   # Exclude specific fields
   article.get_json(exclude_fields=["content", "deleted_at"])

Content Mixins
--------------

SlugMixin
~~~~~~~~~

.. code-block:: python

   from drf_commons.models.content import SlugMixin

Auto-generates URL-safe slug values with deterministic collision avoidance.
Subclasses must implement ``get_slug_source()`` returning the string to slugify.

**Fields**: ``slug`` (SlugField, unique)

**Abstract method required**:

.. code-block:: python

   class Category(BaseModelMixin, SlugMixin):
       name = models.CharField(max_length=255)

       def get_slug_source(self):
           return self.name

Generated slugs:

* ``"Product Category"`` → ``"product-category"``
* ``"Product Category"`` (collision) → ``"product-category-1"``
* ``"Product Category"`` (collision) → ``"product-category-2"``

MetaMixin
~~~~~~~~~

.. code-block:: python

   from drf_commons.models.content import MetaMixin

Provides structured metadata, tagging, and notes on any model.

**Fields**:

.. list-table::
   :widths: 20 20 60
   :header-rows: 1

   * - Field
     - Type
     - Description
   * - ``metadata``
     - ``JSONField``
     - Arbitrary JSON key-value store
   * - ``tags``
     - ``CharField``
     - Comma-separated tag string
   * - ``notes``
     - ``TextField``
     - Free-form text notes

**Methods**:

.. code-block:: python

   obj.get_tags_list()                      # ["tag1", "tag2"]
   obj.add_tag("featured")                  # Adds tag if not present
   obj.remove_tag("featured")               # Removes tag
   obj.get_metadata_value("color")          # Returns value or None
   obj.set_metadata_value("color", "blue")  # Sets key in metadata dict

VersionMixin
~~~~~~~~~~~~

.. code-block:: python

   from drf_commons.models.content import VersionMixin

Implements optimistic locking. Raises
:class:`~drf_commons.models.content.VersionConflictError` when a concurrent
write is detected.

**Fields**:

.. list-table::
   :widths: 20 20 60
   :header-rows: 1

   * - Field
     - Type
     - Description
   * - ``version``
     - ``PositiveIntegerField``
     - Current version number (starts at 1)
   * - ``revision_notes``
     - ``TextField``
     - Optional change description for this version

**Usage**:

.. code-block:: python

   class Document(BaseModelMixin, VersionMixin):
       body = models.TextField()

   # Increment before saving a new version
   doc.revision_notes = "Updated introduction section."
   doc.increment_version()
   doc.save()

   # On concurrent modification:
   # Raises VersionConflictError

Person Mixins
-------------

IdentityMixin
~~~~~~~~~~~~~

.. code-block:: python

   from drf_commons.models.person import IdentityMixin

Provides standard personal identity fields with computed properties.

**Fields**: ``first_name``, ``last_name``, ``middle_name``, ``email``,
``phone``, ``date_of_birth``, ``birth_place``, ``gender``, ``nationality``

**Gender choices**: ``MALE``, ``FEMALE``, ``OTHER``, ``PREFER_NOT_TO_SAY``

**Properties**:

.. code-block:: python

   person.full_name    # "Jane Doe" (first_name + last_name)
   person.initials     # "J.D."
   person.age          # Calculated from date_of_birth

AddressMixin
~~~~~~~~~~~~

.. code-block:: python

   from drf_commons.models.person import AddressMixin

Provides structured postal address fields with coordinate support.

**Fields**: ``street_address``, ``street_address_2``, ``city``,
``state_province``, ``postal_code``, ``country``, ``latitude``, ``longitude``

**Properties and methods**:

.. code-block:: python

   address.full_address       # "123 Main St, New York, NY 10001, US"
   address.short_address      # "New York, NY, US"
   address.has_coordinates    # True if lat/lon both set
   address.get_coordinates()  # (lat, lon) tuple or None

Model Fields
------------

CurrentUserField
~~~~~~~~~~~~~~~~

.. code-block:: python

   from drf_commons.models.fields import CurrentUserField

A ``ForeignKey`` subclass that auto-populates itself with the current
authenticated user. Suitable for models where the relation must always reflect
who performed the action.

**Parameters**:

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Parameter
     - Description
   * - ``on_update``
     - If ``True``, updates the field on every ``save()`` call. Default: ``False``

**Example**:

.. code-block:: python

   class Comment(models.Model):
       article = models.ForeignKey(Article, on_delete=models.CASCADE)
       body = models.TextField()
       # Populated automatically from CurrentUserMiddleware
       author = CurrentUserField(on_update=False)  # Set only on creation

.. note::

   ``CurrentUserField`` with ``on_update=False`` behaves like ``created_by``
   in ``UserActionMixin`` — set once and never changed. With ``on_update=True``
   it mirrors ``updated_by`` behavior.

Mixin Composition Examples
--------------------------

Not all models need the full ``BaseModelMixin`` stack. Compose exactly what you
need:

.. code-block:: python

   from django.db import models
   from drf_commons.models.base import TimeStampMixin, SoftDeleteMixin
   from drf_commons.models.content import MetaMixin

   # Timestamped + soft-deletable + taggable, no user tracking
   class Tag(TimeStampMixin, SoftDeleteMixin, MetaMixin, models.Model):
       name = models.CharField(max_length=64, unique=True)

.. code-block:: python

   from drf_commons.models.base import TimeStampMixin
   from drf_commons.models.content import VersionMixin

   # Versioned document with timestamps only
   class Policy(TimeStampMixin, VersionMixin, models.Model):
       title = models.CharField(max_length=255)
       body = models.TextField()
