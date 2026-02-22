Filters
=======

drf-commons provides filter backends that extend DRF's built-in filtering
with support for computed and annotated fields.

ComputedOrderingFilter
----------------------

.. code-block:: python

   from drf_commons.filters import ComputedOrderingFilter

Extends DRF's ``OrderingFilter`` to support ordering on computed fields —
fields derived from annotations, aggregations, or conditional expressions that
do not exist as columns in the database table.

**Problem**:

Standard ``OrderingFilter`` can only order by actual model fields. Annotated
fields (e.g., ``Count('comments')``, ``Sum('line_items__amount')``) must be
added to the queryset before ordering can be applied. The standard filter
backend has no mechanism for this.

**Solution**:

``ComputedOrderingFilter`` reads a ``computed_ordering_fields`` dict from the
ViewSet. When the requested ordering field is a key in this dict, the filter
applies the annotation to the queryset before ordering.

**ViewSet configuration**:

.. code-block:: python

   from django.db.models import Count, Sum
   from drf_commons.filters import ComputedOrderingFilter
   from drf_commons.views import BaseViewSet

   class ArticleViewSet(BaseViewSet):
       filter_backends = [ComputedOrderingFilter]
       ordering_fields = ["title", "created_at", "updated_at"]

       # Computed fields: key is query param value, value is annotation
       computed_ordering_fields = {
           "comment_count": Count("comments"),
           "total_likes": Count("likes"),
       }

**Query parameter usage**:

.. code-block:: text

   GET /articles/?ordering=comment_count      — ascending by comment count
   GET /articles/?ordering=-comment_count     — descending by comment count
   GET /articles/?ordering=title              — standard field ordering

**Behavior**:

1. Parses the ``ordering`` query parameter
2. Checks if any requested ordering fields are in ``computed_ordering_fields``
3. For computed fields: applies the corresponding annotation to the queryset
4. For standard fields: delegates to DRF's standard ordering logic
5. Applies combined ordering to the annotated queryset

**Complex annotations**:

.. code-block:: python

   from django.db.models import Case, DecimalField, Sum, When

   class OrderViewSet(BaseViewSet):
       computed_ordering_fields = {
           # Order by computed revenue (quantity * unit_price)
           "revenue": Sum(
               Case(
                   When(status="completed", then=models.F("total")),
                   default=0,
                   output_field=DecimalField(),
               )
           ),
       }

Combining with DRF Filter Backends
------------------------------------

``ComputedOrderingFilter`` is compatible with DRF's standard filter backends:

.. code-block:: python

   from django_filters.rest_framework import DjangoFilterBackend
   from rest_framework.filters import SearchFilter
   from drf_commons.filters import ComputedOrderingFilter

   class ArticleViewSet(BaseViewSet):
       filter_backends = [DjangoFilterBackend, SearchFilter, ComputedOrderingFilter]
       filterset_class = ArticleFilterSet
       search_fields = ["title", "content"]
       ordering_fields = ["title", "created_at"]
       computed_ordering_fields = {
           "comment_count": Count("comments"),
       }
