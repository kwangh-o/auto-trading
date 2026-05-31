# Auto Trading Bot

한국투자증권 Open API를 활용한 미국 주식 자동매매 봇.
APScheduler 기반 스케줄러와 FastAPI 관리 서버로 구성된다.

## 요구 사항

- Python 3.9+
- 한국투자증권 Open API 계정 및 앱 키

```bash
pip install fastapi "uvicorn[standard]" pyyaml apscheduler pytz requests
```

## 한국투자증권 API

이 봇은 한국투자증권 Open Trading API를 사용한다. API 스펙, 인증 방법, 거래소 코드 등 상세 내용은 공식 레포를 참고한다.

> https://github.com/koreainvestment/open-trading-api

## 설정

### config.yaml

인프라/인증 설정 파일. 프로젝트 루트에 위치해야 한다.

```yaml
APP_KEY: "..."
APP_SECRET: "..."
CANO: "12345678"        # 계좌번호 앞 8자리
ACNT_PRDT_CD: "01"      # 계좌번호 뒤 2자리
URL_BASE: "https://openapi.koreainvestment.com:9443"
DISCORD_WEBHOOK_URL: "..."
```

### symbols.yaml

종목별 매매 설정. 항목을 추가하는 것만으로 새 종목이 자동 등록된다.

```yaml
symbols:
  - code: "AAPL"
    market: "NASD"                    # 주문/체결/취소 API용 거래소 코드
    price_market: "NAS"               # 시세 조회 전용 코드 (NASD → NAS)
    price_per_order: 100000.0         # 1회 주문 기준 금액 (원)
    buying_amount_list: [1, 1, 2, 4]  # 차수별 price_per_order 배수 (길이 = 최대 매수 횟수)
```

## 실행

모든 명령어는 **프로젝트 루트**에서 실행한다.

```bash
# 포어그라운드
python app.py

# 백그라운드 (로그: nohup.out)
nohup python app.py &
```

## 아키텍처

### 스레드 구조

`app.py` 기동 시 두 개의 실행 흐름이 시작된다.

| 스레드 | 역할 |
|--------|------|
| 메인 스레드 | APScheduler `BlockingScheduler` — 장중 스케줄 작업 실행 |
| 데몬 스레드 | FastAPI/uvicorn 서버 (port 8000) — REST API 제공 |

API 요청과 스케줄러 작업은 `state_manager.lock` (RLock)으로 상호 배제된다.

### 스케줄 (뉴욕 시간 기준, 평일)

| 시각 | 함수 | 역할 |
|------|------|------|
| 09:34 | `initiate_the_day` | 액세스 토큰 발급, 시가/평단가 조회, 상태 초기화 (`last_sold_price` 포함) |
| 매분 :30초 | `check_the_market` | 체결 확인 → 주문 취소/재생성 |
| 16:00 | `terminate_the_day` | 주문 정보 클리어, 장 종료 처리 |


### 매매 전략

평단가 대비 **-10% 추가 매수 / +10% 익절**을 반복하는 분할 매수 사이클 전략이다.
추가 매수 차수마다 투입 금액을 키워(`buying_amount_list`) 한 번 물타기할 때마다
평가 손실률이 절반으로 줄도록 설계되어 있다.

장이 열리면 각 종목에 매수·매도 주문을 동시에 건다.

- **매수 주문**: 시가 × 0.95 와 평단가 × 0.9(주식 잔고가 있을 때) 중 **낮은** 가격
- **매도 주문**: 시가 와 평단가 × 1.1 중 **높은** 가격 (보유 수량 전체)

장 중 체결이 발생하면 반대편 주문을 정리하고 새 기준으로 재주문한다.

- **매수 체결**: 매도 주문을 취소하고, 낮아진 평단가 기준으로 매수·매도 주문을 재생성
- **매도 체결**: 매수 주문을 취소하고, 방금 매도가 × 0.95 가격으로 새 매수 주문 (새 사이클 시작)

차수별 투입 금액은 `buying_amount_list`로 정한다. `[1, 1, 2, 4]`처럼 뒤로 갈수록 큰 배수를
두면 하락 시 평단가를 빠르게 낮춰 물타기마다 손실률을 절반씩 줄인다. 리스트 길이가
최대 매수 횟수이며, 길이를 늘리면 더 깊은 하락까지 분할 매수가 이어진다.

분할 매수 횟수를 늘리면 수익률을 낮추는 대신 리스크를 줄일 수 있고, 반대로 분할 매수 횟수를 줄이면 리스크를 높이는 대신 수익률을 높일 수 있다.

### 매매 로직

**매수**
- 조건: `trading_active AND !buying_ordered AND number_of_purchase < 최대매수횟수`
- 매수가:
  - 신규 사이클(`number_of_purchase == 0`) + 당일 매도 이력 있음: `last_sold_price × 0.95`
  - 그 외: `min(시가 × 0.95, 평단가 × 0.9)` (평단가 없으면 `시가 × 0.95`)

**매도**
- 조건: `trading_active AND !selling_ordered AND average_unit_price > 0`
- 매도가: `max(시가, 평단가 × 1.1)`

**체결 처리**
- 매수 체결 → 기존 매도 주문 취소 후 새 평단가로 매도 주문 재생성
- 매도 체결 → `number_of_purchase = 0` 리셋, 기존 매수 주문 취소
- 매수·매도 동시 체결 → 다음 틱으로 연기

### 파일 구조

```
├── app.py                          # 진입점: 스케줄러 + API 서버 기동
├── config.yaml                     # 인증/인프라 설정
├── symbols.yaml                    # 종목별 매매 설정
├── state.json                      # 런타임 상태 영속 저장소
├── api/
│   ├── app.py                      # FastAPI 앱 정의
│   └── routers/symbols.py          # /symbols 라우터
├── config/
│   └── loader.py                   # 설정 파일 파싱 (SymbolConfig)
├── models/
│   ├── state.py                    # SymbolState, AppState 정의
│   └── order_info.py               # 주문 정보 모델
├── services/
│   ├── state_manager.py            # 전역 상태 싱글톤 (lock 포함)
│   ├── state_store.py              # state.json 직렬화/역직렬화
│   ├── trade_service.py            # 핵심 매매 로직
│   └── message_dispatch_service.py # 로그 + 디스코드 알림
└── utils/
    ├── auto_trade_util.py          # KIS API 호출 전담
    ├── trade_util.py               # 매매 유틸리티
    ├── discord_util.py             # 디스코드 웹훅
    └── log_util.py                 # 로깅
```

## REST API

서버 기동 후 `http://localhost:8000` 에서 접근 가능하다.

| Method | Path | 설명 |
|--------|------|------|
| `GET` | `/symbols` | 전체 종목 현재 상태 조회 (미초기화 종목은 null) |
| `POST` | `/symbols/{code}/pause` | 특정 종목 거래 정지 (`trading_active=false`) |
| `POST` | `/symbols/{code}/resume` | 특정 종목 거래 재개 (`trading_active=true`) |

`trading_active` 플래그는 장 시작/종료 시 리셋되지 않으며, 운영자가 직접 제어한다.

## 알림

Discord 웹훅으로 주요 이벤트(주문 생성/체결/취소, 오류)를 실시간 전송한다.
`config.yaml`의 `DISCORD_WEBHOOK_URL`에 웹훅 URL을 설정한다.
