Core Concepts
=============

This page explains the foundational concepts that underpin drf-commons. A firm
understanding of these concepts is recommended before working with the more
advanced features of the library.

The Composable Mixin Pattern
----------------------------

Every drf-commons component is a mixin class. Mixins in Python are classes
designed to provide specific behavior that can be combined with other classes
through multiple inheritance. They do not stand alone — they are always mixed
into a class that inherits from a concrete base.

This pattern is used at every layer:

**Model layer**:

.. code-block:: python

   # BaseModelMixin is itself a composition of four mixins
   class BaseModelMixin(JsonModelMixin, UserActionMixin, TimeStampMixin, SoftDeleteMixin, models.Model):
       id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

**View layer**:

.. code-block:: python

   # BaseViewSet is a composition of five action mixins
   class BaseViewSet(
       CreateModelMixin,
       ListModelMixin,
       RetrieveModelMixin,
       UpdateModelMixin,
       DestroyModelMixin,
       FileExportMixin,
       GenericViewSet,
   ):
       pass

The benefit is that a developer can inspect any ViewSet class's MRO and
immediately understand its complete capability set, without reading
documentation.

Standardized Response Envelopes
--------------------------------

All drf-commons responses follow a consistent JSON structure. This is a
**contract** between the API server and its clients.

**Success response**:

.. code-block:: json

   {
     "success": true,
     "timestamp": "2024-01-15T10:30:00.000000Z",
     "message": "Operation completed successfully.",
     "data": { ... }
   }

**Error response**:

.. code-block:: json

   {
     "success": false,
     "timestamp": "2024-01-15T10:30:00.000000Z",
     "message": "Validation failed.",
     "errors": {
       "title": ["This field may not be blank."]
     },
     "data": null
   }

The ``timestamp`` field is always an ISO 8601 UTC string, enabling
deterministic client-side parsing without timezone ambiguity.

Context-Local User Resolution
-------------------------------

The ``current_user`` subsystem uses Python's :class:`contextvars.ContextVar`
to make the authenticated request user available anywhere in the call stack
without explicitly passing it as a function argument.

This is particularly valuable at the model layer, where ``UserActionMixin``
auto-populates ``created_by`` and ``updated_by`` on every ``save()`` call.
Without this mechanism, every serializer would need to extract the user from
``self.context['request']`` and pass it into the validated data.

The lifecycle:

1. ``CurrentUserMiddleware`` receives a request
2. Calls ``_set_current_user(request.user)``, storing the user in ``ContextVar``
3. Returns a reset token
4. The request handler executes (model saves, service calls, etc.)
5. Model's ``save()`` calls ``get_current_authenticated_user()``
6. ``CurrentUserMiddleware`` calls ``_reset_current_user(token)`` in ``finally``

The use of reset tokens (rather than simply calling ``clear()``) ensures
correct behavior when middleware is nested or when context is inherited by
spawned coroutines.

Soft Deletion
-------------

Soft deletion is the pattern of marking a record as deleted rather than
issuing a ``DELETE`` SQL statement. The record remains in the database and can
be restored. :class:`~drf_commons.models.base.SoftDeleteMixin` implements this
with two fields:

* ``is_active`` — boolean flag; ``True`` means the record is live
* ``deleted_at`` — timestamp of when the soft delete occurred

.. code-block:: python

   instance.soft_delete()   # sets is_active=False, deleted_at=now()
   instance.restore()       # sets is_active=True, deleted_at=None
   instance.is_deleted      # property; returns not is_active

The application convention is to always filter querysets with
``filter(is_active=True)`` in viewsets. drf-commons does not apply this filter
automatically — it is the developer's responsibility to define the correct
queryset scope.

.. code-block:: python

   class ArticleViewSet(BaseViewSet):
       queryset = Article.objects.filter(is_active=True)  # correct

Optimistic Locking
------------------

:class:`~drf_commons.models.content.VersionMixin` implements optimistic
locking. Every record carries a ``version`` integer. When two concurrent
processes attempt to modify the same record:

* Process A reads version 5, modifies, attempts to write version 6
* Process B reads version 5, modifies, attempts to write version 6
* Process A commits: ``UPDATE ... WHERE version=5`` succeeds, version becomes 6
* Process B commits: ``UPDATE ... WHERE version=5`` fails (version is now 6)
* Process B receives :class:`~drf_commons.models.content.VersionConflictError`

This is safer than pessimistic locking (``SELECT FOR UPDATE``) for APIs where
the "read-then-write" window spans multiple HTTP requests.

Bulk Operation Modes
--------------------

Bulk update in drf-commons supports two execution modes, controlled by the
``use_save_on_bulk_update`` attribute on the ViewSet or Serializer:

**Default mode** (``use_save_on_bulk_update = False``):

Uses Django's ``QuerySet.bulk_update()``. This issues a single ``UPDATE``
statement covering all modified fields for all records. It is significantly
more efficient for large batches but does **not** trigger Django signals
(``pre_save``, ``post_save``) or custom ``save()`` logic.

Audit fields (``updated_at``, ``updated_by``) are automatically populated by
``BulkUpdateListSerializer`` when not present in the incoming payload.

**Save mode** (``use_save_on_bulk_update = True``):

Calls ``instance.save()`` for each object in the batch within a single
transaction. Triggers all signals and custom ``save()`` overrides. Use this
when downstream signal handlers or ``save()`` side effects are required.

Configurable Serializer Fields
--------------------------------

The configurable field system addresses the fundamental tension in DRF
serializer fields between write-time and read-time representations.

A foreign key relation to ``User`` may need to:

* Accept a user ID on write, return full user data on read
* Accept a username string on write, return the user ID on read
* Be completely read-only, returning nested data

Each of these combinations is a separate field class in drf-commons, named
using the ``{InputFormat}To{OutputFormat}Field`` convention:

.. code-block:: python

   # IdToDataField: write by ID, read as nested serializer output
   author = IdToDataField(queryset=User.objects.all(), serializer=UserSerializer)

   # IdOnlyField: write by ID, read as ID
   category_id = IdOnlyField(queryset=Category.objects.all())

   # ReadOnlyDataField: no write, read as nested serializer output
   last_editor = ReadOnlyDataField(serializer=UserSerializer)

The field system is built on a
:class:`~drf_commons.serializers.fields.mixins.base.ConfigurableRelatedFieldMixin`
that implements the input/output transformation protocol. All 20+ field types
are concrete implementations of this mixin.

Settings Namespace
------------------

drf-commons reads configuration from the ``COMMON`` key in Django's settings.
The :class:`~drf_commons.common_conf.settings.CommonSettings` class resolves
each setting with a defined default, falling back to the default if the key is
absent from ``settings.COMMON``.

This design ensures the library works correctly with zero configuration while
allowing operators to override specific settings:

.. code-block:: python

   # settings.py — only override what you need
   COMMON = {
       "BULK_OPERATION_BATCH_SIZE": 2000,
   }
   # All other settings use their defaults

The ``COMMON`` namespace prevents collision with other Django third-party
package settings.
