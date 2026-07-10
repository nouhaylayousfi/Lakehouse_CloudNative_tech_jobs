import os 
from dotenv import load_dotenv 

load_dotenv()

#Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"

#France Travail 
FT_CLIENT_ID = os.getenv("FT_CLIENT_ID")
FT_CLIENT_SECRET = os.getenv("FT_CLIENT_SECRET")
FT_TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=%2Fpartenaire"
FT_API_BASE  = "https://api.francetravail.io/partenaire/offresdemploi/v2"
FT_SCOPE = "api_offresdemploiv2 o2dsoffre"

#Rekrute 
REKRUTE_BASE_URL   = "https://www.rekrute.com"
REKRUTE_SEARCH_URL = "https://www.rekrute.com/offres.html?s=3&lang=fr"

#Adzuna
ADZUNA_APP_ID   = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY  = os.getenv("ADZUNA_APP_KEY")
ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs"

# Emploi.ma
EMPLOIMA_BASE_URL = "https://www.emploi.ma"
EMPLOIMA_SEARCH_URL = "https://www.emploi.ma/recherche-jobs-maroc/informatique"

#Hellowork
HELLOWORK_BASE_URL      = "https://www.hellowork.com"
HELLOWORK_SEARCH_URL    = "https://www.hellowork.com/fr-fr/emploi/recherche.html?k=informatique&l=France"
HELLOWORK_SEARCH_KEYWORD = "informatique"


# APIFY
APIFY_API_TOKEN      = os.getenv("APIFY_API_TOKEN")
APIFY_INDEED_ACTOR   = "misceres~indeed-scraper"

# Tech keywords to search 
TECH_KEYWORDS = [
    "data engineer",
    "data scientist",
    "python developer",
    "devops",
    "cloud engineer",
    "machine learning",
    "fullstack developer",
    "backend developer",
    "software engineer",
]