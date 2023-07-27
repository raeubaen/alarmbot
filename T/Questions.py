import io
from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ConversationHandler, Filters, BaseFilter
from emoji import emojize
from T.models import User, Plaque, Bot
from T.models import Celebrity as CelebrityModel
from django.core.files import File
import logging

def already_checked(chat_id):
    return User.objects.filter(chat_id=chat_id).exists()


class Phone:  # BEFORE ASKING ANY DATA
    def make(self, update, context):
        if already_checked(update.message.chat_id):
            return self.make_new(update, context)  # passes ahead

        update.message.reply_text(
            "Benvenuto nel Bot per la segnalazione delle targhe.\n"
        )
        em1 = emojize(":telephone:", use_aliases=True)
        em2 = emojize(":mobile_phone:", use_aliases=True)
        _contact_button = KeyboardButton(
            text=em1 + " Invia il tuo numero di telefono " + em2, request_contact=True
        )
        _markup = ReplyKeyboardMarkup([[_contact_button]], one_time_keyboard=True)

        update.message.reply_text(
            text="Prima che tu possa inserire una targa dobbiamo controllare che tu sia dei nostri.\n"
            "Inviaci il numero di telefono premendo il tasto in basso.",
            reply_markup=_markup,
        )
        return self.num

    def process(self, update, context):
        chat_id = update.message.chat_id
        try:
            sent_user_id = update.message.contact.user_id
            if sent_user_id == update.message.from_user.id:
                phone = update.message.contact.phone_number
            else:
                raise ValueError("not own number")
        except (AttributeError, ValueError):
            update.message.reply_text(
                "Ritenta, sarai infortunato!"
            )
            return ConversationHandler.END
        #context.bot.send_message(int(Bot.objects.first().admin_id), f"Telefono: {phone}")
        # from phone retrieve DB instance of the Person with that number and adds chat_id to info
        try:
            current_user = User.objects.get(phone__endswith=str(phone))
        except User.DoesNotExist:
            update.message.reply_text(
                ""
                "Il tuo numero non è stato riconosciuto.\n"
                "Mi dispiace ma non puoi interagire con il nostro database.\n"
                "Il tuo numero è stato salvato ed inviato al "
                "Centro Sicurezza Membri per ulteriori controlli. "
                "Buona giornata, skuato camerata.\n"
            )
            return ConversationHandler.END
        except User.MultipleObjectsReturned:
            current_user = User.objects.filter(phone__endswith=phone).first()
            logging.error(f"Il numero {phone} è associato a più utenti.")

        current_user.chat_id = chat_id
        current_user.save()

        return self.make_new(update, context)

    filter = Filters.contact


class Image:
    def make(self, update, context):
        try:
            current_user = User.objects.get(chat_id=update.message.chat_id)
        except User.DoesNotExist:
            logging.error("", exc_info=True)
            update.message.reply_text("C'è stato un problema.\n"
            "Ricomincia la segnalazione inviando un qualunque messaggio.")
            return ConversationHandler.END
        update.message.reply_text(f"Ciao {current_user.name.split(' ')[0]}!\n")
        update.message.reply_text("Dovrai inserire le informazioni nel seguente ordine:\n"
                                "\t - Foto della targa \n"
                                "\t - Informazioni sulla targa \n"
                                "\t - Posizione della targa \n")
        update.message.reply_text("Puoi usare /stop per fermare la procedura, "
          "nel caso in cui hai commesso errori di battitura, "
          "hai sbagliato a inserire la foto o semplicemente "
          "hai cambiato idea o vuoi effettuare la segnalazione in un secondo momento")
        update.message.reply_text("Innanzitutto inviami una foto della targa")
        return self.num

    def process(self, update, context):
        tg_photo = update.message.photo[-1]  # take biggest size
        context.chat_data["photo_file_id"] = tg_photo.file_id

        return self.make_new(update, context)

    filter = Filters.document.image | Filters.photo


class Info:
    def make(self, update, context):
        update.message.reply_text("Inserisci delle info o una trascrizione della targa e invia.")
        return self.num

    def process(self, update, context):
        context.chat_data["Info"] = update.message.text
        return self.make_new(update, context)

    filter = Filters.text


class Celebrity:
    def make(self, update, context):
        update.message.reply_text("Inserisci NOME e COGNOME presenti nella targa e invia.\n"
        "Nel caso in cui ci siano più persone inserisci una descrizione dei nomi \n"
        "(es. CADUTI PRIMA GUERRA MONDIALE, oppure MARTIRI DI KINDU)")
        return self.num

    def process(self, update, context):
        context.chat_data["Cel"] = update.message.text
        return self.make_new(update, context)

    filter = Filters.text


class OnSpotCheck:
    def make(self, update, context):

        _markup = ReplyKeyboardMarkup([["sì"], ["no"]], one_time_keyboard=True)

        update.message.reply_text(
            text="Sei sul posto della targa?\n",
            reply_markup=_markup,
        )
        return self.num

    def process(self, update, context):
        if update.message.text not in ["sì", "no"]: return self.make(update, context)
        context.chat_data["OnSpot"] = True if update.message.text == "sì" else False
        return self.make_new(update, context)

    filter = Filters.text


class Position:
    def make(self, update, context):
        if context.chat_data["OnSpot"]:
          update.message.reply_text(
            "Adesso inserisci la posizione della targa e invia.\n"
            "Premere sul pulsante " + emojize(":paperclip:") + " e selezionare Posizione"
          )
        else:
          update.message.reply_text(
            "Adesso inserisci la posizione della targa (es. 41.844819, 12.448084).\n"
          )

        return self.num

    def process(self, update, context):
        long, lat = 0, 0
        try:
          if context.chat_data["OnSpot"]:
            location = update.message.location
            long = location.longitude
            lat = location.latitude
          else:
            lat, long = update.message.text.split(",")
        except (ValueError, AttributeError): return self.make(update, context)

        maps_url = f"https://www.google.com/maps/place/{lat},{long}"
        user = User.objects.get(chat_id=update.message.chat_id)
        cel = CelebrityModel.objects.get_or_create(anagraphic=context.chat_data["Cel"])[0]
        plaque = Plaque.objects.create(
            latitude=lat,
            longitude=long,
            maps_url=maps_url,
            description=context.chat_data["Info"],
            user=user,
        )
        plaque.celebrities.add(cel)
        buffer = io.BytesIO()
        file_id = context.chat_data["photo_file_id"]
        context.bot.get_file(file_id).download(out=buffer)
        buffer.seek(0)

        # must be fond better solution for 1st argument
        plaque.photo.save(f"{plaque.id}.jpg", File(buffer))
        plaque.photo_link = plaque.get_file_link()
        plaque.place = plaque.get_place()
        plaque.save()
        return self.make_new(update, context)

    filter = Filters.location | Filters.text
