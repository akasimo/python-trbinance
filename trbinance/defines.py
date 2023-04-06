from enum import Enum

class Side(Enum):
    BUY = 0
    SELL = 1

class SymbolType(Enum):
    MAIN = 0
    NEXT = 1

class OrderStatus(Enum):
    SYSTEM_PROCESSING = -2
    NEW = 0
    PARTIALLY_FILLED = 1
    FILLED = 2
    CANCELED = 3
    PENDING_CANCEL = 4
    REJECTED = 5
    EXPIRED = 6

class OrderType(Enum):
    LIMIT = 1
    MARKET = 2
    STOP_LOSS = 3
    STOP_LOSS_LIMIT = 4
    TAKE_PROFIT = 5
    TAKE_PROFIT_LIMIT = 6
    LIMIT_MAKER = 7

class OrderSide(Enum):
    BUY = 0
    SELL = 1

KLINE_INTERVALS = ["1m","3m","5m","15m","30m","1h","2h","4h","6h","8h","12h","1d","3d","1w","1M"]

# # Create a reverse-lookup dictionary
# reverse_lookup = {value: key for key, value in OrderStatus.__members__.items()}