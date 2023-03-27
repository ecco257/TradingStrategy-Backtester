import Configuration.Config as cfg

class LimitOrder:
    def __init__(self, timestamp: int, quantity: float, price: float):
        if cfg.USE_CRYPTO:
            self.security = cfg.CRYPTO_PAIR
        else:
            self.security = cfg.STOCK_TICKER
        self.timestamp = timestamp
        self.quantity = quantity
        self.price = price

    def __str__(self):
        return "Limit Order for " + str(self.quantity) + " " + self.security + " at " + str(self.price) + " on timestamp " + str(self.timestamp)
    
    def __repr__(self):
        return "LimitOrder(" + self.security + ", " + str(self.timestamp) + ", " + str(self.quantity) + ", " + str(self.price) + ")"
    
class MarketOrder:
    def __init__(self, timestamp: int, quantity: float):
        if cfg.USE_CRYPTO:
            self.security = cfg.CRYPTO_PAIR
        else:
            self.security = cfg.STOCK_TICKER
        self.timestamp = timestamp
        self.quantity = quantity

    def __str__(self):
        return "Market Order for " + str(self.quantity) + " " + self.security + " on timestamp " + str(self.timestamp)
    
    def __repr__(self):
        return "MarketOrder(" + self.security + ", " + str(self.timestamp) + ", " + str(self.quantity) + ")"
    
class Trade:
    def __init__(self, timestamp: int, quantity: float, price: float, is_taker: bool = True):
        if cfg.USE_CRYPTO:
            self.security = cfg.CRYPTO_PAIR
        else:
            self.security = cfg.STOCK_TICKER
        self.timestamp = timestamp
        self.quantity = quantity
        self.price = price
        self.is_taker = is_taker

    def __str__(self):
        return "Trade for " + str(self.quantity) + " " + self.security + " at " + str(self.price) + " on timestamp " + str(self.timestamp)
    
    def __repr__(self):
        return "Trade(" + self.security + ", " + str(self.timestamp) + ", " + str(self.quantity) + ", " + str(self.price) + ")"
    
class State:
    def __init__(self, timestamp: int, position: float, open: float, high: float, low: float, close: float, volume: float):
        if cfg.USE_CRYPTO:
            self.security = cfg.CRYPTO_PAIR
        else:
            self.security = cfg.STOCK_TICKER
        self.timestamp = timestamp
        self.position = position
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume

    def __str__(self):
        return "State for " + self.security + " on timestamp " + str(self.timestamp) + " with position " + str(self.position) + " and OHLCV " + str(self.open) + ", " + str(self.high) + ", " + str(self.low) + ", " + str(self.close) + ", " + str(self.volume)        

    def __repr__(self):
        return "State(" + self.security + ", " + str(self.timestamp) + ", " + str(self.position) + ", " + str(self.open) + ", " + str(self.high) + ", " + str(self.low) + ", " + str(self.close) + ", " + str(self.volume) + ")"
