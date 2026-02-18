Internal and Supporting Modules
===============================

This page documents non-primary modules that still affect production behavior, extension strategy, or contributor workflows.

Why this section matters
------------------------

Senior teams usually care less about how to call a helper and more about:

- which internals are safe to depend on,
- which internals are implementation detail and should be wrapped,
- where hidden coupling exists (middleware, settings, templates, logging).

``drf_commons.utils.middleware_checker``
----------------------------------------

Problem addressed
^^^^^^^^^^^^^^^^^

Features that depend on middleware frequently fail late and silently in projects.

Behavior
^^^^^^^^

- ``MiddlewareChecker`` checks whether a middleware path exists in ``settings.MIDDLEWARE``.
- ``require()`` raises ``ImproperlyConfigured`` if missing.
- ``require_middleware(...)`` decorator performs the check when wrapped function executes.

Trade-off
^^^^^^^^^

- fails explicitly when guarded behavior is executed,
- avoids import-time coupling to middleware configuration.

When not to rely on this directly
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Treat it as library-internal guardrail. Application code should prefer explicit startup checks (for example, Django system checks) when custom dependency logic is needed.


``drf_commons.templatetags.dict_extras``
----------------------------------------

Current behavior
^^^^^^^^^^^^^^^^

Contains ``get_item`` template filter for dictionary key access in templates.

This is intentionally minimal and safe to treat as utility-level helper rather than stable business API.


``drf_commons.common_tests``
----------------------------

Role
^^^^

Test support package containing reusable fixtures, factories, and base test utilities.

Why it can matter to adopters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you maintain custom extensions of ``drf-commons``, these helpers can accelerate behavior-regression testing against your wrappers.

Stability guidance
^^^^^^^^^^^^^^^^^^

Treat ``common_tests`` as contributor tooling, not public runtime contract.


Package-level integration tests
-------------------------------

Repository includes integration and end-to-end tests under ``drf_commons/tests`` and submodule test packages.

Documentation stance here:

- behavioral claims in module guides are derived from source code paths,
- tests are useful to verify expected outcomes but should not be treated as sole specification of behavior.


Internal API Surface and Risk Classification
--------------------------------------------

Lower-risk to consume directly:

- top-level packages explicitly exported through public ``__init__`` modules,
- view/model/serializer/service classes intentionally exposed in user docs.

Higher-risk internals (wrap before use):

- deep import pipeline internals (``data_processor``, ``lookup_manager``, ``bulk_operations``),
- logging config internals under ``debug.logging.*``,
- middleware checker decoration behavior.

Recommendation for production systems
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you need internals:

1. create a thin local adapter layer in your project,
2. pin library version,
3. add compatibility tests around your adapter,
4. avoid scattering direct imports from deep internal modules across codebase.


Migration and extension strategy
--------------------------------

For long-lived platforms:

- start from documented high-level APIs,
- only descend into internals when high-level extension points are insufficient,
- propose upstream extension hooks if repeated internal patches are required.

This keeps upgrade cost bounded and avoids lock-in to incidental implementation details.
