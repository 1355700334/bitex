"""
Task:
Do fancy shit.
"""

# Import Built-ins
import logging
import json
import hashlib
import hmac
import base64
import time
import urllib.parse
from requests.auth import AuthBase

# Import Third-Party

# Import Homebrew
from bitex.api.api import RESTAPI


log = logging.getLogger(__name__)


class BitfinexREST(RESTAPI):
    def __init__(self, key='', secret='', api_version='v1',
                 url='https://api.bitfinex.com'):
        super(BitfinexREST, self).__init__(url, api_version=api_version,
                                           key=key, secret=secret)

    def sign(self, url, endpoint, endpoint_path, method_verb, *args, **kwargs):
        try:
            req = kwargs['params']
        except KeyError:
            req = {}
        req['request'] = endpoint_path
        req['nonce'] = self.nonce()

        js = json.dumps(req)
        data = base64.standard_b64encode(js.encode('utf8'))

        h = hmac.new(self.secret.encode('utf8'), data, hashlib.sha384)
        signature = h.hexdigest()
        headers = {"X-BFX-APIKEY": self.key,
                   "X-BFX-SIGNATURE": signature,
                   "X-BFX-PAYLOAD": data}

        return url, {'headers': headers}


class BitstampREST(RESTAPI):
    def __init__(self, user_id='', key='', secret='', api_version='',
                 url='https://www.bitstamp.net/api'):
        self.id = user_id
        super(BitstampREST, self).__init__(url, api_version=api_version,
                                           key=key, secret=secret)

    def load_key(self, path):
        """
        Load key and secret from file.
        """
        with open(path, 'r') as f:
            self.id = f.readline().strip()
            self.key = f.readline().strip()
            self.secret = f.readline().strip()

    def sign(self, url, endpoint, endpoint_path, method_verb, *args, **kwargs):
        nonce = self.nonce()
        message = nonce + self.id + self.key

        signature = hmac.new(self.secret.encode(), message.encode(),
                             hashlib.sha256)
        signature = signature.hexdigest().upper()

        try:
            req = kwargs['params']
        except KeyError:
            req = {}
        req['key'] = self.key
        req['nonce'] = nonce
        req['signature'] = signature
        return url, {'data': req}


class BittrexREST(RESTAPI):
    def __init__(self, key='', secret='', api_version='v1.1',
                 url='https://bittrex.com/api'):
        super(BittrexREST, self).__init__(url, api_version=api_version, key=key,
                                          secret=secret)

    def sign(self, url, endpoint, endpoint_path, method_verb, *args, **kwargs):

        try:
            params = kwargs['params']
        except KeyError:
            params = {}

        nonce = self.nonce()

        req_string = endpoint_path + '?apikey=' + self.key + "&nonce=" + nonce + '&'
        req_string += urllib.parse.urlencode(params)

        headers = {"apisign": hmac.new(self.secret.encode('utf-8'),
                                       req_string.encode('utf-8'),
                                       hashlib.sha512).hexdigest()}

        return req_string, {'headers': headers, 'params': {}}


class CoincheckREST(RESTAPI):
    def __init__(self, key='', secret='', api_version='api',
                 url='https://coincheck.com'):
        super(CoincheckREST, self).__init__(url, api_version=api_version,
                                            key=key, secret=secret)

    def sign(self, url, endpoint, endpoint_path, method_verb, *args, **kwargs):

        nonce = self.nonce()
        try:
            params = kwargs['params']
        except KeyError:
            params = {}

        params = json.dumps(params)
        # sig = nonce + url + req
        data = (nonce + endpoint_path + params).encode('utf-8')
        h = hmac.new(self.secret.encode('utf8'), data, hashlib.sha256)
        signature = h.hexdigest()
        headers = {"ACCESS-KEY": self.key,
                   "ACCESS-NONCE": nonce,
                   "ACCESS-SIGNATURE": signature}

        return url, {'headers': headers}


class GdaxAuth(AuthBase):
    def __init__(self, api_key, secret_key, passphrase):
        self.api_key = api_key.encode('utf-8')
        self.secret_key = secret_key.encode('utf-8')
        self.passphrase = passphrase.encode('utf-8')

    def __call__(self, request):
        timestamp = str(time.time())
        message = (timestamp + request.method + request.path_url +
                   (request.body or ''))
        hmac_key = base64.b64decode(self.secret_key)
        signature = hmac.new(hmac_key, message.encode('utf-8'), hashlib.sha256)
        signature_b64 = base64.b64encode(signature.digest())

        request.headers.update({
            'CB-ACCESS-SIGN': signature_b64,
            'CB-ACCESS-TIMESTAMP': timestamp,
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        })
        return request


class GDAXRest(RESTAPI):
    def __init__(self, passphrase='', key='', secret='', api_version='',
                 url='https://api.gdax.com'):
        self.passphrase = passphrase
        super(GDAXRest, self).__init__(url, api_version=api_version, key=key,
                                       secret=secret)

    def load_key(self, path):
        """
        Load key and secret from file.
        """
        with open(path, 'r') as f:
            self.passphrase = f.readline().strip()
            self.key = f.readline().strip()
            self.secret = f.readline().strip()

    def sign(self, url, endpoint, endpoint_path, method_verb, *args, **kwargs):
        auth = GdaxAuth(self.key, self.secret, self.passphrase)
        try:
            js = kwargs['params']
        except KeyError:
            js = {}

        return url, {'json': js, 'auth': auth}


class KrakenREST(RESTAPI):
    def __init__(self, key='', secret='', api_version='0',
                 url='https://api.kraken.com'):
        super(KrakenREST, self).__init__(url, api_version=api_version,
                                         key=key, secret=secret)

    def sign(self, url, endpoint, endpoint_path, method_verb, *args, **kwargs):
        try:
            req = kwargs['params']
        except KeyError:
            req = {}

        req['nonce'] = self.nonce()
        postdata = urllib.parse.urlencode(req)

        # Unicode-objects must be encoded before hashing
        encoded = (str(req['nonce']) + postdata).encode('utf-8')
        message = (endpoint_path.encode('utf-8') +
                   hashlib.sha256(encoded).digest())

        signature = hmac.new(base64.b64decode(self.secret),
                             message, hashlib.sha512)
        sigdigest = base64.b64encode(signature.digest())

        headers = {
            'API-Key': self.key,
            'API-Sign': sigdigest.decode('utf-8')
        }

        return url, {'data': req, 'headers': headers}


class ItbitREST(RESTAPI):
    def __init__(self, user_id = '', key='', secret='', api_version='v1',
                 url='https://api.itbit.com'):
        self.userId = user_id
        super(ItbitREST, self).__init__(url, api_version=api_version,
                                 key=key, secret=secret)

    def load_key(self, path):
        """
        Load user id, key and secret from file.
        """
        with open(path, 'r') as f:
            self.userId = f.readline().strip()
            self.clientKey = f.readline().strip()
            self.secret = f.readline().strip()

    def sign(self, url, endpoint, endpoint_path, method_verb, *args, **kwargs):
        try:
            params = kwargs['params']
        except KeyError:
            params = {}

        verb = method_verb

        if verb in ('PUT', 'POST'):
            body = params
        else:
            body = {}

        timestamp = self.nonce()
        nonce = self.nonce()

        message = json.dumps([verb, url, body, nonce, timestamp],
                             separators=(',', ':'))
        sha256_hash = hashlib.sha256()
        nonced_message = nonce + message
        sha256_hash.update(nonced_message.encode('utf8'))
        hash_digest = sha256_hash.digest()
        hmac_digest = hmac.new(self.secret.encode('utf-8'),
                               url.encode('utf-8') + hash_digest,
                               hashlib.sha512).digest()
        signature = base64.b64encode(hmac_digest)

        auth_headers = {
            'Authorization': self.key + ':' + signature.decode('utf8'),
            'X-Auth-Timestamp': timestamp,
            'X-Auth-Nonce': nonce,
            'Content-Type': 'application/json'
        }
        return url, {'headers': auth_headers}


class OKCoinREST(RESTAPI):
    def __init__(self, key='', secret='', api_version='v1',
                 url='https://www.okcoin.com/api'):
        super(OKCoinREST, self).__init__(url, api_version=api_version,
                                         key=key,
                                         secret=secret)

    def sign(self,url, endpoint, endpoint_path, method_verb, *args, **kwargs):
        nonce = self.nonce()

        # sig = nonce + url + req
        data = (nonce + url).encode()

        h = hmac.new(self.secret.encode('utf8'), data, hashlib.sha256)
        signature = h.hexdigest()
        headers = {"ACCESS-KEY":       self.key,
                   "ACCESS-NONCE":     nonce,
                   "ACCESS-SIGNATURE": signature}

        return url, {'headers': headers}


class BTCERest(RESTAPI):
    def __init__(self, key='', secret='', api_version='3',
                 url='https://btc-e.com/api'):
        super(BTCERest, self).__init__(url, api_version=api_version, key=key,
                                         secret=secret)

    def sign(self, url, endpoint, endpoint_path, method_verb, *args, **kwargs):
        nonce = self.nonce()
        try:
            params = kwargs['params']
        except KeyError:
            params = {}
        post_params = params
        post_params.update({'nonce': nonce, 'method': endpoint.split('/', 1)[1]})
        post_params = urllib.parse.urlencode(post_params)

        signature = hmac.new(self.secret.encode('utf-8'),
                             post_params.encode('utf-8'), hashlib.sha512)
        headers = {'Key': self.key, 'Sign': signature.hexdigest(),
                   "Content-type": "application/x-www-form-urlencoded"}

        # split by tapi str to gain clean url;
        url = url.split('/tapi', 1)[0] + '/tapi'

        return url, {'headers': headers, 'params': params}


class CCEXRest(RESTAPI):
    def __init__(self, key='', secret='', api_version='',
                 url='https://c-cex.com/t/api_pub.html?a='):
        super(CCEXRest, self).__init__(url, api_version=api_version, key=key,
                                         secret=secret)

    def sign(self, uri, endpoint, endpoint_path, method_verb, *args, **kwargs):
        nonce = self.nonce()
        try:
            params = kwargs['params']
        except KeyError:
            params = {}

        api_key = ''

        params['apikey'] = api_key
        parmas['nonce'] = nonce
        post_params = params
        post_params.update({'nonce': nonce, 'method': endpoint})
        post_params = urllib.parse.urlencode(post_params)

        url = uri.split('_pub')[0] + '.html?a=' + endpoint + post_params

        sig = hmac.new(self.key, url, hashlib.sha512)
        headers = {'apisign': sig}

        return url, {'headers': headers}