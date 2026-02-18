filters
=======

Source modules:

- ``drf_commons/filters/ordering/computed.py``
- ``drf_commons/filters/ordering/processors.py``

Problem this module solves
--------------------------

DRF ordering works well for direct model fields, but product UIs often need sortable columns that map to:

- related model fields,
- compound field order (for example first_name + last_name),
- aggregate expressions.

Default DRF behavior
--------------------

``OrderingFilter`` validates orderable fields and applies them directly in ``order_by``. Complex computed mappings are manual.

``ComputedOrderingFilter`` design
---------------------------------

How it works
^^^^^^^^^^^^

- extends valid ordering fields with keys from ``view.computed_ordering_fields``,
- intercepts requested ordering,
- rewrites computed keys into concrete order expressions,
- applies annotations when aggregate mappings are used,
- falls back to DRF default ordering behavior when no computed mapping is needed.

Supported computed mapping types
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For each key in ``computed_ordering_fields``:

- ``str``: one concrete order field path,
- ``list[str]``: compound ordering sequence,
- ``models.Aggregate``: annotation-backed ordering.

Processor internals
-------------------

- ``parse_order_field`` extracts reverse flag from leading ``-``.
- ``process_string_lookup`` applies reverse prefix when needed.
- ``process_list_lookup`` applies reverse prefix to each field in compound list.
- ``process_aggregate_lookup`` creates annotation name ``<field>_order`` and ordering reference.
- ``process_ordering`` rewrites each requested ordering field and accumulates annotations.

Real integration example
------------------------

.. code-block:: python

   from django.db.models import Count
   from rest_framework import filters
   from drf_commons.filters.ordering.computed import ComputedOrderingFilter

   class CourseViewSet(ReadOnlyViewSet):
       queryset = Course.objects.all()
       serializer_class = CourseSerializer
       filter_backends = [ComputedOrderingFilter, filters.SearchFilter]
       ordering_fields = ["code", "created_at", "instructor", "students_count"]
       computed_ordering_fields = {
           "instructor": ["instructor__first_name", "instructor__last_name"],
           "students_count": Count("enrollments"),
       }

Edge cases and constraints
--------------------------

- unsupported mapping value types raise ``ValueError`` at runtime.
- aggregate ordering depends on annotation naming convention and query correctness.
- for expensive annotations, ordering cost can increase significantly on large datasets.

Performance implications
------------------------

- string/list mappings are lightweight rewrites,
- aggregate mappings add ``annotate`` and may force heavier query plans,
- sort performance depends on DB indexing and relation cardinality.

When not to use
---------------

- if ordering keys are highly dynamic and cannot be safely declared,
- if aggregate sorting produces unacceptable query plans for primary API traffic.

Alternatives
------------

- explicit per-endpoint ordering parser with custom queryset logic,
- precomputed sortable columns/materialized views for heavy aggregate ordering.

Compatibility concerns
----------------------

- relies on DRF ``OrderingFilter`` contract,
- compatible with regular DRF filter backend stacking.

Migration strategy
------------------

1. start with one computed ordering field,
2. benchmark SQL plans for ascending and descending variants,
3. add indexes or denormalized fields where needed,
4. incrementally migrate front-end sort keys to computed mapping keys.
