import json
import os
import urllib.parse
import urllib.request

DATA_FILE = "data/products.json"
ASINS_FILE = "data/asins.json"  # Hier liegen deine hunderten/tausenden zu prüfenden Produkte
AMAZON_TAG = "glitchradar03-21"  # Deine Amazon Store-ID

def load_json(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def apply_amazon_affiliate(asin):
    return f"https://www.amazon.de/dp/{asin}?tag={AMAZON_TAG}"

def send_telegram_message(chat_id, message, token):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    data = urllib.parse.urlencode(payload).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req):
            pass
    except Exception as e:
        print(f"Telegram Fehler: {e}")

def run_scraper():
    print("GlitchRadar Massen-Scraper (Externer Daten-Modus) gestartet...")
    
    token = os.environ.get("TELEGRAM_TOKEN")
    private_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    channel_id = os.environ.get("TELEGRAM_CHANNEL_ID")

    existing_products = load_json(DATA_FILE)
    existing_ids = [p.get("id") for p in existing_products if isinstance(p, dict)]
    
    # Lädt die große Liste aller zu überwachenden Produkte aus einer separaten Datei
    target_deals = load_json(ASINS_FILE)
    
    if not target_deals:
        print("Keine Produkte in 'data/asins.json' gefunden.")
        return

    new_items_added = 0

    for sample_deal in target_deals:
        product_id = sample_deal.get("id")
        if product_id in existing_ids:
            continue

        try:
            old_p = float(sample_deal["old_price"])
            new_p = float(sample_deal["new_price"])
        except (KeyError, ValueError):
            continue

        if old_p <= 0:
            continue

        discount_percent = int(round((1 - (new_p / old_p)) * 100))

        # Filter: Nur Deals ab 50% Rabatt
        if discount_percent >= 50:
            asin = sample_deal.get("asin")
            final_url = apply_amazon_affiliate(asin) if asin else sample_deal.get("url", "https://duhrrom11.github.io/glitchradar/")
            
            processed_deal = {
                "id": product_id,
                "title": sample_deal["title"],
                "old_price": old_p,
                "new_price": new_p,
                "discount": discount_percent,
                "shop": sample_deal.get("shop", "Amazon"),
                "url": final_url
            }
            
            existing_products.insert(0, processed_deal)
            new_items_added += 1
            print(f"Treffer: {processed_deal['title']} (-{discount_percent}%)")

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

                if private_chat_id:
                    send_telegram_message(private_chat_id, message, token)
                if channel_id:
                    send_telegram_message(channel_id, message, token)

    if new_items_added > 0:
        save_json(DATA_FILE, existing_products)
        print(f"{new_items_added} neue Deals erfolgreich verarbeitet und gespeichert.")
    else:
        print("Keine neuen Deals >= 50% Rabatt gefunden.")

if __name__ == "__main__":
    run_scraper()
