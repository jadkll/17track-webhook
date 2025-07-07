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

def ajouter_suivi(numero, user_id):
    sheet.append_row([numero, user_id])
    print(f"✅ Suivi ajouté : {numero} - {user_id}")

def maj_suivi(numero, location, time, description, status):
    cellules = sheet.col_values(1)
    for i, val in enumerate(cellules):
        if val == numero:
            sheet.update_cell(i + 1, 3, location)
            sheet.update_cell(i + 1, 4, time)
            sheet.update_cell(i + 1, 5, description)
            sheet.update_cell(i + 1, 6, status)
            print(f"✅ Suivi mis à jour pour {numero}")
            return
    print(f"⚠️ Numéro {numero} non trouvé dans la feuille")

def get_user_id(numero):
    cellules = sheet.get_all_records()
    for ligne in cellules:
        if ligne.get("numero") == numero:
            return ligne.get("user_id")
    return None
