from dataclasses import dataclass

import yaml


@dataclass(frozen=True)
class SymbolConfig:
    code: str
    market: str
    price_market: str
    price_per_order: float
    buying_amount_list: list[int]


def load_symbol_configs() -> list[SymbolConfig]:
    """Load and return all symbol configurations from symbols.yaml."""
    with open("symbols.yaml", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return [
        SymbolConfig(
            code=s["code"],
            market=s["market"],
            price_market=s["price_market"],
            price_per_order=float(s["price_per_order"]),
            buying_amount_list=list(s["buying_amount_list"]),
        )
        for s in raw.get("symbols", [])
    ]
