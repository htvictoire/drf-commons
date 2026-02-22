Pagination
==========

drf-commons provides two pagination classes that integrate with the
standardized response envelope.

StandardPageNumberPagination
-----------------------------

.. code-block:: python

   from drf_commons.pagination import StandardPageNumberPagination

Page-number based pagination with configurable page sizes.

**Defaults**:

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Attribute
     - Default
   * - ``page_size``
     - ``20``
   * - ``max_page_size``
     - ``100``
   * - ``page_size_query_param``
     - ``page_size``

**Query parameters**:

.. code-block:: text

   GET /articles/?page=2&page_size=50

**Customizing per-viewset**:

.. code-block:: python

   from drf_commons.pagination import StandardPageNumberPagination

   class LargePagePagination(StandardPageNumberPagination):
       page_size = 50
       max_page_size = 500

   class ArticleViewSet(BaseViewSet):
       pagination_class = LargePagePagination

LimitOffsetPaginationWithFormat
--------------------------------

.. code-block:: python

   from drf_commons.pagination import LimitOffsetPaginationWithFormat

Limit-offset based pagination. Useful for clients that implement infinite
scrolling or virtual lists.

**Defaults**:

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Attribute
     - Default
   * - ``default_limit``
     - ``20``
   * - ``max_limit``
     - ``100``

**Query parameters**:

.. code-block:: text

   GET /articles/?limit=25&offset=50

Pagination Control per Request
-------------------------------

drf-commons ``ListModelMixin`` allows clients to bypass pagination on a
per-request basis using the ``paginated`` query parameter:

.. code-block:: text

   GET /articles/?paginated=true   — Paginated response
   GET /articles/?paginated=false  — Full, unpaginated list
   GET /articles/                  — Uses pagination_class default

.. warning::

   The ``?paginated=false`` parameter should be restricted to internal APIs
   or administrative contexts. Returning unbounded datasets to external clients
   risks performance degradation under load.

Paginated Response Structure
-----------------------------

.. code-block:: json

   {
     "success": true,
     "timestamp": "2024-01-15T10:30:00.000000Z",
     "message": "",
     "count": 150,
     "next": "https://api.example.com/articles/?page=3&page_size=20",
     "previous": "https://api.example.com/articles/?page=1&page_size=20",
     "data": [
       {"id": "...", "title": "...", "index": 21},
       ...
     ]
   }

The ``data`` array items include an ``index`` field when ``append_indexes = True``
(ViewSet default). The index represents the object's position in the full
result set, not its position within the current page.
