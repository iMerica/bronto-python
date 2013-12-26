bronto-python
=============

bronto-python is a python query client which wraps the Bronto SOAP API in an
easy to use manner, using the [suds](https://fedorahosted.org/suds/) library.

Getting Started
---------------
```python
from bronto.client import Client

client = Client('https://api.bronto.com/v4?wsdl', 'BRONTO_API_TOKEN')
```

Simple as that!

Addind a Contact
----------------
```python
contact_data = {'email': 'me@domain.com', ...}
client.add_contact(contact_data)
```
