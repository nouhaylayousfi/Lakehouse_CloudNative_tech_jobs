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


# APIFY
APIFY_API_TOKEN      = os.getenv("APIFY_API_TOKEN")
APIFY_INDEED_ACTOR = "misceres~indeed-scraper"

# Tech keywords to search 
TECH_KEYWORDS = [
    # Data
    "data engineer",
    "senior data engineer",
    "junior data engineer",
    "lead data engineer",
    "big data engineer",
    "data architect",
    "data scientist",
    "senior data scientist",
    "junior data scientist",
    "machine learning engineer",
    "ml engineer",
    "ai engineer",
    "genai engineer",
    "llm engineer",
    "analytics engineer",
    "data analyst",
    "business intelligence",
    "bi developer",
    "bi engineer",
    "business intelligence developer",
    "etl developer",
    "etl engineer",
    "data integration engineer",
    "data platform engineer",
    "data ops",
    "dataops engineer",
    "database engineer",
    "database administrator",
    "dba",

    # Software Engineering
    "software engineer",
    "software developer",
    "software architect",
    "application developer",
    "application engineer",

    # Backend
    "backend developer",
    "backend engineer",
    "java developer",
    "python developer",
    "python engineer",
    "c# developer",
    ".net developer",
    "dotnet developer",
    "golang developer",
    "go developer",
    "php developer",
    "node.js developer",
    "nodejs developer",
    "spring boot developer",

    # Frontend
    "frontend developer",
    "front-end developer",
    "frontend engineer",
    "react developer",
    "angular developer",
    "vue developer",
    "javascript developer",
    "typescript developer",

    # Full Stack
    "fullstack developer",
    "full stack developer",
    "full-stack developer",
    "fullstack engineer",

    # Mobile
    "android developer",
    "ios developer",
    "mobile developer",
    "flutter developer",
    "react native developer",

    # Cloud / DevOps
    "cloud engineer",
    "cloud architect",
    "cloud developer",
    "aws engineer",
    "azure engineer",
    "gcp engineer",
    "devops",
    "devops engineer",
    "site reliability engineer",
    "sre",
    "platform engineer",
    "infrastructure engineer",
    "systems engineer",
    "system administrator",
    "linux engineer",

    # Security
    "cybersecurity engineer",
    "security engineer",
    "application security engineer",
    "cloud security engineer",
    "soc analyst",
    "security analyst",
    "penetration tester",
    "ethical hacker",

    # QA
    "qa engineer",
    "qa analyst",
    "quality assurance engineer",
    "test engineer",
    "automation engineer",
    "test automation engineer",
    "sdet",

    # Embedded / Hardware
    "embedded engineer",
    "embedded software engineer",
    "firmware engineer",
    "embedded developer",

    # ERP / CRM
    "sap consultant",
    "sap developer",
    "salesforce developer",
    "crm developer",

    # AI / NLP / CV
    "artificial intelligence engineer",
    "nlp engineer",
    "computer vision engineer",
    "deep learning engineer",
    "research engineer",
    "research scientist",

    # Leadership
    "technical lead",
    "engineering manager",
    "head of engineering",
    "cto"
]