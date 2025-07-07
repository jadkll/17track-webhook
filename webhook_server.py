import os
import json
from fastapi import FastAPI, Request
from bot_telegram import bot

app = FastAPI()
SUIVIS_FILE = "suivis.json"

# --- Charger les suivis ---
def charger_suivis():
    if os.path.exists(SUIVIS_FILE):
        try:
            with open(SUIVIS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

# --- Sauvegarder les suivis ---
def sauvegarder_suivis(data):
    with open(SUIVIS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# --- Endpoint Webhook 17TRACK ---
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

        suivis = charger_suivis()

        # Initialisation si nouveau
        if numero not in suivis:
            suivis[numero] = {
                "user_id": None,
                "history": []
            }

        # Ajouter à l'historique si c'est un nouvel événement
        event_entry = {
            "time": latest_event.get("time"),
            "location": latest_event.get("location"),
            "description": latest_event.get("description"),
            "status": latest_status.get("status"),
            "status_description": latest_status.get("status_description")
        }

        if event_entry not in suivis[numero]["history"]:
            suivis[numero]["history"].append(event_entry)

            # ✅ Notifier l'utilisateur s'il est connu
            user_id = suivis[numero].get("user_id")
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

        sauvegarder_suivis(suivis)
        return {"success": True, "message": "Suivi mis à jour"}
    except Exception as e:
        return {"success": False, "error": str(e)}

from bot_telegram import handle_update

@app.post("/webhook")
async def telegram_webhook(request: Request):
    payload = await request.json()
    handle_update(payload)
    return {"ok": True}

