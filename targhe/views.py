from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from telegram import Update as TelegramUpdate
import json
from T.bot import BotUpdateQueue
from T.models import Bot, Plaque, Celebrity
from telegram import Bot as TelegramBot
import logging
import pandas as pd
import os
import sys

@staff_member_required
def reset(request):
    from django.apps import apps

    models = apps.get_app_config("T").models
    for mod in models:  # da testare
        models[mod].objects.all().delete()  # da testare
    os.execl(sys.argv[0], *sys.argv)


@login_required
def restart(request):
    os.execl(sys.argv[0], *sys.argv)


@login_required
def download_excel(request):
    import os
    from django.http import HttpResponse
    from wsgiref.util import FileWrapper

    total_df = pd.DataFrame()
    for cel in Celebrity.objects.all():
        df = pd.DataFrame(
            cel.plaque_set.all().values_list(
                "photo",
                "photo_link",
                "maps_url",
                "latitude",
                "longitude",
                "place",
                "description",
                "transcription",
                "user__name",
                "date",
            ),
            columns=[
                "Nome file foto",
                "Url foto",
                "Maps Url",
                "Latitudine",
                "Longitudine",
                "Posizione",
                "Descrizione",
                "Trascrizione",
                "Inserito da",
                "Data e Ora (UTC)",
            ],
        )
        df["Data e Ora (UTC)"] = df["Data e Ora (UTC)"].astype(str).str[:-6]
        celebrities =  pd.DataFrame({"Persona Presente": [cel.anagraphic]*cel.plaque_set.count()})
        df = pd.concat([df, celebrities], axis=1)
        total_df = pd.concat([total_df, df])
    total_df.to_excel("excel.xlsx")
    try:
        wrapper = FileWrapper(open("excel.xlsx", "rb"))
        response = HttpResponse(wrapper, content_type="application/force-download")
        response["Content-Disposition"] = "inline; filename=" + os.path.basename(
            "excel.xlsx"
        )
        return response
    except Exception:
        return HttpResponse(status=500)


@login_required
def home(request):
    context = {}
    """
    riempie il context
    """
    return render(request, "home.html", context=context)


class webhook(View):
    def post(self, request, *args, **kwargs):
        get_update(request.body)
        return JsonResponse({"ok": "POST request processed"})


def get_update(text):
    bot = TelegramBot(Bot.objects.first().token)
    update = TelegramUpdate.de_json(json.loads(text), bot)
    update_queue = BotUpdateQueue().queue
    update_queue.put(update)
