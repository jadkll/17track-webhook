import json
import os
from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram.ext import ConversationHandler
import httpx

TOKEN = os.environ.get("TELEGRAM_TOKEN", "YOUR_TOKEN_HERE")
bot = Bot(token=TOKEN)

suivis_file = "suivis.json"
if not os.path.exists(suivis_file):
    with open(suivis_file, "w") as f:
        json.dump({}, f)

SUIVI_COMMANDE, AVIS = range(2)

async def handle_update(update_json):
    update = Update.de_json(update_json, bot)
    dispatcher = Dispatcher(bot, None, workers=0, use_context=True)
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(ConversationHandler(
        entry_points=[MessageHandler(Filters.text & ~Filters.command, recevoir_suivi)],
        states={SUIVI_COMMANDE: [MessageHandler(Filters.text & ~Filters.command, recevoir_suivi)]},
        fallbacks=[],
    ))
    dispatcher.process_update(update)

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Bienvenue ! Envoie-moi ton numéro de suivi.")

def recevoir_suivi(update: Update, context: CallbackContext):
    tracking_number = update.message.text.strip()
    chat_id = update.message.chat.id
    save_tracking(chat_id, tracking_number)
    update.message.reply_text(f"Ton numéro {tracking_number} a été enregistré.")

def save_tracking(chat_id, tracking_number):
    with open(suivis_file, "r") as f:
        data = json.load(f)
    data[str(chat_id)] = {"tracking_number": tracking_number, "last_status": ""}
    with open(suivis_file, "w") as f:
        json.dump(data, f, indent=2)
