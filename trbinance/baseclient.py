import hmac
import hashlib

class BaseClient:
    id = 'trbinance'
    name = 'TrBinance'
    urls = {
            "base" : "https://www.trbinance.com/open/v1",
            "type1" : "https://api.binance.me/api"
        }
    
    def __init__(self, api_key="", secret_key=""):
        self.api_key = api_key
        self.secret_key = secret_key
        self.markets = None
        self.symbols = None

    def _generate_signature(self, params):
        query_string = '&'.join([f"{key}={value}" for key, value in params.items()])
        return hmac.new(self.secret_key.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()