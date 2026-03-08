Development
===========

This page covers the development workflow for contributing to drf-commons.

Environment Setup
-----------------

Clone and configure the development environment:

.. code-block:: bash

   git clone https://github.com/htvictoire/drf-commons
   cd drf-commons

   # Create a virtual environment
   python -m venv .venv
   source .venv/bin/activate

   # Install with all optional dependencies and dev tools
   pip install -e ".[export,import,debug,dev,test,docs]"

Makefile Commands
-----------------

The ``Makefile`` provides all common development commands:

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Command
     - Description
   * - ``make install``
     - Install core dependencies
   * - ``make install-dev``
     - Install core + dev tools
   * - ``make install-test``
     - Install core + test tools
   * - ``make format``
     - Format code with Black
   * - ``make sort-imports``
     - Sort imports with isort
   * - ``make lint``
     - Run flake8 linting
   * - ``make type-check``
     - Run mypy type checking
   * - ``make quality``
     - Run all quality checks (format + sort + lint + type-check)
   * - ``make test``
     - Run test suite
   * - ``make test-verbose``
     - Run test suite with verbose output
   * - ``make coverage``
     - Run tests with coverage report
   * - ``make docs``
     - Build Sphinx documentation
   * - ``make docs-clean``
     - Clean documentation build artifacts
   * - ``make all``
     - quality + test
   * - ``make check``
     - quality + coverage

Code Style
----------

drf-commons uses the following code quality tools:

* **Black** — opinionated code formatter, line length 88
* **isort** — import sorting with Black compatibility
* **flake8** — PEP 8 linting
* **mypy** — strict type checking

Run all checks before committing:

.. code-block:: bash

   make quality

Type Annotations
~~~~~~~~~~~~~~~~

All public API functions and methods must have complete type annotations. mypy
is configured in strict mode for ``drf_commons/`` (excluding tests and
migrations):

.. code-block:: python

   # mypy.ini / pyproject.toml
   [tool.mypy]
   python_version = "3.8"
   disallow_untyped_defs = true
   ignore_missing_imports = true

Running Tests
-------------

The test suite uses pytest with ``pytest-django``:

.. code-block:: bash

   # All tests
   make test

   # Specific test file
   pytest drf_commons/views/tests/test_crud.py

   # Specific test class
   pytest drf_commons/views/tests/test_crud.py::TestCreateModelMixin

   # With verbose output
   make test-verbose

   # With coverage
   make coverage

Test Configuration
~~~~~~~~~~~~~~~~~~

Tests use an in-memory SQLite database configured in
``drf_commons/common_conf/django_settings.py``. No external services are
required to run the test suite.

The ``DJANGO_SETTINGS_MODULE`` is configured in ``pyproject.toml``:

.. code-block:: toml

   [tool.pytest.ini_options]
   DJANGO_SETTINGS_MODULE = "drf_commons.common_conf.django_settings"
   python_files = ["test_*.py", "*_test.py"]
   testpaths = ["drf_commons"]
   addopts = "--strict-markers --tb=short"

Test Factories
~~~~~~~~~~~~~~

Use factory-boy factories from ``drf_commons.common_tests.factories``:

.. code-block:: python

   from drf_commons.common_tests.factories import (
       UserFactory,
       StaffUserFactory,
       SuperUserFactory,
   )

   # In tests
   user = UserFactory()
   staff = StaffUserFactory()
   superuser = SuperUserFactory(username="admin")

Building Documentation
----------------------

Documentation uses Sphinx with the Furo theme:

.. code-block:: bash

   # Install docs dependencies
   pip install -r docs/requirements.txt

   # Build HTML docs
   make docs

   # Open built docs
   open docs/_build/html/index.html

   # Live-rebuild on file changes (requires sphinx-autobuild)
   pip install sphinx-autobuild
   cd docs && make livehtml

Project Structure for Contributors
------------------------------------

When adding a new component:

1. **Source** — Place in the appropriate package under ``drf_commons/``
2. **Tests** — Add tests in the package's ``tests/`` subdirectory
3. **Documentation** — Update the relevant ``.rst`` file in ``docs/``
4. **Exports** — Update the package's ``__init__.py`` if the component is part
   of the public API
5. **Type annotations** — Add complete type annotations
6. **Changelog** — Add an entry to ``docs/changelog.rst``

Pull Request Guidelines
-----------------------

* All tests must pass (``make test``)
* All quality checks must pass (``make quality``)
* New public API must be documented
* New features must include tests achieving at least 90% line coverage
* Breaking changes require a major version bump and must be discussed in an
  issue first

Publishing to PyPI
------------------

.. code-block:: bash

   # Install build tools
   pip install build twine

   # Bump version in drf_commons/__init__.py
   # Update CHANGELOG

   # Build distribution
   python -m build

   # Upload to TestPyPI first
   twine upload --repository testpypi dist/*

   # Verify installation from TestPyPI
   pip install --index-url https://test.pypi.org/simple/ drf-commons

   # Upload to PyPI
   twine upload dist/*
