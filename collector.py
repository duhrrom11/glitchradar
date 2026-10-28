import urllib.request
import xml.etree.ElementTree as ET
import re
import json
import os

ASINS_FILE = "data/asins.json"

TECH_RSS_FEEDS = [
    "https://www.techstage.de/rss.xml",
    "https://winfuture.de/news.rss",
    "https://www.chip.de/rss/rss_chip_alle.xml",
    "https://www.giga.de/feed/",
    "https://www.mydealz.de/rss/deals"
]

def parse_rss_feed(feed_url):
    """
    Durchsucht den RSS-Feed nach Beiträgen und extrahiert den Artikel-Titel sowie den Textinhalt.
    """
    items_data = []
    try:
        req = urllib.request.Request(feed_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            for item in root.findall('.//item'):
                title_elem = item.find('title')
                desc_elem = item.find('description')
                link_elem = item.find('link')
                
                item_title = title_elem.text if title_elem is not None and title_elem.text else "Tech-Deal"
                
                # Text-Blob zusammenbauen, um darin nach ASINs zu suchen
                text_blob = item_title
                if desc_elem is not None and desc_elem.text:
                    text_blob += " " + desc_elem.text
                if link_elem is not None and link_elem.text:
                    text_blob += " " + link_elem.text
                    
                items_data.append((item_title, text_blob))
            return items_data
    except Exception as e:
        print(f"Fehler beim Abrufen des Feeds {feed_url}: {e}")
        return []

def collect_and_update_asins():
    print("Starte intelligente ASIN-Ernte mit echten RSS-Titeln...")
    
    asin_to_title = {}
    pattern = r'/(?:dp|gp/product)/([A-Z0-9]{10})'

    for feed_url in TECH_RSS_FEEDS:
        print(f"Scanne Feed: {feed_url}")
        feed_items = parse_rss_feed(feed_url)
        for item_title, text_blob in feed_items:
            found_asins = re.findall(pattern, text_blob)
            for asin in found_asins:
                # Verknüpfe die ASIN direkt mit der echten Überschrift des Beitrags
                if asin not in asin_to_title:
                    asin_to_title[asin] = item_title.strip()

    if not asin_to_title:
        print("Keine neuen ASINs in den Feeds gefunden.")
        return

    # Bestehende asins.json laden
    existing_data = []
    if os.path.exists(ASINS_FILE):
        try:
            with open(ASINS_FILE, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except Exception:
            pass
            
    existing_asins = {item.get("asin") for item in existing_data if "asin" in item}
    
    added_count = 0
    for asin, title in asin_to_title.items():
        if asin not in existing_asins:
            new_entry = {
                "id": f"rss-auto-{asin}",
                "asin": asin,
                "title": title,  # <--- Hier landet jetzt die echte Überschrift aus dem Feed!
                "old_price": 100.00,  # Platzhalter für den ersten Check
                "new_price": 40.00,   # Test-Basis für den Rabatt-Filter
                "shop": "Amazon"
            }
            existing_data.append(new_entry)
            existing_asins.add(asin)
            added_count += 1

    os.makedirs(os.path.dirname(ASINS_FILE), exist_ok=True)
    with open(ASINS_FILE, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=4)
        
    print(f"Erfolg! {added_count} neue ASINs mit echten Titeln zur asins.json hinzugefügt.")

if __name__ == "__main__":
    collect_and_update_asins()
