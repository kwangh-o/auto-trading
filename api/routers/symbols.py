from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config.loader import load_symbol_configs
from services.state_manager import state_manager

router = APIRouter(prefix="/symbols", tags=["symbols"])


class SymbolResponse(BaseModel):
    code: str
    trading_active: Optional[bool]
    market_opened: Optional[bool]
    number_of_purchase: Optional[int]
    average_unit_price: Optional[float]
    buying_ordered: Optional[bool]
    selling_ordered: Optional[bool]


@router.get("", response_model=list[SymbolResponse])
def get_symbols() -> list[SymbolResponse]:
    """Return all symbols from config.yaml with their current runtime state.

    Symbols that have no runtime state yet return null for all state fields.
    This endpoint never mutates state (no get_or_create).
    """
    codes = [c.code for c in load_symbol_configs()]
    result: list[SymbolResponse] = []

    with state_manager.lock:
        symbols_map = state_manager.app_state.symbols
        for code in codes:
            sym = symbols_map.get(code)
            if sym is None:
                result.append(SymbolResponse(
                    code=code,
                    trading_active=None,
                    market_opened=None,
                    number_of_purchase=None,
                    average_unit_price=None,
                    buying_ordered=None,
                    selling_ordered=None,
                ))
            else:
                result.append(SymbolResponse(
                    code=code,
                    trading_active=sym.trading_active,
                    market_opened=sym.market_opened,
                    number_of_purchase=sym.number_of_purchase,
                    average_unit_price=sym.average_unit_price,
                    buying_ordered=sym.buying_ordered,
                    selling_ordered=sym.selling_ordered,
                ))

    return result


@router.post("/{code}/pause")
def pause_symbol(code: str) -> dict:
    with state_manager.lock:
        sym = state_manager.app_state.symbols.get(code)
        if sym is None:
            raise HTTPException(status_code=404, detail=f"Symbol '{code}' not found")
        sym.trading_active = False
        state_manager.save()
    return {"code": code, "trading_active": False}


@router.post("/{code}/resume")
def resume_symbol(code: str) -> dict:
    with state_manager.lock:
        sym = state_manager.app_state.symbols.get(code)
        if sym is None:
            raise HTTPException(status_code=404, detail=f"Symbol '{code}' not found")
        sym.trading_active = True
        state_manager.save()
    return {"code": code, "trading_active": True}
