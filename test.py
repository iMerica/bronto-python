import os
import unittest

from bronto import client


class BrontoTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._token = os.environ.get('BRONTO_API_KEY', '')
        assert cls._token, 'You must set the BRONTO_API_KEY environment variable'
        cls._client = client.Client(cls._token)
        cls._client.login()


class BrontoContactTest(BrontoTest):
    contact_info = {'email': 'joey@scottsmarketplace.com'}

    def test_add_contact(self):
        contact = self._client.add_contact(self.contact_info)
        self.assertIs(contact.isError, False)

    def test_get_contact(self):
        contact = self._client.get_contact(self.contact_info['email'])
        self.assertEqual(contact.email, self.contact_info['email'])


if __name__ == '__main__':
    unittest.main()
