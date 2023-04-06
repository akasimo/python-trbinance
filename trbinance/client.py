import requests
import time
import hmac
import hashlib

from helper import convert_symbol_convention_from, convert_symbol_convention_to, convert_symboldata_format

from defines import *

class Client:
    id = 'trbinance'
    name = 'TrBinance'

    def __init__(self, api_key="", secret_key=""):
        self.api_key = api_key
        self.secret_key = secret_key
        self.session = requests.Session()
        self.session.headers.update({'X-MBX-APIKEY': api_key})
        self.urls = {
            "base" : "https://www.trbinance.com/open/v1",
            "type1" : "https://api.binance.me/api"
        }

        self.markets = None
        self.symbols = None

    def _request(self, method, endpoint, security_type, symbol_type=0, params=None):
        if symbol_type == 1:
            url = self.urls["type1"] + endpoint
        else:
            url = self.urls["base"] + endpoint

        if security_type.lower() in ['private', 'signed']:
            params['timestamp'] = int(time.time() * 1000)
            signature = self._generate_signature(params)
            params['signature'] = signature

        with requests.Session() as session:
            if method == 'GET':
                response = session.get(url, params=params)
            elif method == 'POST':
                response = session.post(url, data=params)
            else:
                raise Exception('Invalid method')

        response.raise_for_status()
        
        return self._handle_response(response)

    def _generate_signature(self, params):
        query_string = '&'.join([f"{key}={value}" for key, value in params.items()])
        return hmac.new(self.secret_key.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

    def _handle_response(self, raw_response):
        response = raw_response.json()
        if "code" in response:
            if response['code'] != 0:
                raise Exception(f"Error {response['code']}: {response['msg']}")
        return response

    def check_server_time(self):
        endpoint = '/common/time'
        response = self._request('GET', endpoint, 'public')
        data = {"timestamp": response["timestamp"]}
        return data
            
    def get_symbols(self):
        endpoint = '/common/symbols'
        response = self._request('GET', endpoint, 'public')
        data = [convert_symboldata_format(i) for i in response['data']['list']]
        self.symbols = [d['symbol'] for d in data]
        
        data = {d["symbol"]: d for d in data}
        self.markets = data
        return data

    def get_symbol_type(self, symbol):
        if self.symbols is None:
            self.get_symbols()
        symbol_type = self.markets[symbol]["symbolType"]
        assert symbol_type == 1, "Symbol type must be 1. No info what other types are."
        return symbol_type
    
    def get_order_book(self, symbol, limit=100):
        """ Gets order book for a symbol

        Args:
            symbol (_type_): when symbol type is 1, replace _ of symbol with null string
            limit (int, optional): Default 100; max 5000. Valid limits:[5, 10, 20, 50, 100, 500]

        Returns:
            dict: lists of "bids" and "asks" in the order book
        """
        symbol_type = self.get_symbol_type(symbol)
        origin_symbol = convert_symbol_convention_to(symbol)

        if symbol_type == 1:
            endpoint = '/v3/depth'
            origin_symbol = origin_symbol.replace("_", "")
        else:
            endpoint = '/market/depth'
        params = {'symbol': origin_symbol, 'limit': limit}

        data = self._request("GET", endpoint, "public", symbol_type=symbol_type, params=params)

        for key in ['bids', 'asks']:
            data[key] = [[float(value) for value in entry] for entry in data[key]]
        return data

    def get_recent_trades(self, symbol, from_id=None, limit=500):
        symbol_type = self.get_symbol_type(symbol)
        origin_symbol = convert_symbol_convention_to(symbol)

        if symbol_type == 1:
            endpoint = '/v3/trades'
            origin_symbol = origin_symbol.replace("_", "")
        else:
            endpoint = '/market/trades'

        params = {'symbol': origin_symbol, 'limit': limit}
        if from_id:
            params['fromId'] = from_id

        data = self._request("GET", endpoint, "public", symbol_type=symbol_type, params=params)
        return data

    def get_agg_trades(self, symbol, from_id=None, startTime=None, endTime=None, limit=500):
        symbol_type = self.get_symbol_type(symbol)
        origin_symbol = convert_symbol_convention_to(symbol)

        if symbol_type == 1:
            endpoint = '/v3/aggTrades'
            origin_symbol = origin_symbol.replace("_", "")
        else:
            endpoint = '/market/agg-trades'

        params = {'symbol': origin_symbol, 'limit': limit}
        if from_id:
            params['fromId'] = from_id
        if startTime:
            params['startTime'] = startTime
        if endTime:
            params['endTime'] = endTime

        data = self._request("GET", endpoint, "public", symbol_type=symbol_type, params=params)
        return data
    
    def get_klines(self, symbol, interval, startTime=None, endTime=None, limit=500):
        
        assert interval in KLINE_INTERVALS, "Invalid interval. Valid intervals: " + ", ".join(KLINE_INTERVALS) + "."

        symbol_type = self.get_symbol_type(symbol)
        origin_symbol = convert_symbol_convention_to(symbol)

        if symbol_type == 1:
            endpoint = '/v1/klines'
            origin_symbol = origin_symbol.replace("_", "")
        else:
            endpoint = '/market/klines'
        
        params = {'symbol': origin_symbol, 'limit': limit, 'interval': interval}
        if startTime:
            params['startTime'] = startTime
        if endTime:
            params['endTime'] = endTime

        data = self._request("GET", endpoint, "public", symbol_type=symbol_type, params=params)
        return data

    def create_order(self, symbol, side, order_type, **kwargs):
        origin_symbol = convert_symbol_convention_to(symbol)

        # assert side.lower() in ['buy','sell'], "side must be either 'buy' or 'sell'"
        # assert order_type in ['limit', 'market'], "order_type must be either 'limit' or 'market'"

        order_type_num = OrderType[order_type.upper()].value
        if kwargs.get('postOnly', False):
            order_type_num = OrderType["LIMIT_MAKER"].value

        params = {
            'symbol': origin_symbol,
            'side': Side[side.upper()].value,
            'type': order_type_num,
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        
        endpoint = "/orders"
        symbol_type = 0
        data = self._request("POST", endpoint, "private", symbol_type=symbol_type, params=params)
        return data

    def query_order(self, orderId, **kwargs):
        params = {
            'orderId': orderId,
            'timestamp': int(time.time() * 1000),
            **kwargs
        }

        endpoint = "/orders/detail"
        data = self._request("GET", endpoint, "private", symbol_type=0, params=params)
        return data

    def cancel_order(self, orderId, **kwargs):
        params = {
            'orderId': orderId,
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        endpoint = "/orders/cancel"
        data = self._request("POST", endpoint, "private", symbol_type=0, params=params)
        return data

    def all_orders(self, symbol=None, **kwargs):
        params = {
            'timestamp': int(time.time() * 1000),
            **kwargs
        }

        if symbol is not None:
            origin_symbol = convert_symbol_convention_to(symbol)
            params['symbol'] = origin_symbol
        endpoint = "/orders"
        data = self._request("GET", endpoint, "private", symbol_type=0, params=params)
        return data

    def new_oco(self, symbol, side, quantity, price, stopPrice, stopLimitPrice, **kwargs):
        params = {
            'symbol': convert_symbol_convention_to(symbol),
            'side': Side[side.upper()].value,
            'quantity': quantity,
            'price': price,
            'stopPrice': stopPrice,
            'stopLimitPrice': stopLimitPrice,
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        endpoint = "/orders/oco"
        symbol_type = 0
        data = self._request("POST", endpoint, "private", symbol_type=symbol_type, params=params)
        return data

    def account_information(self, **kwargs):
        params = {
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        endpoint = "/account/spot"
        data = self._request("GET", endpoint, "private", symbol_type=0, params=params)
        return data

    def account_asset_information(self, asset, **kwargs):
        params = {
            'asset': asset,
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        endpoint = "/account/spot/asset"
        data = self._request("GET", endpoint, "private", symbol_type=0, params=params)
        return data

    def account_trade_list(self, symbol, **kwargs):
        params = {
            'symbol': convert_symbol_convention_to(symbol),
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        endpoint = "/orders/trades"
        data = self._request("GET", endpoint, "private", symbol_type=0, params=params)
        return data

    def withdraw(self, asset, address, amount, **kwargs):
        params = {
            'asset': asset,
            'address': address,
            'amount': amount,
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        endpoint = "/withdraws"
        data = self._request("POST", endpoint, "private", symbol_type=0, params=params)
        return data

    def withdraw_history(self, **kwargs):
        params = {
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        endpoint = "/withdraws"
        data = self._request("GET", endpoint, "private", symbol_type=0, params=params)
        return data

    def deposit_history(self, **kwargs):
        params = {
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        endpoint = "/deposits"
        data = self._request("GET", endpoint, "private", symbol_type=0, params=params)
        return data


    def deposit_address(self, asset, network, **kwargs):
        params = {
            'asset': asset,
            'network': network,
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        endpoint = "/deposits/address"
        data = self._request("GET", endpoint, "private", symbol_type=0, params=params)
        return data