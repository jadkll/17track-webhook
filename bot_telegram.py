import os
import json
import httpx
from telegram import Bot, Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Dispatcher,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    ConversationHandler
)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
SEVENTEENTRACK_TOKEN = os.environ.get("SEVENTEENTRACK_TOKEN")
bot = Bot(token=TOKEN)

dispatcher = Dispatcher(bot, None, workers=1, use_context=True)

# États de la conversation
SUIVI_COMMANDE, AVIS = range(2)

# Chargement du fichier JSON
def charger_suivis():
    if os.path.exists("suivis.json"):
        with open("suivis.json", "r") as f:
            return json.load(f)
    return {}

def enregistrer_suivi(code, user_id):
    suivis = charger_suivis()
    if code not in suivis:
        suivis[code] = {"user_id": user_id}
        with open("suivis.json", "w") as f:
            json.dump(suivis, f, indent=2)

        # Ajouter à l'API 17track
        headers = {
            "17token": SEVENTEENTRACK_TOKEN,
            "Content-Type": "application/json"
        }
        data = {"numbers": [code]}
        httpx.post("https://api.17track.net/track/v2/register", headers=headers, json=data)

def start(update: Update, context: CallbackContext):
    chat_type = update.message.chat.type
    if chat_type != "private":
        update.message.reply_text("Merci de me parler en message privé pour utiliser le bot.")
        return

    boutons = [
        [KeyboardButton("🔥 Voir les best sellers")],
        [KeyboardButton("📝 Passer une commande")],
        [KeyboardButton("📦 Suivre ma commande")],
        [KeyboardButton("💬 Laisser un avis")]
    ]
    reply_markup = ReplyKeyboardMarkup(boutons, resize_keyboard=True)
    update.message.reply_text("Bienvenue ! Choisis une option ci-dessous :", reply_markup=reply_markup)

def recevoir_message(update: Update, context: CallbackContext):
    text = update.message.text

    if text == "📦 Suivre ma commande":
        update.message.reply_text("Bienvenue ! Envoie-moi ton numéro de suivi.")
        return SUIVI_COMMANDE

    elif text == "💬 Laisser un avis":
        update.message.reply_text("Laisse ton avis ici 👇")
        return AVIS

    elif text == "🔥 Voir les best sellers":
        update.message.reply_text("🛍️ Voici nos best sellers :\n1. Produit A\n2. Produit B")

    elif text == "📝 Passer une commande":
        update.message.reply_text("🧾 Pour passer commande, contacte @TonCompteTelegram.")

    else:
        update.message.reply_text("Commande non reconnue. Choisis une option du menu.")

    return ConversationHandler.END

def recevoir_suivi(update: Update, context: CallbackContext):
    code = update.message.text.strip()
    user_id = update.effective_user.id
    enregistrer_suivi(code, user_id)
    update.message.reply_text(f"Ton suivi **{code}** a été enregistré ✅", parse_mode="Markdown")
    return ConversationHandler.END

def recevoir_avis(update: Update, context: CallbackContext):
    avis = update.message.text.strip()
    user = update.effective_user
    print(f"Avis de {user.username or user.id} : {avis}")
    update.message.reply_text("Merci pour ton avis 🙏")
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("Opération annulée.")
    return ConversationHandler.END

# Handler de conversation
conv_handler = ConversationHandler(
    entry_points=[MessageHandler(Filters.text & ~Filters.command, recevoir_message)],
    states={
        SUIVI_COMMANDE: [MessageHandler(Filters.text & ~Filters.command, recevoir_suivi)],
        AVIS: [MessageHandler(Filters.text & ~Filters.command, recevoir_avis)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    per_user=True,
    per_chat=False
)

# Ajout des handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(conv_handler)
