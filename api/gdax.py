# This file is part of krakenex.
#
# krakenex is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# krakenex is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser
# General Public LICENSE along with krakenex. If not, see
# <http://www.gnu.org/licenses/gpl-3.0.txt>.


import json
import urllib.request, urllib.parse, urllib.error
import requests
import base64
from requests.auth import AuthBase
# private query nonce
import time

# private query signing
import hashlib
import hmac
import base64


class APIError(Exception):
    pass


class CoinbaseExchangeAuth(AuthBase):
    def __init__(self, api_key, secret_key, passphrase):
        self.api_key = api_key.encode()
        self.secret_key = secret_key.encode()
        self.passphrase = passphrase.encode()

    def __call__(self, request):
        timestamp = str(time.time())
        message = timestamp + request.method + request.path_url + (request.body or '')
        hmac_key = base64.b64decode(self.secret_key)
        #print(hmac_key, type(hmac_key))
        #print(message, type(message))
        signature = hmac.new(hmac_key, message.encode(), hashlib.sha256)

        signature_b64 = base64.b64encode(signature.digest())


        request.headers.update({
            'CB-ACCESS-SIGN': signature_b64,
            'CB-ACCESS-TIMESTAMP': timestamp,
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        })
        return request


class API(object):
    """Kraken.com cryptocurrency Exchange API.
    
    """
    def __init__(self, key = '', secret = '', passphrase='', conn = None):
        """Create an object with authentication information.
        
        :param key: key required to make queries to the API
        :type key: str
        :param secret: private key used to sign API messages
        :type secret: str
        :param conn: connection TODO
        :type conn: krakenex.Connection
        
        """
        self.passphrase = passphrase
        self.key = key
        self.secret = secret
        self.uri = 'https://api.gdax.com/'
        self.apiversion = '0'
        self.conn = conn

    def load_key(self, path):
        """Load key and secret from file.
        
        Argument:
        :param path: path to keyfile
        :type path: str
        
        """
        f = open(path, "r")
        self.passphrase = f.readline().strip()
        self.key = f.readline().strip()
        self.secret = f.readline().strip()

    def set_connection(self, conn):
        """Set an existing connection to be used as a default in queries.

        :param conn: connection TODO
        :type conn: krakenex.Connection
        """
        self.conn = conn

    def _query(self, urlpath, req = {}, auth = {}, post=False):
        """Low-level query handling.
        
        :param urlpath: API URL path sans host
        :type urlpath: str
        :param req: additional API request parameters
        :type req: dict
        :param conn: connection TODO
        :type conn: krakenex.Connection
        :param headers: HTTPS headers
        :type headers: dict
        """
        url = self.uri + urlpath
        print(url, req)

        api_query = requests.post if post else requests.get

        if auth:
            r = api_query(url, json=req, auth=auth)
        else:
            r = api_query(url, json=req)

        try:
            response = r.json()
        except:
            print(r.text)
            raise

        if isinstance(response, dict) and 'error' in response:
            print(response)
            raise APIError(response['error'])

        return response

    def query_public(self, method, req = {}, post=False):
        """API queries that do not require a valid key/secret pair.
        
        :param method: API method name
        :type method: str
        :param req: additional API request parameters
        :type req: dict
        :param conn: connection TODO
        :type conn: krakenex.Connection
        """

        return self._query(method, req, post=post)
    
    def query_private(self, method, req={}, post=False):
        """API queries that require a valid key/secret pair.
        
        :param method: API method name
        :type method: str
        :param req: additional API request parameters
        :type req: dict
        :param conn: connection TODO
        :type conn: krakenex.Connection
        """

        auth = CoinbaseExchangeAuth(self.key, self.secret, self.passphrase)

        return self._query(method, req, auth, post=post)
