import math

def format_symbol_data(input_data):
    filters = {item['filterType']: item for item in input_data["filters"]}
    output_data = {
        'id': input_data['symbol'].replace('_', ''),
        'symbol': convert_symbol_convention_from(input_data['symbol']),
        'symbolType' : input_data['type'],
        'base': input_data['baseAsset'],
        'quote': input_data['quoteAsset'],
        'baseId': input_data['baseAsset'],
        'quoteId': input_data['quoteAsset'],
        'active': True,
        'type': 'spot',
        'linear': None,
        'inverse': None,
        'spot': True,
        'swap': False,
        'future': True,
        'option': False,
        'margin': True,
        'contract': False,
        'contractSize': None,
        'expiry': None,
        'expiryDatetime': None,
        'optionType': None,
        'strike': None,
        'settle': None,
        'settleId': None,
        'precision': {
            'amount': -round(math.log(float(filters["LOT_SIZE"]["stepSize"])) / math.log(10)),
            'price': -round(math.log(float(filters["PRICE_FILTER"]["tickSize"])) / math.log(10)),
            "priceTick": float(filters["PRICE_FILTER"]["tickSize"]),
            "amountTick": float(filters["LOT_SIZE"]["stepSize"]),
            'base': float(input_data['basePrecision']),
            'quote': float(input_data['quotePrecision'])
        },
        'limits': {
            'amount': {
                'min': float(filters["LOT_SIZE"]['minQty']),
                'max': float(filters["LOT_SIZE"]['maxQty'])
            },
            'price': {
                'min': float(filters["PRICE_FILTER"]['minPrice']),
                'max': float(filters["PRICE_FILTER"]['maxPrice'])
            },
            'cost': {
                'min': float(filters["MIN_NOTIONAL"]['minNotional']),
                'max': None
            },
            'leverage': {
                'min': None,
                'max': None
            },
            'market': {
                'min': float(filters["MARKET_LOT_SIZE"]['minQty']),
                'max': float(filters["MARKET_LOT_SIZE"]['maxQty'])
            }
        },
        'info': input_data,
        'percentage': True,
        'tierBased': False,
        'taker': 0.001,
        'maker': 0.001,
        'lowercaseId': input_data['symbol'].replace('/', '').lower()
    }
    return output_data

def format_market_data(item):
    item_copy = item.copy()
    item_copy['symbol'] = convert_symbol_convention_from(item['symbol'])
    for key in ["price", "volume", "baseVolume", "amount", "quoteVolume", "low", "high", "open", "close", "change24h"]:
        if key in item_copy:
            item_copy[key] = float(item_copy[key])
    return item_copy

def convert_symbol_convention_from(symbol):
    """
    Original TrBinance Convention is to use underscore. 
    However, we want to convert to ccxt convention of using a slash
    """
    return symbol.replace("_", "/")

def convert_symbol_convention_to(symbol):
    """
    Original TrBinance Convention is to use underscore. 
    However, we want to convert to ccxt convention of using a slash
    """
    return symbol.replace("/", "_")