
from playwright.sync_api import sync_playwright

def check_selector_pw():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Go to a known job page (using the one from previous run)
        url = "https://builtin.com/job/ai-engineering-lead/8276366"
        print(f"Navigating to {url}")
        page.goto(url)
        page.wait_for_timeout(5000)
        
        # Check selectors again
        selectors = [
            ".job-description", 
            ".job-info", 
            "#job-description", 
            "div[class*='description']",
            ".job-listing-description",
            "div.block-content"
        ]
        
        found = False
        for sel in selectors:
            try:
                els = page.query_selector_all(sel)
                print(f"Selector '{sel}': {len(els)} matches")
                if els:
                    text = els[0].inner_text()
                    print(f"  Sample text: {text[:100].strip()}")
                    if len(text) > 100:
                        found = True
            except Exception as e:
                print(f"Error checking {sel}: {e}")
                
        if True: # Always dump for inspection
            print("Dumping page content to inspect...")
            with open("builtin_dump.html", "w", encoding="utf-8") as f:
                f.write(page.content())
                
        browser.close()

if __name__ == "__main__":
    check_selector_pw()
