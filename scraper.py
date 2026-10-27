import json
import os
import urllib.request
import urllib.parse

DATA_FILE = "data/products.json"

def load_products():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_products(products):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

def send_telegram_alert(deal):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("Hinweis: Telegram Secrets sind noch nicht hinterlegt (überspringe Push).")
        return

    # Reiner Text ohne fehleranfälliges Markdown (verhindert HTTP 400 Fehler)
    message = (
        f"🚨 NEUE PREISANOMALIE ENTDECKT!\n\n"
        f"Titel: {deal['title']}\n"
        f"🔥 Rabatt: {deal['discount']}%\n"
        f"💰 Preis: {deal['new_price']:.2f} € (statt ~{deal['old_price']:.2f} €)\n"
        f"🏪 Shop: {deal['shop']}\n\n"
        f"Direkt zum Deal: {deal['url']}"
    )
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    
    data = urllib.parse.urlencode(payload).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req) as response:
            print("Telegram Push erfolgreich gesendet!")
    except Exception as e:
        print(f"Fehler beim Senden der Telegram-Nachricht: {e}")

def run_scraper():
    print("GlitchRadar Scraper gestartet...")
    
    sample_deal = {
        "id": "test-deal-telegram-03",
        "title": "High-End OLED Gaming Monitor (Preisfehler)",
        "old_price": 999.00,
        "new_price": 399.00,
        "discount": 60,
        "shop": "TechStore Test",
        "url": "https://duhrrom11.github.io/glitchradar/"
    }

    products = load_products()
    existing_ids = [p.get("id") for p in products if isinstance(p, dict)]
    
    if sample_deal["id"] not in existing_ids:
        products.insert(0, sample_deal)
        save_products(products)
        print(f"Neuen Deal hinzugefügt: {sample_deal['title']}")
        send_telegram_alert(sample_deal)
    else:
        print("Deal existiert bereits.")

    print("Scraper erfolgreich beendet.")

if __name__ == "__main__":
    run_scraper()
