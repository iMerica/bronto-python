import os
import unittest

from bronto import client


class BrontoTest(unittest.TestCase):
    contact_info = {'email': 'joey@scottsmarketplace.com'}

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


class BrontoContactTest(BrontoTest):

    def test_get_contact(self):
        contact = self._client.get_contact(self.contact_info['email'])
        self.assertEqual(contact.email, self.contact_info['email'])

if __name__ == '__main__':
    unittest.main()
