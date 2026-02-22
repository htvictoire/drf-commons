Best Practices
==============

This page documents recommended patterns for production drf-commons deployments.

Model Design
------------

**Always define explicit QuerySet scope on ViewSets**

drf-commons does not automatically exclude soft-deleted records. Define the
queryset scope explicitly:

.. code-block:: python

   class ArticleViewSet(BaseViewSet):
       # Always explicit — include select_related/prefetch_related for performance
       queryset = (
           Article.objects
           .filter(is_active=True)
           .select_related("created_by", "category")
           .prefetch_related("tags")
       )

**Minimize the BaseModelMixin stack when not needed**

Not every model needs UUID primary keys, user tracking, and soft deletes.
Compose only what you need:

.. code-block:: python

   # Full stack: only for main domain objects
   class Order(BaseModelMixin): ...

   # Timestamps only: for join/through tables
   class OrderTag(TimeStampMixin, models.Model): ...

   # No drf-commons mixins: for lookup/reference tables
   class Country(models.Model): ...

Serializer Design
-----------------

**Use the most restrictive field type that satisfies requirements**

Prefer ``IdToDataField`` over ``FlexibleField`` when the client always sends
IDs. ``FlexibleField``'s auto-detection adds overhead and ambiguity.

.. code-block:: python

   # Good: specific, predictable
   author = IdToDataField(queryset=User.objects.all(), serializer=UserSerializer)

   # Use only when client contract genuinely requires flexible input
   author = FlexibleField(queryset=User.objects.all(), serializer=UserSerializer)

**Avoid deep serializer nesting in list endpoints**

Nested serializers in list responses cause N+1 queries unless properly
prefetched. For list endpoints, prefer flat representations:

.. code-block:: python

   class ArticleListSerializer(BaseModelSerializer):
       author_name = serializers.CharField(source="created_by.get_full_name")

       class Meta:
           model = Article
           fields = ["id", "title", "author_name", "created_at"]

   class ArticleDetailSerializer(BaseModelSerializer):
       author = IdToDataField(queryset=User.objects.all(), serializer=UserSerializer)

       class Meta:
           model = Article
           fields = ["id", "title", "content", "author", "created_at", "updated_at"]

   class ArticleViewSet(BaseViewSet):
       def get_serializer_class(self):
           if self.action == "list":
               return ArticleListSerializer
           return ArticleDetailSerializer

ViewSet Design
--------------

**Always specify permission_classes**

drf-commons ViewSets do not impose default permission classes. Always be
explicit:

.. code-block:: python

   class ArticleViewSet(BaseViewSet):
       permission_classes = [IsAuthenticated]  # Always explicit

**Use bulk operations for large datasets**

For any operation touching more than ~10 records, use bulk endpoints:

.. code-block:: python

   # Don't create 500 articles via 500 POST /articles/ calls
   # Do: POST /articles/bulk-create/ with list of 500 objects

**Define explicit ordering**

Always define ``ordering_fields`` on ViewSets that use
``ComputedOrderingFilter`` to prevent exposure of arbitrary database field
ordering:

.. code-block:: python

   class ArticleViewSet(BaseViewSet):
       filter_backends = [ComputedOrderingFilter]
       ordering_fields = ["title", "created_at"]  # Explicit allowlist
       ordering = ["-created_at"]                 # Default ordering

Bulk Operations
---------------

**Tune batch sizes per environment**

The default ``BULK_OPERATION_BATCH_SIZE`` of 1000 may be too large for
memory-constrained deployments or too small for high-throughput systems:

.. code-block:: python

   # settings/production.py
   COMMON = {
       "BULK_OPERATION_BATCH_SIZE": 500,   # Conservative for memory
   }

   # settings/batch_worker.py (for dedicated batch processing workers)
   COMMON = {
       "BULK_OPERATION_BATCH_SIZE": 5000,
   }

**Use soft delete for user-controlled deletion**

Prefer soft delete for any resource that a user might delete:

.. code-block:: python

   class ArticleViewSet(BaseViewSet):
       def perform_destroy(self, instance):
           instance.soft_delete()

       @action(detail=True, methods=["post"])
       def restore(self, request, pk=None):
           article = self.get_object()
           article.restore()
           return success_response(message="Article restored.")

File Import/Export
------------------

**Validate import configuration at startup**

Use ``ConfigValidator`` or test the import config in application tests to catch
configuration errors before deploying:

.. code-block:: python

   class EmployeeImportTest(TestCase):
       def test_import_config_valid(self):
           from drf_commons.services.import_from_file.config import ConfigValidator
           validator = ConfigValidator(EmployeeViewSet.import_file_config)
           validator.validate()  # Raises on invalid config

**Restrict file export to authorized users**

Export endpoints return potentially sensitive data. Apply permission classes:

.. code-block:: python

   class EmployeeViewSet(BaseViewSet):
       permission_classes = [IsAuthenticated]
       export_permission_classes = [IsAdminUser]  # Stricter for export

**Use chunk_size for large imports**

Any import expected to exceed 1000 rows should use ``chunk_size``:

.. code-block:: python

   import_file_config = {
       "chunk_size": 250,
       ...
   }

Performance
-----------

**Prefer ``use_save_on_bulk_update = False`` for pure data updates**

When signal handlers are not required, the default ``bulk_update()`` mode
reduces database round-trips from N to 1:

.. code-block:: python

   class ProductPriceViewSet(BulkUpdateViewSet):
       use_save_on_bulk_update = False  # 1 SQL UPDATE for all records

**Use ``ReadOnlyViewSet`` for read-heavy resources**

Restricting a resource to read-only removes the overhead of write permission
checks and response serialization for mutation operations:

.. code-block:: python

   class CountryViewSet(ReadOnlyViewSet):
       queryset = Country.objects.all().order_by("name")
       serializer_class = CountrySerializer
       pagination_class = None  # Small, fixed dataset — no pagination needed

Testing
-------

**Use drf-commons test factories in all tests**

.. code-block:: python

   from drf_commons.common_tests.factories import UserFactory, StaffUserFactory

   class ArticleViewSetTest(TestCase):
       def setUp(self):
           self.user = UserFactory()
           self.staff = StaffUserFactory()
           self.client = APIClient()
           self.client.force_authenticate(user=self.user)

**Set the context user in model-level tests**

.. code-block:: python

   from drf_commons.current_user.utils import _set_current_user, _reset_current_user

   class UserActionMixinTest(TestCase):
       def test_created_by_populated(self):
           user = UserFactory()
           token = _set_current_user(user)
           try:
               article = Article.objects.create(title="Test", content="Body")
               self.assertEqual(article.created_by, user)
           finally:
               _reset_current_user(token)
