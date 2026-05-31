from utils.discord_util import DiscordUtil
from utils.log_util import LogUtil


class MessageDispatchService:
    def __init__(self):
        self.logger = LogUtil()
        self.discord_util = DiscordUtil()

    def dispatch_info(self, message):
        self.logger.info(message)
        self.discord_util.send_message(message)

    def log_info(self, message):
        self.logger.info(message)

    def _send_discord_message(self, message):
        self.discord_util.send_message(message)