Current User
============

The ``current_user`` subsystem provides async-safe, request-scoped user
resolution using Python's :class:`contextvars.ContextVar`.

Motivation
----------

The standard DRF pattern for accessing the current user in nested components
(serializers, signals, model methods) involves threading ``request`` or
``request.user`` through each function call. This creates coupling between
the request object and business logic, complicates testing, and fails silently
in async contexts when thread-local storage is used instead.

drf-commons uses a ``ContextVar`` — a value scoped to the current execution
context (thread in WSGI, coroutine in ASGI) — set once per request by
``CurrentUserMiddleware`` and readable anywhere in the call stack without
explicit propagation.

Public API
----------

.. code-block:: python

   from drf_commons.current_user import (
       get_current_user,
       get_current_authenticated_user,
   )

get_current_user
~~~~~~~~~~~~~~~~

Returns the user currently stored in the context variable.

.. code-block:: python

   user = get_current_user()

Returns:

* The authenticated ``User`` instance if the request user is authenticated
* ``AnonymousUser`` if the request user is not authenticated
* ``None`` if called outside a request context (e.g., management commands, Celery tasks)

get_current_authenticated_user
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Returns the authenticated user. Raises if the user is not authenticated or if
called outside a request context.

.. code-block:: python

   user = get_current_authenticated_user()

Use this in contexts where an authenticated user is required:

* ``UserActionMixin.save()`` — populates ``created_by`` / ``updated_by``
* ``CurrentUserField.default`` — populates FK on model creation

Internal API
------------

The following functions are internal to drf-commons and should not be called
directly in application code:

.. code-block:: python

   from drf_commons.current_user.utils import (
       _set_current_user,
       _reset_current_user,
       _clear_current_user,
   )

* ``_set_current_user(user)`` — Sets the context variable, returns a reset token
* ``_reset_current_user(token)`` — Resets the context variable to its previous state
* ``_clear_current_user()`` — Sets the context variable to ``None``

The token-based reset pattern is essential for correctness in async contexts
where coroutines may share a context chain. Using tokens preserves the previous
state rather than clearing it unconditionally.

Usage Outside Request Context
------------------------------

In management commands, Celery tasks, or other non-request contexts, the
context variable is not set by middleware. You can manually set it when
necessary:

.. code-block:: python

   from django.contrib.auth import get_user_model
   from drf_commons.current_user.utils import _set_current_user, _reset_current_user

   User = get_user_model()

   def run_as_user(user_id: int, fn: callable):
       """Execute fn() with the context user set to the given user."""
       user = User.objects.get(pk=user_id)
       token = _set_current_user(user)
       try:
           return fn()
       finally:
           _reset_current_user(token)

This pattern is useful in Celery tasks that perform model modifications and
need ``UserActionMixin`` audit trail population.

Testing with Context User
--------------------------

In tests, set the context user directly:

.. code-block:: python

   from drf_commons.current_user.utils import _set_current_user, _reset_current_user

   class ArticleCreateTestCase(TestCase):
       def test_creates_with_correct_author(self):
           user = UserFactory()
           token = _set_current_user(user)
           try:
               article = Article.objects.create(title="Test", content="Body")
               assert article.created_by == user
           finally:
               _reset_current_user(token)

Or use the provided test utilities and factories from
``drf_commons.common_tests``, which handle this automatically.
