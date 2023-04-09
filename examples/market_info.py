from trbinance import Client

client = Client()

resp = client.get_market_info()
print(resp)
