from fastapi import FastAPI, Request
import uvicorn
import os

app = FastAPI()

@app.post("/")
async def webhook(request: Request):
    payload = await request.json()
    print("📦 Données reçues :", payload)
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
