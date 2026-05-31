import dataclasses
import json
import os
from pathlib import Path

from models.order_info import BuyingOrderInfo, SellingOrderInfo
from models.state import AppState, SymbolState

STATE_FILE = Path("state.json")

# Fields in SymbolState that are handled separately (nested dataclasses).
_ORDER_FIELDS = {"buying_order_info", "selling_order_info"}

# All scalar fields derived at import time so load() stays in sync with the model.
_SCALAR_FIELDS = [
    f for f in dataclasses.fields(SymbolState) if f.name not in _ORDER_FIELDS
]


class StateStore:
    def load(self) -> AppState:
        if not STATE_FILE.exists():
            return AppState()
        with open(STATE_FILE, encoding="utf-8") as f:
            raw = json.load(f)
        app = AppState()
        for code, d in raw.get("symbols", {}).items():
            kwargs: dict = {}
            for field in _SCALAR_FIELDS:
                if field.name in d:
                    kwargs[field.name] = d[field.name]
                # Missing key → dataclass default applies; no KeyError.
            sym = SymbolState(**kwargs)
            if d.get("buying_order_info"):
                sym.buying_order_info = BuyingOrderInfo(**d["buying_order_info"])
            if d.get("selling_order_info"):
                sym.selling_order_info = SellingOrderInfo(**d["selling_order_info"])
            app.symbols[code] = sym
        return app

    def save(self, app: AppState) -> None:
        result: dict = {"symbols": {}}
        for code, sym in app.symbols.items():
            entry: dict = {
                f.name: getattr(sym, f.name) for f in _SCALAR_FIELDS
            }
            entry["buying_order_info"] = (
                dataclasses.asdict(sym.buying_order_info)
                if sym.buying_order_info else None
            )
            entry["selling_order_info"] = (
                dataclasses.asdict(sym.selling_order_info)
                if sym.selling_order_info else None
            )
            result["symbols"][code] = entry
        tmp_path = STATE_FILE.with_suffix(".json.tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, STATE_FILE)
