# test_rekrute_check.py
import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

response = requests.get(
    "https://www.rekrute.com/offres.html?s=3&lang=fr&p=1",
    headers=headers,
    timeout=15
)

soup = BeautifulSoup(response.text, "html.parser")

# Vérifier li.post-id
cards = soup.find_all("li", class_="post-id")
print(f"li.post-id trouvés : {len(cards)}")

if cards:
    first = cards[0]
    print("\n--- Premier card HTML ---")
    print(first.prettify()[:4000])