import csv
import io
import json
import os
import urllib.parse
import urllib.request

DATA_FILE = "data/products.json"

# Deine Affiliate-IDs & Parameter
EBAY_CAMP_ID = "5339233764"       # eBay Partner Network Campaign-ID
AWIN_AFF_ID = "glitchradar-21"    # Awin Standard Affiliate-ID

def load_json(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_json(filepath, data):
    dir_name = os.path.dirname(filepath)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def apply_affiliate_link(url, shop_name=""):
    if not url:
        return "https://duhrrom11.github.io/glitchradar/"
        
    shop_lower = shop_name.lower()
    separator = "&" if "?" in url else "?"
    
    # eBay Partner Network Tracking
    if "ebay" in shop_lower:
        if "campid=" not in url:
            return f"{url}{separator}mkeid=1&mkcid=1&campid={EBAY_CAMP_ID}&toolid=10001&customid=glitchradar"
        return url
        
    # Awin / Standard Netzwerke
    else:
        if "affid=" not in url:
            return f"{url}{separator}affid={AWIN_AFF_ID}"
        return url

def send_telegram_message(chat_id, message, token):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    data = urllib.parse.urlencode(payload).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req):
            pass
    except Exception as e:
        print(f"Telegram Fehler bei {chat_id}: {e}")

def fetch_ebay_api_deals(api_token):
    """
    Fragt echte Produktdaten über die offizielle eBay Browse API ab 
    und filtert Artikel mit reduzierten Preisen heraus.
    """
    deals = []
    if not api_token:
        print("Kein eBay API Token in den Secrets hinterlegt.")
        return deals
        
    print("Verbinde mit eBay Browse API...")
    
    # Suchbegriffe für den automatisierten Scan auf eBay DE
    keywords = ["grafikkarte", "gaming laptop", "smartphone", "oled monitor", "konsole"]
    
    for kw in keywords:
        try:
            encoded_kw = urllib.parse.quote(kw)
            url = f"https://api.ebay.com/buy/browse/v1/item_summary/search?q={encoded_kw}&limit=10"
            
            req = urllib.request.Request(url, headers={
                'Authorization': f'Bearer {api_token}',
                'X-EBAY-C-MARKETPLACE-ID': 'EBAY_DE',
                'User-Agent': 'Mozilla/5.0'
            })
            
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode('utf-8'))
                items = data.get('itemSummaries', [])
                
                for item in items:
                    title = item.get('title')
                    item_id = item.get('itemId')
                    item_web_url = item.get('itemWebUrl')
                    
                    price_info = item.get('price', {})
                    current_price = float(price_info.get('value', 0))
                    
                    orig_price_info = item.get('originalPrice', {})
                    if orig_price_info:
                        old_p = float(orig_price_info.get('value', 0))
                        new_p = current_price
                        
                        if old_p > 0 and new_p < old_p:
                            deals.append({
                                "id": f"ebay-{item_id}",
                                "title": title,
                                "old_price": old_p,
                                "new_price": new_p,
                                "shop": "eBay",
                                "url": item_web_url
                            })
        except Exception as e:
            print(f"Fehler bei eBay API Abfrage für '{kw}': {e}")
            
    print(f"{len(deals)} Artikel von der eBay API abgerufen.")
    return deals

def fetch_live_feed(feed_url, shop_name):
    """
    Lädt CSV/XML-Feeds direkt von Awin-Händlern herunter.
    """
    try:
        req = urllib.request.Request(feed_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            content = response.read().decode('utf-8', errors='ignore')
            f = io.StringIO(content)
            reader = csv.DictReader(f)
            items = []
            for row in reader:
                items.append({
                    "id": row.get("id") or row.get("sku") or row.get("product_id"),
                    "title": row.get("title") or row.get("name"),
                    "old_price": row.get("old_price") or row.get("rrp") or row.get("price_old"),
                    "new_price": row.get("new_price") or row.get("price") or row.get("price_current"),
                    "shop": shop_name,
                    "url": row.get("url") or row.get("link")
                })
            return items
    except Exception as e:
        print(f"Fehler beim Laden des Feeds für {shop_name}: {e}")
        return []

def run_scraper():
    print("GlitchRadar Awin & eBay Scraper gestartet...")
    
    token = os.environ.get("TELEGRAM_TOKEN")
    private_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    channel_id = os.environ.get("TELEGRAM_CHANNEL_ID")
    ebay_api_token = os.environ.get("EBAY_API_TOKEN")

    existing_products = load_json(DATA_FILE)
    existing_ids = [p.get("id") for p in existing_products if isinstance(p, dict)]
    
    all_incoming_deals = []

    # 1. eBay API Produkte einlesen
    ebay_items = fetch_ebay_api_deals(ebay_api_token)
    all_incoming_deals.extend(ebay_items)

    # 2. Awin Live-Feeds einlesen
    live_feed_sources = [
        # {"url": "HIER_AWIN_FEED_URL_EINTRAGEN", "shop": "Alternate"}
    ]

    for source in live_feed_sources:
        feed_items = fetch_live_feed(source["url"], source["shop"])
        all_incoming_deals.extend(feed_items)

    if not all_incoming_deals:
        print("Keine neuen Produkte zum Verarbeiten gefunden.")
        return

    new_items_added = 0
    print(f"Prüfe {len(all_incoming_deals)} Produkte auf Preisfehler...")

    for sample_deal in all_incoming_deals:
        product_id = sample_deal.get("id")
        if not product_id or product_id in existing_ids:
            continue

        try:
            old_p = float(sample_deal["old_price"])
            new_p = float(sample_deal["new_price"])
        except (KeyError, ValueError, TypeError):
            continue

        if old_p <= 0 or new_p >= old_p:
            continue

        discount_percent = int(round((1 - (new_p / old_p)) * 100))

        # Filter: Nur Preisanomalien ab 50% Rabatt
        if discount_percent >= 50:
            shop_name = sample_deal.get("shop", "eBay")
            raw_url = sample_deal.get("url")
            
            final_url = apply_affiliate_link(raw_url, shop_name)
            
            processed_deal = {
                "id": str(product_id),
                "title": sample_deal.get("title", "Unbekanntes Produkt"),
                "old_price": old_p,
                "new_price": new_p,
                "discount": discount_percent,
                "shop": shop_name,
                "url": final_url
            }
            
            existing_products.insert(0, processed_deal)
            existing_ids.append(str(product_id))
            new_items_added += 1
            print(f"🚨 Preisanomalie ({shop_name}): {processed_deal['title']} (-{discount_percent}%)")

            if token:
                message = (
                    f"🚨 *PREISANOMALIE ENTDECKT!*\n\n"
                    f"📦 *{processed_deal['title']}*\n"
                    f"🔥 Rabatt: *{processed_deal['discount']}%*\n"
                    f"💰 Preis: *{processed_deal['new_price']:.2f} €* (statt ~{processed_deal['old_price']:.2f} €)\n"
                    f"🏪 Shop: {processed_deal['shop']}\n\n"
                    f"[Zum Deal]({processed_deal['url']})"
                )

                if private_chat_id:
                    send_telegram_message(private_chat_id, message, token)
                if channel_id:
                    send_telegram_message(channel_id, message, token)

    if new_items_added > 0:
        save_json(DATA_FILE, existing_products)
        print(f"{new_items_added} neue Deals gespeichert und publiziert.")
    else:
        print("Scraper beendet: Keine neuen Deals >= 50% gefunden.")

if __name__ == "__main__":
    run_scraper()
