from config.loader import load_symbol_configs
from models.order_info import BuyingOrderInfo, SellingOrderInfo
from services.message_dispatch_service import MessageDispatchService
from services.state_manager import state_manager
from utils.auto_trade_util import AutoTradeUtil
from utils.trade_util import (
    get_target_buying_amount,
    get_target_buying_price,
    get_target_buying_total_value,
    get_target_selling_price,
)

_auto_trade_util = AutoTradeUtil()
_dispatcher = MessageDispatchService()
_app_state = state_manager.app_state


def initiate_the_day():
    with state_manager.lock:
        _auto_trade_util.init_access_token()
        for sym_cfg in load_symbol_configs():
            sym = _app_state.get_or_create(sym_cfg.code)

            balance = _auto_trade_util.get_stock_balance_with_product_code(
                sym_cfg.market, sym_cfg.code
            )
            sym.average_unit_price = float(balance["pchs_avg_pric"]) if balance else 0.0
            sym.start_price_of_day = float(
                _auto_trade_util.get_today_price_detail(sym_cfg.price_market, sym_cfg.code)["open"]
            )
            sym.buying_ordered = False
            sym.selling_ordered = False
            sym.last_sold_price = 0.0
            sym.market_opened = True

            _dispatcher.dispatch_info(f"[{sym_cfg.code}] Market Opened")
            _dispatcher.dispatch_info(f"[{sym_cfg.code}] Start Price of Day: {sym.start_price_of_day}")
            if sym.average_unit_price > 0:
                _dispatcher.dispatch_info(f"[{sym_cfg.code}] Average Unit Price: {sym.average_unit_price}")

        state_manager.save()


def terminate_the_day():
    with state_manager.lock:
        for sym_cfg in load_symbol_configs():
            sym = _app_state.get_or_create(sym_cfg.code)

            sym.buying_order_info = None
            sym.selling_order_info = None
            sym.buying_ordered = False
            sym.selling_ordered = False
            sym.market_opened = False

            _dispatcher.dispatch_info(f"[{sym_cfg.code}] Market Closed")

        state_manager.save()


def check_the_market():
    with state_manager.lock:
        _check_the_market_locked()


def _check_the_market_locked():
    changed = False

    for sym_cfg in load_symbol_configs():
        code = sym_cfg.code
        market = sym_cfg.market
        price_per_order = sym_cfg.price_per_order
        buying_amount_list = sym_cfg.buying_amount_list
        max_purchase = len(buying_amount_list)

        sym = _app_state.get_or_create(code)
        if not sym.market_opened:
            continue
        if not sym.trading_active:
            continue

        buying_info = sym.buying_order_info
        selling_info = sym.selling_order_info

        is_buying_concluded = (
            _auto_trade_util.is_order_concluded(market=market, order_no=buying_info.order_no)
            if buying_info else False
        )
        is_selling_concluded = (
            _auto_trade_util.is_order_concluded(market=market, order_no=selling_info.order_no)
            if selling_info else False
        )

        # Guard: both concluded in the same tick — defer to next tick to avoid
        # applying conflicting state transitions simultaneously.
        if is_buying_concluded and is_selling_concluded:
            _dispatcher.dispatch_info(
                f"[{code}] Both orders concluded simultaneously — deferring to next tick"
            )
            continue

        if is_buying_concluded:
            sym.number_of_purchase += 1
            sym.buying_ordered = False
            sym.buying_order_info = None
            _dispatcher.dispatch_info(f"[{code}] Buying Order Concluded ({buying_info})")

            balance = _auto_trade_util.get_stock_balance_with_product_code(market, code)
            sym.average_unit_price = float(balance["pchs_avg_pric"]) if balance else 0.0

            if selling_info:
                _auto_trade_util.cancel_order(market, code, selling_info.order_no)
                sym.selling_order_info = None
                sym.selling_ordered = False
                _dispatcher.dispatch_info(f"[{code}] Selling Order Cancelled ({selling_info})")

            changed = True

        elif is_selling_concluded:
            sym.average_unit_price = 0.0
            sym.number_of_purchase = 0
            sym.selling_ordered = False
            sym.last_sold_price = selling_info.order_price
            sym.selling_order_info = None
            _dispatcher.dispatch_info(f"[{code}] Selling Order Concluded ({selling_info})")

            if buying_info:
                _auto_trade_util.cancel_order(market, code, buying_info.order_no)
                sym.buying_order_info = None
                sym.buying_ordered = False
                _dispatcher.dispatch_info(f"[{code}] Buying Order Cancelled ({buying_info})")

            changed = True

        if not sym.buying_ordered and sym.number_of_purchase < max_purchase:
            _dispatcher.log_info(f"[{code}] Buying Order Started")

            exchange_rate = _auto_trade_util.get_exchange_rate()
            if sym.number_of_purchase == 0 and sym.last_sold_price > 0:
                target_price = round(sym.last_sold_price * 0.95, 2)
            else:
                target_price = get_target_buying_price(sym.start_price_of_day, sym.average_unit_price)
            total_value = get_target_buying_total_value(price_per_order, sym.number_of_purchase, buying_amount_list)
            amount = get_target_buying_amount(total_value, exchange_rate, target_price)

            order_no = _auto_trade_util.buy(market, code, amount, target_price)
            sym.buying_ordered = True
            sym.buying_order_info = BuyingOrderInfo(order_no=order_no, order_amount=amount, order_price=target_price)
            _dispatcher.dispatch_info(f"[{code}] Buying Order ({sym.buying_order_info})")
            _dispatcher.log_info(f"[{code}] Buying Order Ended")
            changed = True

        if not sym.selling_ordered and sym.average_unit_price > 0:
            _dispatcher.log_info(f"[{code}] Selling Order Started")

            balance = _auto_trade_util.get_stock_balance_with_product_code(market, code)
            sell_amount = int(balance["ord_psbl_qty"]) if balance else 0
            target_price = get_target_selling_price(sym.start_price_of_day, sym.average_unit_price)

            order_no = _auto_trade_util.sell(market, code, sell_amount, target_price)
            sym.selling_ordered = True
            sym.selling_order_info = SellingOrderInfo(order_no=order_no, order_amount=sell_amount, order_price=target_price)
            _dispatcher.dispatch_info(f"[{code}] Selling Order ({sym.selling_order_info})")
            _dispatcher.log_info(f"[{code}] Selling Order Ended")
            changed = True

    if changed:
        state_manager.save()
