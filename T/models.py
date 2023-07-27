from django.db import models
from django.utils import timezone
from django.core.files.storage import default_storage
from targhe.settings import DROPBOX_OAUTH2_TOKEN
import T.exceptions
import requests
import logging
import csv
from io import StringIO
import json

# Create your models here.
class User(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nome")
    phone = models.CharField(max_length=15, unique = True, verbose_name="Telefono")
    chat_id = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        if self.name != "":
            return self.name
        else:
            return self.phone

    def save(self, *args, **kwargs):
        if self._state.adding and self.__class__.objects.filter(phone=self.phone).exists():
            return
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Utente"
        verbose_name_plural = "Utenti"


class Bot(models.Model):
    id = models.IntegerField(
        unique=True, primary_key=True, default=1
    )  # to be sure there's only one instance of the model
    token = models.CharField(max_length=70, null=True)
    admin_id = models.IntegerField(null=True)
    user_csv = models.FileField(storage=default_storage, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self._state.adding and self.__class__.objects.exists():
            raise T.exceptions.UniqueObjectError(
                f"There can be only one {self.__class__.__name__} instance"
            )
        if self.user_csv:
            csv_f = StringIO(self.user_csv.read().decode())
            csv_reader = csv.reader(csv_f, delimiter=',')
            for row in csv_reader:
                name = row[0]
                phone = row[1]
                User.objects.filter(phone__endswith=phone).delete()
                User.objects.create(name=name, phone=phone)
        super().save(*args, **kwargs)

    def __str__(self):
        return "BotTarghe"

    class Meta:
        verbose_name = "BotTarghe"
        verbose_name_plural = "BotTarghe"


class Celebrity(models.Model):
    anagraphic = models.CharField(max_length=300, verbose_name="Nome")

    def __str__(self):
        return self.anagraphic

    class Meta:
        verbose_name = "Persona Citata"
        verbose_name_plural = "Persone Citate"


class Plaque(models.Model):
    photo = models.FileField(storage=default_storage, blank=True, null=True, verbose_name="Foto")
    photo_link = models.URLField(max_length=256, null=True, blank=True, verbose_name="Link alla foto")
    transcription = models.TextField(max_length=2000, blank=True, null=True, verbose_name="Trascrizione")
    maps_url = models.URLField(max_length=256, null=True, blank=True, verbose_name="Link alla posizione")
    description = models.CharField(max_length=2000, null=True, blank=True, verbose_name="Descrizione")
    latitude = models.FloatField(verbose_name="Latitudine", null=True, blank=True)
    longitude = models.FloatField(verbose_name="Longitidine", null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Inserito da")
    celebrities = models.ManyToManyField(Celebrity, blank=True, verbose_name="Persone Citate")
    place = models.CharField(max_length=2000, null=True, blank=True, verbose_name="Indirizzo/Riferimento")
    date = models.DateTimeField(default=timezone.localtime, verbose_name="Data di inserimento", null=True, blank=True)

    def __str__(self):
        if self.place is not None:
            if self.description is not None:
                return f"{self.description} --- {self.place}"
            if self.desciption is None:
                return self.place
        else:
            if self.description is None:
                return f"Targa {self.id}"

    def get_file_link(self):
        file_name = self.photo.name
        head = {'Authorization': 'Bearer ' + DROPBOX_OAUTH2_TOKEN}
        data = {'path' : f"/{file_name}"}

        url = 'https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings'
        response = requests.post(url, json=data, headers=head)
        try:
            link = response.json()["url"]
        except KeyError:
            try:
                link = response.json()["error"]["shared_link_already_exists"]["metadata"]["url"]
            except KeyError:
                link = "N.D."
                logging.error("", exc_info=True)
        return link

    def get_place(self):
        data = {'lat': self.latitude, 'lon': self.longitude, 'accept-language': "it", "format": "json", "namedetails": 1, "extratags": 1}

        url = 'https://nominatim.openstreetmap.org/reverse'
        try:
            r = requests.post(url, params=data)
            try:
              address = r.json()["address"]
            except: address = ""
            place = ", ".join([address[key] for key in address if key not in ["county", "state", "postcode", "country", "country_code"]])
        except requests.exceptions.HTTPError as err:
            logging.error(err, exc_info=True)
            place = "N.D."
        return place

    class Meta:
        verbose_name = "Targa"
        verbose_name_plural = "Targhe"
