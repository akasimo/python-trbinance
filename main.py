from trbinance import TrBinance

client = TrBinance()

resp = client.get_symbols()
print(resp)

resp = client.check_server_time()
print(resp)
# [{**d, 'symbol': d['symbol'].replace('_', '/')} for d in resp]