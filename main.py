
from fastapi import FastAPI, Request
import json

app = FastAPI()

@app.post("/")
async def receive_webhook(request: Request):
    data = await request.json()
    print("📦 Données reçues :", json.dumps(data, indent=2))
    return {"message": "Webhook reçu"}
