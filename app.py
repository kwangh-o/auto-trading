import threading

import uvicorn
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone

from services.trade_service import check_the_market, initiate_the_day, terminate_the_day


def _start_api() -> None:
    uvicorn.run("api.app:app", host="0.0.0.0", port=8000, log_level="info")


api_thread = threading.Thread(target=_start_api, daemon=True, name="api-server")
api_thread.start()

scheduler = BlockingScheduler()

ny_tz = timezone('America/New_York')

scheduler.add_job(func=initiate_the_day, trigger=CronTrigger(day_of_week="mon-fri", hour=9, minute=34, timezone=ny_tz))
scheduler.add_job(func=check_the_market, trigger=CronTrigger(day_of_week="mon-fri", minute="*/1", second="30", timezone=ny_tz))
scheduler.add_job(func=terminate_the_day, trigger=CronTrigger(day_of_week="mon-fri", hour=16, minute=0, timezone=ny_tz))

scheduler.start()
