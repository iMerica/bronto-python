from suds import WebFault
from suds.client import Client as SudsClient

API_ENDPOINT = 'https://api.bronto.com/v4?wsdl'


class BrontoError(Exception):
    pass


class Client(object):
    _valid_contact_fields = ['email', 'mobileNumber', 'status', 'msgPref',
                             'source', 'customSource', 'listIds', 'fields',
                             'SMSKeywordIDs']
    _valid_order_fields = ['id', 'email', 'contactId', 'products', 'orderDate',
                           'tid']
    _valid_product_fields = ['id', 'sku', 'name', 'description', 'category',
                             'image', 'url', 'quantity', 'price']
    _valid_field_fields = ['id', 'name', 'label', 'type', 'visibility', 'options']
    _valid_list_fields = ['id', 'name', 'label']
    _valid_delivery_fields = ['authentication', 'fatigueOverride', 'fields',
            'fromEmail', 'fromName', 'messageId', 'messageRuleId', 'optin',
            'recipients', 'remail', 'replyEmail', 'replyTracking', 'start',
            'throttle', 'type']

    _cached_fields = {}
    _cached_all_fields = False

    _cached_lists = {}
    _cached_all_lists = False

    _cached_messages = {}
    _cached_all_messages = False

    def __init__(self, token, **kwargs):
        if not token or not isinstance(token, basestring):
            raise ValueError('Must supply a token as a non empty string.')

        self._token = token
        self._client = None

    def login(self):
        self._client = SudsClient(API_ENDPOINT)
        try:
            self.session_id = self._client.service.login(self._token)
            session_header = self._client.factory.create('sessionHeader')
            session_header.sessionId = self.session_id
            self._client.set_options(soapheaders=session_header)
        except WebFault as e:
            raise BrontoError(e.message)

    def _construct_contact_fields(self, fields):
        final_fields = []
        real_fields = self.get_fields(fields.keys())
        for field_key, field_val in fields.iteritems():
            try:
                real_field = filter(lambda x: x.name == field_key,
                                    real_fields)[0]
            except IndexError:
                raise BrontoError('Invalid contactField: %s' %
                                  field_key)
            field_object = self._client.factory.create('contactField')
            field_object.fieldId = real_field.id
            field_object.content = field_val
            final_fields.append(field_object)
        return final_fields

    def add_contacts(self, contacts):
        final_contacts = []
        for contact in contacts:
            if not any([contact.get('email'), contact.get('mobileNumber')]):
                raise ValueError('Must provide either an email or mobileNumber')
            contact_obj = self._client.factory.create('contactObject')
            # FIXME: Add special handling for listIds, SMSKeywordIDs
            for field, value in contact.iteritems():
                if field == 'fields':
                    field_objs = self._construct_contact_fields(value)
                    contact_obj.fields = field_objs
                elif field not in self._valid_contact_fields:
                    raise KeyError('Invalid contact attribute: %s' % field)
                else:
                    setattr(contact_obj, field, value)
            final_contacts.append(contact_obj)
        try:
            response = self._client.service.addContacts(final_contacts)
            if hasattr(response, 'errors'):
                err_str = ', '.join(['%s: %s' % (response.results[x].errorCode,
                                                 response.results[x].errorString)
                                     for x in response.errors])
                raise BrontoError('An error occurred while adding contacts: %s'
                                  % err_str)
        except WebFault as e:
            raise BrontoError(e.message)
        return response

    def add_contact(self, contact):
        contact = self.add_contacts([contact, ])
        try:
            return contact.results[0]
        except:
            return contact.results

    def get_contacts(self, emails, include_lists=False, fields=[],
                     page_number=1, include_sms=False):
        final_emails = []
        filter_operator = self._client.factory.create('filterOperator')
        fop = filter_operator.EqualTo
        for email in emails:
            contact_email = self._client.factory.create('stringValue')
            contact_email.operator = fop
            contact_email.value = email
            final_emails.append(contact_email)
        contact_filter = self._client.factory.create('contactFilter')
        contact_filter.email = final_emails
        filter_type = self._client.factory.create('filterType')
        if len(final_emails) > 1:
            contact_filter.type = filter_type.OR
        else:
            contact_filter.type = filter_type.AND

        try:
            field_objs = self.get_fields(fields)
            field_ids = [x.id for x in field_objs]
            response = self._client.service.readContacts(
                                             contact_filter,
                                             includeLists=include_lists,
                                             fields=field_ids,
                                             pageNumber=page_number,
                                             includeSMSKeywords=include_sms)
        except WebFault as e:
            raise BrontoError(e.message)
        return response

    def get_contact(self, email, include_lists=False, fields=[],
                    include_sms=False):
        contact = self.get_contacts([email, ], include_lists, fields, 1,
                                    include_sms)
        try:
            return contact[0]
        except:
            return contact

    def update_contacts(self, contacts):
        """
        >>> client.update_contacts({'me@domain.com':
                                      {'mobileNumber': '1234567890',
                                       'fields':
                                         {'firstname': 'New', 'lastname': 'Name'}
                                      },
                                    'you@domain.com':
                                      {'email': 'notyou@domain.com',
                                       'fields':
                                         {'firstname': 'Other', 'lastname': 'Name'}
                                      }
                                   })
        >>>
        """
        contact_objs = self.get_contacts(contacts.keys())
        final_contacts = []
        for email, contact_info in contacts.iteritems():
            try:
                real_contact = filter(lambda x: x.email == email,
                                      contact_objs)[0]
            except IndexError:
                raise BrontoError('Contact not found: %s' % email)
            for field, value in contact_info.iteritems():
                if field == 'fields':
                    field_objs = self._construct_contact_fields(value)
                    all_fields = self.get_fields()
                    field_names = dict([(x.id, x.name) for x in all_fields])
                    old_fields = dict([(field_names[x.fieldId], x)
                                       for x in real_contact.fields])
                    new_fields = dict([(field_names[x.fieldId], x)
                                       for x in field_objs])
                    old_fields.update(new_fields)
                    # This sounds backward, but it's not. Honest.
                    real_contact.fields = old_fields.values()
                elif field not in self._valid_contact_fields:
                    raise KeyError('Invalid contact attribute: %s' % field)
                else:
                    setattr(real_contact, field, value)
            final_contacts.append(real_contact)
        try:
            response = self._client.service.updateContacts(final_contacts)
            if hasattr(response, 'errors'):
                err_str = ', '.join(['%s: %s' % (response.results[x].errorCode,
                                                 response.results[x].errorString)
                                     for x in response.errors])
                raise BrontoError('An error occurred while adding contacts: %s'
                                  % err_str)
        except WebFault as e:
            raise BrontoError(e.message)
        return response

    def update_contact(self, email, contact_info):
        contact = self.update_contacts({email: contact_info})
        try:
            return contact.results[0]
        except:
            return contact.results

    def add_or_update_contacts(self, contacts):
        # FIXME: This is entirely too similar to add_contacts.
        # TODO: These two should be refactored.
        final_contacts = []
        for contact in contacts:
            if not any([contact.get('id'), contact.get('email'),
                        contact.get('mobileNumber')]):
                raise ValueError('Must provide one of: id, email, mobileNumber')
            contact_obj = self._client.factory.create('contactObject')
            for field, value in contact.iteritems():
                if field == 'fields':
                    field_objs = self._construct_contact_fields(value)
                    contact_obj.fields = field_objs
                elif field not in self._valid_contact_fields:
                    raise KeyError('Invalid contact attribute: %s' % field)
                else:
                    setattr(contact_obj, field, value)
            final_contacts.append(contact_obj)
        try:
            response = self._client.service.addOrUpdateContacts(final_contacts)
            if hasattr(response, 'errors'):
                err_str = ', '.join(['%s: %s' % (response.results[x].errorCode,
                                                 response.results[x].errorString)
                                     for x in response.errors])
                raise BrontoError('An error occurred while adding contacts: %s'
                                  % err_str)
        except WebFault as e:
            raise BrontoError(e.message)
        return response

    def add_or_update_contact(self, contact):
        contact = self.add_or_update_contacts([contact, ])
        try:
            return contact.results[0]
        except:
            return contact.results

    def delete_contacts(self, emails):
        contacts = self.get_contacts(emails)
        try:
            response = self._client.service.deleteContacts(contacts)
        except WebFault as e:
            raise BrontoError(e.message)
        return response

    def delete_contact(self, email):
        response = self.delete_contacts([email, ])
        try:
            return response.results[0]
        except:
            return response.results

    def add_orders(self, orders):
        final_orders = []
        for order in orders:
            if not order.get('id', None):
                raise ValueError('Each order must provide an id')
            order_obj = self._client.factory.create('orderObject')
            for field, value in order.iteritems():
                if field == 'products':
                    final_products = []
                    for product in value:
                        product_obj = self._client.factory.create('productObject')
                        for pfield, pvalue in product.iteritems():
                            if pfield not in self._valid_product_fields:
                                raise KeyError('Invalid product attribute: %s'
                                               % pfield)
                            setattr(product_obj, pfield, pvalue)
                        final_products.append(product_obj)
                    order_obj.products = final_products
                elif field not in self._valid_order_fields:
                    raise KeyError('Invalid order attribute: %s' % field)
                else:
                    setattr(order_obj, field, value)
            final_orders.append(order_obj)
        try:
            response = self._client.service.addOrUpdateOrders(final_orders)
            if hasattr(response, 'errors'):
                err_str = ', '.join(['%s: %s' % (response.results[x].errorCode,
                                                 response.results[x].errorString)
                                     for x in response.errors])
                raise BrontoError('An error occurred while adding orders: %s'
                                  % err_str)
        except WebFault as e:
            raise BrontoError(e.message)
        return response

    def add_order(self, order):
        order = self.add_orders([order, ])
        try:
            return order.results[0]
        except:
            return order.results

    def get_orders(self, order_ids):
        pass

    def get_order(self, order_id):
        order = self.get_orders([order_id, ])
        try:
            return order[0]
        except:
            return order

    def delete_orders(self, order_ids):
        orders = []
        for order_id in order_ids:
            order = self._client.factory.create('orderObject')
            order.id = order_id
            orders.append(order)
        try:
            response = self._client.service.deleteOrders(orders)
        except WebFault as e:
            raise BrontoError(e.message)
        return response

    def delete_order(self, order_id):
        response = self.delete_orders([order_id, ])
        try:
            return response.results[0]
        except:
            return response.results

    def add_fields(self, fields):
        """
        >>> client.add_fields([{
                    'name': 'internal_name',
                    'label': 'public_name',
                    'type': 'text',
                    'visibility': 'private',
                }, {
                    'name': 'internal_name2',
                    'label': 'public_name2',
                    'type': 'select',
                    'options': [{
                        'value': 'value1',
                        'label': 'Value 1',
                        'isDefault': 0
                        }]
                }])
        >>>
        """
        required_attributes = ['name', 'label', 'type']
        final_fields = []
        for field in fields:
            if not all(key in field for key in required_attributes):
                raise ValueError('The attributes %s are required.'
                        % required_attributes)
            field_obj = self._client.factory.create('fieldObject')
            for attribute, value in field.iteritems():
                if attribute not in self._valid_field_fields:
                    raise KeyError('Invalid field attribute: %s' % attribute)
                else:
                    setattr(field_obj, attribute, value)
            final_fields.append(field_obj)
        try:
            response = self._client.service.addFields(final_fields)
            if hasattr(response, 'errors'):
                err_str = ', '.join(['%s: %s' % (response.results[x].errorCode,
                                                 response.results[x].errorString)
                                     for x in response.errors])
                raise BrontoError('An error occurred while adding fields: %s'
                                  % err_str)
            # If no error we force to refresh the fields' cache
            self._cached_all_fields = False
        except WebFault as e:
            raise BrontoError(e.message)
        return response

    def add_field(self, field):
        request = self.add_fields([field, ])
        try:
            return request.results[0]
        except:
            return request.results

    def get_fields(self, field_names=[]):
        #TODO: Support search per field_id
        final_fields = []
        cached = []
        filter_operator = self._client.factory.create('filterOperator')
        fop = filter_operator.EqualTo
        for field_name in field_names:
            if field_name in self._cached_fields:
                cached.append(self._cached_fields[field_name])
            else:
                field_string = self._client.factory.create('stringValue')
                field_string.operator = fop
                field_string.value = field_name
                final_fields.append(field_string)
        field_filter = self._client.factory.create('fieldsFilter')
        field_filter.name = final_fields
        filter_type = self._client.factory.create('filterType')
        if len(final_fields) > 1:
            field_filter.type = filter_type.OR
        else:
            field_filter.type = filter_type.AND

        if not self._cached_all_fields:
            try:
                response = self._client.service.readFields(field_filter,
                                                           pageNumber=1)
                for field in response:
                    self._cached_fields[field.name] = field
                if not len(final_fields):
                    self._cached_all_fields = True
            except WebFault as e:
                raise BrontoError(e.message)
        else:
            if not field_names:
                response = [y for x, y in self._cached_fields.iteritems()]
            else:
                response = []
        return response + cached

    def get_field(self, field_name):
        field = self.get_fields([field_name, ])
        try:
            return field[0]
        except:
            return field

    def delete_fields(self, field_ids):
        fields = []
        for field_id in field_ids:
            field = self._client.factory.create('fieldObject')
            field.id = field_id
            fields.append(field)
        try:
            response = self._client.service.deleteFields(fields)
        except WebFault as e:
            raise BrontoError(e.message)
        return response

    def delete_field(self, field_id):
        response = self.delete_fields([field_id, ])
        try:
            return response.results[0]
        except:
            return response.results

    def add_lists(self, lists):
        """
        >>> client.add_lists([{
                    'name': 'internal_name',
                    'label': 'Pretty name'
                }, {
                    'name': 'internal_name2',
                    'label': 'Pretty name 2'
                }])
        >>>
        """
        required_attributes = ['name', 'label']
        final_lists = []
        for list_ in lists: # Use list_ as list is a built-in object
            if not all(key in list_ for key in required_attributes):
                raise ValueError('The attributes %s are required.'
                                 % required_attributes)
            list_obj = self._client.factory.create('mailListObject')
            for attribute, value in list_.iteritems():
                if attribute not in self._valid_list_fields:
                    raise KeyError('Invalid list attribute: %s' % attribute)
                else:
                    setattr(list_obj, attribute, value)
            final_lists.append(list_obj)
        try:
            response = self._client.service.addLists(final_lists)
            if hasattr(response, 'errors'):
                err_str = ', '.join(['%s: %s' % (response.results[x].errorCode,
                                                 response.results[x].errorString)
                                     for x in response.errors])
                raise BrontoError('An error occurred while adding fields: %s'
                                  % err_str)
            # If no error we force to refresh the fields' cache
            self._cached_all_fields = False
        except WebFault as e:
            raise BrontoError(e.message)
        return response

    def add_list(self, list_):
        request = self.add_lists([list_, ])
        try:
            return request.results[0]
        except:
            return request.results

    def get_lists(self, list_names=[]):
        #TODO: Support search per list_id
        final_lists = []
        cached = []
        filter_operator = self._client.factory.create('filterOperator')
        fop = filter_operator.EqualTo
        for list_name in list_names:
            if list_name in self._cached_lists:
                cached.append(self._cached_lists[list_name])
            else:
                list_string = self._client.factory.create('stringValue')
                list_string.operator = fop
                list_string.value = list_name
                final_lists.append(list_string)

        if list_names and not final_lists: # if we already have all the lists
            return [self._cached_lists.get(name) for name in list_names]

        list_filter = self._client.factory.create('mailListFilter')
        list_filter.name = final_lists
        filter_type = self._client.factory.create('filterType')
        if len(final_lists) > 1:
            list_filter.type = filter_type.OR
        else:
            list_filter.type = filter_type.AND

        if not self._cached_all_lists:
            try:
                response = self._client.service.readLists(list_filter,
                                                          pageNumber=1)
                for list_ in response:
                    self._cached_lists[list_.name] = list_
                if not len(final_lists):
                    self._cached_all_lists = True
            except WebFault as e:
                raise BrontoError(e.message)
        else:
            if not list_names:
                response = [y for x, y in self._cached_lists.iteritems()]
            else:
                response = []
        return response + cached

    def get_list(self, list_name):
        list_ = self.get_lists([list_name, ])
        try:
            return list_[0]
        except:
            return list_

    def delete_lists(self, list_ids):
        lists = []
        for list_id in list_ids:
            list_ = self._client.factory.create('mailListObject')
            list_.id = list_id
            lists.append(list_)
        try:
            response = self._client.service.deleteLists(lists)
        except WebFault as e:
            raise BrontoError(e.message)
        return response

    def delete_list(self, list_id):
        response = self.delete_lists([list_id, ])
        try:
            return response.results[0]
        except:
            return response.results


    def add_contacts_to_list(self, list_, contacts):
        """
        The list must have either an id or a name defined.
        The contacts must have either an id or an email defined.
        >>> client.add_contacts_to_list({'id': 'xxx-xxx'},
                [{id: 'yyy-yyy'}, {email: 'email2@example.com'}])
        >>> client.add_contacts_to_list({'name': 'my_list'},
                [{id: 'yyy-yyy'}, {email: 'email2@example.com'}])
        >>>
        """
        valid_list_attributes = ['id', 'name']
        valid_contact_attributes = ['id', 'email']

        if not any(key in list_ for key in valid_list_attributes):
            raise ValueError('Must provide either a name '
                    'or id for your lists.')
        final_list = self._client.factory.create('mailListObject')
        for attribute in valid_list_attributes:
            if attribute in list_:
                setattr(final_list, attribute, list_[attribute])

        final_contacts = []
        for contact in contacts:
            if not any(key in contact for key in valid_contact_attributes):
                raise ValueError('Must provide either an email '
                        'or id for your contacts.')
            contact_obj = self._client.factory.create('contactObject')
            for attribute in valid_contact_attributes:
                if attribute in contact:
                    setattr(contact_obj, attribute, contact[attribute])
            final_contacts.append(contact_obj)
        try:
            response = self._client.service.addToList(final_list,
                    final_contacts)

            if hasattr(response, 'errors'):
                err_str = ', '.join(['%s: %s' % (response.results[x].errorCode,
                                                 response.results[x].errorString)
                                     for x in response.errors])
                raise BrontoError(
                        'An error occurred while adding contacts to a list: %s'
                        % err_str)
            # If no error we force to refresh the fields' cache
            self._cached_all_fields = False
        except WebFault as e:
            raise BrontoError(e.message)
        return response

    def add_contact_to_list(self, list_, contact):
        """
        Add one contact to one list

        """
        request = self.add_contacts_to_list(list_, [contact,])
        try:
            return request.results[0]
        except:
            return request.results

    def get_messages(self, message_names=[]):
        #TODO: Support search per message_id
        final_messages = []
        cached = []
        filter_operator = self._client.factory.create('filterOperator')
        fop = filter_operator.EqualTo
        for message_name in message_names:
            if message_name in self._cached_messages:
                cached.append(self._cached_messages[message_name])
            else:
                message_string = self._client.factory.create('stringValue')
                message_string.operator = fop
                message_string.value = message_name
                final_messages.append(message_string)

        if message_names and not final_messages: # if we already have all the messages
            return [self._cached_messages.get(name) for name in message_names]

        message_filter = self._client.factory.create('messageFilter')
        message_filter.name = final_messages
        filter_type = self._client.factory.create('filterType')
        message_filter.type = filter_type.OR

        if not self._cached_all_messages:
            try:
                response = self._client.service.readMessages(message_filter,
                                                             pageNumber=1)
                for message in response:
                    self._cached_messages[message.name] = message
                if not len(final_messages):
                    self._cached_all_messages = True
            except WebFault as e:
                raise BrontoError(e.message)
        else:
            if not message_names:
                response = [y for x, y in self._cached_messages.iteritems()]
            else:
                response = []
        return response + cached

    def get_message(self, message_name):
        messages = self.get_messages([message_name, ])
        try:
            return messages[0]
        except:
            return messages

    def add_deliveries(self, deliveries):
        """
        >>> client.add_deliveries([{
                'start': '2014-05-07T00:42:07',
                'messageId': 'xxxxx-xxxx-xxxxx',
                'fromName': 'John Doe',
                'fromEmail': 'test@example.com',
                'recipients': [{
                    'type': 'contact',
                    'id': 'xxxxx-xxxx-xxxxx'
                }],
                'type': 'transactional',
                'fields': [{
                    'name': 'link',
                    'type': 'html',
                    'content': '<a href="http://www.test.com">link</a>'
                    }, {
                    'name': 'message',
                    'type': 'html',
                    'content': 'Dynamic message!!!'
                }]
            }])
        >>>

        The timezone of the start date is considered to be the one you have setup
        in your bronto account if you don't specify it. If you want to use UTC,
        you can use:
        from datetime import datetime
        datetime.strftime(datetime.utcnow(), '%FT%T+00:00')

        For more details: http://dev.bronto.com/api/v4/data-format
        """
        required_attributes = ['start', 'messageId', 'type', 'fromEmail',
                #'replyEmail', Even if the doc says so, it's not required
                'fromName', 'recipients']
        final_deliveries = []
        for delivery in deliveries:
            if not all(key in delivery for key in required_attributes):
                raise ValueError('The attributes %s are required.'
                                 % required_attributes)
            delivery_obj = self._client.factory.create('deliveryObject')
            for attribute, value in delivery.iteritems():
                if attribute not in self._valid_delivery_fields:
                    raise KeyError('Invalid list attribute: %s' % attribute)
                else:
                    setattr(delivery_obj, attribute, value)
            final_deliveries.append(delivery_obj)
        try:
            response = self._client.service.addDeliveries(final_deliveries)
            if hasattr(response, 'errors'):
                err_str = ', '.join(['%s: %s' % (response.results[x].errorCode,
                                                 response.results[x].errorString)
                                     for x in response.errors])
                raise BrontoError('An error occurred while adding deliveries: %s'
                                  % err_str)
        except WebFault as e:
            raise BrontoError(e.message)
        return response

    def add_delivery(self, delivery):
        request = self.add_deliveries([delivery, ])
        try:
            return request.results[0]
        except:
            return request.results
