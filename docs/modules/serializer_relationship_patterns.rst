Serializer Relationship Patterns
================================

This guide is a deep technical reference for relation writes with ``drf_commons.serializers``.
It focuses on production behavior with explicit examples using Book/Author models.

It complements ``docs/modules/serializers.rst`` and drills into concrete relation topologies.


Why This Document Exists
------------------------

DRF already provides relation fields (``PrimaryKeyRelatedField``, nested serializers, etc.),
but relation writes in large systems usually fail in one of these ways:

- nested writes happen during validation and leak partial rows on later failure,
- reverse relation writes are hand-coded differently on every endpoint,
- team members mis-handle ``related_name`` paths (especially reverse FK vs reverse M2M),
- bulk relation operations behave differently across serializers.

``drf_commons`` addresses this by:

- keeping nested relation input validation in ``to_internal_value``,
- deferring nested persistence to serializer save-time,
- orchestrating relation writes in ``BaseModelSerializer`` under transaction,
- supporting explicit relation-write policies for reverse paths.


Runtime Contract (Important)
----------------------------

For configurable relation fields with nested input:

- ``serializer.is_valid()`` validates nested payloads but does not save nested rows,
- nested rows are saved when parent serializer ``save()`` runs,
- all write orchestration runs inside ``BaseModelSerializer.save()`` transaction.

If you use configurable nested relation input on a serializer that does **not**
inherit ``BaseModelSerializer``, you lose this deferred-write orchestration.


Relation Write Configuration
----------------------------

All configurable relation presets accept ``relation_write``.

Supported keys:

- ``relation_kind``:
  - ``"auto"``, ``"generic"``, ``"fk"``, ``"m2m"``, ``"reverse_fk"``, ``"reverse_m2m"``
- ``write_order``:
  - ``"auto"``, ``"dependency_first"``, ``"root_first"``
- ``child_link_field``:
  - required for reverse FK linking, for example ``"author"``
- ``sync_mode``:
  - ``"append"``, ``"replace"``, ``"sync"``

Auto defaults by inferred relation:

- direct FK / direct M2M => ``dependency_first``
- reverse FK / reverse M2M => ``root_first``

Inference scope and limits:

- auto inference is derived from serializer model metadata and top-level relation field lookup.
- it is best-effort and should not be treated as guaranteed for every serializer shape.
- if ``source`` is dotted/computed or not a direct model relation attribute, inference can degrade to ``generic`` behavior.
- for production endpoints with strict contracts, configure reverse relations explicitly and set ``child_link_field`` explicitly for reverse FK whenever there is ambiguity.

``sync_mode`` behavior:

- ``append``:
  - keep existing links, add new ones
- ``replace`` and ``sync``:
  - reverse M2M and direct M2M: use ``manager.set(...)``
  - reverse FK: null out children not present in payload (requires nullable child FK)


Model Topologies Used In Examples
---------------------------------

The next sections use three model shapes.

1. Direct M2M from ``Book`` to ``Author``

.. code-block:: python

   class Author(models.Model):
       name = models.CharField(max_length=200, unique=True)

   class Book(models.Model):
       title = models.CharField(max_length=255)
       isbn = models.CharField(max_length=20, unique=True)
       authors = models.ManyToManyField(Author, related_name="books")

2. Reverse ``related_name`` of that same M2M from ``Author`` side

- no extra model change; ``Author.books`` is reverse manager from ``related_name``.

3. Reverse ``related_name`` for FK

.. code-block:: python

   class Author(models.Model):
       name = models.CharField(max_length=200, unique=True)

   class Book(models.Model):
       title = models.CharField(max_length=255)
       isbn = models.CharField(max_length=20, unique=True)
       author = models.ForeignKey(
           Author,
           related_name="books",
           on_delete=models.PROTECT,
           null=True,  # if you need reverse_fk sync/replace semantics
           blank=True,
       )


Pattern A: Book -> Authors (Direct M2M)
---------------------------------------

Problem this solves
^^^^^^^^^^^^^^^^^^^

API clients often want to create/update Book and Author links in one request:

- by existing IDs,
- by nested author objects,
- by mixed payloads.

Default DRF behavior
^^^^^^^^^^^^^^^^^^^^

DRF can do this with ``PrimaryKeyRelatedField`` or custom nested logic, but teams
typically write custom create/update and call nested serializers manually.

Why that is usually insufficient
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- nested save sequencing differs per endpoint,
- error-handling consistency suffers,
- write-time behavior around transactions is easy to get wrong.

Implementation with ``drf_commons``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from rest_framework import serializers
   from drf_commons.serializers.base import BaseModelSerializer
   from drf_commons.serializers.fields.many import ManyDataToIdField

   class AuthorSerializer(serializers.ModelSerializer):
       class Meta:
           model = Author
           fields = ["id", "name"]

   class BookSerializer(BaseModelSerializer):
       authors = ManyDataToIdField(
           queryset=Author.objects.all(),
           serializer_class=AuthorSerializer,
           relation_write={
               "relation_kind": "m2m",          # optional; auto usually infers this
               "write_order": "dependency_first",
               "sync_mode": "append",           # for direct M2M, DRF create/update will manage set semantics
           },
       )

       class Meta(BaseModelSerializer.Meta):
           model = Book
           fields = ["id", "title", "isbn", "authors"]

What happens internally
^^^^^^^^^^^^^^^^^^^^^^^

At validation:

- each nested author dict is validated by ``AuthorSerializer``;
- nested saves are deferred (no row written yet).

At save:

- deferred author serializers are resolved first (dependency-first),
- parent ``Book`` create/update runs,
- DRF M2M assignment uses resolved ``Author`` instances.

Edge cases
^^^^^^^^^^

- if payload mixes author IDs and nested authors, both are supported;
- string payload with both ``id`` and ``slug`` enabled prefers ID branch first;
- very large author lists still incur serializer instantiation overhead.

Performance notes
^^^^^^^^^^^^^^^^^

- relation resolution can still cause many writes for large nested lists;
- representation may trigger N+1 if not prefetched.

When not to use this pattern
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- if authors must never be created from book endpoint,
- if relation writes should be handled only in domain/service layer.


Pattern B: Author -> Books via M2M Reverse ``related_name``
------------------------------------------------------------

Problem this solves
^^^^^^^^^^^^^^^^^^^

Clients often update an author and its books from the author endpoint, even though
``books`` is reverse manager, not direct field on ``Author`` model class.

Implementation
^^^^^^^^^^^^^^

.. code-block:: python

   from rest_framework import serializers
   from drf_commons.serializers.base import BaseModelSerializer
   from drf_commons.serializers.fields.many import ManyDataToIdField

   class BookChildSerializer(serializers.ModelSerializer):
       class Meta:
           model = Book
           fields = ["id", "title", "isbn"]

   class AuthorWithBooksSerializer(BaseModelSerializer):
       books = ManyDataToIdField(
           source="books",  # reverse manager from related_name on Book.authors
           queryset=Book.objects.all(),
           serializer_class=BookChildSerializer,
           relation_write={
               "relation_kind": "reverse_m2m",  # optional, auto can infer
               "write_order": "root_first",     # required behavior for reverse relation manager writes
               "sync_mode": "replace",          # replace existing links with payload set
           },
       )

       class Meta(BaseModelSerializer.Meta):
           model = Author
           fields = ["id", "name", "books"]

Internal flow
^^^^^^^^^^^^^

- validation defers nested book writes;
- serializer saves ``Author`` first (root-first);
- resolved books are applied using reverse manager:
  - ``append`` => ``author.books.add(...)``
  - ``replace``/``sync`` => ``author.books.set(...)``

Trade-offs
^^^^^^^^^^

- ``replace`` is deterministic but can remove links not in payload;
- ``append`` is safer for additive workflows but requires explicit cleanup path.

Compatibility concerns
^^^^^^^^^^^^^^^^^^^^^^

- if ``source`` points to non-top-level or unsupported relation structures, auto inference may not work; set ``relation_kind`` explicitly.
- even when auto currently infers correctly, schema or serializer refactors can change inferred kind/order; pin ``relation_write`` explicitly on critical endpoints to avoid silent behavior drift.


Pattern C: Author -> Books via Reverse FK ``related_name``
-----------------------------------------------------------

Problem this solves
^^^^^^^^^^^^^^^^^^^

In many domains each Book has one Author (FK). From author endpoint you still want
to create/reassign books without custom serializer methods.

Implementation
^^^^^^^^^^^^^^

.. code-block:: python

   from rest_framework import serializers
   from drf_commons.serializers.base import BaseModelSerializer
   from drf_commons.serializers.fields.many import ManyDataToIdField

   class BookChildSerializer(serializers.ModelSerializer):
       class Meta:
           model = Book
           fields = ["id", "title", "isbn"]

   class AuthorWithBooksSerializer(BaseModelSerializer):
       books = ManyDataToIdField(
           source="books",  # related_name from Book.author FK
           queryset=Book.objects.all(),
           serializer_class=BookChildSerializer,
           relation_write={
               "relation_kind": "reverse_fk",
               "write_order": "root_first",
               "child_link_field": "author",   # Book.author
               "sync_mode": "append",          # or replace/sync if Book.author is nullable
           },
       )

       class Meta(BaseModelSerializer.Meta):
           model = Author
           fields = ["id", "name", "books"]

Internal mechanics
^^^^^^^^^^^^^^^^^^

After parent save:

- each resolved book gets ``book.author = parent_author`` and ``save(update_fields=["author"])``;
- for ``replace``/``sync``, books not in payload are detached via ``update(author=None)``.

Important constraint:

- reverse FK ``replace``/``sync`` requires nullable FK on child model.
- if FK is non-nullable, use ``append`` only (or custom domain migration strategy).

Production consequence if misconfigured
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you force reverse FK ``replace`` on non-nullable child FK, detaching omitted rows
cannot be represented and serializer raises validation error.


Request/Response Examples
-------------------------

Book create with nested authors (direct M2M):

.. code-block:: json

   {
     "title": "Domain-Driven APIs",
     "isbn": "978-1-55555-010-0",
     "authors": [
       {"name": "Ada North"},
       {"name": "K. Flores"}
     ]
   }

Author update with reverse M2M ``replace``:

.. code-block:: json

   {
     "name": "Ada North",
     "books": [
       15,
       {"title": "Distributed Boundaries", "isbn": "978-1-55555-011-7"}
     ]
   }

Author update with reverse FK ``append``:

.. code-block:: json

   {
     "name": "Primary Author",
     "books": [
       101,
       {"title": "Newly Assigned", "isbn": "978-1-55555-012-4"}
     ]
   }


Failure and Safety Behavior
---------------------------

Validation phase failures:

- no nested DB write is committed,
- response surfaces nested serializer error tree.

Save phase failures:

- parent + related writes are under serializer transaction,
- transaction rollback protects against partial parent/child persistence.

Contract implication:

- this behavior assumes usage of ``BaseModelSerializer``.


Migration Strategy
------------------

Move to these patterns in stages:

1. Start with direct M2M on one endpoint and explicit contract tests.
2. Introduce reverse ``related_name`` writes only where required.
3. Default to ``append`` first; adopt ``replace`` after clear API contract review.
4. For reverse FK replace/sync, make child FK nullable before rollout.
5. Track query count and lock behavior on high-volume endpoints.


When Not To Use These Patterns
------------------------------

- your service boundary forbids nested writes in public APIs,
- relation assignment has domain side-effects requiring service-layer orchestration,
- you need per-row partial success reporting for large relation payloads.


Alternative Approaches
----------------------

- DRF ``PrimaryKeyRelatedField`` only, with explicit service-layer relation updates,
- explicit serializer ``create/update`` methods per endpoint,
- dedicated command endpoints for linking/unlinking relationships.


Checklist for Production Adoption
---------------------------------

- serializer inherits ``BaseModelSerializer``,
- relation field ``queryset`` is scoped correctly for permissions/tenancy,
- ``relation_write`` configured explicitly on reverse relations,
- bulk payload size limits are enforced at view layer,
- integration tests cover:
  - validation failure without nested writes,
  - successful parent + nested commit,
  - reverse relation sync semantics (append vs replace),
  - unauthorized relation IDs rejected by queryset scope.
