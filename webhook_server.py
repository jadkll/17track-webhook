import os
import json
from fastapi import FastAPI, Request
from bot_telegram.bot import bot  # Ou bot si renommé
from bot_telegram.sheets_utils import ajouter_suivi, maj_suivi, get_user_id

app = FastAPI()

@app.post("/")
async def recevoir_webhook_17track(request: Request):
    payload = await request.json()
    print("📦 Données reçues :", payload)

    try:
        numero = payload.get("data", {}).get("number")
        track_info = payload.get("data", {}).get("track_info", {})
        latest_event = track_info.get("latest_event", {})
        latest_status = track_info.get("latest_status", {})

        if not numero or not track_info:
            return {"success": False, "error": "Numéro ou infos manquants."}

        # --- Enregistrement initial si nécessaire
        enregistrer_suivi(numero, user_id=None)

        # --- Récupération des infos à notifier
        event_entry = {
            "location": latest_event.get("location", "Inconnu"),
            "time": latest_event.get("time", "Inconnu"),
            "description": latest_event.get("description", "Aucune description"),
            "status": latest_status.get("status", "Inconnu"),
        }

        # --- Mise à jour dans Google Sheets
        maj_suivi(numero, event_entry["location"], event_entry["time"], event_entry["description"], event_entry["status"])

        # --- Notification si on connaît le user_id
        user_id = trouver_user_par_numero(numero)
        if user_id:
            msg = (
                f"📦 Mise à jour pour {numero} :\n\n"
                f"📍 {event_entry['location']}\n"
                f"🕒 {event_entry['time']}\n"
                f"📋 {event_entry['description']}"
            )
            try:
                bot.send_message(chat_id=user_id, text=msg)
            except Exception as e:
                print(f"❌ Erreur d'envoi Telegram : {e}")

        return {"success": True, "message": "Suivi mis à jour"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Endpoint pour Telegram Webhook ---
from bot_telegram.bot import handle_update

@app.post("/webhook")
async def telegram_webhook(request: Request):
    payload = await request.json()
    handle_update(payload)
    return {"ok": True}
