from trbinance import Client

client = Client()

resp = client.get_order_book("BTC/TRY")
print(resp)