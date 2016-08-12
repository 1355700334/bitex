"""
Task:
Do fancy shit.
"""

# Import Built-Ins
import logging
import requests
import time
# Import Third-Party

# Import Homebrew


log = logging.getLogger(__name__)


class RESTAPI:

    def __init__(self, uri, api_version='', key='', secret=''):
        """
        Base Class for REST API connections.
        """
        self.key = key
        self.secret = secret
        self.uri = uri
        self.apiversion = api_version
        self.req_methods = {'POST': requests.post, 'PUT': requests.put,
                            'GET': requests.get, 'DELETE': requests.delete,
                            'PATCH': requests.patch}
        print("URI is: ", uri)

    def load_key(self, path):
        """
        Load key and secret from file.
        """
        with open(path, 'r') as f:
            self.key = f.readline().strip()
            self.secret = f.readline().strip()

    def nonce(self):
        return str(int(1000 * time.time()))

    def sign(self, url=None, *args, **kwargs):
        """
        Dummy Signature creation method. Override this in child.
        Returned dict must have keywords usable by requests.get or requests.post
        URL is required to be returned, as some Signatures use the url for
        sig generation, and api calls made must match the address exactly.
        """
        url = self.uri

        return url, {'params': {'test_param': "authenticated_chimichanga"}}

    def query(self, method, endpoint, authenticate=False,
              *args, **kwargs):
        """
        Queries exchange using given data. Defaults to unauthenticated GET query.
        """
        request_method = self.req_methods[method]

        if self.apiversion:
            urlpath = '/' + self.apiversion + '/' + endpoint
        else:
            urlpath = '/' + endpoint

        print(endpoint, authenticate, request_method, args, kwargs)

        if authenticate:  # Pass all locally vars to sign(); Sorting left to children
            kwargs['urlpath'] = urlpath
            kwargs['request_method'] = request_method
            url, request_kwargs = self.sign(endpoint, *args, **kwargs)
        else:
            url = self.uri + urlpath
            request_kwargs = kwargs

        print(url)
        r = request_method(url, timeout=5, **request_kwargs)

        return r

    def auth_query(self, endpoint):
        pass

    def public_query(self):
        pass






