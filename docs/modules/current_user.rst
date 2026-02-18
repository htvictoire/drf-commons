current_user
============

Source modules:

- ``drf_commons/current_user/utils.py``
- ``drf_commons/middlewares/current_user.py``

Why this exists
---------------

Problem
^^^^^^^

Model layer code (for example ``save()`` hooks) often needs current actor, but DRF request objects are unavailable there.

Default DRF behavior
^^^^^^^^^^^^^^^^^^^^

DRF exposes ``request.user`` in views/serializers via context, but does not propagate it automatically into model-level utilities.

How ``drf-commons`` solves it
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A ``threading.local`` holder stores a callable that resolves current user for the active synchronous request thread.

Core mechanics
--------------

Storage
^^^^^^^

- thread-local object: ``_thread_locals = local()``
- attribute name from ``settings.LOCAL_USER_ATTR_NAME``

Setter primitives
^^^^^^^^^^^^^^^^^

- ``_do_set_current_user(user_fun)`` stores callable bound through descriptor protocol,
- ``_set_current_user(user=None)`` stores lambda returning fixed user (useful for manual context seeding).

Getter primitives
^^^^^^^^^^^^^^^^^

- ``get_current_user()`` resolves stored callable/value or ``None``,
- ``get_current_authenticated_user()`` returns ``None`` for ``AnonymousUser``.

Middleware lifecycle
^^^^^^^^^^^^^^^^^^^^

``SetCurrentUser`` context manager:

- ``__enter__`` stores lambda returning ``request.user``,
- ``__exit__`` resets storage to lambda returning ``None``.

``CurrentUserMiddleware`` wraps request handling with this context manager.

Edge cases and failure modes
----------------------------

- Storage is ``threading.local``; actor context is isolated per thread and does not propagate across asyncio task boundaries.
- In async/background contexts without explicit seeding, getters return ``None``.
- Thread-local does not cross process boundaries or worker queues.
- Long-running worker threads that manually set current user must clear it to avoid leakage across tasks.

Performance implications
------------------------

Overhead is negligible relative to request processing: one lambda bind/unbind per request and function call for retrieval.

Trade-offs
----------

Pros:

- avoids passing actor through many call layers,
- enables model hooks to access request actor.

Cons:

- implicit context can obscure data flow,
- tightly tied to middleware correctness,
- not a substitute for distributed context propagation.

When not to use
---------------

- systems with primarily async/event-driven writes,
- architectures enforcing explicit dependency injection of actor context.

Alternatives
------------

- explicit ``actor`` argument in service layer methods,
- contextvars-based propagation for async-aware designs,
- audit-event table populated in API/service layer.

Integration pattern
-------------------

Typical integration:

.. code-block:: python

   MIDDLEWARE = [
       # ...
       "drf_commons.middlewares.current_user.CurrentUserMiddleware",
   ]

   # model mixins/fields then consume get_current_authenticated_user()

Migration strategy
------------------

1. add middleware in all Django entry points that serve API requests,
2. enable model mixins/fields requiring current user,
3. audit non-request write paths and seed actor explicitly where required.

Compatibility concerns
----------------------

- behavior assumes Django request lifecycle semantics,
- correctness depends on middleware execution order including authentication middleware upstream.
- ASGI deployments should not treat this mechanism as async-context propagation for work executed outside request thread scope.
