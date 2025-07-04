from fastapi import FastAPI, Request
import httpx
import json
import os
from datetime import datetime

# --- Config ---
TOKEN = "7730051219:AAEX9y8dky-PobSLBiAATD8bIPBlbLQRebE"
API_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
DATA_FILE = "data.json"

# Mapping topic_id -> vendeur_user_id
vendeurs_par_topic = {
    -1002493828642: 6258031868,
}

# --- FastAPI setup ---
app = FastAPI()

# --- Utilitaires ---

def sauvegarder_donnees(payload: dict):
    now = datetime.utcnow().isoformat()
    data_entry = {"timestamp": now, "payload": payload}

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = []
    else:
        existing = []

    existing.append(data_entry)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)

def extraire_topic_id(tracking_number: str) -> int:
    return -1002493828642  # à adapter plus tard

def formater_message(data: dict) -> str:
    numero = data.get("number", "❓")
    statut = data.get("track_info", {}).get("latest_status", {}).get("status", "❓")
    desc = data.get("track_info", {}).get("latest_event", {}).get("description", "")
    loc = data.get("track_info", {}).get("latest_event", {}).get("location", "")
    date = data.get("track_info", {}).get("latest_event", {}).get("time_iso", "")

    message = f"📦 Suivi mis à jour :\n\n📮 Numéro : {numero}\n📍 Lieu : {loc}\n🕒 Date : {date}\n🚚 Statut : {statut}\n📝 Détail : {desc}"
    return message

async def envoyer_telegram(user_id: int, message: str):
    async with httpx.AsyncClient() as client:
        await client.post(API_URL, data={
            "chat_id": user_id,
            "text": message,
        })

# --- Endpoint principal ---
@app.post("/")
async def webhook(request: Request):
    payload = await request.json()
    print("📦 Données reçues :", payload)

    # ➕ Sauvegarde dans fichier
    sauvegarder_donnees(payload)

    if payload.get("event") == "TRACKING_UPDATED":
        data = payload.get("data", {})
        topic_id = extraire_topic_id(data.get("number", ""))

        user_id = vendeurs_par_topic.get(topic_id)
        if user_id:
            message = formater_message(data)
            await envoyer_telegram(user_id, message)
        else:
            print(f"❌ Aucun vendeur trouvé pour le topic_id {topic_id}")

    return {"ok": True}
