models
======

This page documents model-layer behavior from implementation in:

- ``drf_commons/models/mixins.py``
- ``drf_commons/models/base.py``
- ``drf_commons/models/content.py``
- ``drf_commons/models/fields.py``
- ``drf_commons/models/person.py``

It is intentionally architecture-first and production-oriented.

Why This Layer Exists
---------------------

DRF itself is serializer/view focused. It does not solve model concerns such as:

- attribution of writes to current authenticated user without passing ``request`` everywhere,
- consistent soft-delete semantics,
- reusable slug/version/metadata patterns,
- safe default wiring for model fields that depend on request context.

``drf-commons`` moves those concerns to reusable abstract model mixins and a custom user field.

``UserActionMixin``
-------------------

Problem it solves
^^^^^^^^^^^^^^^^^

In vanilla Django/DRF, ``created_by`` and ``updated_by`` are typically set in serializer ``create``/``update`` or viewset ``perform_create``/``perform_update``. That approach is repetitive, and easy to miss in batch jobs, admin paths, or custom save paths.

Default Django/DRF behavior
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Django models do not know about the current request user.
- DRF does not implicitly persist current user into model fields.
- You must pass actor context manually in each write path.

What this mixin changes
^^^^^^^^^^^^^^^^^^^^^^^

``UserActionMixin`` adds ``created_by`` and ``updated_by`` foreign keys and overrides ``save()``:

- on every save it calls ``set_created_by_and_updated_by()``,
- if ``get_current_authenticated_user()`` returns an authenticated user:

  - ``created_by`` is set only when currently empty,
  - ``updated_by`` is always set.

Internal mechanics
^^^^^^^^^^^^^^^^^^

The mixin depends on thread-local user context from ``drf_commons.current_user.utils``.
A middleware requirement is enforced when attribution logic executes (save path), not at module import time.

Production implications
^^^^^^^^^^^^^^^^^^^^^^^

- ``save(update_fields=[...])`` caveat: if ``updated_by`` is assigned in ``save()`` but not included in ``update_fields``, the assignment is not persisted.
- bulk updates performed with queryset ``update(...)`` bypass ``save()`` and therefore bypass this attribution logic.
- ``save()`` attribution path enforces presence of ``CurrentUserMiddleware`` in settings and raises ``ImproperlyConfigured`` when it is not configured.
- any non-request execution context without manual user injection results in ``created_by/updated_by`` staying unchanged or ``None``.

When not to use
^^^^^^^^^^^^^^^

Avoid this pattern when:

- writes come primarily from asynchronous workers that do not carry user context,
- your audit model requires immutable append-only event rows rather than mutable ``updated_by`` fields,
- you rely heavily on queryset ``update()`` and want guaranteed actor attribution.

Alternatives
^^^^^^^^^^^^

- explicit actor propagation in service layer (pass ``actor`` into domain service methods),
- DB-level auditing triggers,
- dedicated audit-event table with request-id/actor-id correlation.

Integration and migration
^^^^^^^^^^^^^^^^^^^^^^^^^

For existing models with manual attribution, migration can be incremental:

1. Add nullable ``created_by``/``updated_by``.
2. Start using ``UserActionMixin`` for new writes.
3. Backfill historical rows with best-effort mapping.
4. Only then tighten constraints (if desired).

Real integration example
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from django.db import models
   from drf_commons.models.mixins import UserActionMixin, TimeStampMixin

   class Incident(UserActionMixin, TimeStampMixin, models.Model):
       severity = models.CharField(max_length=16)
       summary = models.TextField()

       class Meta:
           db_table = "ops_incident"


``TimeStampMixin`` and ``SoftDeleteMixin``
------------------------------------------

Problem it solves
^^^^^^^^^^^^^^^^^

Teams repeatedly implement ``created_at``, ``updated_at``, and a soft-delete flag/timestamp with inconsistent field names and semantics.

Default DRF behavior
^^^^^^^^^^^^^^^^^^^^

DRF has no model-level soft-delete primitive; it only serializes whatever model behavior exists.

How ``drf-commons`` implements it
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``TimeStampMixin``:

- ``created_at = DateTimeField(auto_now_add=True)``
- ``updated_at = DateTimeField(auto_now=True)``

``SoftDeleteMixin``:

- ``deleted_at`` nullable datetime,
- ``is_active`` boolean default ``True``,
- ``soft_delete()`` sets ``deleted_at=timezone.now()`` and ``is_active=False`` then saves only those fields,
- ``restore()`` clears ``deleted_at``, sets ``is_active=True`` and saves,
- ``is_deleted`` property returns ``not self.is_active``.

Edge cases and trade-offs
^^^^^^^^^^^^^^^^^^^^^^^^^

- There is no default manager filtering inactive rows. Every queryset must enforce its own active-only policy.
- ``soft_delete()`` and ``restore()`` use ``save(update_fields=[...])``. If combined with ``UserActionMixin``, ``updated_by`` assignment is not persisted unless included in update fields.
- bulk soft delete in view mixins uses queryset ``update(...)`` and bypasses model methods/signals.

When not to use
^^^^^^^^^^^^^^^

Do not use this soft-delete approach when legal/compliance requires hard delete or immutable tombstone tables with retention policies.

Alternatives
^^^^^^^^^^^^

- custom managers + queryset subclasses for mandatory active filtering,
- packages with full soft-delete query semantics,
- archival tables plus hard delete.


``BaseModelMixin``
------------------

Problem it solves
^^^^^^^^^^^^^^^^^

Projects commonly re-implement the same base fields and utility methods repeatedly.

What it composes
^^^^^^^^^^^^^^^^

``BaseModelMixin`` inherits:

- ``UserActionMixin``
- ``TimeStampMixin``
- ``SoftDeleteMixin``

and adds:

- UUID primary key ``id``,
- ``get_json(...)`` helper.

``get_json`` behavior details
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- serializes only ``self._meta.fields`` (no M2M, no reverse relations),
- optional include list via ``fields``,
- optional exclude list via ``exclude_fields``,
- foreign key objects are converted to their ``pk`` if attribute has ``pk``,
- optional ``exclude_general_fields`` removes ``created_at``, ``updated_at``, ``created_by``, ``updated_by``,
- returns JSON string via ``DjangoJSONEncoder``.

Performance profile
^^^^^^^^^^^^^^^^^^^

- O(number of model fields) Python-level attribute access.
- for FK fields not already selected, attribute access may trigger lazy DB fetches.
- not suitable as a high-throughput response serializer replacement.

Use cases
^^^^^^^^^

Good for logging snapshots, lightweight change records, and admin debugging.


Content Mixins: ``SlugMixin``, ``MetaMixin``, ``VersionMixin``
---------------------------------------------------------------

``SlugMixin``
^^^^^^^^^^^^^

- requires subclass implementation of ``get_slug_source()``.
- auto-generates slug on save only when slug is empty.
- builds deterministic slug candidates using ``base_slug``, ``base_slug-1``, ``base_slug-2``, ...
- retries bounded by ``slug_conflict_retry_limit`` (default: 20).
- each candidate save runs in an atomic transaction and relies on DB uniqueness enforcement.

Operational contract:

- if all retries are exhausted, ``save()`` raises ``IntegrityError``.
- for high-contention slug domains, increase ``slug_conflict_retry_limit`` per model.

``MetaMixin``
^^^^^^^^^^^^^

- ``metadata`` JSON field,
- ``tags`` comma-separated string field with helper parse/add/remove methods,
- ``notes`` text field.

Operational caveat: helper methods mutate in-memory fields but do not call ``save()``.

``VersionMixin``
^^^^^^^^^^^^^^^^

- ``version`` positive integer default 1,
- ``revision_notes`` text,
- update path uses optimistic locking with compare-and-swap:

  - conditional update: ``filter(pk=self.pk, version=expected_version).update(version=F("version")+1)``
  - if no row is updated, raises ``VersionConflictError``.

- successful update increments ``self.version`` and persists model fields in the same transaction.
- ``skip_version_increment=True`` bypasses version bump logic for the save call.

Conflict handling:

- catch ``drf_commons.models.content.VersionConflictError`` at service/API boundaries,
- map to conflict response (for example HTTP 409) when version alignment is required by client contract.


``CurrentUserField``
--------------------

Problem it solves
^^^^^^^^^^^^^^^^^

Reducing repetitive ``ForeignKey(User, default=current_user)`` boilerplate, including update-time actor stamping.

How DRF/Django usually behave
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Standard Django ``ForeignKey`` defaults are static callables but provide no built-in update-time auto-stamping.

Implementation behavior
^^^^^^^^^^^^^^^^^^^^^^^

``CurrentUserField`` subclasses ``models.ForeignKey`` and enforces defaults:

- ``null=True``
- ``default=get_current_authenticated_user``
- ``to=AUTH_USER_MODEL``

Additional option:

- ``on_update=True`` switches behavior so ``pre_save`` sets current authenticated user each save.
- with ``on_update=True``, field is forced ``editable=False`` and ``blank=True``.

Warnings and normalization:

- passing overriding ``default``, ``null``, or ``to`` values triggers warnings,
- if ``to`` is case-insensitive equivalent to default user model, it is normalized.

Edge cases
^^^^^^^^^^

- if current user is absent/anonymous, value resolves to ``None``.
- middleware requirement is checked when ``pre_save`` executes.
- ``pre_save`` raises ``ImproperlyConfigured`` when ``CurrentUserMiddleware`` is not configured in the active Django settings.
- ``pre_save`` with ``on_update=True`` sets the FK attname to user PK directly.

Compatibility concerns
^^^^^^^^^^^^^^^^^^^^^^

- tightly coupled to middleware-based thread-local context.
- non-request write paths need explicit user seeding or accept ``None``.
- write paths that use settings without ``CurrentUserMiddleware`` configured fail fast with ``ImproperlyConfigured``.

Migration strategy
^^^^^^^^^^^^^^^^^^

For existing explicit FK fields:

1. Keep existing schema, replace field declaration with ``CurrentUserField`` matching DB column.
2. Deploy with nullable column first.
3. Monitor for unexpected null actors in worker paths.
4. Add guardrails in services/tasks where request context is absent.


Person Mixins
-------------

``IdentityMixin`` and ``AddressMixin`` provide generic person/address fields and computed properties.

Behavior notes from source:

- ``IdentityMixin.email`` is unique.
- ``full_name``, ``initials``, and ``age`` are computed properties.
- ``AddressMixin`` provides ``full_address``, ``short_address``, and coordinate helpers.


Adoption Guidance
-----------------

Use these model components when your API platform needs:

- consistent actor/timestamp metadata,
- soft-delete semantics with explicit query control,
- reusable content metadata/versioning helpers,
- standardized user FK defaults.

Avoid blanket adoption. For high-scale systems, evaluate each mixin separately against your write model, concurrency requirements, and audit obligations.
