serializers
===========

This page documents serializer behavior from:

- ``drf_commons/serializers/base.py``
- ``drf_commons/serializers/fields/base.py``
- ``drf_commons/serializers/fields/mixins/base.py``
- ``drf_commons/serializers/fields/mixins/config.py``
- ``drf_commons/serializers/fields/mixins/conversion.py``
- ``drf_commons/serializers/fields/mixins/deferred.py``
- ``drf_commons/serializers/fields/mixins/inference.py``
- ``drf_commons/serializers/fields/mixins/relations.py``
- ``drf_commons/serializers/fields/single.py``
- ``drf_commons/serializers/fields/many.py``
- ``drf_commons/serializers/fields/readonly.py``
- ``drf_commons/serializers/fields/custom.py``

For exhaustive relation-orchestration patterns with Book/Author examples, see
``docs/modules/serializer_relationship_patterns.rst``.

Why This Serializer Layer Exists
--------------------------------

DRF provides strong primitives for single-object serialization, but three recurring problems remain in large APIs:

- safe bulk update semantics are repetitive and easy to implement inconsistently,
- related-field input/output requirements vary per endpoint and become boilerplate-heavy,
- nested relation writes often require custom, duplicated conversion logic.

``drf-commons`` addresses these with a bulk list serializer and a configurable related-field system.

Bulk Serializer Foundation
--------------------------

``BulkUpdateListSerializer``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Problem it solves

- DRF ``ListSerializer`` does not provide a default robust multi-instance update policy.
- Teams often fall back to N save calls per row, producing unnecessary query volume.

How default DRF behaves

- list update behavior is application-defined; DRF intentionally does not prescribe full semantics for matching data rows to instances.

Implementation behavior

``BulkUpdateListSerializer.update(instance, validated_data)``:

1. starts an atomic transaction,
2. asserts instance count equals validated row count,
3. iterates with ``zip(instance, validated_data)``,
4. sets validated attributes on each in-memory instance,
5. unions all touched field names into ``update_fields``,
6. executes one ``bulk_update`` using model class from first instance,
7. returns updated instance list.

Internal mechanics and implications

- Matching remains positional inside the list serializer. Safe usage depends on caller supplying ID-aligned instances.
- Length mismatch now raises ``ValidationError`` instead of silently truncating.
- ``bulk_update`` bypasses model ``save()``, model signals, and per-instance side effects.

Performance characteristics

- excellent query reduction for homogeneous updates,
- memory pressure grows with request size because all instances are materialized before update,
- does not solve expensive queryset fetch costs; upstream queryset construction still dominates if not optimized.

Trade-offs

- speed and reduced query count versus loss of model-level hooks.
- no row-level success/failure isolation inside one call; validation failures happen before update, DB failure aborts whole transaction.

When not to use

- when model ``save()`` side effects, signals, or audit hooks must run per row,
- when caller cannot guarantee ID-aligned instance ordering before invoking serializer list update,
- when partial-success semantics are required.

Alternatives

- explicit row loop with ``save(update_fields=...)`` and per-row error collection,
- service-layer bulk logic with deterministic ID mapping and reconciliation report,
- database-native upsert strategies.

``BaseModelSerializer``
^^^^^^^^^^^^^^^^^^^^^^^

``BaseModelSerializer`` sets ``list_serializer_class = BulkUpdateListSerializer``,
wraps ``save`` in ``transaction.atomic``, and orchestrates deferred related writes
from configurable related fields.

This is not a new data model. It is a transactional safety wrapper plus a default
list serializer choice and relation-write coordinator.

Real integration example
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from rest_framework import serializers
   from drf_commons.serializers.base import BaseModelSerializer
   from incidents.models import Incident

   class IncidentSerializer(BaseModelSerializer):
       class Meta(BaseModelSerializer.Meta):
           model = Incident
           fields = ["id", "severity", "summary", "updated_at"]

You still need deterministic instance selection/order in view logic.


Configurable Related Fields
---------------------------

Core problem
^^^^^^^^^^^^

DRF's built-in relation fields are intentionally single-purpose:

- ``PrimaryKeyRelatedField`` favors ID IO,
- ``SlugRelatedField`` favors one slug field,
- nested serializers require explicit create/update orchestration.

In real APIs, different clients may require mixed contracts: accept nested objects on write, return IDs on read, or return custom formatted relation payloads.

Core classes
^^^^^^^^^^^^

- ``ConfigurableRelatedField`` for single relation
- ``ConfigurableManyToManyField`` for many relation
- ``ReadOnlyRelatedField``
- ``WriteOnlyRelatedField``

Configuration model
^^^^^^^^^^^^^^^^^^^

Inputs:

- ``input_formats`` subset of ``["id", "nested", "slug", "object"]``
- ``lookup_field`` default ``"pk"``
- ``create_if_nested`` default ``True``
- ``update_if_exists`` default ``False``

Outputs:

- ``output_format`` in ``["id", "str", "serialized", "custom"]``
- ``serializer_class`` required for ``serialized`` and nested input
- ``custom_output_callable`` required for ``custom`` output

Relation write orchestration:

- ``relation_write.relation_kind`` in ``["auto", "generic", "fk", "m2m", "reverse_fk", "reverse_m2m"]``
- ``relation_write.write_order`` in ``["auto", "dependency_first", "root_first"]``
- ``relation_write.child_link_field`` for reverse-FK linking (for example ``"category"`` on child model)
- ``relation_write.sync_mode`` in ``["append", "replace", "sync"]``

Validation is strict at field construction time. Invalid config raises ``ValueError``.

Auto inference behavior (important):

- ``relation_write`` is optional; when omitted it behaves like ``{}``.
- ``relation_kind="auto"`` and ``write_order="auto"`` are resolved from model metadata at field bind time.
- inference is best-effort, not a guarantee.
- if field ``source`` is non-top-level (for example dotted paths), computed, or otherwise not resolvable by model metadata lookup, resolution can fall back to ``generic``.
- production guidance: keep auto for straightforward direct model relations; configure reverse relations and non-trivial ``source`` explicitly.

Input conversion algorithm
^^^^^^^^^^^^^^^^^^^^^^^^^^

``to_internal_value`` decision order:

1. ``None`` or ``""`` => DRF null handling using ``allow_null``,
2. ``dict`` and ``nested`` enabled => nested serializer validation only (no DB write),
3. ``int`` or ``str`` and ``id`` enabled => ID lookup,
4. model instance and ``object`` enabled => pass-through,
5. ``str`` and ``slug`` enabled => slug/name lookup,
6. otherwise DRF incorrect type failure.

Critical edge case:

If both ``id`` and ``slug`` are enabled, string input is handled as ID first. Slug branch will not execute for string values in that configuration.

Nested behavior details
^^^^^^^^^^^^^^^^^^^^^^^

- nested create/update is validated in ``to_internal_value`` and deferred,
- no nested write occurs during ``serializer.is_valid()``,
- deferred writes are resolved during parent serializer ``create/update`` inside ``BaseModelSerializer.save()``,
- ``update_if_exists=True`` uses ``lookup_field`` in nested payload to resolve update target,
- nested validation errors are surfaced as nested serializer errors.

Write ordering:

- ``dependency_first``: related objects are persisted before parent create/update payload is committed
  (typical for parent model FK fields),
- ``root_first``: parent is persisted first, then relation manager/child links are written
  (typical for reverse relations like ``related_name`` collections).
- ``sync_mode="replace"``/``"sync"`` on ``reverse_fk`` requires nullable child FK;
  non-nullable reverse FK supports ``append`` safely.

Book/Author concrete mapping:

- ``Book.author`` (direct FK) typically resolves to ``dependency_first``.
- ``Book.authors`` (direct M2M) typically resolves to ``dependency_first``.
- ``Author.books`` when it is reverse FK ``related_name`` typically resolves to ``root_first``.
- ``Author.books`` when it is reverse M2M ``related_name`` typically resolves to ``root_first``.
- treat these as inferred defaults, not hard guarantees; set explicit ``relation_write`` if endpoint contracts depend on strict ordering.

Read/output behavior
^^^^^^^^^^^^^^^^^^^^

- ``id`` returns ``getattr(value, lookup_field)``,
- ``str`` returns ``str(value)``,
- ``serialized`` instantiates ``serializer_class(value, context=self.context)``,
- ``custom`` calls ``custom_output_callable(value, context)``.

Many relation behavior
^^^^^^^^^^^^^^^^^^^^^^

``ConfigurableManyToManyField`` forces ``many=True`` and:

- ``to_representation`` iterates ``value.all()`` if relation manager-like,
- ``to_internal_value`` requires list and maps each element through single-item conversion.

Performance considerations

- representation can trigger N+1 queries if the relation is not prefetched,
- nested create/update can still explode write-query count for large relation lists,
- serializer-per-item instantiation has nontrivial CPU overhead on large payloads.

Real integration examples
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from rest_framework import serializers
   from drf_commons.serializers.base import BaseModelSerializer
   from drf_commons.serializers.fields.single import DataToIdField
   from drf_commons.serializers.fields.many import ManyDataToIdField
   from catalog.models import Book, Category

   class CategorySerializer(serializers.ModelSerializer):
       class Meta:
           model = Category
           fields = ["id", "name", "slug"]

   class BookSerializer(BaseModelSerializer):
       category = DataToIdField(
           queryset=Category.objects.all(),
           serializer_class=CategorySerializer,
       )

       class Meta(BaseModelSerializer.Meta):
           model = Book
           fields = ["id", "title", "isbn", "category"]

   class BookChildSerializer(serializers.ModelSerializer):
       class Meta:
           model = Book
           fields = ["id", "title", "isbn"]

   class CategoryWithBooksSerializer(BaseModelSerializer):
       books = ManyDataToIdField(
           source="books",
           queryset=Book.objects.all(),
           serializer_class=BookChildSerializer,
           relation_write={
               "relation_kind": "reverse_fk",
               "write_order": "root_first",
               "child_link_field": "category",
               "sync_mode": "append",
           },
       )

       class Meta(BaseModelSerializer.Meta):
           model = Category
           fields = ["id", "name", "books"]


Preconfigured Field Variants
----------------------------

The ``single.py``, ``many.py``, ``readonly.py``, and ``custom.py`` modules provide configuration presets:

- single relation presets such as ``IdToDataField``, ``DataToIdField``, ``StrToDataField``,
- many relation presets such as ``ManyIdToDataField``, ``ManyDataToIdField``, ``ManyFlexibleField``,
- read-only helpers such as ``ReadOnlyIdField`` and ``ReadOnlyDataField``,
- custom-output helpers such as ``CustomOutputField``.

These are thin wrappers around the same core mixin behavior, not separate IO engines.
All preset fields accept ``relation_write`` and forward it unchanged to the core mixin.

Compatibility and integration concerns
--------------------------------------

- Works with DRF serializer context patterns; custom output callables receive that context.
- Assumes ``queryset`` is provided for lookup-capable paths.
- Nested operations require serializers that can actually create/update target models.
- Deferred nested writes require ``BaseModelSerializer`` so relation operations execute during ``save``.

Notable API-contract risks
--------------------------

- ID/slug ambiguity when both formats are enabled for string payloads.
- Misconfigured ``relation_write`` ordering can produce relation assignment errors on reverse paths.
- Direct use of ``BulkUpdateListSerializer`` without ID-aligned instance preparation can still corrupt updates.

Migration strategy
------------------

For mature codebases:

1. Introduce field presets only on one endpoint with strict contract tests.
2. Keep existing serializer output schema stable; migrate input acceptance first.
3. If adopting bulk serializer directly, enforce deterministic ID-based payload-to-instance mapping before serializer update.
4. Only then roll out to high-volume endpoints.

When to avoid this layer
------------------------

Skip these abstractions when:

- relation contracts are simple and stable (DRF built-ins are clearer),
- strict per-field validation transparency is more important than flexible polymorphic input,
- your platform standard forbids nested writes from public APIs.
