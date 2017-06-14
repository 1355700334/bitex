# Import Built-Ins
import logging
from unittest import TestCase
import time
import hmac
import hashlib

# Import Third-Party
import requests

# Import Homebrew
from bitex.base import BaseAPI, RESTAPI
from bitex.rest import BitstampREST
from bitex.exceptions import IncompleteCredentialsWarning, IncompleteCredentialsError

# Init Logging Facilities
log = logging.getLogger(__name__)


class BaseAPITests(TestCase):
    def test_base_api_parameters_initialize_correctly(self):
        # Raises an error if a Kwarg wasn't given (i.e. instantiation must
        # specify kwargs explicitly)
        with self.assertRaises(TypeError):
            api = BaseAPI(addr='Bangarang')

        # raise error if address is None
        with self.assertRaises(ValueError):
            api = BaseAPI(addr=None, key=None, secret=None,
                          config=None, version=None)

        # silently initialize if all other parameters are none
        api = BaseAPI(addr='Bangarang', key=None, secret=None, config=None,
                      version=None)

        # if version is None, make version an empty string
        self.assertEqual(api.version, '')

        # if key is None, make key None
        self.assertIs(api.key, None)

        # if secret is None, make secret None
        self.assertIs(api.secret, None)

        # raise warning if only key or only secret is passed
        with self.assertWarns(IncompleteCredentialsWarning):
            api = BaseAPI(addr='Bangarang', key='SomeKey', secret=None,
                          config=None, version=None)
        with self.assertWarns(IncompleteCredentialsWarning):
            api = BaseAPI(addr='Bangarang', key=None, secret='SomeSecret',
                          config=None, version=None)

        # raise a Value Error if an empty string is passed in either key or
        # secret kwarg
        with self.assertRaises(ValueError):
            api = BaseAPI(addr='Bangarang', key='', secret=None,
                          config=None, version=None)
        with self.assertRaises(ValueError):
            api = BaseAPI(addr='Bangarang', key=None, secret='',
                          config=None, version=None)

        # Make sure all attributes are correctly updated if a config file is
        # given
        api = BaseAPI(addr='http://some.api.com', key='shadow', secret='panda',
                      config='/home/nils/git/bitex/tests/configs/config.ini',
                      version='v2')
        self.assertEqual(api.addr, 'http://some.api.com')
        self.assertEqual(api.secret, 'panda')
        self.assertEqual(api.key, 'shadow')
        self.assertEqual(api.version, 'v2')

        # Make sure nonce() method always supplies increasing Nonce
        previous_nonce = 0
        for i in range(100):
            time.sleep(0.01)
            new_nonce = int(api.nonce())
            self.assertLess(previous_nonce, new_nonce)
            previous_nonce = new_nonce


class RESTAPITests(TestCase):
    def test_generate_methods_work_correctly(self):
        api = RESTAPI(addr='http://some.api.com', key='shadow', secret='panda',
                      version='v2')

        # generate_uri returns a string of version + endpoint
        uri = api.generate_uri('market')
        self.assertEqual(uri, '/v2/market')

        # generate_url returns a string of address + uri
        self.assertEqual(api.generate_url(uri), 'http://some.api.com/v2/market')

    def test_sign_request_kwargs_method_and_signature(self):
        api = RESTAPI(addr='http://some.api.com', key='shadow', secret='panda',
                      version='v2')
        # generate_request_kwargs returns a dict with all necessary keys present
        d = api.sign_request_kwargs('market')
        template = {'url': 'http://some.api.com/v2/market',
                    'headers': None, 'files': None, 'data': None, 'hooks': None,
                    'params': None, 'auth': None, 'cookies': None, 'json': None}
        for k in template:
            self.assertTrue(k in d)

    def test_query_methods_return_as_expected(self):
        # assert that an InvalidCredentialsError is raised, if any of the auth
        # attributes are None (key, secret)
        api = RESTAPI(addr='http://some.api.com', key='shadow', secret=None,
                      version='v2', timeout=5)

        with self.assertRaises(IncompleteCredentialsError):
            api.private_query('GET', 'market', url='https://www.someapi.com')

        api = RESTAPI(addr='http://some.api.com', key=None, secret='panda',
                      version='v2')

        with self.assertRaises(IncompleteCredentialsError):
            api.private_query('GET', 'market', url='https://www.someapi.com')

        api = RESTAPI(addr='http://some.api.com', key=None, secret=None,
                      version='v2')

        with self.assertRaises(IncompleteCredentialsError):
            api.private_query('GET', 'market', url='https://www.someapi.com')

        # assert that _query() silently returns an requests.Response() obj, if
        # the request was good
        try:
            resp = api._query('GET', url='https://api.kraken.com/0/public/Time')
        except requests.exceptions.ConnectionError:
            self.fail("No Internet connection detected to ")
        self.assertIsInstance(resp, requests.Response)

        # assert that _query() raises an appropriate error on status code other
        # than 200
        with self.assertRaises(requests.exceptions.HTTPError):
            api._query('data', url='https://api.kraken.com/0/public/Wasabi')
        self.fail("finish this test!")


class BitstampRESTTests(TestCase):
    def test_initialization(self):
        # test that all default values are assigned correctly if No kwargs are
        # given
        api = BitstampREST()
        self.assertIs(api.secret, None)
        self.assertIs(api.key, None)
        self.assertEqual(api.addr, 'https://www.bitstamp.net/api')
        self.assertIs(api.version, '')
        self.assertIs(api.config_file, None)
        # make sure a warning is displayed upon incomplete credentials
        with self.assertWarns(IncompleteCredentialsWarning):
            api = BitstampREST(addr='Bangarang', user_id=None, key='SomeKey',
                               secret='SomeSecret', config=None, version=None)

        # make sure an exception is raised if user_id is passed as ''
        with self.assertRaises(ValueError):
            api = BitstampREST(addr='Bangarang', user_id='', key='SomeKey',
                               secret='SomeSecret', config=None,
                               version=None)

        # make sure user_id is assigned properly
        api = BitstampREST(addr='Bangarang', user_id='woloho')
        self.assertIs(api.user_id, 'woloho')

        # make sure that load_config loads user_id correctly, and issues a
        # warning if user_id param isn't available
        with self.assertWarns(IncompleteCredentialsWarning):
            api = BitstampREST(addr='Bangarang',
                               config='/home/nls/git/bitex/tests/configs/config.ini')

        config_path = '/home/nls/git/bitex/tests/configs/config_bitstamp.ini'
        api = BitstampREST(config=config_path)
        self.assertTrue(api.config_file == config_path)
        self.assertEqual(api.user_id, 'testuser')

    def test_private_query_raises_error_on_incomplete_credentials(self):
        config_path = '/home/nls/git/bitex/tests/keys/bitstamp.ini'
        api = BitstampREST(config=config_path)
        with self.assertRaises(IncompleteCredentialsError):
            api.private_query('POST', 'balance')


    def test_sign_request_kwargs_method_and_signature(self):
        # Test that the sign_request_kwargs generate appropriate kwargs:
        config_path = '/home/nls/git/bitex/tests/keys/bitstamp.ini'
        api = BitstampREST(config=config_path)
        resp = api.private_query('POST', 'balance/btcusd')
        self.assertEqual(resp.status, 200)
        self.fail("Finish this test")

if __name__ == '__main__':
    import unittest
    unittest.main()
