from dataclasses import dataclass


@dataclass
class OrderInfo:
    order_no: str = ""
    order_amount: int = 0
    order_price: float = 0.0

    def __str__(self):
        return f"order_no={self.order_no}, order_amount={self.order_amount}, order_price={self.order_price}"

@dataclass
class BuyingOrderInfo(OrderInfo):
    order_type: str = "buy"

@dataclass
class SellingOrderInfo(OrderInfo):
    order_type: str = "sell"