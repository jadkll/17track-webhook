import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURATION ---
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
SPREADSHEET_ID = "1H9b6LMqhQi07_FzGzbeRz3qg5TE5AxlEeXqwy8nOjnw"

# --- Charger les credentials à partir de la variable d'environnement ---
credentials_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
if not credentials_json:
    raise Exception("⚠️ GOOGLE_CREDENTIALS_JSON n'est pas défini dans les variables Render")

credentials_dict = json.loads(credentials_json)
credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, SCOPE)

# --- Google Sheet ---
gc = gspread.authorize(credentials)
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1
