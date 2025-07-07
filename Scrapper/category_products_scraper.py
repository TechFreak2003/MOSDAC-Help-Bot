import os
import json
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://mosdac.gov.in"

# Product name to URL mapping (Open Data)
PRODUCT_PAGES = {
    "Bayesian based MT-SAPHIR rainfall": "https://mosdac.gov.in/bayesian-based-mt-saphir-rainfall",
    "GPS derived Integrated water vapour": "https://mosdac.gov.in/gps-derived-integrated-water-vapour",
    "GSMap ISRO Rain": "https://mosdac.gov.in/gsmap-isro-rain",
    "METEOSAT8 Cloud Properties": "https://mosdac.gov.in/meteosat8-cloud-properties",
    "3D Volumetric TERLS DWRproduct": "https://mosdac.gov.in/3d-volumetric-terls-dwrproduct",
    "Inland Water Height": "https://mosdac.gov.in/inland-water-height",
    "River Discharge": "https://mosdac.gov.in/river-discharge",
    "Soil Moisture": "https://mosdac.gov.in/soil-moisture-0",
    "Global Ocean Surface Current": "https://mosdac.gov.in/global-ocean-surface-current",
    "High Resolution Sea Surface Salinity": "https://mosdac.gov.in/high-resolution-sea-surface-salinity",
    "Indian Mainland Coastal Product": "https://mosdac.gov.in/indian-mainland-coastal-product",
    "Ocean Subsurface": "https://mosdac.gov.in/ocean-subsurface",
    "Oceanic Eddies Detection": "https://mosdac.gov.in/oceanic-eddies-detection",
    "Sea Ice Occurrence Probability": "https://mosdac.gov.in/sea-ice-occurrence-probability",
    "Wave-based Renewable Energy": "https://mosdac.gov.in/wave-based-renewable-energy",
}

def fetch_html(url):
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"[!] Failed to fetch {url}: {e}")
        return None

def scrape_product_page(name, url):
    html = fetch_html(url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    product = {
        "name": name,
        "url": url,
        "description": "",
        "documents": []
    }

    # ✅ Extract description from <meta name="description">
    try:
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            product["description"] = meta_desc["content"].strip()
    except Exception as e:
        print(f"[!] Error parsing meta description for {name}: {e}")

    # ✅ Extract document links (ignore global STQC.pdf)
    try:
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if any(href.lower().endswith(ext) for ext in [".pdf", ".doc", ".docx"]):
                if "stqc.pdf" in href.lower():
                    continue  # skip common global docs
                product["documents"].append({
                    "title": a.get_text(strip=True),
                    "url": href if href.startswith("http") else f"{BASE_URL}{href}"
                })
    except Exception as e:
        print(f"[!] Error parsing documents for {name}: {e}")

    return product

def scrape_all_products():
    all_products = []
    print("🌐 Scraping Open Data Products...\n")

    for i, (name, url) in enumerate(PRODUCT_PAGES.items(), 1):
        print(f"[{i}/{len(PRODUCT_PAGES)}] {name}")
        product = scrape_product_page(name, url)
        if product:
            all_products.append(product)

    return all_products

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    products = scrape_all_products()

    with open("data/products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Done. Saved {len(products)} products to data/products.json")
