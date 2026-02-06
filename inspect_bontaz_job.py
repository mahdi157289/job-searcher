from playwright.sync_api import sync_playwright

def inspect():
    url = "https://bontaz-career.talent-soft.com/offre-de-emploi/emploi-master-data-administrator-m-f-d-_505.aspx"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        
        # Count elements with the class
        elements = page.query_selector_all(".ts-offer-page__block")
        print(f"Found {len(elements)} elements with class .ts-offer-page__block")
        
        for i, el in enumerate(elements):
            text = el.inner_text()
            print(f"Block {i} length: {len(text)}")
            print(f"Preview: {text[:50]}...")
            
        browser.close()

if __name__ == "__main__":
    inspect()
