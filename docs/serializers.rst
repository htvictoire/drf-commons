Serializers
===========

drf-commons extends DRF's serializer system with atomic write handling,
dependency-ordered relation writes, and a comprehensive system of configurable
relation field types.

BaseModelSerializer
-------------------

.. code-block:: python

   from drf_commons.serializers import BaseModelSerializer

The base serializer for all drf-commons projects. Extends
``rest_framework.serializers.ModelSerializer`` with:

* **Atomic writes** — All ``create()`` and ``update()`` operations are wrapped
  in ``transaction.atomic()``.
* **Relation write ordering** — Fields can be designated ``root_first`` or
  ``dependency_first`` to control the order in which nested relation saves are
  applied.

**Relation write ordering**:

.. code-block:: python

   class InvoiceSerializer(BaseModelSerializer):
       # dependency_first: save the nested object first, then set FK on parent
       customer = CustomerSerializer(dependency_first=True)

       # root_first: save the parent first, then assign FK on children
       line_items = LineItemSerializer(many=True, root_first=True)

       class Meta:
           model = Invoice
           fields = ["id", "number", "customer", "line_items"]

BulkUpdateListSerializer
------------------------

.. code-block:: python

   from drf_commons.serializers.base import BulkUpdateListSerializer

The ``list_serializer_class`` for ``BaseModelSerializer``. Used automatically
by all bulk update operations.

**Behavior**:

* Validates that the incoming data list length matches the queryset length
* Applies audit field defaults (``updated_at``, ``updated_by``) when absent
* In default mode: issues a single ``bulk_update()`` call
* In save mode: calls ``instance.save()`` for each object within an atomic block
* Rejects deferred nested relation writes in bulk mode (would require N+1 saves)

Configurable Field Types
------------------------

The configurable field system provides a consistent, composable approach to
representing foreign key and many-to-many relations in different contexts.

All field names follow the convention: ``{WriteFormat}To{ReadFormat}Field``.

Single Relation Fields
~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :widths: 30 20 20 30
   :header-rows: 1

   * - Field Class
     - Write Accepts
     - Read Returns
     - Primary Use Case
   * - ``IdToDataField``
     - Primary key
     - Nested serializer output
     - Standard API pattern
   * - ``IdToStrField``
     - Primary key
     - String (``__str__``)
     - Lightweight references
   * - ``DataToIdField``
     - Nested data
     - Primary key
     - Accept full payload, return ID
   * - ``DataToStrField``
     - Nested data
     - String (``__str__``)
     - Accept nested, return label
   * - ``DataToDataField``
     - Nested data
     - Nested serializer output
     - Full nested read-write
   * - ``StrToDataField``
     - String (lookup)
     - Nested serializer output
     - Lookup by name/code
   * - ``IdOnlyField``
     - Primary key
     - Primary key
     - Pure ID relation
   * - ``StrOnlyField``
     - String (lookup)
     - String (``__str__``)
     - String-keyed relations
   * - ``FlexibleField``
     - ID or string (auto-detected)
     - Nested serializer output
     - Flexible client contracts
   * - ``CustomOutputField``
     - Primary key
     - Custom function output
     - Computed representations

Many-to-Many Fields
~~~~~~~~~~~~~~~~~~~

All single relation fields have a ``Many`` prefixed variant:

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Field Class
     - Description
   * - ``ManyIdToDataField``
     - Accept list of IDs, return list of nested data
   * - ``ManyDataToIdField``
     - Accept list of nested data, return list of IDs
   * - ``ManyStrToDataField``
     - Accept list of strings, return list of nested data
   * - ``ManyIdOnlyField``
     - Accept and return list of IDs
   * - ``ManyStrOnlyField``
     - Accept and return list of strings
   * - ``ManyFlexibleField``
     - Accept mixed IDs/strings, return list of nested data

Read-Only Fields
~~~~~~~~~~~~~~~~

These fields do not accept write input:

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Field Class
     - Description
   * - ``ReadOnlyIdField``
     - Returns primary key only
   * - ``ReadOnlyStrField``
     - Returns ``__str__`` representation
   * - ``ReadOnlyDataField``
     - Returns full nested serializer output
   * - ``ReadOnlyCustomField``
     - Returns custom function output

Import:

.. code-block:: python

   from drf_commons.serializers.fields import (
       IdToDataField,
       IdToStrField,
       DataToIdField,
       DataToDataField,
       StrToDataField,
       IdOnlyField,
       StrOnlyField,
       FlexibleField,
       CustomOutputField,
       ManyIdToDataField,
       ManyDataToIdField,
       ManyIdOnlyField,
       ManyFlexibleField,
       ReadOnlyIdField,
       ReadOnlyStrField,
       ReadOnlyDataField,
       ReadOnlyCustomField,
   )

Field Usage Examples
--------------------

**Standard foreign key (write by ID, read nested)**:

.. code-block:: python

   class ArticleSerializer(BaseModelSerializer):
       author = IdToDataField(
           queryset=User.objects.all(),
           serializer=UserSerializer,
       )

**Many-to-many (write list of IDs, read list of nested data)**:

.. code-block:: python

   class ArticleSerializer(BaseModelSerializer):
       tags = ManyIdToDataField(
           queryset=Tag.objects.all(),
           serializer=TagSerializer,
       )

**Flexible field (accept ID or string, return nested data)**:

.. code-block:: python

   class OrderSerializer(BaseModelSerializer):
       product = FlexibleField(
           queryset=Product.objects.all(),
           serializer=ProductSerializer,
           # Tries to parse as UUID (ID); falls back to string lookup
       )

**Read-only computed relation**:

.. code-block:: python

   class UserSerializer(BaseModelSerializer):
       department = ReadOnlyDataField(serializer=DepartmentSerializer)
       role_label = ReadOnlyStrField()  # returns str(instance.role)

**Custom output**:

.. code-block:: python

   class ArticleSerializer(BaseModelSerializer):
       author = CustomOutputField(
           queryset=User.objects.all(),
           output_fn=lambda user: {"id": str(user.id), "display": user.get_full_name()},
       )

Building Custom Field Types
---------------------------

All field types inherit from
:class:`~drf_commons.serializers.fields.mixins.base.ConfigurableRelatedFieldMixin`.
Implementing a custom field type requires subclassing the appropriate base and
implementing the abstract transform methods:

.. code-block:: python

   from drf_commons.serializers.fields.base import ConfigurableRelatedField

   class UrnToDataField(ConfigurableRelatedField):
       """
       Accept a URN string (e.g., "urn:product:uuid-here"), resolve to the
       object, return nested serializer data.
       """

       def to_internal_value(self, data):
           # Parse URN, extract ID, resolve object
           _, _, raw_id = data.partition(":")
           try:
               return self.get_queryset().get(pk=raw_id)
           except self.get_queryset().model.DoesNotExist:
               self.fail("does_not_exist", pk_value=raw_id)

       def to_representation(self, value):
           serializer = self.serializer_class(value, context=self.context)
           return serializer.data
