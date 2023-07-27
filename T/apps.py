from django.apps import AppConfig
import sys
import os
import logging
from T.bot_config import bot_config
from telegram import Bot as telegramBot
from targhe.settings import DEBUG


class adminHandler(logging.Handler):
    def __init__(self, token=None, admin_id=None):
        self.bot = telegramBot(token)
        self.admin_id = admin_id
        logging.Handler.__init__(self)

    def emit(self, record):
        with open("log.txt", "w") as out_file:
            out_file.write(self.format(record))
        try:
            with open("log.txt", "rb") as in_file:
                self.bot.send_document(self.admin_id, in_file)
        except: #otherwise the exception's logging becomes recursive
            pass


class TConfig(AppConfig):
    name = 'T'

    def ready(self):
        import T.signals
        if "targhe.wsgi" in sys.argv or "runserver" in sys.argv:
            import T.bot
            from T.models import Bot
            from T.exceptions import UniqueObjectError
            Bot.objects.all().delete()
            bot = Bot.objects.create(**bot_config)
            _hd = adminHandler(token=bot.token, admin_id=bot.admin_id)
            _hd.setLevel(logging.ERROR)
            if not DEBUG:
                logging.getLogger("").addHandler(_hd)

            T.bot.run()
