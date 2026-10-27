import csv
import io
import json
import os
import urllib.parse
import urllib.request

DATA_FILE = "data/products.json"
AFFILIATE_TAG = "glitchradar-21"  # Deine persönliche Affiliate-ID[span_3](start_span)[span_3](end_span)

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
    if not url:
        return "https://duhrrom11.github.io/glitchradar/"
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}affid={AFFILIATE_TAG}"

def send_telegram_broadcast(deal):
    token = os.environ.get("TELEGRAM_TOKEN")
    private_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    channel_id = os.environ.get("TELEGRAM_CHANNEL_ID")
    
    if not token:
        return

    # Edler Text für den öffentlichen Kanal & Push
    message = (
        f"🚨 PREISANOMALIE ENTDECKT!\n\n"
        f"📦 {deal['title']}\n"
        f"🔥 Rabatt: -{deal['discount']}%\n"
        f"💰 Neuer Preis: {deal['new_price']:.2f} € (statt ~{deal['old_price']:.2f} €)\n"
        f"🏪 Shop: {deal['shop']}\n\n"
        f"👉 Direkt zum Deal: {deal['url']}\n\n"
        f"⚡ Mehr Fehler auf: https://duhrrom11.github.io/glitchradar/"
    )

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    # 1. An dich privat senden (optional zur Kontrolle)
    if private_chat_id:
        try:
            payload = {"chat_id": private_chat_id, "text": message}
            data = urllib.parse.urlencode(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, method="POST")
            urllib.request.urlopen(req)
        except Exception as e:
            print(f"Privater Push Fehler: {e}")

    # 2. In den öffentlichen Kanal broadcasten (Traffic-Loop)[span_4](start_span)[span_4](end_span)
    if channel_id:
        try:
            payload = {"chat_id": channel_id, "text": message}
            data = urllib.parse.urlencode(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, method="POST")
            with urllib.request.urlopen(req) as response:
                print("Erfolgreich in den Telegram-Kanal gepostet!")
        except Exception as e:
            print(f"Kanal Broadcast Fehler: {e}")

def run_scraper():
    print("GlitchRadar Traffic-Loop Scraper gestartet...")
    
    existing_products = load_products()
    existing_ids = [p.get("id") for p in existing_products if isinstance(p, dict)]
    
    # Test-Anomalie für den Kanal-Loop
    incoming_items = [
        {
            "id": "channel-loop-test-01",
            "title": "High-End OLED Gaming Monitor 4K (Preisfehler-Test)",
            "old_price": 999.00,
            "new_price": 399.00,
            "shop": "GlitchTech Store",
            "raw_url": "https://duhrrom11.github.io/glitchradar/"
        }
    ]

    new_found_count = 0

    for item in incoming_items:
        old_p = float(item["old_price"])
        new_p = float(item["new_price"])
        discount_percent = int(round((1 - (new_p / old_p)) * 100))
        
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
            print(f"Neuer Deal gefunden: {processed_deal['title']}")
            
            # Broadcast in den Kanal auslösen!
            send_telegram_broadcast(processed_deal)
            new_found_count += 1

    if new_found_count > 0:
        save_products(existing_products)
        print("Produkte gespeichert.")
    else:
        print("Keine neuen Deals.")

    print("Scraper beendet.")

if __name__ == "__main__":
    run_scraper()
