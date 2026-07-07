import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Page liste offres informatique
response = requests.get(
    "https://www.emploi.ma/recherche-jobs-maroc/informatique",
    headers=headers,
    timeout=15
)

print("Status:", response.status_code)
print("HTML length:", len(response.text))

# Sauvegarder pour inspecter
with open("emploima_raw.html", "w", encoding="utf-8") as f:
    f.write(response.text)

soup = BeautifulSoup(response.text, "html.parser")

# Chercher les cartes d'offres avec différents sélecteurs
for selector in ["article", "div.job", "li.job", ".job-item", ".offer", "div.card"]:
    elements = soup.select(selector)
    if elements:
        print(f"\nSélecteur '{selector}' → {len(elements)} éléments trouvés")
        print("Premier élément HTML:")
        print(elements[0].prettify()[:1000])
        break
else:
    # Afficher les premières balises du body pour comprendre la structure
    body = soup.find("body")
    print("\nAucun sélecteur standard trouvé. Premiers éléments du body:")
    print(body.prettify()[:2000] if body else "Body non trouvé")