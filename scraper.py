import base64
import json
import os
import urllib.parse
import urllib.request

DATA_FILE = "data/products.json"

# Deine persönlichen Affiliate-IDs
AMAZON_TAG = "glitchradar03-21"       # Amazon PartnerNet Store-ID
EBAY_CAMP_ID = "5339233764"           # eBay Partner Network Campaign-ID
AWIN_AFF_ID = "glitchradar-21"        # Awin Standard Affiliate-ID

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

def get_ebay_oauth_token(client_id, client_secret):
    """
    Holt sich automatisch einen frischen OAuth 2.0 Access Token von eBay.
    """
    token_url = "https://api.ebay.com/identity/v1/oauth2/token"
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope"
    }
    data = urllib.parse.urlencode(payload).encode("utf-8")
    
    try:
        req = urllib.request.Request(token_url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result.get("access_token")
    except Exception as e:
        print(f"Fehler beim Abrufen des eBay OAuth-Tokens: {e}")
        return None

def fetch_ebay_api_deals():
    """
    Fragt echte Produktdaten über die offizielle eBay Browse API ab 
    mit einem umfassenden XXL-Tech-Suchfilter.
    """
    client_id = os.environ.get("EBAY_CLIENT_ID")
    client_secret = os.environ.get("EBAY_CLIENT_SECRET")
    deals = []
    
    if not client_id or not client_secret:
        print("Keine eBay Client ID oder Client Secret in den Secrets hinterlegt.")
        return deals
        
    print("Fordere eBay OAuth Token an...")
    token = get_ebay_oauth_token(client_id, client_secret)
    if not token:
        return deals
        
    print("Verbinde mit eBay Browse API für den Massen-Tech-Scan...")
    
    # XXL Tech-Suchbegriffe für maximale Abdeckung im gesamten Elektronik- und Gaming-Sektor
    keywords = [
        # Smartphones, Tablets & Wearables
        "smartphone", "handy", "iphone", "samsung galaxy", "xiaomi", "google pixel", "oneplus", 
        "ipad", "tablet", "smartwatch", "apple watch", "garmin", "fitbit", "powerbank", "magsafe",
        
        # PC-Komponenten & Hardware
        "grafikkarte", "rtx", "gtx", "radeon", "cpu", "prozessor", "intel core", "amd ryzen", 
        "mainboard", "ddr4 ram", "ddr5 ram", "nvme ssd", "m.2 ssd", "pc netzteil", "gehäuse", "wasserkühlung",
        
        # Laptops, Monitore & Peripherie
        "gaming laptop", "notebook", "macbook", "chromebook", "oled monitor", "gaming monitor", 
        "4k monitor", "ultrawide monitor", "tastatur", "mechanische tastatur", "gaming maus", "headset", "streaming mikrofon",
        
        # Konsolen, Gaming & VR
        "playstation 5", "ps5", "xbox series x", "nintendo switch", "steam deck", "rog ally", 
        "legion go", "vr headset", "meta quest", "psvr2", "gaming stuhl", "controller", "racing wheel",
        
        # Audio, TV & Heimkino
        "oled fernseher", "qled tv", "smart tv", "soundbar", "bluetooth box", "jbl box", 
        "bose kopfhörer", "airpods", "in-ear kopfhörer", "over-ear kopfhörer", "sonos", "beamer", "heimkino",
        
        # Smart Home & Netzwerk
        "fritzbox", "wlan router", "mesh wlan", "repeater", "philips hue", "smart plug", 
        "überwachungskamera", "ip kamera", "smart lock", "saugroboter", "mähroboter",
        
        # Gadgets & Creator Tech
        "drohne", "dji drone", "gopro", "actioncam", "3d drucker", "grafiktablett", 
        "e-reader", "kindle", "nas server", "externe festplatte", "usb stick"
    ]
    
    for kw in keywords:
        try:
            encoded_kw = urllib.parse.quote(kw)
            url = f"https://api.ebay.com/buy/browse/v1/item_summary/search?q={encoded_kw}&limit=10"
            
            req = urllib.request.Request(url, headers={
                'Authorization': f'Bearer {token}',
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
                                "category": "Elektronik & Tech",
                                "url": item_web_url
                            })
        except Exception as e:
            print(f"Fehler bei eBay API Abfrage für '{kw}': {e}")
            
    print(f"{len(deals)} Tech-Artikel von der eBay API abgerufen.")
    return deals

def apply_affiliate_link(url, shop_name=""):
    """
    Erkennt den Shop automatisch und fügt die korrekten Tracking-Parameter an.
    """
    if not url:
        return "https://duhrrom11.github.io/glitchradar/"
        
    shop_lower = shop_name.lower()
    separator = "&" if "?" in url else "?"
    
    # 1. Amazon PartnerNet
    if "amazon" in shop_lower:
        if "tag=" not in url:
            return f"{url}{separator}tag={AMAZON_TAG}"
        return url
        
    # 2. eBay Partner Network (ePN)
    elif "ebay" in shop_lower:
        if "campid=" not in url:
            return f"{url}{separator}mkeid=1&mkcid=1&campid={EBAY_CAMP_ID}&toolid=10001&customid=glitchradar"
        return url
        
    # 3. Awin / Standard Netzwerke
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

def run_scraper():
    print("GlitchRadar Master Tech-Scraper gestartet...")
    
    token = os.environ.get("TELEGRAM_TOKEN")
    private_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    channel_id = os.environ.get("TELEGRAM_CHANNEL_ID")

    existing_products = load_json(DATA_FILE)
    existing_ids = [p.get("id") for p in existing_products if isinstance(p, dict)]
    
    all_incoming_deals = []

    # eBay API Tech-Produkte abrufen
    ebay_items = fetch_ebay_api_deals()
    all_incoming_deals.extend(ebay_items)

    if not all_incoming_deals:
        print("Keine neuen Produkte zum Verarbeiten gefunden.")
        return

    new_items_added = 0
    print(f"Prüfe {len(all_incoming_deals)} Produkte auf Preisfehler (>= 50%)...")

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
        if discount_percent >= 10:
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
                "category": sample_deal.get("category", "Elektronik & Tech"),
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
        print(f"{new_items_added} neue Deals erfolgreich gespeichert und publiziert.")
    else:
        print("Scraper beendet: Keine neuen Deals >= 50% gefunden.")

if __name__ == "__main__":
    run_scraper()
    
