import requests
import time

from .helper import *
from .defines import *
from .base_client import BaseClient

class Client(BaseClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _request(self, method, endpoint, security_type, symbol_type=0, params=None):
        if symbol_type == 1:
            url = self.urls["type1"] + endpoint
        elif symbol_type == "hidden":
            url = self.urls["hidden"] + endpoint
        else:
            url = self.urls["base"] + endpoint

        with requests.Session() as session:
            if security_type.lower() in ['private', 'signed']:
                params['timestamp'] = int(time.time() * 1000)
                signature = self._generate_signature(params)
                params['signature'] = signature
                session.headers.update({'X-MBX-APIKEY': self.api_key})
                
            if method == 'GET':
                response = session.get(url, params=params)
            elif method == 'POST':
                response = session.post(url, data=params)
            else:
                raise Exception('Invalid method')

        response.raise_for_status()
        return self._handle_response(response)

    def _handle_response(self, raw_response, **kwargs):
        response = raw_response.json()
        used_weight = [x for x in list(raw_response.headers) if "X-MBX-USED-" in x.upper()]
        for x in used_weight:
            timeframe = x.split("-")[-1]
            if timeframe == "weight":
                timeframe = "total"
            self.used_weight[timeframe] = float(raw_response.headers[x])

        return response
    
    def check_server_time(self):
        endpoint = '/common/time'
        response = self._request('GET', endpoint, 'public')
        data = {"timestamp": response["timestamp"]}
        return data
            
    def get_symbols(self):
        endpoint = '/common/symbols'
        response = self._request('GET', endpoint, 'public')
        data = [format_symbol_data(i) for i in response['data']['list']]
        self.symbols = [d['symbol'] for d in data]
        
        data = {d["symbol"]: d for d in data}
        self.markets = data
        return data
    
    def get_market_info(self, quoteAsset=None, offset=0, limit=1000):
        endpoint = '/market/trading-pairs'
        params = {
            "limit": limit,
        }
        if offset != 0:
            params["offset"] = offset
        if quoteAsset:
            params["quoteAsset"] = quoteAsset

        response = self._request("GET", endpoint, "public", symbol_type="hidden", params=params)
        data = response["data"]["list"]
        
        data = [format_market_data(i) for i in data]
        data = {i["symbol"]: i for i in data}
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
        # {
        #     'orderId': '5467573389', 
        #     'bOrderListId': 0, 
        #     'clientId': 'e8d4abfa4e0774c039aec7717b5f1b4b9', 
        #     'bOrderId': 207765154128, 
        #     'symbol': 'BTC_USDT', 
        #     'symbolType': 1, 
        #     'side': 0, 
        #     'type': 1, 
        #     'price': '10000', 
        #     'origQty': '0.001', 
        #     'origQuoteQty': '10.00000000', 
        #     'executedQty': '0.00000000', 
        #     'executedPrice': '0', 
        #     'executedQuoteQty': '0.00000000', 
        #     'timeInForce': 1, 
        #     'stopPrice': 0, 
        #     'icebergQty': '0', 
        #     'status': 0, 
        #     'createTime': 1681279199188
        # }

        origin_symbol = convert_symbol_convention_to(symbol)
        order_type_num = OrderType[order_type.upper()].value
        
        assert order_type_num in [1,2,4,6], "order_type must be either 'LIMIT','MARKET','STOP_LOSS_LIMIT' or 'TAKE_PROFIT_LIMIT' "

        params = {
            'symbol': origin_symbol,
            'side': Side[side.upper()].value,
            'type': order_type_num,
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        
        endpoint = "/orders"
        symbol_type = 0
        resp = self._request("POST", endpoint, "private", symbol_type=symbol_type, params=params)
        if "code" in resp:
            if resp["code"] != 0:
                return resp
        data = format_order_data(resp["data"])
        data["timestamp"] = resp["timestamp"]
        return data

    def query_order(self, orderId, **kwargs):
        # {
        #     'orderId': '5467572389', 
        #     'clientId': 'e8d4abfa4e0774c039aec7717b5f1b4b9', 
        #     'bOrderId': '207765135418', 
        #     'bOrderListId': '0', 
        #     'symbol': 'BTC_USDT', 
        #     'symbolType': 1, 
        #     'side': 0, 
        #     'type': 1, 
        #     'price': '10000', 
        #     'origQty': '0.001', 
        #     'origQuoteQty': '10', 
        #     'executedQty': '0', 
        #     'executedPrice': '0', 
        #     'executedQuoteQty': '0', 
        #     'timeInForce': 1, 
        #     'stopPrice': '0', 
        #     'icebergQty': '0', 
        #     'status': 0, 
        #     'createTime': 1681279392188
        #     }

        params = {
            'orderId': orderId,
            'timestamp': int(time.time() * 1000),
            **kwargs
        }

        endpoint = "/orders/detail"
        resp = self._request("GET", endpoint, "private", symbol_type=0, params=params)
        if "data" not in resp:
            return resp
        data = format_order_data(resp["data"])
        data["timestamp"] = resp["timestamp"]
        return data

    def cancel_order(self, orderId, **kwargs):
        # {
        #     'orderId': '5467571389', 
        #     'bOrderListId': '0', 
        #     'clientId': 'e8d4abf4ae0774c039aec7717b5f1b4b9', 
        #     'bOrderId': '207736515418', 
        #     'symbol': 'BTC_USDT', 
        #     'symbolType': 1, 
        #     'type': 1, 
        #     'side': 0, 
        #     'price': '10000.0000000000000000', 
        #     'origQty': '0.0010000000000000', 
        #     'origQuoteQty': '10.0000000000000000', 
        #     'executedPrice': '0.0000000000000000', 
        #     'executedQty': '0.00000000', 
        #     'executedQuoteQty': '0.00000000', 
        #     'timeInForce': 1, 
        #     'stopPrice': '0.0000000000000000', 
        #     'icebergQty': '0.0000000000000000', 
        #     'status': 3
        # }
        params = {
            'orderId': orderId,
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        endpoint = "/orders/cancel"
        resp = self._request("POST", endpoint, "private", symbol_type=0, params=params)
        if "data" not in resp:
            return resp
        data = format_order_data(resp["data"])
        data["timestamp"] = resp["timestamp"]
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
        resp = self._request("GET", endpoint, "private", symbol_type=0, params=params)
        data_list = resp["data"]["list"]
        data = [format_order_data(i) for i in data_list]
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
        resp = self._request("POST", endpoint, "private", symbol_type=symbol_type, params=params)
        return resp["data"]

    def account_information(self, **kwargs):
        params = {
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        endpoint = "/account/spot"
        resp = self._request("GET", endpoint, "private", symbol_type=0, params=params)
        data = resp["data"]
        data['accountAssets'] = format_balance(data['accountAssets']) 
        return data

    def account_balance(self):
        data = self.account_information()
        balance_dict = data['accountAssets']
        return balance_dict
    
    def account_asset_information(self, asset, **kwargs):
        params = {
            'asset': asset,
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        endpoint = "/account/spot/asset"
        resp = self._request("GET", endpoint, "private", symbol_type=0, params=params)
        return resp["data"]

    def account_trade_list(self, symbol=None, **kwargs):
        params = {
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        if symbol is not None:
            origin_symbol = convert_symbol_convention_to(symbol)
            params['symbol'] = origin_symbol
        endpoint = "/orders/trades"
        resp = self._request("GET", endpoint, "private", symbol_type=0, params=params)
        return resp["data"]["list"]
    
    def withdraw(self, asset, address, amount, **kwargs):
        params = {
            'asset': asset,
            'address': address,
            'amount': amount,
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        endpoint = "/withdraws"
        resp = self._request("POST", endpoint, "private", symbol_type=0, params=params)
        return resp["data"]

    def withdraw_history(self, **kwargs):
        params = {
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        endpoint = "/withdraws"
        resp = self._request("GET", endpoint, "private", symbol_type=0, params=params)
        return resp["data"]

    def deposit_history(self, **kwargs):
        params = {
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        endpoint = "/deposits"
        resp = self._request("GET", endpoint, "private", symbol_type=0, params=params)
        return resp["data"]

    def deposit_address(self, asset, network, **kwargs):
        params = {
            'asset': asset,
            'network': network,
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        endpoint = "/deposits/address"
        resp = self._request("GET", endpoint, "private", symbol_type=0, params=params)
        return resp["data"]
