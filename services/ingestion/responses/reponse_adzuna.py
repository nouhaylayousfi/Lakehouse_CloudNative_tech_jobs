# test_adzuna_raw.py
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

APP_ID  = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")

# Adzuna France — recherche "data engineer"
response = requests.get(
    "https://api.adzuna.com/v1/api/jobs/fr/search/1",
    params={
        "app_id":         APP_ID,
        "app_key":        APP_KEY,
        "what":           "data engineer",  # mot-clé
        "results_per_page": 1,              # 1 seul résultat pour inspecter
        "content-type":   "application/json",
    },
    timeout=15,
)

print("Status:", response.status_code)
print(json.dumps(response.json(), indent=2, ensure_ascii=False))