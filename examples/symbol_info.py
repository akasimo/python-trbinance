from trbinance import Client

client = Client()

resp = client.get_symbols()
print(resp)
