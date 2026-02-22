Production Usage
================

This page covers deployment considerations, stability guarantees, and
operational guidance for drf-commons in production environments.

Stability Guarantees
--------------------

**Versioning**

drf-commons follows `Semantic Versioning <https://semver.org/>`_. The public
API (all components documented in this reference) will not introduce breaking
changes within a major version. Internal modules (prefixed with ``_`` or
located under ``common_conf/``) are not part of the public API.

**Django version support**

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Django Version
     - Support Status
   * - 3.2 LTS
     - Fully supported
   * - 4.0, 4.1, 4.2 LTS
     - Fully supported
   * - 5.0, 5.1, 5.2 LTS
     - Fully supported
   * - 6.0
     - Fully supported

**Python version support**

Python 3.8, 3.9, 3.10, 3.11, 3.12, 3.13, 3.14 — all fully supported.

WSGI and ASGI Deployment
------------------------

drf-commons is tested under both WSGI (Gunicorn, uWSGI) and ASGI (Uvicorn,
Daphne) deployments. ``CurrentUserMiddleware`` uses ``ContextVar``, which is
safe in both contexts.

**WSGI (Gunicorn)**:

.. code-block:: bash

   gunicorn myproject.wsgi:application --workers 4

``ContextVar`` in WSGI contexts behaves identically to thread-local storage
but is implementationally cleaner.

**ASGI (Uvicorn)**:

.. code-block:: bash

   uvicorn myproject.asgi:application --workers 4

Under ASGI, each request coroutine has its own context. The context variable
set by ``CurrentUserMiddleware`` is scoped to the coroutine's context, not
leaked to other concurrent requests.

Database Considerations
------------------------

Bulk Operations
~~~~~~~~~~~~~~~

**Batch sizing**: The default ``BULK_OPERATION_BATCH_SIZE`` of 1000 is
appropriate for most PostgreSQL deployments. For MySQL, consider reducing to
500 due to different locking behavior during bulk writes.

**Transaction scope**: Each bulk operation (create, update, delete) is wrapped
in a single ``atomic()`` block. Under PostgreSQL, this means a single
transaction lock for the duration of the batch. Size batches appropriately
to avoid long-lived transactions under high write concurrency.

**Soft delete and indexes**: Models using ``SoftDeleteMixin`` should have a
partial index on ``is_active``:

.. code-block:: python

   class Article(BaseModelMixin):
       class Meta:
           indexes = [
               models.Index(
                   fields=["is_active"],
                   condition=models.Q(is_active=True),
                   name="article_active_idx",
               )
           ]

UUID Primary Keys
~~~~~~~~~~~~~~~~~

``BaseModelMixin`` uses UUID primary keys (random ``uuid4``). Under PostgreSQL,
random UUID inserts can cause B-tree index fragmentation. For very
high-insert-rate tables, consider:

* Using ``UUIDField(default=uuid.uuid4)`` with a ULID or UUIDv7 (ordered)
  default for better index locality
* Explicitly setting ``Meta.ordering`` to prevent full-table scans

Connection Pooling
~~~~~~~~~~~~~~~~~~

drf-commons does not manage database connections. Use Django's built-in
connection pooling (Django 4.2+) or external poolers (PgBouncer, pgpool-II):

.. code-block:: python

   # Django 4.2+ connection pooling
   DATABASES = {
       "default": {
           "ENGINE": "django.db.backends.postgresql",
           "OPTIONS": {
               "pool": {
                   "min_size": 2,
                   "max_size": 10,
               }
           },
       }
   }

Caching
-------

drf-commons does not implement application-level caching. Response caching
for read-heavy endpoints should be implemented at the view layer using Django's
cache framework or a reverse proxy (Nginx, Varnish, Cloudflare).

The ``cache_debug`` decorator provides visibility into cache operation timing
for development debugging but does not implement caching itself.

Security
--------

Response Data Sanitization
~~~~~~~~~~~~~~~~~~~~~~~~~~

``api_request_logger`` automatically redacts common sensitive fields from
logged request bodies. Verify the default redaction list covers your
application's sensitive fields and extend it if necessary:

.. code-block:: python

   @api_request_logger(
       log_body=True,
       redact_fields=["ssn", "tax_id", "card_number", "cvv"],
   )

Export Authorization
~~~~~~~~~~~~~~~~~~~~

File export endpoints return potentially sensitive data. Apply appropriate
permission classes and rate limiting:

.. code-block:: python

   class EmployeeViewSet(BaseViewSet):
       permission_classes = [IsAuthenticated, IsHRManager]

Bulk Deletion Safeguards
~~~~~~~~~~~~~~~~~~~~~~~~~

Bulk delete endpoints accept lists of IDs and delete them without additional
confirmation. Implement safeguards for sensitive resources:

.. code-block:: python

   class CriticalResourceViewSet(BulkViewSet):
       def bulk_delete(self, request, *args, **kwargs):
           # Require supervisor confirmation header
           if not request.headers.get("X-Confirm-Delete"):
               return error_response(
                   message="Bulk delete requires X-Confirm-Delete header.",
                   status_code=428,
               )
           return super().bulk_delete(request, *args, **kwargs)

Monitoring and Observability
-----------------------------

**Structured logging**:

``StructuredLogger`` emits JSON-structured log records compatible with log
aggregation systems (ELK Stack, Datadog, CloudWatch Logs):

.. code-block:: python

   # settings.py
   LOGGING = {
       "version": 1,
       "formatters": {
           "json": {
               "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
               "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
           }
       },
       "handlers": {
           "json_file": {
               "class": "logging.handlers.RotatingFileHandler",
               "filename": "/var/log/myapp/api.log",
               "formatter": "json",
               "maxBytes": 100 * 1024 * 1024,  # 100MB
               "backupCount": 5,
           }
       },
       "root": {
           "handlers": ["json_file"],
           "level": "INFO",
       },
   }

**Performance alerting**:

Configure ``DEBUG_SLOW_REQUEST_THRESHOLD`` and ``DEBUG_HIGH_QUERY_COUNT_THRESHOLD``
to generate log entries for slow requests and high-query endpoints. Route these
to a separate log destination for alerting:

.. code-block:: python

   COMMON = {
       "DEBUG_SLOW_REQUEST_THRESHOLD": 0.5,          # Alert on requests > 500ms
       "DEBUG_HIGH_QUERY_COUNT_THRESHOLD": 15,       # Alert on > 15 queries/request
   }

Integration with Large Systems
-------------------------------

**Microservice patterns**:

In microservice architectures, drf-commons is deployed per-service. Each
service has independent settings, independent ``BULK_OPERATION_BATCH_SIZE``
tuning, and independent middleware configuration. There is no cross-service
shared state.

**API Gateway integration**:

The standardized response envelope simplifies API Gateway response mapping.
The ``success`` boolean and ``errors`` structure provide a consistent contract
for gateway-level error handling.

**Event-driven architecture**:

For models using ``UserActionMixin``, the ``created_by`` / ``updated_by``
fields provide an audit trail that can be published to an event stream on
``post_save``:

.. code-block:: python

   from django.db.models.signals import post_save
   from django.dispatch import receiver

   @receiver(post_save, sender=Article)
   def publish_article_event(sender, instance, created, **kwargs):
       event = {
           "type": "article.created" if created else "article.updated",
           "id": str(instance.id),
           "actor": str(instance.created_by_id if created else instance.updated_by_id),
           "timestamp": instance.created_at.isoformat() if created else instance.updated_at.isoformat(),
       }
       event_bus.publish("articles", event)
