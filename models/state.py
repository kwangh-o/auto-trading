from dataclasses import dataclass, field
from typing import Optional

from models.order_info import BuyingOrderInfo, SellingOrderInfo


@dataclass
class SymbolState:
    market_opened: bool = False
    buying_ordered: bool = False
    selling_ordered: bool = False
    trading_active: bool = True
    start_price_of_day: float = 0.0
    number_of_purchase: int = 0
    average_unit_price: float = 0.0
    last_sold_price: float = 0.0
    buying_order_info: Optional[BuyingOrderInfo] = None
    selling_order_info: Optional[SellingOrderInfo] = None


@dataclass
class AppState:
    symbols: dict[str, SymbolState] = field(default_factory=dict)

    def get_or_create(self, code: str) -> SymbolState:
        if code not in self.symbols:
            self.symbols[code] = SymbolState()
        return self.symbols[code]
