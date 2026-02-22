common_conf
===========

Source modules:

- ``drf_commons/common_conf/settings.py``
- ``drf_commons/common_conf/django_settings.py``

Role in the system
------------------

``common_conf`` is the configuration contract layer for the library.

Problem it solves
^^^^^^^^^^^^^^^^^

Without a dedicated config resolver, reusable libraries usually force either:

- hard-coded defaults in many modules,
- direct global setting names that collide with application settings,
- repeated ``getattr(settings, ..., default)`` logic scattered everywhere.

Implementation strategy
^^^^^^^^^^^^^^^^^^^^^^^

``CommonSettings.get(key, default)`` resolves in this order:

1. ``COMMON_<KEY>``
2. ``<KEY>``
3. provided default

Resolved values are read directly from Django settings on each access.

Why this matters in DRF deployments
-----------------------------------

DRF-heavy systems frequently run mixed settings estates (legacy global names plus namespaced module settings). The resolver allows incremental migration to namespaced settings without immediate breakage.

Internal mechanics and caveats
------------------------------

- settings are resolved dynamically from Django settings on each access.

Key configuration domains
-------------------------

The module defines settings used by:

- current-user context (``LOCAL_USER_ATTR_NAME``),
- debug middleware/logger thresholds and category enablement,
- import/export batch and rendering parameters,
- bulk operation size limits,
- export layout/format heuristics.

Performance implications
------------------------

Configuration lookup is a simple settings attribute read. Real performance impact comes from how values are used:

- low thresholds can produce high-volume debug logging,
- oversized import/export batch settings increase memory pressure,
- lax thresholds can hide production hotspots.

When not to rely on dynamic mutation
------------------------------------

Do not assume changing Django settings at runtime will reconfigure behavior of all already-imported constants. Use deploy-time configuration management.

Alternative approaches
----------------------

- strict Pydantic/settings objects instantiated once at startup,
- environment-variable-only config loading,
- Django app config validation hooks with explicit fail-fast checks.

Integration pattern
-------------------

Recommended project settings style:

.. code-block:: python

   COMMON_IMPORT_BATCH_SIZE = 500
   COMMON_BULK_OPERATION_BATCH_SIZE = 200
   COMMON_DEBUG_ENABLED_LOG_CATEGORIES = [
       "errors",
       "database",
       "performance",
   ]

Use namespaced keys for maintainability and to reduce accidental conflicts.

Migration strategy
------------------

1. Keep existing unprefixed settings in place.
2. Introduce equivalent ``COMMON_`` settings in staging.
3. Verify behavior parity.
4. Remove legacy unprefixed keys.

Compatibility concerns
----------------------

The package test settings module (``django_settings.py``) is tuned for in-memory SQLite and test/dev defaults. It should not be copied blindly into production projects.
