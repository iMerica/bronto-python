#!/usr/bin/env python

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

    addl_contact_info = {'email': 'joey+bronto@scottsmarketplace.com',
                         'source': 'api',
                         'customSource': 'Python client test suite',
                         'fields': {'firstname': 'Josephus',
                                    'lastname': 'Wilhelm'}}

    @classmethod
    def setUpClass(cls):
        cls._token = os.environ.get('BRONTO_API_KEY', '')
        assert cls._token, 'You must set the BRONTO_API_KEY environment variable'
        cls._client = client.Client(cls._token)
        cls._client.login()

    def setUp(self):
        try:
            contact = self._client.add_contact(self.contact_info)
            self.assertIs(contact.isError, False)
        except client.BrontoError:
            # Get the data from Bronto if the contact wasn't deleted in the
            # previous tests due to an error.
            self.contact_info = self._client.get_contact(self.contact_info['email'])

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
            else:
                all_fields = self._client.get_fields()
                field_names = dict([x.id, x.name] for x in all_fields)
                field_data = dict([(field_names[x.fieldId], x.content)
                                   for x in contact.fields if
                                   field_names[x.fieldId] in self.contact_info['fields']])
                for fkey, fval in field_data.iteritems():
                    self.assertEqual(self.contact_info['fields'][fkey], fval)

    def test_add_contact_no_info(self):
        with self.assertRaises(ValueError):
            self._client.add_contacts([{}])

    def test_add_or_update_contacts(self):
        new_mobile = '6025555555'
        new_firstname = 'Other'
        old_contact = self._client.get_contact(self.contact_info['email'])
        self._client.add_or_update_contact({'email': self.contact_info['email'],
                                            'mobileNumber': new_mobile,
                                            'fields': {'firstname': new_firstname}
                                           })
        contact = self._client.get_contact(self.contact_info['email'],
                                           fields=['firstname', ])
        self.assertEqual(old_contact.id, contact.id)
        self.assertEqual(contact.mobileNumber, new_mobile)
        self.assertEqual(contact.fields[0].content, new_firstname)
        new_contact = self._client.add_or_update_contact(self.addl_contact_info)
        self.assertIs(new_contact.isError, False)
        self.assertIs(new_contact.isNew, True)
        # Delete the extra user
        self._client.delete_contact(self.addl_contact_info['email'])

    def test_update_contact(self):
        new_mobile = '6025555555'
        new_firstname = 'Other'
        old_contact = self._client.get_contact(self.contact_info['email'])
        self._client.update_contact(self.contact_info['email'],
                                    {'mobileNumber': new_mobile,
                                     'fields': {'firstname': new_firstname}
                                    })
        contact = self._client.get_contact(self.contact_info['email'],
                                           fields=['firstname', ])
        self.assertEqual(old_contact.id, contact.id)
        self.assertEqual(contact.mobileNumber, new_mobile)
        self.assertEqual(contact.fields[0].content, new_firstname)

class BrontoFieldTest(BrontoTest):
    """
    You need to have at least 1 field left in your account
    http://app.bronto.com/mail/field/index/
    """

    field_info = {'name': 'new_field',
                  'label': 'New Field',
                  'type': 'text'}

    def setUp(self):
        try:
            field = self._client.add_field(self.field_info)
            self.assertIs(field.isError, False)
            self.field_info['id'] = field['id']
        except client.BrontoError:
            # Pull the field info from Bronto if previous failure in the tests
            self.field_info = self._client.get_field(self.field_info['name'])

    def tearDown(self):
        response = self._client.delete_field(self.field_info['id'])
        self.assertIs(response.isError, False)

    def test_get_field(self):
        field = self._client.get_field(self.field_info['name'])
        for key, val in self.field_info.iteritems():
            self.assertEqual(getattr(field, key), val)

    def test_add_field_no_info(self):
        with self.assertRaises(ValueError):
            self._client.add_field([{}])

    def test_add_field_not_all_required_attributes(self):
        with self.assertRaises(ValueError):
            self._client.add_field([{
                'name': 'mising_something',
                'label': 'Missing the type I think',
                'visibility': 'private'
                }])

    """
    TODO: Implement the update_field function in the client
    def test_update_field(self):
        new_name = 'new_name'
        new_label = 'Updated field'
        new_visibility = 'private'
        old_field = self._client.get_field(self.field_info['name'])
        self._client.update_field(self.field_info['id'],
                                    {'name': new_name,
                                     'label': new_label,
                                     'visibility': new_visibility
                                    })
        field = self._client.get_field(new_name)
        self.assertEqual(old_field.id, field.id)
        self.assertEqual(field.name, new_name)
        self.assertEqual(field.label, new_label)
        self.assertEqual(field.visibility, new_visibility)
    """

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


class BrontoListTest(BrontoTest):

    list_info = {'name': 'new_list',
                 'label': 'New List'
                 }

    def setUp(self):
        try:
            list_ = self._client.add_list(self.list_info)
            self.assertIs(list_.isError, False)
            self.list_info['id'] = list_['id']
        except client.BrontoError:
            # Pull the list id from Bronto if previous failure in the tests
            self.list_info = self._client.get_list(self.list_info['name'])

    def tearDown(self):
        response = self._client.delete_list(self.list_info['id'])
        self.assertIs(response.isError, False)

    def test_get_list(self):
        list_ = self._client.get_list(self.list_info['name'])
        for key, val in self.list_info.iteritems():
            self.assertEqual(getattr(list_, key), val)

    def test_add_list_no_info(self):
        with self.assertRaises(ValueError):
            self._client.add_list([{}])

    def test_add_list_not_all_required_attributes(self):
        with self.assertRaises(ValueError):
            self._client.add_list([{
                'name': 'mising the label',
                }])

    def test_add_contact_to_list(self):
        try:
            super(BrontoListTest, self).setUp()
            response = self._client.add_contact_to_list(
                    {'name': self.list_info['name']},
                    {'email': self.contact_info['email']})
            self.assertIs(response.isError, False)
        finally:
            super(BrontoListTest, self).tearDown()

    """
    TODO: Implement the update_list function in the client
    def test_update_list(self):
        new_name = 'new_name'
        new_label = 'Updated list'
        old_list = self._client.get_list(self.list_info['name'])
        self._client.update_list(self.list_info['id'],
                                    {'name': new_name,
                                     'label': new_label
                                    })
        list = self._client.get_list(new_name)
        self.assertEqual(old_list.id, list.id)
        self.assertEqual(list.name, new_name)
        self.assertEqual(list.label, new_label)
    """

class BrontoMessageTest(BrontoTest):

    message_info = {
            'name': 'bronto_api_test',
            }

    def test_get_message(self):
        message = self._client.get_message(self.message_info['name'])
        if not message:
            raise Exception("You need to create a message with the name bronto_api_test")
        for key, val in self.message_info.iteritems():
            self.assertEqual(getattr(message, key), val)

    def test_get_message_wrong_name(self):
        message = self._client.get_message('IDontExist')
        self.assertEqual(len(message), 0)

    def test_get_messages(self):
        messages = self._client.get_messages([self.message_info['name']])
        if not messages:
            raise Exception("You need to create a message with the name bronto_api_test")
        self.assertEqual(len(messages), 1)
        for key, val in self.message_info.iteritems():
            self.assertEqual(getattr(messages[0], key), val)

# TODO add tests for the deliveries

if __name__ == '__main__':
    unittest.main()
