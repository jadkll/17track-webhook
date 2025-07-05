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
    user_id = update.message.from_user.id
    username = f"@{update.message.from_user.username}" if update.message.from_user.username else str(user_id)
    numero_suivi = update.message.text.strip()

    if not numero_suivi or len(numero_suivi) < 8:
        update.message.reply_text("❌ Le numéro de suivi semble invalide.")
        return ConversationHandler.END

    commandes[user_id] = numero_suivi
    utilisateur_topic[user_id] = update.effective_chat.id
    topic_id = utilisateur_topic.get(user_id)
    vendeur_id = vendeurs_par_topic.get(topic_id)

    if vendeur_id:
        context.bot.send_message(chat_id=vendeur_id, text=f"📦 {username} a demandé un suivi pour : {numero_suivi}")

    update.message.reply_text("🔁 Suivi en cours. Tu recevras une notification dès qu’on a du nouveau !")

    # ⏩ Appel API 17track pour activer le suivi
    asyncio.create_task(enregistrer_sur_17track(numero_suivi))

    return ConversationHandler.END

def save_tracking(chat_id, tracking_number):
    with open(suivis_file, "r") as f:
        data = json.load(f)
    data[str(chat_id)] = {"tracking_number": tracking_number, "last_status": ""}
    with open(suivis_file, "w") as f:
        json.dump(data, f, indent=2)
        
import httpx
import asyncio

async def enregistrer_sur_17track(numero):
    headers = {
        "17token": os.getenv("SEVENTEENTRACK_TOKEN"),
        "Content-Type": "application/json"
    }
    payload = {
        "number": numero
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("https://api.17track.net/trackings/post", json=payload, headers=headers)
            print("📡 Envoi à 17track:", response.status_code, response.text)
    except Exception as e:
        print("❌ Erreur API 17track:", e)

