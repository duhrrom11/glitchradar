import urllib.request
import xml.etree.ElementTree as ET
import re
import json
import os

ASINS_FILE = "data/asins.json"

TECH_RSS_FEEDS = [
    # Hier kannst du öffentliche RSS-Feeds von Tech-Seiten eintragen
]

def parse_rss_feed(feed_url):
    try:
        req = urllib.request.Request(feed_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            content_blob = ""
            for item in root.findall('.//item'):
                title = item.find('title')
                description = item.find('description')
                link = item.find('link')
                if title is not None and title.text:
                    content_blob += " " + title.text
                if description is not None and description.text:
                    content_blob += " " + description.text
                if link is not None and link.text:
                    content_blob += " " + link.text
            return content_blob
    except Exception as e:
        print(f"Fehler beim Abrufen des Feeds {feed_url}: {e}")
        return ""

def collect_and_update_asins():
    print("Starte automatische ASIN-Ernte aus RSS-Feeds...")
    all_text_data = ""
    for feed_url in TECH_RSS_FEEDS:
        all_text_data += " " + parse_rss_feed(feed_url)

    if not all_text_data.strip():
        print("Keine Feed-Daten erhalten.")
        return

    pattern = r'/(?:dp|gp/product)/([A-Z0-9]{10})'
    found_asins = set(re.findall(pattern, all_text_data))
    
    if not found_asins:
        print("Keine neuen ASINs gefunden.")
        return

    existing_data = []
    if os.path.exists(ASINS_FILE):
        try:
            with open(ASINS_FILE, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except Exception:
            pass
            
    existing_asins = {item.get("asin") for item in existing_data if "asin" in item}
    
    added_count = 0
    for asin in found_asins:
        if asin not in existing_asins:
            new_entry = {
                "id": f"rss-auto-{asin}",
                "asin": asin,
                "title": f"Auto-Importiertes Tech-Produkt ({asin})",
                "old_price": 150.00,
                "new_price": 50.00,
                "shop": "Amazon"
            }
            existing_data.append(new_entry)
            existing_asins.add(asin)
            added_count += 1

    os.makedirs(os.path.dirname(ASINS_FILE), exist_ok=True)
    with open(ASINS_FILE, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=4)
        
    print(f"{added_count} neue ASINs zur asins.json hinzugefügt.")

if __name__ == "__main__":
    collect_and_update_asins()
