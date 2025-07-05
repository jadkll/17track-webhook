from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (Updater, CommandHandler, CallbackQueryHandler,
                          ConversationHandler, MessageHandler, Filters, CallbackContext)
import json
import os

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

vendeurs_par_topic = {
    -1002493828642: 6258031868,
}

utilisateur_topic = {}
commandes = {}
avis_clients = {}

SUIVI_COMMANDE, AVIS = range(2)

def charger_donnees_suivi():
    try:
        with open("suivis.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def personnaliser_tracking(texte):
    remplacements = {
        "China": "Germany",
        "CN": "DE",
        "Shenzhen": "Berlin",
        "Guangzhou": "Hamburg",
        "Shanghai": "Munich",
        "Yanwen": "DHL",
        "Cainiao": "Hermes",
        "Departed country": "Left Germany",
        "Arrived at destination country": "Arrived in France",
        "Processing": "En cours de traitement",
        "Delivered": "Livré",
    }
    for original, modifie in remplacements.items():
        texte = texte.replace(original, modifie)
    return texte

def get_tracking_status(num_suivi):
    suivis = charger_donnees_suivi()
    info = suivis.get(num_suivi)

    if not info:
        return None

    statut = info.get("latest_status", {}).get("status", "")
    lieu = info.get("latest_event", {}).get("location", "")
    brut = f"Statut : {statut}\nLieu : {lieu}"
    return personnaliser_tracking(brut)

def start(update: Update, context: CallbackContext):
    if update.effective_chat.type in ["group", "supergroup"]:
        keyboard = [
            [InlineKeyboardButton("🔥 Voir les best sellers", callback_data="catalogue")],
            [InlineKeyboardButton("📝 Passer une commande", callback_data="commande")],
            [InlineKeyboardButton("📦 Suivre ma commande", callback_data="suivi")],
            [InlineKeyboardButton("💬 Laisser un avis", callback_data="avis")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Bienvenue ! Choisis une option ci-dessous :",
            reply_markup=reply_markup,
            message_thread_id=update.message.message_thread_id if update.message else None,
            disable_notification=True
        )
    else:
        update.message.reply_text("Salut ! Va dans le topic de ta ville et utilise les boutons pour interagir.")

def bouton_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    username = f"@{query.from_user.username}" if query.from_user.username else str(user_id)

    if query.message:
        utilisateur_topic[user_id] = query.message.chat_id

    if query.data == "catalogue":
        context.bot.send_message(chat_id=user_id, text="🔥 Voici notre flyer avec LE produit du moment !")
        context.bot.send_photo(chat_id=user_id, photo=open("b22_flyer.jpg", "rb"))
    elif query.data == "commande":
        context.bot.send_message(chat_id=user_id, text="📝 Clique ici pour passer ta commande : https://tally.so/r/nPWWeB")
        topic_id = utilisateur_topic.get(user_id)
        vendeur_id = vendeurs_par_topic.get(topic_id)
        if vendeur_id:
            context.bot.send_message(chat_id=vendeur_id, text=f"🛒 {username} a cliqué sur le lien de commande.")
    elif query.data == "suivi":
        context.bot.send_message(chat_id=user_id, text="Merci d’entrer ton numéro de suivi (ex : LB123456789CN) :")
        return SUIVI_COMMANDE
    elif query.data == "avis":
        context.bot.send_message(chat_id=user_id, text="Merci de nous donner ton avis sur ta commande :")
        return AVIS

    return ConversationHandler.END

def recevoir_suivi(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    username = f"@{update.message.from_user.username}" if update.message.from_user.username else str(user_id)
    numero_suivi = update.message.text.strip()

    if not numero_suivi or len(numero_suivi) < 8:
        update.message.reply_text("❌ Le numéro de suivi semble invalide.")
        return ConversationHandler.END

    commandes[user_id] = numero_suivi
    topic_id = utilisateur_topic.get(user_id)
    vendeur_id = vendeurs_par_topic.get(topic_id)

    if vendeur_id:
        context.bot.send_message(chat_id=vendeur_id, text=f"📦 {username} a demandé un suivi pour : {numero_suivi}")

    statut = get_tracking_status(numero_suivi)

    if statut:
        update.message.reply_text("📦 Ton suivi personnalisé :\n\n" + statut)
    else:
        update.message.reply_text("❌ Impossible d'obtenir le suivi pour ce numéro. Réessaie plus tard.")

    return ConversationHandler.END

def recevoir_avis(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    message_avis = update.message.text
    avis_clients[user_id] = message_avis
    topic_id = utilisateur_topic.get(user_id)
    vendeur_id = vendeurs_par_topic.get(topic_id)

    update.message.reply_text("🙏 Merci pour ton retour ! Il sera transmis au vendeur.")

    if vendeur_id:
        context.bot.send_message(chat_id=vendeur_id, text=f"💬 Nouvel avis de @{update.message.from_user.username or user_id} :\n\n{message_avis}")

    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("❌ Annulé.")
    return ConversationHandler.END

def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(bouton_handler)],
        states={
            SUIVI_COMMANDE: [MessageHandler(Filters.text & ~Filters.command, recevoir_suivi)],
            AVIS: [MessageHandler(Filters.text & ~Filters.command, recevoir_avis)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True,
        per_chat=False
    )

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
