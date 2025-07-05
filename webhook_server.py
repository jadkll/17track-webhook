import os
import json

from fastapi import FastAPI, Request
from bot_telegram import handle_update, commandes, bot

app = FastAPI()

SUIVIS_FILE = "suivis.json"


def sauvegarder_suivi(numero, donnees):
    try:
        if os.path.exists(SUIVIS_FILE):
            with open(SUIVIS_FILE, "r", encoding="utf-8") as f:
                tous_les_suivis = json.load(f)
        else:
            tous_les_suivis = {}
    except json.JSONDecodeError:
        tous_les_suivis = {}

    tous_les_suivis[numero] = donnees

    with open(SUIVIS_FILE, "w", encoding="utf-8") as f:
        json.dump(tous_les_suivis, f, indent=2, ensure_ascii=False)


@app.post("/webhook")
async def telegram_webhook(request: Request):
    payload = await request.json()
    await handle_update(payload)
    return {"status": "ok"}


@app.post("/")
async def recevoir_webhook_17track(request: Request):
    payload = await request.json()
    print("📦 Données reçues :", payload)

    try:
        numero = payload.get("data", {}).get("number")
        track_info = payload.get("data", {}).get("track_info", {})

        if numero and track_info:
            resume = {
                "latest_status": track_info.get("latest_status", {}),
                "latest_event": track_info.get("latest_event", {}),
            }
            sauvegarder_suivi(numero, resume)

            # Notifie utilisateur s'il est connu
            for chat_id, suivi in commandes.items():
                if suivi == numero:
                    message = f"📦 Mise à jour pour {numero} :\n\n📍 {track_info.get('latest_status', {}).get('status_description', 'Nouvelle info')}"
                    bot.send_message(chat_id=chat_id, text=message)

            return {"success": True, "message": f"Suivi {numero} sauvegardé."}
        else:
            return {"success": False, "error": "Numéro ou données manquantes."}
    except Exception as e:
        return {"success": False, "error": str(e)}
