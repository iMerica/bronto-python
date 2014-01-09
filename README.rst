bronto-python
=============

bronto-python is a python query client which wraps the Bronto SOAP API in an
easy to use manner, using the `suds <https://fedorahosted.org/suds/>`_ library.

Getting Started
===============

.. code:: python

    from bronto.client import Client
    
    client = Client('BRONTO_API_TOKEN')
    client.login()

Simple as that!

Contacts
========

Adding a Contact
----------------

.. code:: python

    contact_data = {'email': 'me@domain.com',
                    'source': 'api',
                    'customSource': 'Using bronto-python to import my contact'}
    client.add_contact(contact_data)

Retrieving a contact
--------------------

.. code:: python

    client.get_contact('me@domain.com')

Deleting a contact
------------------

.. code:: python

    client.delete_contact('me@domain.com')

Orders
======

Adding an order
---------------

.. code:: python

    order_data = {'id': 'xyz123',
                  'email': 'me@domain.com',
                  'products': [
                    {'id': 1,
                     'sku': '1111',
                     'name': 'Test Product 1',
                     'description': 'This is our first test product.',
                     'quantity': 1,
                     'price': 3.50},
                    {'id': 2,
                     'sku': '2222',
                     'name': 'Second Test Product',
                     'description': 'Here we have another product for testing.',
                   'quantity': 12,
                   'price': 42.00}
                  ]
                 }
    client.add_order(order_data)

Deleting an order
-----------------

.. code:: python

    client.delete_order('xyz123')  # Orders are deleted by their orderId

**NOTE:** This client is not built with long-running processes in mind. The
Bronto API connection will time out after 20 minutes of inactivity, and this
client does NOT handle those timeouts.
