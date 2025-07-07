import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURATION ---
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")  # ← remplace par le chemin vers le fichier .json
SPREADSHEET_ID = "1H9b6LMqhQi07_FzGzbeRz3qg5TE5AxlEeXqwy8nOjnw"  # ← remplace par l'ID (dans l'URL de ta Google Sheet)

# --- INITIALISATION ---
credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
gc = gspread.authorize(credentials)
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1  # On suppose que tu veux la première feuille

# --- FONCTIONS UTILISABLES ---
def ajouter_suivi(numero, user_id):
    lignes = sheet.get_all_records()
    for ligne in lignes:
        if ligne["numero"] == numero:
            return  # Numéro déjà présent

    sheet.append_row([numero, str(user_id), "", "", "", ""])  # Ajoute une ligne vide prête à être remplie

def mettre_a_jour_suivi(numero, location, time, description, status):
    lignes = sheet.get_all_records()
    for i, ligne in enumerate(lignes):
        if ligne["numero"] == numero:
            row = i + 2  # +2 car la première ligne est l'en-tête
            sheet.update(f"C{row}:G{row}", [[location, time, description, status, "OK"]])
            break

def get_user_id(numero):
    lignes = sheet.get_all_records()
    for ligne in lignes:
        if ligne["numero"] == numero:
            return ligne["user_id"]
    return None
