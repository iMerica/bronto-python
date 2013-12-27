import os
import unittest

from bronto import client


class BrontoTest(unittest.TestCase):

    def setUp(self):
        self.token = os.environ.get('BRONTO_API_KEY', '')
        assert self.token, 'You must set the BRONTO_API_KEY environment variable'


class BrontoLoginTest(BrontoTest):

    def test_login(self):
        c = client.Client(self.token)
        c.login()


if __name__ == '__main__':
    unittest.main()
