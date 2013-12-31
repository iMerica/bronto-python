import os
import unittest
import uuid

from bronto import client


class BrontoTest(unittest.TestCase):
    contact_info = {'email': 'joey@scottsmarketplace.com',
                    'source': 'api',
                    'customSource': 'Python client test suite',
                    'fields': {'firstname': 'Test',
                               'lastname': 'User'}}

    @classmethod
    def setUpClass(cls):
        cls._token = os.environ.get('BRONTO_API_KEY', '')
        assert cls._token, 'You must set the BRONTO_API_KEY environment variable'
        cls._client = client.Client(cls._token)
        cls._client.login()

    def setUp(self):
        contact = self._client.add_contact(self.contact_info)
        self.assertIs(contact.isError, False)

    def tearDown(self):
        response = self._client.delete_contact(self.contact_info['email'])
        self.assertIs(response.isError, False)


class TestFailures(unittest.TestCase):

    def test_no_token(self):
        with self.assertRaises(ValueError):
            c = client.Client(None)

    def test_invalid_token(self):
        with self.assertRaises(client.BrontoError):
            c = client.Client('invalid')
            c.login()


class BrontoContactTest(BrontoTest):

    def test_get_contact(self):
        contact = self._client.get_contact(self.contact_info['email'])
        for key, val in self.contact_info.iteritems():
            if key != 'fields':
                self.assertEqual(getattr(contact, key), val)


class BrontoOrderTest(BrontoTest):
    products = [
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

    def setUp(self):
        super(BrontoOrderTest, self).setUp()
        contact = self._client.get_contact(self.contact_info['email'])
        self._order_id = uuid.uuid4().hex
        order_info = {'id': self._order_id,
                      'email': contact.email,
                      'contactId': contact.id,
                      'products': self.products}
        order = self._client.add_order(order_info)
        self.assertIs(order.isError, False)

    def tearDown(self):
        super(BrontoOrderTest, self).tearDown()
        response = self._client.delete_order(self._order_id)
        self.assertIs(response.isError, False)

    def test_dummy(self):
        pass  # This is just to ensure that setUp/tearDown work


if __name__ == '__main__':
    unittest.main()
