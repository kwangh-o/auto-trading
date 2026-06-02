from __future__ import annotations
from datetime import datetime, timedelta
import json
import time
import pytz
import requests
import yaml

class AutoTradeUtil:
    def __init__(self):
        with open('config.yaml', encoding='UTF-8') as f:
            _cfg = yaml.load(f, Loader=yaml.FullLoader)
        self.APP_KEY = _cfg['APP_KEY']
        self.APP_SECRET = _cfg['APP_SECRET']
        self.URL_BASE = _cfg['URL_BASE']
        self.CANO = _cfg['CANO']
        self.ACNT_PRDT_CD = _cfg['ACNT_PRDT_CD']

        # self.init_access_token()

    def init_access_token(self):
        # self.ACCESS_TOKEN = ""
        self.ACCESS_TOKEN = self.get_access_token()

    """토큰 발급"""
    def get_access_token(self):
        headers = {"content-type":"application/json"}
        body = {"grant_type":"client_credentials",
        "appkey": self.APP_KEY, 
        "appsecret": self.APP_SECRET}
        PATH = "oauth2/tokenP"
        URL = f"{self.URL_BASE}/{PATH}"
        res = requests.post(URL, headers=headers, data=json.dumps(body))
        return res.json()["access_token"]
        
    """암호화"""
    def hashkey(self, datas):
        PATH = "uapi/hashkey"
        URL = f"{self.URL_BASE}/{PATH}"
        headers = {
        'content-Type' : 'application/json',
        'appKey' :  self.APP_KEY,
        'appSecret' : self.APP_SECRET,
        }
        res = requests.post(URL, headers=headers, data=json.dumps(datas))
        hashkey = res.json()["HASH"]
        return hashkey

    """주식 잔고조회"""
    def get_stock_balance(self):
        PATH = "uapi/overseas-stock/v1/trading/inquire-balance"
        URL = f"{self.URL_BASE}/{PATH}"
        headers = {"Content-Type":"application/json", 
            "authorization": f"Bearer {self.ACCESS_TOKEN}",
            "appKey": self.APP_KEY,
            "appSecret": self.APP_SECRET,
            "tr_id": "TTTS3012R",
        }
        params = {
            "CANO": self.CANO,
            "ACNT_PRDT_CD": self.ACNT_PRDT_CD,
            "OVRS_EXCG_CD": "AMEX",
            "TR_CRCY_CD": "USD",
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": ""
        }
        res = requests.get(URL, headers=headers, params=params)
        stock_list = res.json()['output1']
        stock_dict = {}
        for stock in stock_list:
            if int(stock['ovrs_cblc_qty']) > 0:
                stock_dict[stock['ovrs_pdno']] = stock['ovrs_cblc_qty']
                time.sleep(0.1)
        return stock_dict

    """주식 잔고조회 (종목)"""
    def get_stock_balance_with_product_code(self, market: str, product_code: str) -> dict | None:
        PATH = "uapi/overseas-stock/v1/trading/inquire-balance"
        URL = f"{self.URL_BASE}/{PATH}"
        headers = {"Content-Type":"application/json",
            "authorization": f"Bearer {self.ACCESS_TOKEN}",
            "appKey": self.APP_KEY,
            "appSecret": self.APP_SECRET,
            "tr_id": "TTTS3012R",
        }
        params = {
            "CANO": self.CANO,
            "ACNT_PRDT_CD": self.ACNT_PRDT_CD,
            "OVRS_EXCG_CD": market,
            "TR_CRCY_CD": "USD",
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": ""
        }
        res = requests.get(URL, headers=headers, params=params)
        stock_list = res.json()['output1']
        for stock in stock_list:
            if stock['ovrs_pdno'] == product_code:
                return stock
        return None

    """미국 주식 지정가 매수"""
    def buy(self, market="NASD", code="AAPL", qty="1", price="0"):
        PATH = "uapi/overseas-stock/v1/trading/order"
        URL = f"{self.URL_BASE}/{PATH}"
        data = {
            "CANO": self.CANO,
            "ACNT_PRDT_CD": self.ACNT_PRDT_CD,
            "OVRS_EXCG_CD": market,
            "PDNO": code,
            "ORD_DVSN": "00",
            "ORD_QTY": str(int(qty)),
            "OVRS_ORD_UNPR": f"{round(price,2)}",
            "ORD_SVR_DVSN_CD": "0"
        }
        headers = {
            "Content-Type": "application/json", 
            "authorization": f"Bearer {self.ACCESS_TOKEN}",
            "appKey": self.APP_KEY,
            "appSecret": self.APP_SECRET,
            "tr_id": "TTTT1002U",
            "custtype": "P",
            "hashkey" : self.hashkey(data)
        }
        res = requests.post(URL, headers=headers, data=json.dumps(data))
        if res.json()['rt_cd'] == '0':
            return res.json()["output"]["ODNO"]
        else:
            return None

    """미국 주식 지정가 매도"""
    def sell(self, market="NASD", code="AAPL", qty="1", price="0"):
        PATH = "uapi/overseas-stock/v1/trading/order"
        URL = f"{self.URL_BASE}/{PATH}"
        data = {
            "CANO": self.CANO,
            "ACNT_PRDT_CD": self.ACNT_PRDT_CD,
            "OVRS_EXCG_CD": market,
            "PDNO": code,
            "ORD_DVSN": "00",
            "ORD_QTY": str(int(qty)),
            "OVRS_ORD_UNPR": f"{round(price,2)}",
            "ORD_SVR_DVSN_CD": "0"
        }
        headers = {
            "Content-Type": "application/json", 
            "authorization": f"Bearer {self.ACCESS_TOKEN}",
            "appKey": self.APP_KEY,
            "appSecret": self.APP_SECRET,
            "tr_id": "TTTT1006U",
            "custtype": "P",
            "hashkey" : self.hashkey(data)
        }
        res = requests.post(URL, headers=headers, data=json.dumps(data))
        if res.json()['rt_cd'] == '0':
            return res.json()["output"]["ODNO"]
        else:
            return None

    """환율 조회"""
    def get_exchange_rate(self):
        PATH = "uapi/overseas-stock/v1/trading/inquire-present-balance"
        URL = f"{self.URL_BASE}/{PATH}"
        headers = {
            "Content-Type":"application/json", 
            "authorization": f"Bearer {self.ACCESS_TOKEN}",
            "appKey": self.APP_KEY,
            "appSecret": self.APP_SECRET,
            "tr_id": "CTRP6504R"
            }
        params = {
            "CANO": self.CANO,
            "ACNT_PRDT_CD": self.ACNT_PRDT_CD,
            "OVRS_EXCG_CD": "NASD",
            "WCRC_FRCR_DVSN_CD": "01",
            "NATN_CD": "840",
            "TR_MKET_CD": "01",
            "INQR_DVSN_CD": "00"
        }
        res = requests.get(URL, headers=headers, params=params)
        exchange_rate = 1460.0
        if len(res.json()['output2']) > 0:
            exchange_rate = float(res.json()['output2'][0]['frst_bltn_exrt'])
        return exchange_rate

    def get_today_price_detail(self, market="AMS", code="AAPL"):
        PATH = "uapi/overseas-price/v1/quotations/price-detail"
        URL = f"{self.URL_BASE}/{PATH}"
        headers = {
            "Content-Type": "application/json", 
            "authorization": f"Bearer {self.ACCESS_TOKEN}",
            "appKey": self.APP_KEY,
            "appSecret": self.APP_SECRET,
            "tr_id": "HHDFS76200200"
        }
        params = {
            "AUTH": "",
            "EXCD": market,
            "SYMB": code,
        }
        res = requests.get(URL, headers=headers, params=params)
        return res.json()['output']

    """현재가 조회"""
    def get_current_price(self, market="NASD", code="AAPL"):
        PATH = "uapi/overseas-price/v1/quotations/price"
        URL = f"{self.URL_BASE}/{PATH}"
        headers = {
            "Content-Type": "application/json", 
            "authorization": f"Bearer {self.ACCESS_TOKEN}",
            "appKey": self.APP_KEY,
            "appSecret": self.APP_SECRET,
            "tr_id": "HHDFS00000300"
        }
        params = {
            "AUTH": "",
            "EXCD": market,
            "SYMB": code,
        }
        res = requests.get(URL, headers=headers, params=params)
        return float(res.json()['output']['last']) if res.json()['output']['last'] != '' else 0.0

    """미체결내역 조회 (01: 매도, 02: 매수)"""
    def get_not_concluded_order(self, market="NASD", sll_buy_dvsn_cd="01"):
        PATH = "uapi/overseas-stock/v1/trading/inquire-nccs"
        URL = f"{self.URL_BASE}/{PATH}"
        headers = {
            "Content-Type": "application/json", 
            "authorization": f"Bearer {self.ACCESS_TOKEN}",
            "appKey": self.APP_KEY,
            "appSecret": self.APP_SECRET,
            "tr_id": "TTTS3018R"
        }
        params = {
            "CANO": self.CANO,
            "ACNT_PRDT_CD": self.ACNT_PRDT_CD,
            "OVRS_EXCG_CD": market,
            "SORT_SQN": "",
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": ""
        }
        res = requests.get(URL, headers=headers, params=params)
        return [order for order in res.json()["output"] if order["sll_buy_dvsn_cd"] == sll_buy_dvsn_cd]

    """주문 체결여부 조회"""
    def is_order_concluded(self, market="NASD", code="%", order_no=""):
        PATH = "uapi/overseas-stock/v1/trading/inquire-nccs"
        URL = f"{self.URL_BASE}/{PATH}"
        timezone = pytz.timezone('Asia/Seoul')
        now = datetime.now(timezone)
        today = now.strftime("%Y%m%d")
        yesterday = (now - timedelta(days=1)).strftime("%Y%m%d")
        headers = {
            "Content-Type": "application/json", 
            "authorization": f"Bearer {self.ACCESS_TOKEN}",
            "appKey": self.APP_KEY,
            "appSecret": self.APP_SECRET,
            "tr_id": "TTTS3035R"
        }
        params = {
            "CANO": self.CANO,
            "ACNT_PRDT_CD": self.ACNT_PRDT_CD,
            "PDNO": code,
            "ORD_STRT_DT": yesterday,
            "ORD_END_DT": today,
            "SLL_BUY_DVSN": "00",
            "CCLD_NCCS_DVSN": "01",
            "OVRS_EXCG_CD": market,
            "SORT_SQN": "DS",
            "ORD_DT": "",
            "ORD_GNO_BRNO": "",
            "ODNO": "",
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": ""
        }
        res = requests.get(URL, headers=headers, params=params)
        order = next((order for order in res.json()["output"] if order["odno"] == order_no), None)
        return order is not None and int(order["nccs_qty"]) == 0

    """주문 취소"""
    def cancel_order(self, market="NASD", code="AAPL", order_no=""):
        PATH = "uapi/overseas-stock/v1/trading/order-rvsecncl"
        URL = f"{self.URL_BASE}/{PATH}"
        headers = {
            "Content-Type": "application/json", 
            "authorization": f"Bearer {self.ACCESS_TOKEN}",
            "appKey": self.APP_KEY,
            "appSecret": self.APP_SECRET,
            "tr_id": "TTTT1004U"
        }
        params = json.dumps({
            "CANO": self.CANO,
            "ACNT_PRDT_CD": self.ACNT_PRDT_CD,
            "OVRS_EXCG_CD": market,
            "PDNO": code,
            "ORGN_ODNO": order_no,
            "RVSE_CNCL_DVSN_CD": "02",  # 01: 정정, 02: 취소
            "ORD_QTY": "0",
            "OVRS_ORD_UNPR": "0"
        })
        res = requests.post(URL, headers=headers, data=params)
        return res.json()["rt_cd"] == "0"

    """종목 정보 조회"""
    def get_stock_info(self, market="NASD", code="AAPL"):
        PATH = "uapi/overseas-price/v1/quotations/search-info"
        URL = f"{self.URL_BASE}/{PATH}"
        market_code_map = {
            "AMEX": "529",
            "NASD": "512",
        }
        headers = {
            "Content-Type": "application/json", 
            "authorization": f"Bearer {self.ACCESS_TOKEN}",
            "appKey": self.APP_KEY,
            "appSecret": self.APP_SECRET,
            "tr_id": "CTPF1702R",
            "custType": "P"
        }
        params = {
            "PRDT_TYPE_CD": market_code_map[market],
            "PDNO": code,
        }
        res = requests.get(URL, headers=headers, params=params)
        return res.json()['output']
    