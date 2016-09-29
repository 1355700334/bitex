"""
Task:
Descripion of script here.
"""

# Import Built-Ins
import logging

# Import Third-Party

# Import Homebrew
from bitex.api.rest import BittrexREST
from bitex.utils import return_json

# Init Logging Facilities
#logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class Bittrex(BittrexREST):
    def __init__(self, key='', secret='', key_file=''):
        super(Bittrex, self).__init__(key, secret)
        if key_file:
            self.load_key(key_file)

    def public_query(self, endpoint, **kwargs):
        return self.query('GET', 'public/' + endpoint, **kwargs)

    def private_query(self, endpoint, **kwargs):
        return self.query('POST', endpoint, authenticate=True, **kwargs)

    def pairs(self):
        return self.public_query('getmarkets')

    def currencies(self):
        return self.public_query('getcurrencies')

    def ticker(self, pair):
        return self.public_query('getticker', params={'market': pair})

    def statistics(self, pair=None):
        if pair:
            return self.public_query('getmarketsummary', params={'market': pair})
        else:
            return self.public_query('getmarketsummaries')

    def order_book(self, pair, side='both', **kwargs):
        q = {'market': pair, 'type': side}
        q.update(kwargs)
        return self.public_query('getorderbook', params=q)

    def trades(self, pair, **kwargs):
        q = {'market': pair}
        q.update(kwargs)
        return self.public_query('getmarkethistory', params=q)

