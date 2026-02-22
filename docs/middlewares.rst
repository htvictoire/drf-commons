Middlewares
===========

drf-commons includes middleware for request context management and development
debugging.

CurrentUserMiddleware
---------------------

.. code-block:: python

   from drf_commons.middlewares import CurrentUserMiddleware

The most important middleware in drf-commons. Sets the authenticated request
user into a ``ContextVar`` for the duration of each request, enabling
automatic audit field population at the model layer without serializer context
threading.

**Configuration**:

.. code-block:: python

   MIDDLEWARE = [
       "django.middleware.security.SecurityMiddleware",
       "django.contrib.sessions.middleware.SessionMiddleware",
       "django.middleware.common.CommonMiddleware",
       "django.contrib.auth.middleware.AuthenticationMiddleware",
       # Must come after AuthenticationMiddleware:
       "drf_commons.middlewares.CurrentUserMiddleware",
       ...
   ]

**Async support**:

``CurrentUserMiddleware`` detects whether the handler is a coroutine function
and dispatches to the appropriate sync or async implementation:

.. code-block:: python

   # Sync handler path (WSGI)
   def __call__(self, request):
       token = _set_current_user(request.user)
       try:
           response = self.get_response(request)
       finally:
           _reset_current_user(token)
       return response

   # Async handler path (ASGI)
   async def __acall__(self, request):
       token = _set_current_user(request.user)
       try:
           response = await self.get_response(request)
       finally:
           _reset_current_user(token)
       return response

The ``finally`` block guarantees the context is always reset, even if the
handler raises an exception. The reset token pattern (rather than
``ContextVar.set(None)``) ensures that nested middleware chains maintain
correct context state.

**Context API**:

.. code-block:: python

   from drf_commons.current_user import get_current_user, get_current_authenticated_user

   # Get user (may be anonymous)
   user = get_current_user()           # Returns User or AnonymousUser or None

   # Get authenticated user only
   user = get_current_authenticated_user()  # Returns User, raises if not authenticated

Debug Middlewares
-----------------

Debug middlewares are intended for **development environments only**. Do not
enable them in production — they add significant overhead.

DebugMiddleware
~~~~~~~~~~~~~~~

.. code-block:: python

   from drf_commons.middlewares import DebugMiddleware

Base debug middleware. Tracks request context and timing metadata. Parent class
for the specialized debug middlewares.

SQLDebugMiddleware
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from drf_commons.middlewares import SQLDebugMiddleware

Captures all SQL queries executed during a request and logs:

* Total query count
* Individual query durations
* Slow queries (above ``DEBUG_SLOW_QUERY_THRESHOLD``)
* Alerts when query count exceeds ``DEBUG_HIGH_QUERY_COUNT_THRESHOLD``

**Configuration**:

.. code-block:: python

   COMMON = {
       "DEBUG_SLOW_QUERY_THRESHOLD": 0.1,          # seconds per query
       "DEBUG_HIGH_QUERY_COUNT_THRESHOLD": 10,     # query count alert
   }

**Development setup**:

.. code-block:: python

   # settings/development.py
   if DEBUG:
       MIDDLEWARE += [
           "drf_commons.middlewares.SQLDebugMiddleware",
       ]

ProfilerMiddleware
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from drf_commons.middlewares import ProfilerMiddleware

Profiles request handler execution using Python's ``cProfile``. Logs function
call statistics for slow requests (above ``DEBUG_SLOW_REQUEST_THRESHOLD``).

.. code-block:: python

   COMMON = {
       "DEBUG_SLOW_REQUEST_THRESHOLD": 1.0,  # seconds; log profiling data above this
   }

**Development setup**:

.. code-block:: python

   if DEBUG:
       MIDDLEWARE += [
           "drf_commons.middlewares.ProfilerMiddleware",
       ]

Middleware Order Reference
--------------------------

Recommended middleware order for a project using all drf-commons middleware:

.. code-block:: python

   MIDDLEWARE = [
       "django.middleware.security.SecurityMiddleware",
       "whitenoise.middleware.WhiteNoiseMiddleware",       # if using whitenoise
       "django.contrib.sessions.middleware.SessionMiddleware",
       "django.middleware.common.CommonMiddleware",
       "django.middleware.csrf.CsrfViewMiddleware",
       "django.contrib.auth.middleware.AuthenticationMiddleware",
       "drf_commons.middlewares.CurrentUserMiddleware",   # after auth
       "django.contrib.messages.middleware.MessageMiddleware",
       "django.middleware.clickjacking.XFrameOptionsMiddleware",
   ]

   # Development only:
   if DEBUG:
       MIDDLEWARE += [
           "drf_commons.middlewares.SQLDebugMiddleware",
           "drf_commons.middlewares.ProfilerMiddleware",
       ]
