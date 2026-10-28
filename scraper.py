import json
import os
import urllib.parse
import urllib.request

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

def apply_affiliate_link(url, shop_name=""):
    if not url:
        return "https://duhrrom11.github.io/glitchradar/"
        
    shop_lower = shop_name.lower()
    separator = "&" if "?" in url else "?"
    
    # 1. Amazon PartnerNet (Deine Store-ID: glitchradar03-21)
    if "amazon" in shop_lower:
        if "tag=" not in url:
            return f"{url}{separator}tag=glitchradar03-21"
        return url
        
    # 2. eBay Partner Network (Deine Campaign-ID: 5339233764)
    elif "ebay" in shop_lower:
        if "campid=" not in url:
            return f"{url}{separator}mkeid=1&mkcid=1&campid=5339233764&toolid=10001&customid=glitchradar"
        return url
        
    # 3. Standard Netzwerke (Awin, Admitad etc.)
    else:
        return f"{url}{separator}affid=glitchradar-21"

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
    print("GlitchRadar Multi-Shop Scraper gestartet...")
    
    token = os.environ.get("TELEGRAM_TOKEN")
    private_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    channel_id = os.environ.get("TELEGRAM_CHANNEL_ID")

    existing_products = load_products()
    existing_ids = [p.get("id") for p in existing_products if isinstance(p, dict)]
    
    # Test-Deal mit Amazon (prüft die automatische Tag-Zuweisung)
    sample_deal = {
        "id": "multishop-test-01",
        "title": "Amazon Echo Smart Speaker (Multi-Shop Test)",
        "old_price": 99.99,
        "new_price": 39.99,
        "shop": "Amazon",
        "raw_url": "https://www.amazon.de/dp/B09B8W1LZ9"
    }

    old_p = float(sample_deal["old_price"])
    new_p = float(sample_deal["new_price"])
    discount_percent = int(round((1 - (new_p / old_p)) * 100))

    if discount_percent >= 50 and sample_deal["id"] not in existing_ids:
        # Hier greift nun die neue Multi-Shop Logik mit deinen echten IDs
        final_url = apply_affiliate_link(sample_deal["raw_url"], sample_deal["shop"])
        
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
        print(f"Deal gespeichert: {processed_deal['title']}")

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

            # An privaten Chat senden
            if private_chat_id:
                print(f"Sende an privaten Chat: {private_chat_id}")
                send_telegram_message(private_chat_id, message, token)

            # An den öffentlichen Kanal senden (@glitchradarlive)
            if channel_id:
                print(f"Sende an Kanal: {channel_id}")
                send_telegram_message(channel_id, message, token)
        else:
            print("Kein TELEGRAM_TOKEN gefunden.")
    else:
        print("Deal existiert bereits oder Rabatt unter 50%.")

    print("Scraper beendet.")

if __name__ == "__main__":
    run_scraper()
