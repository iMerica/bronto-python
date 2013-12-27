bronto-python
=============

bronto-python is a python query client which wraps the Bronto SOAP API in an
easy to use manner, using the [suds](https://fedorahosted.org/suds/) library.

Getting Started
---------------
```python
from bronto.client import Client

client = Client('BRONTO_API_TOKEN')
client.login()
```

Simple as that!

Adding a Contact
----------------
```python
contact_data = {'email': 'me@domain.com', ...}
client.add_contact(contact_data)
```

Retrieving a contact
--------------------
```python
client.get_contact('me@domain.com')
```

**NOTE:** This client is not built with long-running processes in mind. The
Bronto API connection will time out after 20 minutes of inactivity, and this
client does NOT handle those timeouts.
