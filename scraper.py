import csv
import io
import json
import os
import urllib.parse
import urllib.request

DATA_FILE = "data/products.json"

# HIER TRÄGST DU SPÄTER DEINEN ECHTEN FEED EIN:
# Sobald du bei Awin oder SuperClix angemeldet bist, bekommst du dort eine Download-URL für den CSV-Feed.
# Für den Test nutzen wir vorerst eine simulierbare Struktur.
FEED_URL = "" 

AFFILIATE_TAG = "glitchradar-21"  # Deine persönliche Publisher-ID

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
    """Fügt vollautomatisch deine Affiliate-Tracking-ID an den Shop-Link an[span_2](start_span)[span_2](end_span)."""
    if not url:
        return "#"
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}affid={AFFILIATE_TAG}"

def send_telegram_alert(deal):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
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
            pass
    except Exception as e:
        print(f"Telegram Fehler: {e}")

def run_scraper():
    print("GlitchRadar Live-Feed-Scraper gestartet...")
    
    existing_products = load_products()
    existing_ids = [p.get("id") for p in existing_products if isinstance(p, dict)]
    
    # Fallback-Daten, falls noch keine echte Feed-URL hinterlegt ist (simuliert echten Händler-Feed)
    incoming_items = []
    
    if FEED_URL:
        try:
            print(ન્દ Lade echten Händler-Feed von URL...")
            response = urllib.request.urlopen(FEED_URL)
            csv_data = response.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(csv_data))
            for row in reader:
                incoming_items.append({
                    "id": row.get("product_id"),
                    "title": row.get("name"),
                    "old_price": float(row.get("retail_price", 0)),
                    "new_price": float(row.get("sale_price", 0)),
                    "shop": row.get("merchant_name"),
                    "raw_url": row.get("deep_link")
                })
        except Exception as e:
            print(f"Fehler beim Abrufen des Feeds: {e}")
    else:
        # Robuster Fallback mit frischen Test-Anomalien, solange die Awin/SuperClix Freigabe läuft
        incoming_items = [
            {
                "id": "live-feed-901",
                "title": "High-End 4K Laser Beamer Home Cinema",
                "old_price": 2499.00,
                "new_price": 999.00,
                "shop": "CineTech Global",
                "raw_url": "https://example.com/beamer"
            },
            {
                "id": "live-feed-902",
                "title": "Ergonomic Gaming Chair Pro",
                "old_price": 399.00,
                "new_price": 149.00,
                "shop": "OfficeSeating Direct",
                "raw_url": "https://example.com/chair"
            }
        ]

    new_found_count = 0

    for item in incoming_items:
        try:
            old_p = float(item["old_price"])
            new_p = float(item["new_price"])
            
            if old_p <= 0 or new_p >= old_p:
                continue

            # Rabatt in Prozent berechnen
            discount_percent = int(round((1 - (new_p / old_p)) * 100))
            
            # Hater Filter: Nur krasse Preisfehler ab >= 50% Rabatt[span_3](start_span)[span_3](end_span)
            if discount_percent >= 50 and item["id"] not in existing_ids:
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
                print(f"Preisfehler entdeckt: {processed_deal['title']} (-{discount_percent}%)")
                send_telegram_alert(processed_deal)
                new_found_count += 1
        except Exception as err:
            print(f"Fehler beim Verarbeiten eines Artikels: {err}")

    if new_found_count > 0:
        save_products(existing_products)
        print(f"{new_found_count} neue Anomalien gespeichert & gepusht.")
    else:
        print("Keine neuen Anomalien über 50% gefunden.")

    print("Scraper erfolgreich beendet.")

if __name__ == "__main__":
    run_scraper()
