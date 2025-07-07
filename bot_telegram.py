import os
import json
from fastapi import FastAPI, Request
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Dispatcher, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from telegram.utils.request import Request as TGRequest
import httpx

# --- Configurations ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
SEVENTEENTRACK_TOKEN = os.environ.get("SEVENTEENTRACK_TOKEN")
HEADERS = {"17token": SEVENTEENTRACK_TOKEN, "Content-Type": "application/json"}

bot = Bot(token=TELEGRAM_TOKEN, request=TGRequest())
dispatcher = Dispatcher(bot, None, workers=1, use_context=True)
app = FastAPI()

# --- Fichier de stockage suivi ---
SUIVIS_FILE = "suivis.json"

def load_suivis():
    if not os.path.exists(SUIVIS_FILE):
        return {}
    with open(SUIVIS_FILE, "r") as f:
        return json.load(f)

def save_suivis(data):
    with open(SUIVIS_FILE, "w") as f:
        json.dump(data, f, indent=2)

# --- Commande /start dans le groupe ---
def start(update: Update, context: CallbackContext):
    if update.message.chat.type in ["group", "supergroup"]:
        keyboard = [
            [InlineKeyboardButton("🔥 Voir les best sellers", callback_data="bestsellers")],
            [InlineKeyboardButton("📝 Passer une commande", callback_data="commande")],
            [InlineKeyboardButton("📦 Suivre ma commande", callback_data="suivi")],
            [InlineKeyboardButton("💬 Laisser un avis", callback_data="avis")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # ✅ Envoie sans répondre au message de l'admin
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Bienvenue ! Choisis une option ci-dessous :",
            reply_markup=reply_markup,
            reply_to_message_id=None  # Évite de répondre au message /start
        )

# --- Callback des boutons ---
def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    try:
        query.answer()  # Répond immédiatement pour éviter l'erreur de timeout

        if query.data == "suivi":
            bot.send_message(chat_id=user_id, text="📦 Envoie-moi ton numéro de suivi ici.")
        elif query.data == "avis":
            bot.send_message(chat_id=user_id, text="💬 Tu peux laisser ton avis ici, merci !")
        elif query.data == "bestsellers":
            bot.send_message(chat_id=user_id, text="🔥 Nos best sellers sont :\n1. Produit A\n2. Produit B")
        elif query.data == "commande":
            bot.send_message(chat_id=user_id, text="📝 Pour passer commande, suis ce lien : https://tonsite.com")
    except Exception as e:
        print("❌ Erreur callback:", e)

# --- Réception du numéro de suivi en DM ---
def handle_message(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    tracking_number = update.message.text.strip().upper()

    suivis = load_suivis()

    # ✅ Si le numéro existe déjà dans la base
    if tracking_number in suivis:
        suivis[tracking_number]["user_id"] = user_id  # Met à jour l'association
        save_suivis(suivis)

        latest_status = suivis[tracking_number].get("latest_status", {})
        latest_event = suivis[tracking_number].get("latest_event", {})

        status = latest_status.get("status", "Inconnu")
        location = latest_event.get("location", "Inconnu")
        time = latest_event.get("time", "Inconnu")
        description = latest_event.get("description", "Aucune description")

        msg = (
            f"📦 Statut : {status}\n"
            f"🗺️ Lieu : {location}\n"
            f"🕒 Date : {time}\n"
            f"📝 {description}\n\n"
            "✅ Tu recevras automatiquement les prochaines mises à jour ici."
        )
        update.message.reply_text(msg)

    # ❌ Si le numéro est encore inconnu
    else:
        suivis[tracking_number] = {"user_id": user_id}
        save_suivis(suivis)

        update.message.reply_text(
            "🔍 Le numéro a bien été enregistré, mais il n’y a pas encore d’information disponible.\n"
            "📬 Tu recevras les mises à jour automatiquement ici dès qu’on en aura."
        )

# --- Dispatcher handlers ---
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CallbackQueryHandler(handle_callback))
dispatcher.add_handler(MessageHandler(Filters.private & Filters.text, handle_message))

# --- Fonction appelée depuis webhook_server ---
def handle_update(payload):
    update = Update.de_json(payload, bot)
    dispatcher.process_update(update)
