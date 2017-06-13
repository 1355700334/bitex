"""
Contains all API Client sub-classes, which store exchange specific details
and feature the respective exchanges authentication method (sign()).
"""
# Import Built-ins
import logging
import json
import hashlib
import hmac
import base64
import time
import urllib
import urllib.parse
import warnings

# Import Third-Party
from requests.auth import AuthBase

try:
    import pyjwt as jwt
    jwt = True
except ImportError:
    jwt = False

# Import Homebrew
from bitex.api.base import RESTAPI
from bitex.exceptions import IncompleteCredentialsWarning


log = logging.getLogger(__name__)


class BitfinexREST(RESTAPI):
    def __init__(self, addr='https://api.bitfinex.com', key=None, secret=None,
                 version='v1', config=None, timeout=None):
        super(BitfinexREST, self).__init__(addr=addr, version=version, key=key,
                                           secret=secret, timeout=timeout,
                                           config=config)

    def sign_request_kwargs(self, endpoint, *args, **kwargs):
        req_kwargs = super(BitfinexREST, self).sign_request_kwargs(endpoint,
                                                                   **kwargs)

        # Parameters go into headers, so pop params key and generate signature
        params = req_kwargs.pop('params')
        params['request'] = self.generate_uri(endpoint)
        params['nonce'] = self.nonce()

        # convert to json, encode and hash
        js = json.dumps(params)
        data = base64.standard_b64encode(js.encode('utf8'))

        h = hmac.new(self.secret.encode('utf8'), data, hashlib.sha384)
        signature = h.hexdigest()

        # Update headers and return
        req_kwargs['headers'] = {"X-BFX-APIKEY": self.key,
                                 "X-BFX-SIGNATURE": signature,
                                 "X-BFX-PAYLOAD": data}

        return req_kwargs


class BitstampREST(RESTAPI):
    def __init__(self, addr=None, user_id=None, key=None, secret=None,
                 version=None, timeout=5, config=None):
        addr = 'https://www.bitstamp.net/api' if not addr else addr
        if user_id == '':
            raise ValueError("Invalid user id - cannot be empty string! "
                             "Pass None instead!")
        self.user_id = user_id
        if (not all(x is None for x in (user_id, key, secret)) or
                not all(x is not None for x in (user_id, key, secret))):
            warnings.warn("Incomplete Credentials were given - authentication "
                          "may not work!", IncompleteCredentialsWarning)

        super(BitstampREST, self).__init__(addr=addr, version=version,
                                           key=key, secret=secret,
                                           timeout=timeout, config=config)

    def load_config(self, fname):
        conf = super(BitstampREST, self).load_config(fname)
        try:
            self.user_id = conf['AUTH']['user_id']
        except KeyError:
            warnings.warn(IncompleteCredentialsWarning,
                          "'user_id' not found in config!")

    def load_key(self, path):
        """
        Load key and secret from file.
        """
        with open(path, 'r') as f:
            self.key = f.readline().strip()
            self.secret = f.readline().strip()
            self.id = f.readline().strip()

    def sign_request_kwargs(self, endpoint, **kwargs):
        req_kwargs = super(BitstampREST, self).sign_request_kwargs(endpoint,
                                                                   **kwargs)

        # Generate Signature
        nonce = self.nonce()
        message = nonce + self.user_id + self.key
        signature = hmac.new(self.secret.encode('utf-8'), message.encode('utf-8'),
                             hashlib.sha256)
        signature = signature.hexdigest().upper()

        # Parameters go into the data kwarg, so move it there from 'params'
        params = req_kwargs.pop('params')
        params['key'] = self.key
        params['nonce'] = nonce
        params['signature'] = signature
        req_kwargs['data'] = params

        return req_kwargs


class BittrexREST(RESTAPI):
    def __init__(self, key=None, secret=None, version=None,
                 addr=None, timeout=5, config=None):
        version = 'v1.1' if not version else version
        addr = 'https://bittrex.com/api' if not addr else addr
        super(BittrexREST, self).__init__(addr=addr, version=version, key=key,
                                          secret=secret, timeout=timeout,
                                          config=config)

    def sign_request_kwargs(self, endpoint, **kwargs):
        """
        Bittrex requires the request address to be included as a sha512 encoded
        string in the query header. This means that the request address used for
        signing, and the actual address used to send the request (incuding order
        of parameters) needs to be identical. Hence, we must build the request
        address ourselves, instead of relying on the requests library to do it
        for us.
        """
        req_kwargs = super(BittrexREST, self).sign_request_kwargs(endpoint,
                                                                  **kwargs)

        # Prepare arguments for query request.
        try:
            params = kwargs.pop('params')
        except KeyError:
            params = {}
        nonce = self.nonce()
        uri = self.generate_uri(endpoint)
        url = self.generate_url(uri)

        # Build request address
        req_string = '?apikey=' + self.key + "&nonce=" + nonce + '&'
        req_string += urllib.parse.urlencode(params)
        request_address = url + req_string
        req_kwargs['url'] = request_address

        # generate signature
        signature = hmac.new(self.secret.encode('utf-8'),
                             request_address.encode('utf-8'),
                             hashlib.sha512).hexdigest()
        req_kwargs['headers'] = {"apisign": signature}

        return req_kwargs


class CoincheckREST(RESTAPI):
    def __init__(self, key=None, secret=None, version=None,
                 addr=None, timeout=5):
        addr = 'https://coincheck.com' if not url else url
        version = 'api' if not version else version
        super(CoincheckREST, self).__init__(addr=addr, version=api_version,
                                            key=key, secret=secret,
                                            timeout=timeout)

    def sign_request_kwargs(self, endpoint, **kwargs):
        req_kwargs = super(CoincheckREST, self).sign_request_kwargs(endpoint,
                                                                    **kwargs)

        # Prepare argument for signature
        try:
            params = kwargs.pop('params')
        except KeyError:
            params = {}
        nonce = self.nonce()
        params = json.dumps(params)

        # Create signature
        # sig = nonce + url + req
        data = (nonce + self.generate_uri(endpoint) + params).encode('utf-8')
        h = hmac.new(self.secret.encode('utf8'), data, hashlib.sha256)
        signature = h.hexdigest()

        # Update headers
        req_kwargs['headers'] = {"ACCESS-KEY": self.key,
                                 "ACCESS-NONCE": nonce,
                                 "ACCESS-SIGNATURE": signature}

        return req_kwargs


class GDAXAuth(AuthBase):
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

        request.headers.update({'CB-ACCESS-SIGN': signature_b64,
                                'CB-ACCESS-TIMESTAMP': timestamp,
                                'CB-ACCESS-KEY': self.api_key,
                                'CB-ACCESS-PASSPHRASE': self.passphrase,
                                'Content-Type': 'application/json'})
        return request


class GDAXREST(RESTAPI):
    def __init__(self, passphrase=None, key=None, secret=None, version=None,
                 addr=None, config=None, timeout=5):
        if passphrase == '':
            raise ValueError("Invalid user id - cannot be empty string! "
                             "Pass None instead!")
        if (not all(x is None for x in (passphrase, key, secret)) or
                not all(x is not None for x in (passphrase, key, secret))):
            warnings.warn("Incomplete Credentials were given - authentication "
                          "may not work!", IncompleteCredentialsWarning)
        self.passphrase = passphrase
        addr = 'https://api.gdax.com' if not addr else addr

        super(GDAXREST, self).__init__(addr=addr, version=version, key=key,
                                       secret=secret, timeout=timeout,
                                       config=config)

    def load_config(self, fname):
        conf = super(GDAXREST, self).load_config(fname)
        try:
            self.passphrase = conf['AUTH']['passphrase']
        except KeyError:
            warnings.warn(IncompleteCredentialsWarning,
                          "'passphrase' not found in config!")

    def sign_request_kwargs(self, endpoint, **kwargs):
        req_kwargs = super(GDAXREST, self).sign_request_kwargs(endpoint,
                                                               **kwargs)
        req_kwargs['auth'] = GDAXAuth(self.key, self.secret, self.passphrase)

        try:
            req_kwargs['json'] = kwargs['params']
        except KeyError:
            pass

        return req_kwargs


class KrakenREST(RESTAPI):
    def __init__(self, key=None, secret=None, version=None,
                 addr=None, timeout=5, config=None):
        addr = 'https://api.kraken.com' if not addr else addr
        version = '0' if not version else version
        super(KrakenREST, self).__init__(addr=addr, version=version, key=key,
                                         config=config, secret=secret,
                                         timeout=timeout)

    def sign_request_kwargs(self, endpoint, **kwargs):
        req_kwargs = super(KrakenREST, self).sign_request_kwargs(endpoint,
                                                                 **kwargs)
        # Prepare Payload
        try:
            payload = kwargs['params']
        except KeyError:
            payload = {}
        payload['nonce'] = self.nonce()

        # Generate Signature
        postdata = urllib.parse.urlencode(payload)
        encoded = (str(payload['nonce']) + postdata).encode('utf-8')
        message = (self.generate_uri(endpoint).encode('utf-8') +
                   hashlib.sha256(encoded).digest())

        sig_hmac = hmac.new(base64.b64decode(self.secret),
                             message, hashlib.sha512)
        signature = base64.b64encode(sig_hmac.digest())

        # Update request kwargs
        req_kwargs['headers'] = {'API-Key': self.key,
                                 'API-Sign': signature.decode('utf-8')}
        req_kwargs['data'] = payload

        return req_kwargs


class ITbitREST(RESTAPI):
    def __init__(self, user_id =None key=None, secret=None, version=None,
                 addr=None timeout=5, config=None):
        self.userId = user_id
        version = 'v1' if not version else version
        addr = 'https://api.itbit.com' if not addr else addr

        if user_id == '':
            raise ValueError("Invalid user id - cannot be empty string! "
                             "Pass None instead!")
        self.user_id = user_id
        if (not all(x is None for x in (user_id, key, secret)) or
                not all(x is not None for x in (user_id, key, secret))):
            warnings.warn("Incomplete Credentials were given - authentication "
                          "may not work!", IncompleteCredentialsWarning)

        super(ItbitREST, self).__init__(addr=addr, version=version, key=key,
                                        secret=secret, timeout=timeout,
                                        config=config)

    def load_config(self, fname):
        conf = super(ITbitREST, self).load_config(fname)
        try:
            self.user_id = conf['AUTH']['user_id']
        except KeyError:
            warnings.warn(IncompleteCredentialsWarning,
                          "'user_id' not found in config!")

    def sign_request_kwargs(self, endpoint, **kwargs):
        req_kwargs = super(ITbitREST, self).sign_request_kwargs(endpoint,
                                                                **kwargs)

        # Prepare payload arguments
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

        # Update request kwargs header variable
        req_kwargs['headers'] = {
            'Authorization': self.key + ':' + signature.decode('utf8'),
            'X-Auth-Timestamp': timestamp,
            'X-Auth-Nonce': nonce,
            'Content-Type': 'application/json'
        }
        return req_kwargs


class OKCoinREST(RESTAPI):
    def __init__(self, key=None, secret=None, version='v1', config=None
                 addr='https://www.okcoin.com/api', timeout=5):
        super(OKCoinREST, self).__init__(url, api_version=api_version,
                                         key=key, secret=secret,
                                         timeout=timeout)

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
    def __init__(self, key=None, secret=None, api_version='3',
                 url='https://btc-e.com/api', timeout=5):
        super(BTCERest, self).__init__(url, api_version=api_version, key=key,
                                         secret=secret, timeout=timeout)

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
    def __init__(self, key=None, secret=None, api_version=None,
                 url='https://c-cex.com/t', timeout=5):
        super(CCEXRest, self).__init__(url, api_version=api_version, key=key,
                                         secret=secret, timeout=timeout)

    def sign(self, uri, endpoint, endpoint_path, method_verb, *args, **kwargs):
        nonce = self.nonce()
        try:
            params = kwargs['params']
        except KeyError:
            params = {}

        params['apikey'] = self.key
        params['nonce'] = nonce
        post_params = params
        post_params.update({'nonce': nonce, 'method': endpoint})
        post_params = urllib.parse.urlencode(post_params)

        url = uri + post_params

        sig = hmac.new(url, self.secret, hashlib.sha512)
        headers = {'apisign': sig}

        return url, {'headers': headers}


class CryptopiaREST(RESTAPI):
    def __init__(self, key=None, secret=None, api_version=None,
                 url='https://www.cryptopia.co.nz/api', timeout=5):
        super(CryptopiaREST, self).__init__(url, api_version=api_version, key=key,
                                         secret=secret, timeout=timeout)

    def sign(self, uri, endpoint, endpoint_path, method_verb, *args, **kwargs):
        nonce = self.nonce()
        try:
            params = kwargs['params']
        except KeyError:
            params = {}


        post_data = json.dumps(params)
        md5 = base64.b64encode(hashlib.md5().updated(post_data).digest())

        sig = self.key + 'POST' + urllib.parse.quote_plus(uri).lower() + nonce + md5
        hmac_sig = base64.b64encode(hmac.new(base64.b64decode(self.secret),
                                              sig, hashlib.sha256).digest())
        header_data = 'amx' + self.key + ':' + hmac_sig + ':' + nonce
        headers = {'Authorization': header_data,
                   'Content-Type': 'application/json; charset=utf-8'}

        return uri, {'headers': headers, 'data': post_data}


class GeminiREST(RESTAPI):
    def __init__(self, key=None, secret=None, api_version='v1',
                 url='https://api.gemini.com', timeout=5):
        super(GeminiREST, self).__init__(url, api_version=api_version, key=key,
                                         secret=secret, timeout=timeout)

    def sign(self, uri, endpoint, endpoint_path, method_verb, *args, **kwargs):
        nonce = self.nonce()
        try:
            params = kwargs['params']
        except KeyError:
            params = {}
        payload = params
        payload['nonce'] = nonce
        payload['request'] = endpoint_path
        payload = base64.b64encode(json.dumps(payload))
        sig = hmac.new(self.secret, payload, hashlib.sha384).hexdigest()
        headers = {'X-GEMINI-APIKEY': self.key,
                   'X-GEMINI-PAYLOAD': payload,
                   'X-GEMINI-SIGNATURE': sig}
        return uri, {'headers': headers}


class YunbiREST(RESTAPI):
    def __init__(self, key=None, secret=None, api_version='v2',
                 url='https://yunbi.com/api', timeout=5):
        super(YunbiREST, self).__init__(url, api_version=api_version, key=key,
                                         secret=secret, timeout=timeout)

    def sign(self, uri, endpoint, endpoint_path, method_verb, *args, **kwargs):
        nonce = self.nonce()
        try:
            params = kwargs['params']
        except KeyError:
            params = {}
        params['tonce'] = nonce
        params['access_key'] = self.key
        post_params = urllib.parse.urlencode(params)
        msg = '%s|%s|%s' % (method_verb, endpoint_path, post_params)

        sig = hmac.new(self.secret, msg, hashlib.sha256).hexdigest()
        uri += post_params + '&signature=' + sig

        return uri, {}


class RockTradingREST(RESTAPI):
    def __init__(self, key=None, secret=None, api_version='v1',
                 url='https://api.therocktrading.com', timeout=5):
        super(RockTradingREST, self).__init__(url, api_version=api_version,
                                              key=key, secret=secret,
                                              timeout=timeout)

    def sign(self, uri, endpoint, endpoint_path, method_verb, *args, **kwargs):
        nonce = self.nonce()
        try:
            params = kwargs['params']
        except KeyError:
            params = {}
        payload = params
        payload['nonce'] = int(nonce)
        payload['request'] = endpoint_path

        msg = nonce + uri
        sig = hmac.new(self.secret.encode(), msg.encode(), hashlib.sha384).hexdigest()
        headers = {'X-TRT-APIKEY': self.key,
                   'X-TRT-Nonce': nonce,
                   'X-TRT-SIGNATURE': sig, 'Content-Type': 'application/json'}
        return uri, {'headers': headers}


class PoloniexREST(RESTAPI):
    def __init__(self, key=None, secret=None, api_version=None,
                 url='https://poloniex.com', timeout=5):
        super(PoloniexREST, self).__init__(url, api_version=api_version,
                                           key=key, secret=secret,
                                           timeout=timeout)

    def sign(self, uri, endpoint, endpoint_path, method_verb, *args, **kwargs):
        try:
            params = kwargs['params']
        except KeyError:
            params = {}
        params['nonce'] = self.nonce()
        payload = params

        msg = urllib.parse.urlencode(payload).encode('utf-8')
        sig = hmac.new(self.secret.encode('utf-8'), msg, hashlib.sha512).hexdigest()
        headers = {'Key': self.key, 'Sign': sig}
        return uri, {'headers': headers, 'data': params}


class QuoineREST(RESTAPI):
    """
    The Quoine Api requires the API version to be designated in each requests's
    header as {'X-Quoine-API-Version': 2}
    """
    def __init__(self, key=None, secret=None, api_version=None,
                 url='https://api.quoine.com/', timeout=5):
        if not jwt:
            raise SystemError("No JWT Installed! Quoine API Unavailable!")
        super(QuoineREST, self).__init__(url, api_version=api_version,
                                         key=key, secret=secret, timeout=timeout)

    def sign(self, uri, endpoint, endpoint_path, method_verb, *args, **kwargs):
        try:
            params = kwargs['params']
        except KeyError:
            params = {}

        path = endpoint_path + urllib.parse.urlencode(params)
        msg = {'path': path, 'nonce': self.nonce(), 'token_id': self.key}

        signature = jwt.encode(msg, self.secret, algorithm='HS256')
        headers = {'X-Quoine-API-Version': '2', 'X-Quoine-Auth': signature,
                   'Content-Type': 'application/json'}
        return self.uri+path, {'headers': headers}


class QuadrigaCXREST(RESTAPI):
    def __init__(self, key=None, secret=None, client_id='', api_version='v2',
                 url='https://api.quoine.com/', timeout=5):
        self.client_id = client_id
        super(QuadrigaCXREST, self).__init__(url, api_version=api_version,
                                             key=key, secret=secret,
                                             timeout=timeout)

    def load_key(self, path):
        """
        Load key and secret from file.
        """
        with open(path, 'r') as f:
            self.key = f.readline().strip()
            self.secret = f.readline().strip()
            self.client_id = f.readline().strip()

    def sign(self, uri, endpoint, endpoint_path, method_verb, *args, **kwargs):
        try:
            params = kwargs['params']
        except KeyError:
            params = {}
        nonce = self.nonce()
        msg = nonce + self.client_id + self.key

        signature = hmac.new(self.secret.encode(encoding='utf-8'),
                             msg.encode(encoding='utf-8'), hashlib.sha256)
        headers = {'key': self.key, 'signature': signature,
                   'nonce': nonce}
        return self.uri, {'headers': headers, 'data': params}


class HitBTCREST(RESTAPI):
    def __init__(self, key=None, secret=None, api_version='1',
                 url='http://api.hitbtc.com/api/', timeout=5):
        api_version = '' if not api_version else api_version
        super(HitBTCREST, self).__init__(url, api_version=api_version,
                                         key=key, secret=secret,
                                         timeout=timeout)

    def sign(self, uri, endpoint, endpoint_path, method_verb, *args, **kwargs):
        try:
            params = kwargs['params']
        except KeyError:
            params = {}
        nonce = self.nonce()
        kwargs['nonce'] = nonce
        kwargs['apikey'] = self.key
        msg = endpoint_path + urllib.parse.urlencode(params)

        signature = hmac.new(self.secret.encode(encoding='utf-8'),
                             msg.encode(encoding='utf-8'), hashlib.sha512)
        headers = {'Api-signature': signature}
        return self.uri + msg, {'headers': headers, 'data': params}


class VaultoroREST(RESTAPI):
    def __init__(self, key=None, secret=None, api_version=None,
                 url='https://api.vaultoro.com', timeout=5):
        api_version = '' if not api_version else api_version
        super(VaultoroREST, self).__init__(url, api_version=api_version,
                                           key=key, secret=secret,
                                           timeout=timeout)

    def sign(self, uri, endpoint, endpoint_path, method_verb, *args, **kwargs):
        try:
            params = kwargs['params']
        except KeyError:
            params = {}
        nonce = self.nonce()
        kwargs['nonce'] = nonce
        kwargs['apikey'] = self.key
        msg = uri + urllib.parse.urlencode(params)

        signature = hmac.new(self.secret.encode(encoding='utf-8'),
                             msg.encode(encoding='utf-8'), hashlib.sha256).hexdigest()
        headers = {'X-Signature': signature}
        return msg, {'headers': headers}


class BterREST(RESTAPI):
    def __init__(self, key=None, secret=None, api_version=None,
                 url='http://data.bter.com/api', timeout=5):
        api_version = '1' if not api_version else api_version
        super(BterREST, self).__init__(url, api_version=api_version,
                                           key=key, secret=secret,
                                           timeout=timeout)

    def sign(self, uri, endpoint, endpoint_path, method_verb, *args, **kwargs):
        try:
            params = kwargs['params']
        except KeyError:
            params = {}
        nonce = self.nonce()
        kwargs['nonce'] = nonce

        msg = urllib.parse.urlencode(params)

        signature = hmac.new(self.secret.encode(encoding='utf-8'),
                             msg.encode(encoding='utf-8'), hashlib.sha512).hexdigest()
        headers = {'Key': signature, 'Sign': signature}
        return uri + msg, {'headers': headers}
