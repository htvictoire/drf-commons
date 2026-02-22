Quickstart
==========

This guide walks through constructing a complete, production-grade API resource
using drf-commons. It assumes familiarity with Django, Django REST Framework,
and the concept of serializers and viewsets.

Defining a Model
----------------

drf-commons model mixins are composable. The highest-level mixin,
:class:`~drf_commons.models.base.BaseModelMixin`, composes timestamping,
user action tracking, soft deletion, and JSON serialization:

.. code-block:: python

   from django.db import models
   from drf_commons.models import BaseModelMixin

   class Article(BaseModelMixin):
       title = models.CharField(max_length=255)
       content = models.TextField()
       published = models.BooleanField(default=False)
       published_at = models.DateTimeField(null=True, blank=True)

       class Meta:
           ordering = ["-created_at"]

       def __str__(self):
           return self.title

``Article`` now has:

* ``id`` — UUID primary key
* ``created_at``, ``updated_at`` — auto-populated timestamps
* ``created_by``, ``updated_by`` — auto-populated from the request context
* ``is_active``, ``deleted_at`` — soft delete support
* ``get_json()`` — flexible JSON serialization

No migrations beyond ``python manage.py makemigrations`` are required.

Defining a Serializer
---------------------

:class:`~drf_commons.serializers.base.BaseModelSerializer` is a drop-in
replacement for DRF's ``ModelSerializer`` that adds atomic write handling and
configurable relation fields:

.. code-block:: python

   from django.contrib.auth import get_user_model
   from drf_commons.serializers import BaseModelSerializer
   from drf_commons.serializers.fields import IdToDataField

   User = get_user_model()

   class UserSummarySerializer(BaseModelSerializer):
       class Meta:
           model = User
           fields = ["id", "username", "email"]

   class ArticleSerializer(BaseModelSerializer):
       # Accept a user ID on write; return the nested UserSummarySerializer on read
       created_by = IdToDataField(
           queryset=User.objects.all(),
           serializer=UserSummarySerializer,
           read_only=True,
       )

       class Meta:
           model = Article
           fields = [
               "id",
               "title",
               "content",
               "published",
               "published_at",
               "created_by",
               "created_at",
               "updated_at",
           ]

Defining a ViewSet
------------------

:class:`~drf_commons.views.base.BaseViewSet` provides full CRUD plus file
export with standardized response formatting:

.. code-block:: python

   from rest_framework.permissions import IsAuthenticated
   from drf_commons.views import BaseViewSet

   class ArticleViewSet(BaseViewSet):
       queryset = Article.objects.filter(is_active=True).select_related("created_by")
       serializer_class = ArticleSerializer
       permission_classes = [IsAuthenticated]

       # Optional: configure file export columns
       export_field_config = {
           "title": "Title",
           "published": "Published",
           "created_at": "Created At",
       }

Registering Routes
------------------

Use DRF's router as usual:

.. code-block:: python

   # urls.py
   from rest_framework.routers import DefaultRouter
   from .views import ArticleViewSet

   router = DefaultRouter()
   router.register("articles", ArticleViewSet, basename="article")

   urlpatterns = router.urls

Available endpoints:

.. list-table::
   :widths: 15 15 70
   :header-rows: 1

   * - Method
     - URL
     - Action
   * - ``GET``
     - ``/articles/``
     - List articles (paginated or full, based on ``?paginated=true``)
   * - ``POST``
     - ``/articles/``
     - Create an article
   * - ``GET``
     - ``/articles/{id}/``
     - Retrieve an article
   * - ``PUT``
     - ``/articles/{id}/``
     - Full update
   * - ``PATCH``
     - ``/articles/{id}/``
     - Partial update
   * - ``DELETE``
     - ``/articles/{id}/``
     - Delete an article
   * - ``POST``
     - ``/articles/export/``
     - Export articles to CSV/XLSX/PDF

Enabling Bulk Operations
------------------------

Replace :class:`~drf_commons.views.base.BaseViewSet` with
:class:`~drf_commons.views.base.BulkViewSet`:

.. code-block:: python

   from drf_commons.views import BulkViewSet

   class ArticleViewSet(BulkViewSet):
       queryset = Article.objects.filter(is_active=True)
       serializer_class = ArticleSerializer
       permission_classes = [IsAuthenticated]

Additional endpoints:

.. list-table::
   :widths: 15 25 60
   :header-rows: 1

   * - Method
     - URL
     - Action
   * - ``POST``
     - ``/articles/bulk-create/``
     - Bulk create articles
   * - ``PUT``
     - ``/articles/bulk-update/``
     - Bulk full update
   * - ``PATCH``
     - ``/articles/bulk-update/``
     - Bulk partial update
   * - ``DELETE``
     - ``/articles/bulk-delete/``
     - Bulk delete by IDs
   * - ``DELETE``
     - ``/articles/bulk-soft-delete/``
     - Bulk soft delete by IDs

Response Format
---------------

All drf-commons viewsets return responses in a standardized envelope:

**Success (list)**:

.. code-block:: json

   {
     "success": true,
     "timestamp": "2024-01-15T10:30:00.000000Z",
     "message": "",
     "data": [
       {"id": "...", "title": "...", "index": 1},
       {"id": "...", "title": "...", "index": 2}
     ]
   }

**Success (create)**:

.. code-block:: json

   {
     "success": true,
     "timestamp": "2024-01-15T10:30:00.000000Z",
     "message": "",
     "data": {"id": "...", "title": "My Article"}
   }

**Validation error**:

.. code-block:: json

   {
     "success": false,
     "timestamp": "2024-01-15T10:30:00.000000Z",
     "message": "Validation failed.",
     "errors": {
       "title": ["This field is required."]
     },
     "data": null
   }

Next Steps
----------

* :doc:`models` — Complete model mixin reference
* :doc:`views` — ViewSet classes and mixin reference
* :doc:`serializers` — Serializer and field reference
* :doc:`services` — Import/export service documentation
* :doc:`architecture` — Design rationale and system architecture
