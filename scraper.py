import json
import os
import urllib.request
import urllib.parse

DATA_FILE = "data/products.json"
AFFILIATE_TAG = "glitchradar-21"  # Hier trägst du später deine echte Awin/SuperClix ID ein

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

def apply_affiliate_link(url):
    """Fügt automatisch die Affiliate-Tracking-ID an den Shop-Link an[span_5](start_span)[span_5](end_span)."""
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}affid={AFFILIATE_TAG}"

def send_telegram_alert(deal):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("Hinweis: Telegram Secrets sind nicht hinterlegt.")
        return

    message = (
        f"🚨 NEUE PREISANOMALIE ENTDECKT!\n\n"
        f"Titel: {deal['title']}\n"
        f"🔥 Rabatt: {deal['discount']}%\n"
        f"💰 Preis: {deal['new_price']:.2f} € (statt ~{deal['old_price']:.2f} €)\n"
        f"🏪 Shop: {deal['shop']}\n\n"
        f"Direkt zum Deal: {deal['url']}"
    )
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    
    data = urllib.parse.urlencode(payload).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req) as response:
            print("Telegram Push erfolgreich gesendet!")
    except Exception as e:
        print(f"Fehler beim Senden der Telegram-Nachricht: {e}")

def run_scraper():
    print("GlitchRadar Multi-Shop Scraper gestartet...")
    
    # Beispiel für eintreffende Rohdaten aus verschiedenen Shop-Feeds
    raw_incoming_feeds = [
        {
            "id": "feed-item-101",
            "title": "UltraWide Curved Gaming Display 34 Zoll",
            "old_price": 799.00,
            "new_price": 299.00,
            "shop": "ElectroWorld",
            "raw_url": "https://example.com/product101"
        },
        {
            "id": "feed-item-102",
            "title": "Standard USB-Kabel 1m",
            "old_price": 10.00,
            "new_price": 9.00,
            "shop": "CableShop",
            "raw_url": "https://example.com/product102"
        },
        {
            "id": "feed-item-103",
            "title": "Professional Carbon Drone 4K",
            "old_price": 1299.00,
            "new_price": 499.00,
            "shop": "SkyTech Global",
            "raw_url": "https://example.com/product103"
        }
    ]

    existing_products = load_products()
    existing_ids = [p.get("id") for p in existing_products if isinstance(p, dict)]
    
    new_found_count = 0

    for item in raw_incoming_feeds:
        old_p = item["old_price"]
        new_p = item["new_price"]
        
        # Rabatt berechnen
        discount_percent = int(round((1 - (new_p / old_p)) * 100))
        
        # Harten Filter anwenden: Nur Deals mit >= 50% Rabatt[span_6](start_span)[span_6](end_span)
        if discount_percent >= 50 and item["id"] not in existing_ids:
            
            # Affiliate Deep-Linking anwenden[span_7](start_span)[span_7](end_span)
            final_url = apply_affiliate_link(item["raw_url"])
            
            processed_deal = {
                "id": item["id"],
                "title": item["title"],
                "old_price": old_p,
                "new_price": new_p,
                "discount": discount_percent,
                "shop": item["shop"],
                "url": final_url
            }
            
            existing_products.insert(0, processed_deal)
            print(f"Anomalie erkannt & verarbeitet: {processed_deal['title']} (-{discount_percent}%)")
            
            # Push-Benachrichtigung senden
            send_telegram_alert(processed_deal)
            new_found_count += 1

    if new_found_count > 0:
        save_products(existing_products)
        print(f"{new_found_count} neue Anomalien erfolgreich in Datenbank gespeichert.")
    else:
        print("Keine neuen Anomalien über 50% Rabatt gefunden.")

    print("Scraper erfolgreich beendet.")

if __name__ == "__main__":
    run_scraper()

