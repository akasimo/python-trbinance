import aiohttp
import time

from .helper import *
from .defines import *
from .base_client import BaseClient

class AsyncClient(BaseClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers = {'X-MBX-APIKEY': self.api_key}

    async def _request(self, method, endpoint, security_type, symbol_type=0, params=None):
        if symbol_type == 1:
            url = self.urls["type1"] + endpoint
        elif symbol_type == "hidden":
            url = self.urls["hidden"] + endpoint
        else:
            url = self.urls["base"] + endpoint

        if security_type.lower() in ['private', 'signed']:
            params['timestamp'] = int(time.time() * 1000)
            signature = self._generate_signature(params)
            params['signature'] = signature

        async with aiohttp.ClientSession(headers=self.headers) as session:
            if method == 'GET':
                async with session.get(url, params=params) as response:
                    return await self._handle_response(response)
            elif method == 'POST':
                async with session.post(url, data=params) as response:
                    return await self._handle_response(response)
            else:
                raise Exception('Invalid method')

    async def _handle_response(self, raw_response):
        response = await raw_response.json()
        used_weight = [x for x in list(raw_response.headers) if "X-MBX-USED-" in x.upper()]
        for x in used_weight:
            timeframe = x.split("-")[-1]
            if timeframe == "weight":
                timeframe = "total"
            self.used_weight[timeframe] = float(raw_response.headers[x])
        
        return response
    
    async def check_server_time(self):
        endpoint = '/common/time'
        response = await self._request('GET', endpoint, 'public')
        data = {"timestamp": response["timestamp"]}
        return data
    
    async def get_symbols(self):
        endpoint = '/common/symbols'
        response = await self._request('GET', endpoint, 'public')
        data = [format_symbol_data(i) for i in response['data']['list']]
        self.symbols = [d['symbol'] for d in data]
        
        data = {d["symbol"]: d for d in data}
        self.markets = data
        return data

    async def get_market_info(self, quoteAsset=None, offset=0, limit=1000):
        endpoint = '/market/trading-pairs'
        params = {
            "limit": limit,
        }

        if offset != 0:
            params["offset"] = offset
        if quoteAsset:
            params["quoteAsset"] = quoteAsset

        response = await self._request("GET", endpoint, "public", symbol_type="hidden", params=params)
        data = response["data"]["list"]
        data = [format_market_data(i) for i in data]
        data = {i["symbol"]: i for i in data}
        return data
    
    async def get_symbol_type(self, symbol):
        if self.symbols is None:
            self.get_symbols()
        symbol_type = self.markets[symbol]["symbolType"]
        assert symbol_type == 1, "Symbol type must be 1. No info what other types are."
        return symbol_type
    
    async def get_order_book(self, symbol, limit=100):
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

        data = await self._request("GET", endpoint, "public", symbol_type=symbol_type, params=params)

        for key in ['bids', 'asks']:
            data[key] = [[float(value) for value in entry] for entry in data[key]]
        return data

    async def get_recent_trades(self, symbol, from_id=None, limit=500):
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

        data = await self._request("GET", endpoint, "public", symbol_type=symbol_type, params=params)
        return data

    async def get_agg_trades(self, symbol, from_id=None, startTime=None, endTime=None, limit=500):
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

        data = await self._request("GET", endpoint, "public", symbol_type=symbol_type, params=params)
        return data
    
    async def get_klines(self, symbol, interval, startTime=None, endTime=None, limit=500):
        
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

        data = await self._request("GET", endpoint, "public", symbol_type=symbol_type, params=params)
        return data

    async def create_order(self, symbol, side, order_type, **kwargs):

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
        resp = await self._request("POST", endpoint, "private", symbol_type=symbol_type, params=params)
        if "code" in resp:
            if resp["code"] != 0:
                return resp
        data = format_order_data(resp["data"])
        data["timestamp"] = resp["timestamp"]
        return data

    async def query_order(self, orderId, **kwargs):
        params = {
            'orderId': orderId,
            'timestamp': int(time.time() * 1000),
            **kwargs
        }

        endpoint = "/orders/detail"
        resp = await self._request("GET", endpoint, "private", symbol_type=0, params=params)
        if "data" not in resp:
            return resp
        data = format_order_data(resp["data"])
        data["timestamp"] = resp["timestamp"]
        return data

    async def cancel_order(self, orderId, **kwargs):
        params = {
            'orderId': orderId,
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        endpoint = "/orders/cancel"
        resp = await self._request("POST", endpoint, "private", symbol_type=0, params=params)
        if "data" not in resp:
            return resp
        data = format_order_data(resp["data"])
        data["timestamp"] = resp["timestamp"]
        return data

    async def all_orders(self, symbol=None, **kwargs):
        params = {
            'timestamp': int(time.time() * 1000),
            **kwargs
        }

        if symbol is not None:
            origin_symbol = convert_symbol_convention_to(symbol)
            params['symbol'] = origin_symbol
        endpoint = "/orders"
        resp = await self._request("GET", endpoint, "private", symbol_type=0, params=params)
        data_list = resp["data"]["list"]
        data = [format_order_data(i) for i in data_list]
        return data

    async def new_oco(self, symbol, side, quantity, price, stopPrice, stopLimitPrice, **kwargs):
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
        resp = await self._request("POST", endpoint, "private", symbol_type=symbol_type, params=params)
        return resp["data"]

    async def account_information(self, **kwargs):
        params = {
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        endpoint = "/account/spot"
        resp = await self._request("GET", endpoint, "private", symbol_type=0, params=params)
        data = resp["data"]
        data['accountAssets'] = format_balance(data['accountAssets']) 
        return data

    async def account_balance(self):
        data = await self.account_information()
        balance_dict = data['accountAssets']
        return balance_dict
    
    async def account_asset_information(self, asset, **kwargs):
        params = {
            'asset': asset,
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        endpoint = "/account/spot/asset"
        resp = await self._request("GET", endpoint, "private", symbol_type=0, params=params)
        return resp["data"]

    async def account_trade_list(self, symbol=None, **kwargs):
        params = {
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        if symbol is not None:
            origin_symbol = convert_symbol_convention_to(symbol)
            params['symbol'] = origin_symbol
        endpoint = "/orders/trades"
        resp = await self._request("GET", endpoint, "private", symbol_type=0, params=params)
        return resp["data"]["list"]

    async def withdraw(self, asset, address, amount, **kwargs):
        params = {
            'asset': asset,
            'address': address,
            'amount': amount,
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        endpoint = "/withdraws"
        resp = await self._request("POST", endpoint, "private", symbol_type=0, params=params)
        return resp["data"]

    async def withdraw_history(self, **kwargs):
        params = {
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        endpoint = "/withdraws"
        resp = await self._request("GET", endpoint, "private", symbol_type=0, params=params)
        return resp["data"]

    async def deposit_history(self, **kwargs):
        params = {
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        endpoint = "/deposits"
        resp = await self._request("GET", endpoint, "private", symbol_type=0, params=params)
        return resp["data"]

    async def deposit_address(self, asset, network, **kwargs):
        params = {
            'asset': asset,
            'network': network,
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        endpoint = "/deposits/address"
        resp = await self._request("GET", endpoint, "private", symbol_type=0, params=params)
        return resp["data"]