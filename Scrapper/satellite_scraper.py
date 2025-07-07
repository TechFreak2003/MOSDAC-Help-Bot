import os
import json
import time
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://mosdac.gov.in"
SITEMAP_URL = f"{BASE_URL}/sitemap"

def fetch_html(url):
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"[!] Failed to fetch {url}: {e}")
        return None

def get_satellite_links():
    html = fetch_html(SITEMAP_URL)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    missions = []

    missions_section = soup.find("a", string="Missions")
    if not missions_section:
        print("[!] Could not find 'Missions' section in sitemap.")
        return []

    mission_list = missions_section.find_next("ul", class_="site-map-menu")
    for li in mission_list.find_all("li"):
        a_tag = li.find("a")
        if a_tag and "/satellite" not in a_tag.get("href"):  # valid links (e.g. /insat-3dr)
            name = a_tag.get_text(strip=True)
            url = BASE_URL + a_tag["href"]
            missions.append({"name": name, "url": url})
    
    return missions

def scrape_satellite_details(link):
    html = fetch_html(link["url"])
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    mission = {
        "name": link["name"],
        "url": link["url"],
        "description": None,
        "documents": [],
        "metadata": {}
    }

    # Description block
    try:
        content_block = soup.find("div", class_="field-item")
        if content_block:
            paragraphs = content_block.find_all("p")
            mission["description"] = " ".join(p.get_text(strip=True) for p in paragraphs)

            # Extract metadata from description if possible
            text = mission["description"].lower()
            if "launch" in text:
                for line in text.split("."):
                    if "launch" in line:
                        mission["metadata"]["launch_info"] = line.strip()
            if "orbit" in text:
                for line in text.split("."):
                    if "orbit" in line:
                        mission["metadata"]["orbit_info"] = line.strip()
            if "sensor" in text or "payload" in text:
                for line in text.split("."):
                    if "sensor" in line or "payload" in line:
                        mission["metadata"]["sensors"] = line.strip()
    except Exception as e:
        print(f"Metadata extraction failed for {link['name']}: {e}")

    # Documents
    try:
        for a in soup.find_all("a", href=True):
            if any(ext in a["href"] for ext in [".pdf", ".doc", ".docx"]):
                mission["documents"].append({
                    "title": a.get_text(strip=True),
                    "url": a["href"] if a["href"].startswith("http") else BASE_URL + a["href"]
                })
    except:
        pass

    return mission

def scrape_all():
    print("🛰 Fetching satellite list from sitemap...")
    links = get_satellite_links()
    print(f"[✓] Found {len(links)} satellites.\n")

    missions = []
    for i, link in enumerate(links, 1):
        print(f"[{i}/{len(links)}] Scraping: {link['name']}")
        mission = scrape_satellite_details(link)
        if mission:
            missions.append(mission)
        else:
            print(f"⚠️ Skipped {link['name']} due to fetch error.")

    return missions

if __name__ == "__main__":
    print("=== MOSDAC Satellite Scraper ===")
    all_missions = scrape_all()

    os.makedirs("data", exist_ok=True)
    with open("data/satellites.json", "w", encoding="utf-8") as f:
        json.dump(all_missions, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Done. Saved {len(all_missions)} missions to data/satellites.json")