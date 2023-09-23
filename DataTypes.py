import Configuration.Config as cfg
from typing import Union    

class Order:
    def __init__(self, security: str, timestamp: int, quantity: float):
        self.security = security
        self.timestamp = timestamp
        self.quantity = quantity

    def __str__(self):
        return f"{self.__class__.__name__} for {self.quantity} {self.security} on timestamp {self.timestamp}"

    def __repr__(self):
        return f"{self.__class__.__name__}({self.security}, {self.timestamp}, {self.quantity})"

class LimitOrder(Order):
    def __init__(self, security: str, timestamp: int, quantity: float, price: float):
        super().__init__(security, timestamp, quantity)
        self.price = price

    def __str__(self):
        return f"{super().__str__()} at {self.price}"

class MarketOrder(Order):
    def __init__(self, security: str, timestamp: int, quantity: float):
        super().__init__(security, timestamp, quantity)
    
class Trade:
    def __init__(self, security: str, timestamp: int, quantity: float, price: float, is_taker: bool = True, filled: Union[int, None] = None):
        self.security = security
        self.timestamp = timestamp
        self.quantity = quantity
        self.price = price
        self.is_taker = is_taker
        self.filled = filled

    def __str__(self):
        return "Trade for " + str(self.quantity) + " " + self.security + " at " + str(self.price) + " on timestamp " + str(self.timestamp)
    
    def __repr__(self):
        return "Trade(" + self.security + ", " + str(self.timestamp) + ", " + str(self.quantity) + ", " + str(self.price) + ")"
    
class State:
    def __init__(self, security: str, timestamp: int, position: float, open: float, high: float, low: float, close: float, volume: float, cash: float, pnl: float, hidden_state: int = None):
        self.security = security
        self.timestamp = timestamp
        self.position = position
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.cash = cash
        self.pnl = pnl
        self.hidden_state = hidden_state

    def __str__(self):
        return "State for " + self.security + " on timestamp " + str(self.timestamp) + " with position " + str(self.position) + " and OHLCV " + str(self.open) + ", " + str(self.high) + ", " + str(self.low) + ", " + str(self.close) + ", " + str(self.volume) + " and PnL " + str(self.pnl) + " and hidden state " + str(self.hidden_state)      

    def __repr__(self):
        return "State(" + self.security + ", " + str(self.timestamp) + ", " + str(self.position) + ", " + str(self.open) + ", " + str(self.high) + ", " + str(self.low) + ", " + str(self.close) + ", " + str(self.volume) + ", " + str(self.pnl) + ", " + str(self.hidden_state) + ")"
