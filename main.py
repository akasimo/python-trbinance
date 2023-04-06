from trbinance import TrBinance
import os
import json
# import env variables from dotenv file
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("API_KEY","")
secret_key = os.getenv("SECRET_KEY","")

client = TrBinance(api_key, secret_key)

# resp = client.get_symbols()
# print(resp)

# resp = client.get_order_book("BTC/TRY", limit=5)
# resp = client.get_agg_trades("BTC/TRY")
# resp = client.get_klines("BTC/TRY", "12m", limit=100)


symbol = "BTC/TRY"
side = "BUY"
order_type = "LIMIT_MAKER"
quantity = "0.001"
price = "100000"

resp = client.create_order(symbol, side, order_type, quantity=quantity, price=price)

print(resp)

