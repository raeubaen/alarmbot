from telegram.ext import MessageHandler, Filters, ConversationHandler, CommandHandler
from T.Questions import Phone, Info, Image, Position, OnSpotCheck, Celebrity

# what happens when conversation_handler.END is triggered
def end_conversation(update, context):
    update.message.reply_text(
        "Grazie di aver contribuito al database Membri.\n"
        "Hic nunc et semper!\n"
        "Per inviare un'altra segnalazione inviami un qualunque messaggio"
    )
    update.message.reply_text("======FINE======")
    return ConversationHandler.END


# callback for /stop command
def cancel(update, context):
    update.message.reply_text(
        "Hai fermato la segnalazione. Per ricominciare inviami un qualunque messaggio."
    )
    return ConversationHandler.END


def istances(classes_list):  # makes the conv handler work - connects make, process and new questions
    ist = [cls() for cls in classes_list]
    for i in range(len(ist)):
        ist[i].num = i
        try:
            ist[i].make_new = ist[i + 1].make
        except IndexError:
            ist[i].make_new = end_conversation
    return ist


def states(istances):  # sets the Conversational Handler
    stg = {}
    for ist in istances:
        stg[ist.num] = [
            CommandHandler("stop", cancel),
            MessageHandler(ist.filter, ist.process),
            MessageHandler(~ist.filter, ist.make),
        ]
    return stg


classes_list = [Image, Info, Celebrity, OnSpotCheck, Position]
classes_list.insert(0, Phone)
ist = istances(classes_list)

conv_handler = ConversationHandler(
    entry_points=[MessageHandler(Filters.all, ist[0].make)],
    states=states(ist),
    fallbacks=[CommandHandler("stop", cancel)],
)
