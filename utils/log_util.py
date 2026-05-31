import logging.handlers
import os
from datetime import datetime

import pytz

LOG_PATH = 'logs/log.log'


class LogUtil:
    def __init__(self):
        self.init_logger()

    def init_logger(self):
        logger = logging.getLogger("auto_trade")

        if not logger.handlers:
            formatter = LoggingTimeFormatter('%(asctime)s - %(levelname)s - %(message)s')

            os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
            file_handler = logging.handlers.TimedRotatingFileHandler(
                filename=LOG_PATH,
                when='W0',
                interval=1,
                backupCount=5,
            )
            file_handler.suffix = "-%Y%m%d"
            file_handler.setFormatter(formatter)

            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)

            logger.addHandler(file_handler)
            logger.addHandler(stream_handler)
            logger.setLevel(logging.INFO)

        self.logger = logger

    def info(self, message):
        self.logger.info(message)


class LoggingTimeFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        now = datetime.fromtimestamp(record.created, tz=pytz.timezone('Asia/Seoul'))
        return now.strftime('%Y-%m-%d %H:%M:%S')
