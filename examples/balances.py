import os
from dotenv import load_dotenv

from trbinance import Client

load_dotenv()

api_key = os.getenv("API_KEY","")
secret_key = os.getenv("SECRET_KEY","")

client = Client(api_key, secret_key)

balances = client.account_balance()
print(balances["free"])
print(balances["total"])
print(client.used_weight)