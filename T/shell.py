import io
import os
import sys
import threading
import subprocess
from subprocess import Popen, PIPE
from telegram.ext import Filters, CommandHandler, MessageHandler, ConversationHandler


class _Shell(object):
    def __init__(self):
        self.stdout = io.BytesIO()
        self.env = os.environ.copy()

    def run(self, bot, admin_id):
        self.bot = bot
        self.admin_id = admin_id
        self.p = Popen(
            "/bin/bash",
            stdin=PIPE,
            stdout=PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            env=self.env,
        )
        self.writer = threading.Thread(target=self.get_output, args=(self.p,))
        self.writer.start()

    def get_output(self, p):
        while True:
            data = p.stdout.read(1)
            if not data:
                break
            self.stdout.write(data)
            if data == b"\n":
                self.stdout.seek(0)
                self.bot.send_message(self.admin_id, self.stdout.read().decode("utf-8"))
                self.stdout.truncate(0)

    def write(self, message):
        self.p.stdin.write((message + "\n").encode())
        self.p.stdin.flush()

    def kill(self):
        self.p.kill()


class Shell:
    class __Shell(_Shell):
        pass

    instance = None

    def __new__(cls):  # __new__ always a classmethod
        if not Shell.instance:
            Shell.instance = Shell.__Shell()
        return Shell.instance

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __setattr__(self, name, value):
        return setattr(self.instance, name, value)


def conv_handler(bot, admin_id):

    def run(update, context):
        Shell().run(bot, admin_id)
        return 1
    
    def write(update, context):
        Shell().write(update.message.text)
        return 1

    def close(update, context):
        Shell().kill()
        return ConversationHandler.END

    ch = ConversationHandler(
        [CommandHandler("shell", run, filters=Filters.chat(admin_id))],
        {1: [MessageHandler(Filters.text, write)]},
        [CommandHandler("close", close, filters=Filters.chat(admin_id))],
    )
    return ch
