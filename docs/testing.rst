Testing
=======

drf-commons includes testing infrastructure to simplify writing tests for
applications built on the library.

Test Factories
--------------

.. code-block:: python

   from drf_commons.common_tests.factories import (
       UserFactory,
       StaffUserFactory,
       SuperUserFactory,
   )

Built with `factory_boy <https://factoryboy.readthedocs.io/>`_.

UserFactory
~~~~~~~~~~~

Generates test users with sequential usernames:

.. code-block:: python

   user1 = UserFactory()                    # username="user1"
   user2 = UserFactory()                    # username="user2"
   custom = UserFactory(username="alice")   # username="alice"
   with_email = UserFactory(email="alice@example.com")

By default:

* Username: ``user{n}`` (sequentially numbered)
* Email: ``{username}@example.com``
* Password: set via ``post_generation`` hook

StaffUserFactory
~~~~~~~~~~~~~~~~

Like ``UserFactory`` but with ``is_staff=True``:

.. code-block:: python

   staff = StaffUserFactory()

SuperUserFactory
~~~~~~~~~~~~~~~~

Like ``UserFactory`` but with ``is_staff=True`` and ``is_superuser=True``:

.. code-block:: python

   superuser = SuperUserFactory()

APIRequestFactoryWithUser
--------------------------

.. code-block:: python

   from drf_commons.common_tests.factories import APIRequestFactoryWithUser

A DRF ``APIRequestFactory`` wrapper that returns pre-authenticated DRF
``Request`` objects:

.. code-block:: python

   factory = APIRequestFactoryWithUser(user=UserFactory())

   request = factory.get("/api/articles/")
   request = factory.post("/api/articles/", data={"title": "Test"})
   request = factory.patch("/api/articles/1/", data={"title": "Updated"})
   request = factory.delete("/api/articles/1/")

All returned requests are DRF ``Request`` objects with ``request.user``
pre-set to the factory's user.

Testing with Context User
--------------------------

Model-level tests that exercise ``UserActionMixin`` or ``CurrentUserField``
must set the context user manually:

.. code-block:: python

   from django.test import TestCase
   from drf_commons.common_tests.factories import UserFactory
   from drf_commons.current_user.utils import _set_current_user, _reset_current_user

   class ArticleModelTest(TestCase):
       def test_created_by_auto_populated(self):
           user = UserFactory()
           token = _set_current_user(user)
           try:
               article = Article.objects.create(title="Test", content="Body")
               self.assertEqual(article.created_by, user)
               self.assertIsNotNone(article.created_at)
           finally:
               _reset_current_user(token)

       def test_updated_by_changes_on_save(self):
           initial_user = UserFactory()
           updating_user = UserFactory()

           token = _set_current_user(initial_user)
           try:
               article = Article.objects.create(title="Test", content="Body")
           finally:
               _reset_current_user(token)

           token = _set_current_user(updating_user)
           try:
               article.title = "Updated"
               article.save()
               article.refresh_from_db()
               self.assertEqual(article.updated_by, updating_user)
           finally:
               _reset_current_user(token)

Testing ViewSets
----------------

Use DRF's ``APIClient`` for ViewSet integration tests:

.. code-block:: python

   from django.test import TestCase
   from rest_framework.test import APIClient
   from drf_commons.common_tests.factories import UserFactory

   class ArticleViewSetTest(TestCase):
       def setUp(self):
           self.user = UserFactory()
           self.client = APIClient()
           self.client.force_authenticate(user=self.user)

       def test_list_returns_standardized_envelope(self):
           response = self.client.get("/api/articles/")
           self.assertEqual(response.status_code, 200)
           self.assertTrue(response.data["success"])
           self.assertIn("data", response.data)
           self.assertIn("timestamp", response.data)

       def test_create_returns_201(self):
           response = self.client.post(
               "/api/articles/",
               {"title": "Test Article", "content": "Body"},
               format="json",
           )
           self.assertEqual(response.status_code, 201)
           self.assertTrue(response.data["success"])

       def test_bulk_create(self):
           data = [
               {"title": f"Article {i}", "content": "Body"}
               for i in range(10)
           ]
           response = self.client.post(
               "/api/articles/bulk-create/",
               data,
               format="json",
           )
           self.assertEqual(response.status_code, 201)

Testing Soft Deletes
--------------------

.. code-block:: python

   def test_soft_delete_does_not_remove_record(self):
       article = Article.objects.create(title="Test", content="Body")
       article.soft_delete()

       # Not returned by is_active queryset
       self.assertFalse(Article.objects.filter(is_active=True, pk=article.pk).exists())

       # Still in database
       self.assertTrue(Article.objects.filter(pk=article.pk).exists())

   def test_restore_reactivates_record(self):
       article = Article.objects.create(title="Test", content="Body")
       article.soft_delete()
       article.restore()

       self.assertTrue(Article.objects.filter(is_active=True, pk=article.pk).exists())
       article.refresh_from_db()
       self.assertIsNone(article.deleted_at)

Testing Version Conflicts
--------------------------

.. code-block:: python

   from drf_commons.models.content import VersionConflictError

   def test_version_conflict_raises(self):
       doc = Document.objects.create(body="Initial")

       # Simulate concurrent reads
       doc_a = Document.objects.get(pk=doc.pk)
       doc_b = Document.objects.get(pk=doc.pk)

       # First write succeeds
       doc_a.body = "Updated by A"
       doc_a.increment_version()
       doc_a.save()

       # Second write raises conflict
       doc_b.body = "Updated by B"
       doc_b.increment_version()
       with self.assertRaises(VersionConflictError):
           doc_b.save()

Integration Tests
-----------------

drf-commons ships with integration tests in ``drf_commons/tests/``:

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - Test File
     - Coverage
   * - ``test_e2e.py``
     - End-to-end API request/response cycles
   * - ``test_bulk_update_modes.py``
     - Bulk update vs. save mode equivalence
   * - ``test_viewset_integration.py``
     - ViewSet composition and action dispatch
   * - ``test_middleware_integration.py``
     - Middleware context propagation
   * - ``test_service_integration.py``
     - Import/export service integration
   * - ``test_installation.py``
     - Package import and configuration validation

Run all integration tests:

.. code-block:: bash

   pytest drf_commons/tests/
