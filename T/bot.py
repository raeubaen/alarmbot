#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import sys
from telegram.ext import Dispatcher
from queue import Queue
from telegram import Bot
import threading
import targhe.settings as settings
import requests
from T.models import Bot as BotModel
import T.Conversation as Conversation
import T.shell as shell

# Handling logging and exceptions
DEBUG = settings.DEBUG


def not_hand_exc(exctype, value, trace_back):
    logging.error(
        "Uncaught Exception: ERROR!!", exc_info=(exctype, value, trace_back)
    )


def error(update, context):
    try:
        raise context.error
    except Exception:  # to log almost all exceptions
        logging.exception(f"Update: {update}")


sys.excepthook = not_hand_exc

# implements Singleton pattern - boring
class BotUpdateQueue(object):
    class __BotUpdateQueue:
        def __init__(self):
            self.queue = None
        def __str__(self):
            return str(self)
    instance = None
    def __new__(cls):  # __new__ always a classmethod
        if not BotUpdateQueue.instance:
            BotUpdateQueue.instance = BotUpdateQueue.__BotUpdateQueue()
        return BotUpdateQueue.instance
    def __getattr__(self, name):
        return getattr(self.instance, name)
    def __setattr__(self, name, value):
        return setattr(self.instance, name, value)


def run():
    # importing data from database
    bot_table = BotModel.objects.first()
    token = bot_table.token

    # initializing
    bot = Bot(token)
    update_queue = Queue()
    BotUpdateQueue().queue = update_queue
    dp = Dispatcher(bot, update_queue, use_context=True)

    dp.add_handler(shell.conv_handler(bot, bot_table.admin_id))
    dp.add_handler(Conversation.conv_handler)  # Conversation module
    dp.add_error_handler(error)

    thread = threading.Thread(target=dp.start, name="dispatcher")
    thread.start()

    print(f"Debug: {DEBUG}")

    if not DEBUG:  # in production
        webhook_url = "https://targhe-git-photobefore-raeubaen.vercel.app/bot/"
    if DEBUG:  # in localhost
        from pyngrok import ngrok

        ngrok_url = ngrok.connect(port=8000)
        webhook_url = ngrok_url.replace("http", "https") + "/bot/"
    req = requests.post(
        "https://api.telegram.org/bot" + token + "/setWebhook", {"url": webhook_url, "allowed_updates": ["callback_query", "message"]}
    )
    print("risposta al setwebhook: ",  req)
    if req.status_code != 200:
        logging.error("Webhook not set!")


if __name__ == "__main__":
    run()
