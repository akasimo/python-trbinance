import os
from dotenv import load_dotenv

from trbinance import Client

load_dotenv()

api_key = os.getenv("API_KEY","")
secret_key = os.getenv("SECRET_KEY","")

client = Client(api_key, secret_key)

resp = client.account_trade_list("USDT/TRY")
print(resp)
