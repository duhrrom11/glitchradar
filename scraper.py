import json
import os
import urllib.parse
import urllib.request

DATA_FILE = "data/products.json"
AFFILIATE_TAG = "glitchradar-21"  # Deine persönliche Affiliate-ID

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

def send_telegram_message(chat_id, message, token):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    data = urllib.parse.urlencode(payload).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req) as response:
            print(f"Erfolgreich an {chat_id} gesendet!")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"HTTP Fehler bei {chat_id}: {e.code} - {error_body}")
    except Exception as e:
        print(f"Fehler bei {chat_id}: {e}")

def run_scraper():
    print("GlitchRadar Test-Scraper gestartet...")
    
    token = os.environ.get("TELEGRAM_TOKEN")
    private_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    channel_id = os.environ.get("TELEGRAM_CHANNEL_ID") # Sollte @glitchradarlive sein

    existing_products = load_products()
    existing_ids = [p.get("id") for p in existing_products if isinstance(p, dict)]
    
    # Frischer Test-Deal mit neuer ID für den Kanal-Test
    sample_deal = {
        "id": "channel-test-id-05",
        "title": "High-End OLED Gaming Monitor 4K (Kanal-Test)",
        "old_price": 999.00,
        "new_price": 399.00,
        "shop": "GlitchTech Store",
        "raw_url": "https://duhrrom11.github.io/glitchradar/"
    }

    old_p = float(sample_deal["old_price"])
    new_p = float(sample_deal["new_price"])
    discount_percent = int(round((1 - (new_p / old_p)) * 100))

    if discount_percent >= 50 and sample_deal["id"] not in existing_ids:
        final_url = apply_affiliate_link(sample_deal["raw_url"])
        
        processed_deal = {
            "id": sample_deal["id"],
            "title": sample_deal["title"],
            "old_price": old_p,
            "new_price": new_p,
            "discount": discount_percent,
            "shop": sample_deal["shop"],
            "url": final_url
        }
        
        existing_products.insert(0, processed_deal)
        save_products(existing_products)
        print(f"Test-Deal gespeichert: {processed_deal['title']}")

        if token:
            message = (
                f"🚨 PREISANOMALIE ENTDECKT!\n\n"
                f"📦 {processed_deal['title']}\n"
                f"🔥 Rabatt: -{processed_deal['discount']}%\n"
                f"💰 Neuer Preis: {processed_deal['new_price']:.2f} € (statt ~{processed_deal['old_price']:.2f} €)\n"
                f"🏪 Shop: {processed_deal['shop']}\n\n"
                f"👉 Direkt zum Deal: {processed_deal['url']}\n\n"
                f"⚡ Mehr Fehler auf: https://duhrrom11.github.io/glitchradar/"
            )

            # An privaten Chat senden (falls hinterlegt)
            if private_chat_id:
                print(f"Sende an privaten Chat: {private_chat_id}")
                send_telegram_message(private_chat_id, message, token)

            # An den öffentlichen Kanal senden (@glitchradarlive)
            if channel_id:
                print(f"Sende an öffentlichen Kanal: {channel_id}")
                send_telegram_message(channel_id, message, token)
        else:
            print("Kein TELEGRAM_TOKEN gefunden.")
    else:
        print("Deal existiert bereits oder Rabatt unter 50%.")

    print("Scraper beendet.")

if __name__ == "__main__":
    run_scraper()
