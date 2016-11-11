"""
https://yunbi.com/documents/api/guide
"""

# Import Built-Ins
import logging

# Import Third-Party

# Import Homebrew
from bitex.api.rest import YunbiREST
from bitex.utils import return_json

# Init Logging Facilities
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class Yunbi(YunbiREST):
    def __init__(self, key='', secret='', key_file=''):
        super(Yunbi, self).__init__(key, secret)
        if key_file:
            self.load_key(key_file)
        print(self.uri)

    def public_query(self, endpoint, **kwargs):
        return self.query('GET', endpoint + '.json', **kwargs)

    def private_query(self, endpoint, **kwargs):
        return self.query('POST', endpoint, authenticate=True, **kwargs)

    @return_json(None)
    def pairs(self):
        return self.public_query('symbols')

    @return_json(None)
    def ticker(self, pair=None):
        if pair:
            return self.public_query('tickers/%s' % pair)
        else:
            return self.public_query('tickers')

    @return_json(None)
    def ohlc(self, pair, **kwargs):
        q = {'market': pair}
        q.update(kwargs)
        return self.public_query('k', params=q)

    @return_json(None)
    def order_book(self, pair, **kwargs):
        q = {'market': pair}
        q.update(kwargs)
        return self.public_query('order_book', params=q)

    @return_json(None)
    def trades(self, pair, **kwargs):
        q = {'market': pair}
        q.update(kwargs)
        return self.public_query('trades', params=q)

    @return_json(None)
    def auction(self, pair):
        return self.public_query('auction/%s' % pair)

    @return_json(None)
    def auction_history(self, pair, **kwargs):
        return self.public_query('auction/%s/history' % pair, params=kwargs)



