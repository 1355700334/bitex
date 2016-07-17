"""
Task:
Descripion of script here.
"""

# Import Built-Ins
import logging
import hashlib
import hmac
import time
import json

# Import Third-Party
import requests

# Import Homebrew
from bitex.api.api import RESTAPI

# Init Logging Facilities
log = logging.getLogger(__name__)


class APIError(Exception):
    pass


class API(RESTAPI):
    def __init__(self, user_id='', key='', secret='', api_version='',
                 url='https://www.bitstamp.net/api'):
        self.id = user_id
        super(API, self).__init__(url, api_version=api_version, key=key,
                                  secret=secret)

    def load_key(self, path):
        """
        Load key and secret from file.
        """
        with open(path, 'r') as f:
            self.id = f.readline().strip()
            self.key = f.readline().strip()
            self.secret = f.readline().strip()

    def sign(self, *args, **kwargs):
        nonce = str(int(time.time() * 1e6))
        message = nonce + self.id + self.key

        signature = hmac.new(bytes(self.secret, 'utf-8'), bytes(message, 'utf-8'),
                             hashlib.sha256)
        signature = signature.hexdigest().upper()

        try:
            req = kwargs['data']
        except KeyError:
            req = {}
        req['key'] = self.key
        req['nonce'] = nonce
        req['signature'] = signature
        print(req)

        return {'data': req}
