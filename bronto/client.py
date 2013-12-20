from suds import WebFault
from suds.client import Client as SudsClient


class BrontoError(Exception):
    pass


class Client(object):
    _valid_contact_fields = ['email', 'mobileNumber', 'status', 'msgPref',
                             'source', 'customSource', 'listIds', 'fields',
                             'SMSKeywordIDs']

    def __init__(self, endpoint, token, **kwargs):
        if not endpoint or not isinstance(endpoint, basestring):
            raise ValueError('Must supply an endpoint as a non empty string.')
        if not token or not isinstance(endpoint, basestring):
            raise ValueError('Must supply a token as a non empty string.')

        self._endpoint = endpoint
        self._token = token

    def login(self):
        self.client = SudsClient(self._endpoint)
        try:
            self.session_id = self.client.service.login(self._token)
            session_header = self.client.factory.create('sessionHeader')
            session_header.sessionId = self.session_id
            self.client.set_options(soapheaders=session_header)
        except WebFault as e:
            raise BrontoError(e.message)

    def add_contacts(self, contacts):
        final_contacts = []
        for contact in contacts:
            if not isinstance(contact, dict):
                raise ValueError('Each contact must be a dictionary of contact attributes')
            if not any([contact.get('email'), contact.get('mobileNumber')]):
                raise ValueError('Must provide either an email or mobileNumber')
            contact_obj = self.client.factory.create('contactObject')
            # FIXME: Add special handling for listIds, fields and SMSKeywordIDs
            for field, value in contact:
                if field not in self._valid_contact_fields:
                    raise KeyError('Invalid contact attribute: %s' % field)
                setattr(contact_obj, field, value)
            final_contacts.append(contact_obj)
        try:
            response = self.client.service.addContacts(final_contacts)
            if response.errors:
                err_str = ', '.join(['%s: %s' % (response.results[x].errorCode,
                                                 response.results[x].errorString)
                                     for x in response.errors])
                raise BrontoError('An error occurred while adding contacts: %s'
                                  % err_str)
        except WebFault as e:
            raise BrontoError(e.message)
        return response

    def add_contact(self, contact):
        return self.add_contacts([contact, ])
