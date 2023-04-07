import os
from dotenv import load_dotenv

from trbinance import Client

load_dotenv()

api_key = os.getenv("API_KEY","")
secret_key = os.getenv("SECRET_KEY","")

client = Client(api_key, secret_key)

symbol = "BTC/USDT"
side = "BUY"
order_type = "LIMIT"
quantity = "0.001"
price = "10000"

resp = client.create_order(symbol, side, order_type, quantity=quantity, price=price)
print("Create order:", resp)

order_id = resp["orderId"]
resp = client.query_order(order_id)
print("Query order:", resp)

resp = client.cancel_order(order_id)
print("Cancel order:", resp)