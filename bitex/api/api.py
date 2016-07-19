"""
Task:
Do fancy shit.
"""

# Import Built-Ins
import logging
import requests
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
        print("URI is: ", uri)

    def load_key(self, path):
        """
        Load key and secret from file.
        """
        with open(path, 'r') as f:
            self.key = f.readline().strip()
            self.secret = f.readline().strip()

    def sign(self, *args, **kwargs):
        """
        Dummy Signature creation method. Override this in child.
        Returned dict must have keywords usable by requests.get or requests.post
        URL is required to be returned, as some Signatures use the url for
        sig generation, and api calls made must match the address exactly.
        """

        return url, kwargs

    def query(self, endpoint, authenticate=False, request_method=requests.get,
              *args, **kwargs):
        """
        Queries exchange using given data. Defaults to unauthenticated GET query.
        """
        if self.apiversion:
            urlpath = '/' + self.apiversion + '/' + endpoint
        else:
            urlpath = '/' + endpoint

        print(endpoint, authenticate, request_method, args, kwargs)

        if authenticate:  # Pass all locally vars to sign(); Sorting left to children
            kwargs['urlpath'] = urlpath
            url, kwargs = self.sign(endpoint, *args, **kwargs)
        else:
            url = self.uri + urlpath

        print(url)
        r = request_method(url, timeout=5, **kwargs)

        return r








