import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

GALLERY_URL = "https://mosdac.gov.in/gallery/"
GO_BUTTON_XPATH = '//a[contains(@class, "button") and text()="GO"]'

def wait_for_dropdown(driver, dropdown_id, timeout=10):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.ID, dropdown_id))
    )

def get_dropdown_options(select_element):
    return [option.text.strip() for option in select_element.options if option.text.strip()]

def scrape_gallery_with_urls():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    driver.get(GALLERY_URL)
    time.sleep(5)  # give time to load JavaScript
    print(driver.page_source[:1500])  # 🔍 Print part of the HTML for inspection


    gallery = []

    try:
        wait_for_dropdown(driver, "sat")
        sat_select = Select(driver.find_element(By.ID, "sat"))
        satellite_options = get_dropdown_options(sat_select)

        for sat_name in satellite_options:
            print(f"🛰️ {sat_name}")
            sat_select.select_by_visible_text(sat_name)
            time.sleep(1)

            wait_for_dropdown(driver, "sen")
            sen_select = Select(driver.find_element(By.ID, "sen"))
            sensor_options = get_dropdown_options(sen_select)

            sensors = []
            for sen_name in sensor_options:
                print(f"   🔧 {sen_name}")
                sen_select.select_by_visible_text(sen_name)

            # 🔄 Wait until product dropdown is populated
                WebDriverWait(driver, 10).until(
                    lambda d: len(Select(d.find_element(By.ID, "prodt")).options) > 1
                )

                wait_for_dropdown(driver, "prodt")
                prodt_select = Select(driver.find_element(By.ID, "prodt"))
                product_options = get_dropdown_options(prodt_select)

                products = []
                for prod_name in product_options:
                    prodt_select.select_by_visible_text(prod_name)
                    time.sleep(0.5)

                    # Try to find GO button and get URL
                    try:
                        go_btn = driver.find_element(By.XPATH, GO_BUTTON_XPATH)
                        go_url = go_btn.get_attribute("href")
                    except:
                        go_url = None

                    products.append({
                        "name": prod_name,
                        "url": go_url
                    })

                sensors.append({
                    "name": sen_name,
                    "products": products
                })

            gallery.append({
                "satellite": sat_name,
                "sensors": sensors
            })

    finally:
        driver.quit()

    return gallery

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    result = scrape_gallery_with_urls()

    with open("data/gallery_products.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Done. Saved {len(result)} satellite entries to data/gallery_products.json")