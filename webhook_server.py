from fastapi import FastAPI, Request
import threading
import json
import os
import bot_telegram  # Ton fichier renommé correctement

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

@app.post("/")
async def recevoir_webhook(request: Request):
    payload = await request.json()
    print("📦 Données reçues :", payload)

    try:
        numero = payload.get("data", {}).get("number")
        track_info = payload.get("data", {}).get("track_info", {})

        if numero and track_info:
            resume = {
                "latest_status": track_info.get("latest_status", {}),
                "latest_event": track_info.get("latest_event", {})
            }
            sauvegarder_suivi(numero, resume)
            return {"success": True, "message": f"Suivi {numero} sauvegardé."}
        else:
            return {"success": False, "error": "Numéro ou données manquantes."}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.on_event("startup")
def startup_event():
    threading.Thread(target=bot_telegram.main, daemon=True).start()
