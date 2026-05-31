import datetime
import requests
import yaml


class DiscordUtil:
    def __init__(self):
        with open('config.yaml', encoding='UTF-8') as f:
            _cfg = yaml.load(f, Loader=yaml.FullLoader)
        self.discord_webhook_url = _cfg['DISCORD_WEBHOOK_URL']

    def send_message(self, msg):
        """디스코드 메세지 전송"""
        url = self.discord_webhook_url
        message = {"content": f"{str(msg)}"}
        requests.post(url, data=message)
