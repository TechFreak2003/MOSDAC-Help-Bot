import os
import json
import requests
from bs4 import BeautifulSoup
import time
import re

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
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=15, headers=headers)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"[!] Failed to fetch {url}: {e}")
        return None

def clean_text(text):
    """Clean and normalize text content"""
    if not text:
        return ""
    
    # Remove extra whitespace and normalize
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    cleaned = '\n'.join(lines)
    
    # Remove excessive whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()

def extract_table_data(soup):
    """Extract structured table data (like MetaData table)"""
    tables = []
    
    for table in soup.find_all('table'):
        table_data = {
            'headers': [],
            'rows': []
        }
        
        # Extract headers
        header_row = table.find('tr')
        if header_row:
            headers = header_row.find_all(['th', 'td'])
            table_data['headers'] = [clean_text(h.get_text()) for h in headers]
        
        # Extract data rows
        for row in table.find_all('tr')[1:]:  # Skip header row
            cells = row.find_all(['td', 'th'])
            if cells:
                row_data = []
                for cell in cells:
                    # Check if cell contains links
                    links = cell.find_all('a', href=True)
                    cell_content = {
                        'text': clean_text(cell.get_text()),
                        'links': []
                    }
                    
                    for link in links:
                        href = link.get('href')
                        if href:
                            full_url = href if href.startswith('http') else f"{BASE_URL}{href}"
                            cell_content['links'].append({
                                'text': clean_text(link.get_text()),
                                'url': full_url
                            })
                    
                    row_data.append(cell_content)
                
                table_data['rows'].append(row_data)
        
        if table_data['headers'] or table_data['rows']:
            tables.append(table_data)
    
    return tables

def extract_sections(soup):
    """Extract content organized by sections/headings"""
    sections = {}
    
    # Common section headings to look for
    section_patterns = [
        r'data\s+access',
        r'data\s+version',
        r'data\s+sources?',
        r'processing\s+steps?',
        r'metadata',
        r'abstract',
        r'description',
        r'methodology',
        r'technical\s+details?',
        r'specifications?',
        r'parameters?',
        r'coverage',
        r'temporal\s+coverage',
        r'spatial\s+coverage',
        r'contact',
        r'references?'
    ]
    
    # Find headings (h1, h2, h3, h4, h5, h6)
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    
    for heading in headings:
        heading_text = clean_text(heading.get_text())
        
        # Check if heading matches any pattern
        for pattern in section_patterns:
            if re.search(pattern, heading_text, re.IGNORECASE):
                section_key = heading_text.lower().replace(' ', '_')
                
                # Find content after this heading until next heading
                content_elements = []
                current = heading.next_sibling
                
                while current:
                    if current.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        break
                    
                    if hasattr(current, 'get_text'):
                        text = clean_text(current.get_text())
                        if text and len(text) > 10:  # Only substantial content
                            # Check for links in this element
                            links = []
                            if hasattr(current, 'find_all'):
                                for link in current.find_all('a', href=True):
                                    href = link.get('href')
                                    if href:
                                        full_url = href if href.startswith('http') else f"{BASE_URL}{href}"
                                        links.append({
                                            'text': clean_text(link.get_text()),
                                            'url': full_url
                                        })
                            
                            content_elements.append({
                                'text': text,
                                'links': links
                            })
                    
                    current = current.next_sibling
                
                if content_elements:
                    sections[section_key] = content_elements
                break
    
    return sections

def extract_main_description(soup):
    """Extract the main description/abstract from the page"""
    
    # Look for main content paragraphs
    main_paragraphs = []
    
    # Try different selectors for main content
    content_selectors = [
        'div.field-item p',
        'div.content p',
        'div.node-content p',
        'article p',
        'main p'
    ]
    
    for selector in content_selectors:
        paragraphs = soup.select(selector)
        for p in paragraphs:
            text = clean_text(p.get_text())
            if text and len(text) > 50:  # Only substantial paragraphs
                main_paragraphs.append(text)
    
    # If no paragraphs found, look for any substantial text blocks
    if not main_paragraphs:
        for element in soup.find_all(['p', 'div']):
            text = clean_text(element.get_text())
            if text and len(text) > 100 and 'menu' not in text.lower():
                main_paragraphs.append(text)
                if len(main_paragraphs) >= 3:  # Limit to avoid too much content
                    break
    
    return main_paragraphs

def extract_links(soup):
    """Extract all relevant links from the page"""
    links = []
    
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = clean_text(a.get_text())
        
        # Skip empty links or navigation links
        if not text or len(text) < 2:
            continue
        
        # Skip common navigation words
        skip_words = ['home', 'back', 'next', 'previous', 'menu', 'login', 'register']
        if any(word in text.lower() for word in skip_words):
            continue
        
        full_url = href if href.startswith("http") else f"{BASE_URL}{href}"
        
        # Categorize links
        link_type = "general"
        if any(href.lower().endswith(ext) for ext in [".pdf", ".doc", ".docx"]):
            link_type = "document"
        elif "data" in text.lower() or "download" in text.lower():
            link_type = "data_access"
        elif "contact" in text.lower():
            link_type = "contact"
        
        links.append({
            "text": text,
            "url": full_url,
            "type": link_type
        })
    
    return links

def scrape_product_page(name, url):
    html = fetch_html(url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    product = {
        "name": name,
        "url": url,
        "meta_description": "",
        "main_description": [],
        "sections": {},
        "tables": [],
        "links": [],
        "documents": []
    }

    # ✅ Extract meta description
    try:
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            product["meta_description"] = clean_text(meta_desc["content"])
    except Exception as e:
        print(f"[!] Error parsing meta description for {name}: {e}")

    # ✅ Extract main description paragraphs
    try:
        product["main_description"] = extract_main_description(soup)
    except Exception as e:
        print(f"[!] Error parsing main description for {name}: {e}")

    # ✅ Extract structured sections
    try:
        product["sections"] = extract_sections(soup)
    except Exception as e:
        print(f"[!] Error parsing sections for {name}: {e}")

    # ✅ Extract tables
    try:
        product["tables"] = extract_table_data(soup)
    except Exception as e:
        print(f"[!] Error parsing tables for {name}: {e}")

    # ✅ Extract all links
    try:
        product["links"] = extract_links(soup)
    except Exception as e:
        print(f"[!] Error parsing links for {name}: {e}")

    # ✅ Extract documents separately for backward compatibility
    try:
        for link in product["links"]:
            if link["type"] == "document":
                product["documents"].append({
                    "title": link["text"],
                    "url": link["url"]
                })
    except Exception as e:
        print(f"[!] Error parsing documents for {name}: {e}")

    return product

def scrape_all_products():
    all_products = []
    print("🌐 Scraping Open Data Products with Structured Extraction...\n")

    for i, (name, url) in enumerate(PRODUCT_PAGES.items(), 1):
        print(f"[{i}/{len(PRODUCT_PAGES)}] {name}")
        product = scrape_product_page(name, url)
        if product:
            all_products.append(product)
            
            # Print summary
            sections_count = len(product.get('sections', {}))
            tables_count = len(product.get('tables', []))
            links_count = len(product.get('links', []))
            docs_count = len(product.get('documents', []))
            
            print(f"    ✅ Sections: {sections_count}, Tables: {tables_count}, Links: {links_count}, Docs: {docs_count}")
        else:
            print(f"    ❌ Failed to scrape")
        
        # Add delay to be respectful to the server
        time.sleep(1)

    return all_products

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    products = scrape_all_products()

    with open("data/products_structured.json", "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Done. Saved {len(products)} products to data/products_structured.json")
    
    # Print detailed summary
    print("\n📊 Detailed Summary:")
    for product in products:
        print(f"\n🔍 {product['name']}:")
        print(f"   📝 Main description: {len(product.get('main_description', []))} paragraphs")
        print(f"   📂 Sections: {list(product.get('sections', {}).keys())}")
        print(f"   📊 Tables: {len(product.get('tables', []))}")
        print(f"   🔗 Links: {len(product.get('links', []))}")
        print(f"   📄 Documents: {len(product.get('documents', []))}")
        
        # Show table structure if exists
        for i, table in enumerate(product.get('tables', [])):
            print(f"      Table {i+1}: {len(table.get('headers', []))} columns, {len(table.get('rows', []))} rows")