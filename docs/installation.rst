Installation
============

Runtime dependencies
--------------------

Base package:

.. code-block:: bash

   pip install drf-commons

Optional extras:

.. code-block:: bash

   # Export extras (XLSX/PDF)
   pip install drf-commons[export]

   # Import extras (CSV/XLS/XLSX import pipeline)
   pip install drf-commons[import]

   # Debug extras (memory usage utilities)
   pip install drf-commons[debug]

Equivalent standalone dependency installs:

.. code-block:: bash

   # Export support
   # CSV: no extra dependency
   # XLSX:
   pip install openpyxl>=3.0
   # PDF:
   pip install weasyprint>=60.0

   # Import support
   pip install pandas>=1.3
   # for xlsx input
   pip install openpyxl>=3.0
   # for xls input
   pip install xlrd

   # Debug support
   pip install psutil>=5.9

Dependency activation semantics:

- base install (``pip install drf-commons``) is sufficient for project startup and non import/export features.
- CSV export works on base install.
- XLSX/PDF export dependencies are loaded when those exporters run.
- import pipeline dependencies are required when using import services/endpoints or import-template generation command.
- debug memory utilities require ``psutil`` and are activated when ``memory_usage`` is called.

Django setup:

.. code-block:: python

   INSTALLED_APPS = [
       "drf_commons",
   ]

Development dependencies
------------------------

.. code-block:: bash

   pip install -e .[dev,test]

Documentation dependencies
--------------------------

.. code-block:: bash

   pip install -r docs/requirements.txt

Build docs locally
------------------

.. code-block:: bash

   make -C docs html

Output is generated under ``docs/_build/html``.

Django settings for docs
------------------------

Docs use ``docs/django_settings.py`` so that Sphinx can import Django/DRF-aware modules during API generation without requiring a full project.
