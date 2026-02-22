Decorators
==========

drf-commons provides a suite of function/method decorators for logging,
performance monitoring, query analysis, and cache debugging.

.. code-block:: python

   from drf_commons.decorators import (
       api_request_logger,
       log_function_call,
       log_exceptions,
       log_db_query,
       api_performance_monitor,
       cache_debug,
   )

api_request_logger
------------------

Logs incoming API requests and outgoing responses with configurable field
redaction.

.. code-block:: python

   @api_request_logger(
       log_body: bool = True,
       log_headers: bool = False,
       redact_fields: list = None,     # Additional fields to redact
       max_body_length: int = 1000,    # Truncate body beyond this length
   )

**Default redacted fields** (always sanitized regardless of configuration):

* Authorization headers
* ``password``, ``token``, ``api_key``, ``secret``, ``access_token``

**Usage**:

.. code-block:: python

   from drf_commons.decorators import api_request_logger
   from rest_framework.views import APIView

   class PaymentView(APIView):
       @api_request_logger(log_body=True, log_headers=False, redact_fields=["card_number"])
       def post(self, request):
           ...

**Log output example**:

.. code-block:: json

   {
     "event": "api_request",
     "method": "POST",
     "path": "/api/payments/",
     "user": "john@example.com",
     "body": {"amount": "99.99", "card_number": "[REDACTED]"},
     "duration_ms": 145.3,
     "status_code": 201
   }

log_function_call
-----------------

Logs function invocations with timing information and optional argument/result
capture.

.. code-block:: python

   @log_function_call(
       logger_name: str = "drf_commons",
       log_args: bool = False,
       log_result: bool = False,
       category: str = None,
   )

**Usage**:

.. code-block:: python

   from drf_commons.decorators import log_function_call

   @log_function_call(
       logger_name="billing",
       log_args=True,
       log_result=True,
       category="BILLING",
   )
   def calculate_invoice_total(invoice_id: int, apply_discount: bool = False):
       ...

**Log output** (on call):

.. code-block:: json

   {
     "event": "function_call",
     "function": "calculate_invoice_total",
     "args": {"invoice_id": 42, "apply_discount": false},
     "duration_ms": 23.1,
     "result": {"total": "149.99", "currency": "USD"}
   }

log_exceptions
--------------

Logs exceptions raised within a function. Optionally suppresses re-raising.

.. code-block:: python

   @log_exceptions(
       logger_name: str = "drf_commons",
       reraise: bool = True,
   )

**Usage**:

.. code-block:: python

   from drf_commons.decorators import log_exceptions

   @log_exceptions(logger_name="payments", reraise=True)
   def charge_card(amount, card_token):
       # Exceptions logged with full context and re-raised
       ...

   @log_exceptions(logger_name="notifications", reraise=False)
   def send_welcome_email(user_id):
       # Exceptions logged but suppressed; function returns None on failure
       ...

log_db_query
------------

Monitors database queries executed during function execution. Logs query
count, individual queries, and execution time.

.. code-block:: python

   @log_db_query(query_type: str = "unknown")

**Usage**:

.. code-block:: python

   from drf_commons.decorators import log_db_query

   @log_db_query(query_type="read")
   def get_dashboard_data(user_id: int):
       articles = Article.objects.filter(created_by_id=user_id).count()
       comments = Comment.objects.filter(author_id=user_id).count()
       return {"articles": articles, "comments": comments}

**Log output**:

.. code-block:: json

   {
     "event": "db_query",
     "function": "get_dashboard_data",
     "query_type": "read",
     "query_count": 2,
     "duration_ms": 12.4,
     "queries": [
       {"sql": "SELECT COUNT(*) FROM articles WHERE ...", "duration_ms": 6.1},
       {"sql": "SELECT COUNT(*) FROM comments WHERE ...", "duration_ms": 5.2}
     ]
   }

api_performance_monitor
-----------------------

Monitors API endpoint performance. Tracks request/response timing and logs
a warning when execution exceeds the configured threshold.

.. code-block:: python

   @api_performance_monitor()

**Usage**:

.. code-block:: python

   from drf_commons.decorators import api_performance_monitor

   class HeavyReportView(APIView):
       @api_performance_monitor()
       def get(self, request):
           ...

The threshold is read from ``COMMON["DEBUG_SLOW_REQUEST_THRESHOLD"]`` (default: 1.0 seconds).

cache_debug
-----------

Logs cache operations (get, set, delete) with timing information.

.. code-block:: python

   @cache_debug(cache_key_func: callable = None)

**Usage**:

.. code-block:: python

   from drf_commons.decorators import cache_debug
   from django.core.cache import cache

   @cache_debug(cache_key_func=lambda args, kwargs: f"user:{args[0]}")
   def get_user_permissions(user_id: int):
       key = f"user:{user_id}:permissions"
       result = cache.get(key)
       if result is None:
           result = compute_permissions(user_id)
           cache.set(key, result, timeout=300)
       return result

Combining Decorators
--------------------

Decorators compose naturally. Standard Python decorator stacking applies:

.. code-block:: python

   @api_request_logger(log_body=False)
   @api_performance_monitor()
   @log_db_query(query_type="read")
   @log_exceptions(reraise=True)
   def complex_view(request):
       ...

Execution order (outermost first): ``api_request_logger`` → ``api_performance_monitor``
→ ``log_db_query`` → ``log_exceptions`` → function body.
