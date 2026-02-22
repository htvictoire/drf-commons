.. drf-commons documentation master file

drf-commons
===========

.. image:: https://img.shields.io/badge/python-3.8%2B-blue.svg
   :target: https://www.python.org/downloads/
.. image:: https://img.shields.io/badge/django-3.2%2B-green.svg
   :target: https://www.djangoproject.com/
.. image:: https://img.shields.io/badge/djangorestframework-3.12%2B-red.svg
   :target: https://www.django-rest-framework.org/
.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://opensource.org/licenses/MIT

**drf-commons** is a production-grade utility library for Django REST Framework.
It eliminates architectural repetition, enforces API consistency, and provides
composable abstractions for building scalable, maintainable REST APIs.

.. admonition:: Philosophy

   drf-commons is not a framework on top of DRF. It is a structural layer
   composed atop DRF internals using DRF's own documented extension points.
   Every component is independently usable, explicitly opted-in, and designed
   for production deployment.

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
