pagination
==========

Source module: ``drf_commons/pagination/base.py``

Why this module exists
----------------------

Problem
^^^^^^^

DRF pagination classes are configurable but many codebases repeatedly re-declare identical defaults.

Default DRF behavior
^^^^^^^^^^^^^^^^^^^^

- pagination behavior depends entirely on configured class and attributes,
- no project-level opinion unless you define one.

What ``drf-commons`` provides
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Two thin subclasses with explicit defaults:

- ``StandardPageNumberPagination``
- ``LimitOffsetPaginationWithFormat``

``StandardPageNumberPagination``
--------------------------------

Configuration:

- ``page_size = 20``
- ``page_size_query_param = "page_size"``
- ``max_page_size = 100``

Use when:

- client teams prefer page-number semantics,
- bounded page-size override is required.

``LimitOffsetPaginationWithFormat``
-----------------------------------

Configuration:

- ``default_limit = 20``
- ``limit_query_param = "limit"``
- ``offset_query_param = "offset"``
- ``max_limit = 100``

Use when:

- clients need offset-style paging for scrollable tables or SQL-like navigation.

Performance implications
------------------------

- page-number and limit-offset both require count operations in common DRF paths,
- large table counts can dominate latency on complex queries,
- these classes do not add optimizations beyond DRF defaults.

Trade-offs
----------

Pros:

- consistent defaults across endpoints,
- avoids repeated local class declarations.

Cons:

- fixed conservative defaults may not fit high-throughput endpoints,
- no cursor-based pagination for deep-page performance.

When not to use
---------------

- very large datasets where offset pagination degrades,
- APIs requiring stable pagination under concurrent writes (cursor often better).

Alternatives
------------

- DRF ``CursorPagination`` for high-volume ordered streams,
- endpoint-specific pagination classes for domain-specific constraints.

Integration example
-------------------

.. code-block:: python

   from drf_commons.pagination.base import StandardPageNumberPagination
   from drf_commons.views.base import ReadOnlyViewSet

   class AuditTrailViewSet(ReadOnlyViewSet):
       queryset = AuditEvent.objects.order_by("-created_at")
       serializer_class = AuditEventSerializer
       pagination_class = StandardPageNumberPagination

Migration strategy
------------------

1. pick one default pagination style platform-wide,
2. apply class to base viewsets,
3. keep explicit exceptions for endpoints with specialized access patterns.
