import json
import os

DATA_FILE = "data/products.json"

def load_products():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_products(products):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

def run_scraper():
    print("GlitchRadar Scraper gestartet...")

    # Hier binden wir später die echten Affiliate-Feeds ein.
    # Für den Test simulieren wir einen gefundenen Preisfehler (>50% Rabatt):
    sample_deal = {
        "id": "test-deal-01",
        "title": "High-End OLED Gaming Monitor (Preisfehler)",
        "old_price": 999.00,
        "new_price": 399.00,
        "discount": 60,
        "shop": "TechStore Test",
        "url": "https://example.com"
    }

    products = load_products()

    # Prüfen, ob der Deal schon da ist (Deduplizierung)
    existing_ids = [p["id"] for p in products]
    if sample_deal["id"] not in existing_ids:
        products.insert(0, sample_deal)  # Neuer Deal nach oben
        print(f"Neuen Deal hinzugefügt: {sample_deal['title']}")
    else:
        print("Deal existiert bereits.")

    save_products(products)
    print("Scraper erfolgreich beendet.")

if __name__ == "__main__":
    run_scraper()
