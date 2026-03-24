.. drf-commons documentation master file

drf-commons
===========

.. image:: https://github.com/htvictoire/drf-commons/actions/workflows/tests.yml/badge.svg?branch=main
   :target: https://github.com/htvictoire/drf-commons/actions/workflows/tests.yml
.. image:: https://codecov.io/gh/htvictoire/drf-commons/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/htvictoire/drf-commons
.. image:: https://img.shields.io/pypi/v/drf-commons.svg
   :target: https://pypi.org/project/drf-commons/
.. image:: https://img.shields.io/pypi/dm/drf-commons.svg
   :target: https://pypi.org/project/drf-commons/
.. image:: https://img.shields.io/badge/python-3.8%2B-blue.svg
   :target: https://www.python.org/downloads/
.. image:: https://img.shields.io/badge/django-3.2%2B-green.svg
   :target: https://www.djangoproject.com/
.. image:: https://img.shields.io/badge/djangorestframework-3.12%2B-red.svg
   :target: https://www.django-rest-framework.org/
.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://opensource.org/licenses/MIT
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
.. image:: https://img.shields.io/badge/Django%20Packages-drf--commons-8c3c26.svg
   :target: https://djangopackages.org/packages/p/drf-commons/

**drf-commons** is a utility library for Django REST Framework that adds audit
tracking, standardized responses, bulk operations, configurable serializer fields,
and import/export — built on DRF's own extension points without replacing its internals.

.. admonition:: Philosophy

   drf-commons is not a framework replacement. It extends DRF using its own
   documented extension points, leaving DRF's existing behavior intact. Each
   component is a mixin: independently usable, explicitly opted-in, and
   composable to suit exactly what your API needs.

Getting Started
---------------

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   installation
   quickstart

Core Reference
--------------

.. toctree::
   :maxdepth: 2
   :caption: Core Reference

   architecture
   core_concepts
   models
   views
   serializers
   responses
   exceptions
   middlewares
   pagination
   filters
   decorators

Advanced Topics
---------------

.. toctree::
   :maxdepth: 2
   :caption: Advanced Topics

   services
   current_user
   utilities
   extensibility
   testing

Operations
----------

.. toctree::
   :maxdepth: 2
   :caption: Operations

   production_usage
   best_practices
   development

Appendices
----------

.. toctree::
   :maxdepth: 1
   :caption: Appendices

   changelog
   contributing

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
