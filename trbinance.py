import requests
import time
import hmac
import hashlib

from helper import convert_symbol_convention_from, convert_symbol_convention_to, convert_symboldata_format


class TrBinance:
    id = 'trbinance'
    def __init__(self, api_key="", secret_key=""):
        self.api_key = api_key
        self.secret_key = secret_key
        self.session = requests.Session()
        self.session.headers.update({'X-MBX-APIKEY': api_key})
        # self.base_url = 'https://api.binance.me'
        # self.open_api_url = 'https://api.binance.me/open/v1'
        self.base_url = 'https://www.trbinance.com'
        self.open_api_url = f'{self.base_url}/open/v1'
        self.markets = None
        self.symbols = None

    # def __enter__(self):
    #     return self

    # def __exit__(self, exc_type, exc_val, exc_tb):
    #     self.session.close()

    # def __del__(self):
    #     if self.session:
    #         try:
    #             self.session.close()
    #         except Exception as e:
    #             pass

    def _request(self, method, endpoint, security_type, params=None):
        url = self.open_api_url + endpoint

        if security_type.lower() in ['private', 'signed']:
            params['timestamp'] = int(time.time() * 1000)
            signature = self._generate_signature(params)
            params['signature'] = signature

        # if method == 'GET':
        #     response = self.session.get(url, params=params)
        # elif method == 'POST':
        #     response = self.session.post(url, data=params)
        with requests.Session() as session:
            if method == 'GET':
                response = session.get(url, params=params)
            elif method == 'POST':
                response = session.post(url, data=params)

        response.raise_for_status()
        
        return self._handle_response(response)

    def _generate_signature(self, params):
        query_string = '&'.join([f"{key}={value}" for key, value in params.items()])
        return hmac.new(self.secret_key.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

    def _handle_response(self, raw_response):
        response = raw_response.json()
        if response['code'] != 0:
            raise Exception(f"Error {response['code']}: {response['msg']}")
        return response

    def check_server_time(self):
        # endpoint = f'{self.open_api_url}/common/time'
        endpoint = f'/common/time'
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

    def get_order_book(self, symbol, symbol_type, limit=100):
        if symbol_type == 1:
            symbol = symbol.replace("_", "")
            response = requests.get(f'{self.base_url}/api/v3/depth', params={'symbol': symbol, 'limit': limit})
        else:
            response = requests.get(f'{self.open_api_url}/market/depth', params={'symbol': symbol, 'limit': limit})
        return response.json()

    def get_recent_trades(self, symbol, symbol_type, from_id=None, limit=500):
        params = {'symbol': symbol.replace("_", "") if symbol_type == 1 else symbol, 'limit': limit}
        if from_id:
            params['fromId'] = from_id

        if symbol_type == 1:
            response = requests.get(f'{self.base_url}/api/v3/trades', params=params)
        else:
            response = requests.get(f'{self.open_api_url}/market/trades', params=params)
        return response.json()

    def get_agg_trades(self, symbol, symbol_type, from_id=None, startTime=None, endTime=None, limit=500):
        params = {'symbol': symbol.replace("_", "") if symbol_type == 1 else symbol, 'limit': limit}
        if from_id:
            params['fromId'] = from_id
        if startTime:
            params['startTime'] = startTime
        if endTime:
            params['endTime'] = endTime

        if symbol_type == 1:
            response = requests.get(f'{self.base_url}/api/v3/aggTrades', params=params)
        else:
            response = requests.get(f'{self.open_api_url}/market/agg-trades', params=params)
        return response.json()

    def get_klines(self, symbol, symbol_type, interval, startTime=None, endTime=None, limit=500):
        params = {'symbol': symbol.replace("_", "") if symbol_type == 1 else symbol, 'interval': interval, 'limit': limit}
        if startTime:
            params['startTime'] = startTime
        if endTime:
            params['endTime'] = endTime

        if symbol_type == 1:
            response = requests.get(f'{self.base_url}/api/v1/klines', params=params)
        else:
            response = requests.get(f'{self.open_api_url}/market/klines', params=params)
        return response.json()

    def new_order(self, symbol, side, order_type, **kwargs):
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        params['signature'] = self._sign(params)
        headers = {'X-MBX-APIKEY': self.api_key}
        url = f"{self.base_url}/open/v1/orders"
        return requests.post(url, params=params, headers=headers).json()

    def query_order(self, orderId, **kwargs):
        params = {
            'orderId': orderId,
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        params['signature'] = self._sign(params)
        headers = {'X-MBX-APIKEY': self.api_key}
        url = f"{self.base_url}/open/v1/orders/detail"
        return requests.get(url, params=params, headers=headers).json()

    def cancel_order(self, orderId, **kwargs):
        params = {
            'orderId': orderId,
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        params['signature'] = self._sign(params)
        headers = {'X-MBX-APIKEY': self.api_key}
        url = f"{self.base_url}/open/v1/orders/cancel"
        return requests.post(url, params=params, headers=headers).json()

    def all_orders(self, symbol, **kwargs):
        params = {
            'symbol': symbol,
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        params['signature'] = self._sign(params)
        headers = {'X-MBX-APIKEY': self.api_key}
        url = f"{self.base_url}/open/v1/orders"
        return requests.get(url, params=params, headers=headers).json()

    def new_oco(self, symbol, side, quantity, price, stopPrice, stopLimitPrice, **kwargs):
        params = {
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': price,
            'stopPrice': stopPrice,
            'stopLimitPrice': stopLimitPrice,
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        params['signature'] = self._sign(params)
        headers = {'X-MBX-APIKEY': self.api_key}
        url = f"{self.base_url}/open/v1/orders/oco"
        return requests.post(url, params=params, headers=headers).json()

    def account_information(self, **kwargs):
        params = {
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        params['signature'] = self._sign(params)
        headers = {'X-MBX-APIKEY': self.api_key}
        url = f"{self.base_url}/open/v1/account/spot"
        return requests.get(url, params=params, headers=headers).json()

    def account_asset_information(self, asset, **kwargs):
        params = {
            'asset': asset,
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        params['signature'] = self._sign(params)
        headers = {'X-MBX-APIKEY': self.api_key}
        url = f"{self.base_url}/open/v1/account/spot/asset"
        return requests.get(url, params=params, headers=headers).json()

    def account_trade_list(self, symbol, **kwargs):
        params = {
            'symbol': symbol,
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        params['signature'] = self._sign(params)
        headers = {'X-MBX-APIKEY': self.api_key}
        url = f"{self.base_url}/open/v1/orders/trades"
        return requests.get(url, params=params, headers=headers).json()

    def withdraw(self, asset, address, amount, **kwargs):
        params = {
            'asset': asset,
            'address': address,
            'amount': amount,
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        params['signature'] = self._sign(params)
        headers = {'X-MBX-APIKEY': self.api_key}
        url = f"{self.base_url}/open/v1/withdraws"
        return requests.post(url, params=params, headers=headers).json()

    def withdraw_history(self, **kwargs):
        params = {
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        params['signature'] = self._sign(params)
        headers = {'X-MBX-APIKEY': self.api_key}
        url = f"{self.base_url}/open/v1/withdraws"
        return requests.get(url, params=params, headers=headers).json()

    def deposit_history(self, **kwargs):
        params = {
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        params['signature'] = self._sign(params)
        headers = {'X-MBX-APIKEY': self.api_key}
        url = f"{self.base_url}/open/v1/deposits"
        return requests.get(url, params=params, headers=headers).json()

    def deposit_address(self, asset, network, **kwargs):
        params = {
            'asset': asset,
            'network': network,
            'timestamp': int(time.time() * 1000),
            **kwargs
        }
        params['signature'] = self._sign(params)
        headers = {'X-MBX-APIKEY': self.api_key}
        url = f"{self.base_url}/open/v1/deposits/address"
        return requests.get(url, params=params, headers=headers).json()
