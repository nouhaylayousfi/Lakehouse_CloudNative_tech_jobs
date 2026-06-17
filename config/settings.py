import os 
from dotenv import load_dotenv 

load_dotenv()

#France Travail 
FT_CLIENT_ID = os.getenv("FT_CLIENT_ID")
FT_CLIENT_SECRET = os.getenv("FT_CLIENT_SECRET")
FT_TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=%2Fpartenaire"
FT_API_BASE  = "https://api.francetravail.io/partenaire/offresdemploi/v2"
FT_SCOPE = "api_offresdemploiv2 o2dsoffre"

#Rekrute 
REKRUTE_BASE_URL   = "https://www.rekrute.com"
REKRUTE_SEARCH_URL = "https://www.rekrute.com/offres.html?s=3&lang=fr"