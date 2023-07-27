import os

token = 0
token = os.getenv("BOTTARGHE_TOKEN")
if token==None:
  token = open(".token").read().rstrip()

bot_config = {
    "admin_id": 788342587,
    "token": token
}

update_queue = None
