import os
import json
import asyncio
import httpx

from telegram import Update, Bot
from telegram.ext import (
    Dispatcher,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    ConversationHandler,
)

TOKEN = os.environ.get("TELEGRAM_TOKEN", "YOUR_TOKEN_HERE")
bot = Bot(token=TOKEN)

SUIVI_COMMANDE = range(1)
suivis_file = "suivis.json"

if not os.path.exists(suivis_file):
    with open(suivis_file, "w") as f:
        json.dump({}, f)

commandes = {}  # user_id -> tracking_number


async def enregistrer_sur_17track(numero):
    headers = {
        "17token": os.getenv("SEVENTEENTRACK_TOKEN"),
        "Content-Type": "application/json",
    }
    payload = {"number": numero}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.17track.net/trackings/post", json=payload, headers=headers
            )
            print("📡 Envoi à 17track:", response.status_code, response.text)
    except Exception as e:
        print("❌ Erreur API 17track:", e)


def save_tracking(chat_id, tracking_number):
    with open(suivis_file, "r") as f:
        data = json.load(f)
    data[str(chat_id)] = {"tracking_number": tracking_number, "last_status": ""}
    with open(suivis_file, "w") as f:
        json.dump(data, f, indent=2)


def start(update: Update, context: CallbackContext):
    update.message.reply_text("Bienvenue ! Envoie-moi ton numéro de suivi.")
    return SUIVI_COMMANDE


def recevoir_suivi(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    numero = update.message.text.strip()

    if not numero or len(numero) < 8:
        update.message.reply_text("❌ Numéro invalide.")
        return ConversationHandler.END

    commandes[chat_id] = numero
    update.message.reply_text("✅ Suivi enregistré ! Tu seras notifié dès qu'on a une mise à jour.")

    save_tracking(chat_id, numero)
    asyncio.create_task(enregistrer_sur_17track(numero))

    return ConversationHandler.END


def setup_dispatcher(dispatcher: Dispatcher):
    dispatcher.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={SUIVI_COMMANDE: [MessageHandler(Filters.text & ~Filters.command, recevoir_suivi)]},
            fallbacks=[],
        )
    )


async def handle_update(update_json):
    update = Update.de_json(update_json, bot)
    dispatcher = Dispatcher(bot, None, workers=0, use_context=True)
    setup_dispatcher(dispatcher)
    dispatcher.process_update(update)
