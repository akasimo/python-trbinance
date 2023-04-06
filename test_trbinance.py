import os
import json
import unittest
from unittest.mock import MagicMock
import trbinance

class TestTrbinancePublicEndpoints(unittest.TestCase):

    def setUp(self):
        self.api_key = 'YOUR_API_KEY'
        self.secret_key = 'YOUR_SECRET_KEY'
        # self.base_url = 'https://test.trbinance.com'  # Use test environment URL
        self.trbinance = trbinance.TrBinance(self.api_key, self.secret_key)

    @staticmethod
    def _load_test_data(filename):
        with open(os.path.join('test_responses', filename), 'r') as f:
            return json.load(f)

    # def test_get_ticker_price(self):
    #     self.trbinance._public_get = MagicMock(return_value={'symbol': 'BTCUSDT', 'price': '20000'})
    #     result = self.trbinance.get_ticker_price('BTCUSDT')
    #     self.assertEqual(result['symbol'], 'BTCUSDT')
    #     self.assertEqual(result['price'], '20000')

    def test_check_server_time(self):
        test_data = self._load_test_data('check_server_time.json')
        self.trbinance._request = MagicMock(return_value=test_data)
        result = self.trbinance.check_server_time()
        self.assertEqual(result["timestamp"], 1625836016000)

    def test_get_symbols(self):
        # test_data = self._load_test_data('get_symbols.json')
        # self.trbinance._request = MagicMock(return_value=test_data)
        result = self.trbinance.get_symbols()
        self.assertEqual(result["BTC/TRY"]['symbol'], 'BTC/TRY')
        self.assertEqual(result["BTC/TRY"]['base'], 'BTC')
        self.assertEqual(result["BTC/TRY"]['quote'], 'TRY')
        self.assertEqual(result["BTC/TRY"]['precision']['amount'], 5)
        self.assertEqual(result["BTC/TRY"]['precision']['price'], 0)
        self.assertEqual(result["BTC/TRY"]['limits']['amount']['max'], 9000)






    # def test_get_exchange_info(self):
    #     self.trbinance._public_get = MagicMock(return_value={'timezone': 'UTC', 'serverTime': 1625836016000})
    #     result = self.trbinance.get_exchange_info()
    #     self.assertEqual(result['timezone'], 'UTC')
    #     self.assertEqual(result['serverTime'], 1625836016000)

if __name__ == '__main__':
    unittest.main()
