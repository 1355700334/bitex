# BitEx
BitEx is a collection of API Clients for Crypto Currency Exchanges.

It provides primarily REST-based clients for a variety of Crypto exchanges. It handles authentication and requests to common endpoints via convenience methods, 
as well as granting access to all other endpoint via the low level api interface.


# Before you download this

..be aware that it's still in pre-alpha-half-baked-work-in-progress-stage - many features and implementations may change rapidly and in ways you may not desire. Once I get to a point that I'm comfortable with, I will release a version on pypy, which will then serve as basis for further releases. So until then, nothing's final!

For an up-to-date version (which is likely to have some very rough edges and terrible bugs and errors), check out the dev branch.


# State
--------------------------------

**API** : **Completed**

**Clients** : **WIP**

--------------------------------
As of now, only REST APIs are supported, implementations of websockets and FIX connections are being considered.

The following exchanges are supported

REST-based APIs:
- GDAX (backend done)
- Bitfinex (backend done)
- Bitstamp (backend done)
- Kraken (backend done)
- Coincheck (backend done)
- OKCoin (backend done)
- BTC-E (in progress)
- Bittrex (backend done)


-`planned`: I'm currently designing base code for this exchange

-`backend done`: You're able to communicate with the API using its respective API class

-`overlay funcs done`: I've added convenience methods which allow communication with the API, but not all arguments are integrated into the arguments list, and documenation may be missing.

-`fully implemented`: All API endpoints have a overlay method, which features all minimally required arguments, as well as additional kwargs.

Additional clients will be added to (or removed from) this list, according to their liquidity and market volume.

In their basic form, clients provide a simple connection to APIs - that is, they handle authentication and request construction for you. As soon the above list is completed to a point where most of the exchanges are implemented (or whenever I feel like it), I will add convenience layers to the clients; this layer will aim to make calling the api feel more like a function, instead of string construction (i.e. `kraken.ticker('XBTEUR')`, instead of typing `kraken.public_query({'pair': 'XBTEUR'})`). 

# REST APIs

The above listed exchanges all have an implemented API class in `bitex.api`. These provide low-level access to the
respective exchange's REST API, including handling of authentication. They do not feature convenience methods, so you will
have to write some things yourself. 

At their core, they can be thought of as simple overlay methods for `requests.request()` methods, as all
kwargs passed to query, are also passed to these methods as well. 

An example:
```
from bitex.api.rest import KrakenREST, BitstampREST

k = KrakenREST()
k.load_key('kraken.key')

k.query('public/Depth', params={'pair': 'XXBTZUSD'})
k.query('GET', 'private/AddOrder', authenticate=True,
            params={'pair': 'XXBTZUSD', 'type': 'sell', 'ordertype': 'limit',
                    'price': 1000.0, 'volume': 0.01, 'validate': True})
```

# REST Clients for usage within your code

These clients have a unified interface, hence some functionality does not have a method in the Overlay clients 
(i.e. all clients in the `bitex.http` module) - you can still access these endpoint by making use of the 
low-lvl API interface in `bitex.api`. 

The base methods for all clients are defined as follows:

Public Endpoints:
- Client.ticker()
- Client.order_book()
- Client.trades()

Private Endpoints:
- Client.balance()
- Client.orders()
- Client.ledger()
- Client.add_order()
- Client.cancel_order()
- Client.fees()

Keep in mind that, in order to provide correct and unified data across all platforms, some of these methods may use more than one
API call to the exchange to acquire all necessary data. This is usually documented in the method's docstring. 


For further documentation, consult the source code.


# Installation
`python3 setup.py install`


# Usage
Import any client from the `http` submodule.
```
from bitex.http import KrakenHTTP
uix = KrakenHTTP()
uix.order_book('XBTEUR')
```

If you'd like to query a private endpoint, you'll have to either supply your secret & api keys like this:
```
uix = KrakenHTTP(key='your-api-key-here', secret='your-api-secret-here')
```

Or, which I'd recommend for safety and convenience reasons, pass a keyfile containing your api and secret on a seperate line each (Note: some clients require additional args to authenticate! These should come before the api and secret in the file!):
```
>my_api.key
513423534dljr1234  # Api key
knjer23053n90d02d3nd90d23d23d==  # Api Secret

>main.py
from bitex.http import KrakenHTTP
uix = KrakenHTTP(key_file='./my_api.key')
```






