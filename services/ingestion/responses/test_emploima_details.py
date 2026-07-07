import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

response = requests.get(
    "https://www.emploi.ma/offre-emploi-maroc/ingenieur-logiciel-tanger-9366454",
    headers=headers,
    timeout=15
)

print("Status:", response.status_code) 

soup = BeautifulSoup(response.text, "html.parser")

# Sauvegarder
with open("emploima_detail.html", "w", encoding="utf-8") as f:
    f.write(response.text)

# Chercher les sections principales
for selector in [
    ".job-description", ".field-job-description",
    "article", ".content", "#content",
    ".field--name-body", ".job-detail"
]:
    el = soup.select_one(selector)
    if el:
        print(f"\nSélecteur '{selector}' trouvé:")
        print(el.text.strip()[:500])
        break

# Chercher ville, contrat, expérience
for label in ["Ville", "Type de contrat", "Expérience", "Secteur", "Fonction"]:
    tag = soup.find(string=lambda t: t and label in t)
    if tag:
        print(f"\n{label}:", tag.parent.text.strip()[:100])

soup = BeautifulSoup(response.text, "html.parser")

# Chercher tous les éléments qui contiennent ces labels
labels = ["Ville", "Type de contrat", "Expérience", "Secteur", "Fonction", "Niveau d'études"]

for label in labels:
    tag = soup.find(string=lambda t: t and label in str(t))
    if tag:
        # Afficher le parent et le parent du parent pour voir la structure
        parent = tag.parent
        grandparent = parent.parent if parent else None
        print(f"\n=== {label} ===")
        print("Parent HTML:")
        print(parent.prettify() if parent else "None")
        print("Grandparent HTML:")
        print(grandparent.prettify()[:300] if grandparent else "None")