from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import json
import os

CATALOG_URL = "https://mosdac.gov.in/catalog/satellite.php"

def get_rendered_html(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(5)  # wait for JS to render
    html = driver.page_source
    driver.quit()
    return html

def parse_rendered_catalog(html):
    soup = BeautifulSoup(html, "html.parser")
    data = []

    table = soup.find("table")
    if not table:
        print("[!] No table found after rendering.")
        return []

    current_sat = None
    for row in table.find_all("tr"):
        cols = row.find_all("td")
        if not cols:
            continue

        if len(cols) >= 2:
            # Check if satellite name exists in first cell
            sat = cols[0].get_text(strip=True)
            if sat:
                current_sat = sat
                sensor = cols[1].get_text(strip=True)
            else:
                sensor = cols[0].get_text(strip=True)

            url_tag = cols[-1].find("a", href=True) if cols[-1] else None
            product_url = url_tag["href"] if url_tag else None

            data.append({
                "satellite": current_sat,
                "sensor": sensor,
                "product_url": product_url
            })

    return data

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    html = get_rendered_html(CATALOG_URL)
    records = parse_rendered_catalog(html)

    with open("data/catalog_satellite_products.json", "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Done. Saved {len(records)} entries to data/catalog_satellite_products.json")
