from playwright.sync_api import sync_playwright
import logging
import sys
import os
import time

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from scraper.strategies.snaphunt import SnaphuntStrategy

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_snaphunt():
    url = "https://odixcity.snaphunt.com"
    print(f"--- Testing Snaphunt Scraper: {url} ---")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        
        # Anti-detection
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        strategy = SnaphuntStrategy()
        
        try:
            print("Starting scrape...")
            jobs = strategy.scrape(page, url)
            
            print(f"\n--- SCRAPE RESULTS ---")
            print(f"Total Jobs Found: {len(jobs)}")
            print(f"Pages/Scrolls: {strategy.stats.get('pages', 0)}")
            
            if jobs:
                print(f"Sample Job 1: {jobs[0]['title']}")
                print(f"Sample Job Link: {jobs[0]['link']}")
                desc_len = len(jobs[0].get('description', ''))
                print(f"Sample Description Length: {desc_len}")
                if desc_len > 100:
                    print("SUCCESS: Description found and is substantial.")
                    print(f"Preview: {jobs[0].get('description', '')[:200]}...")
                else:
                    print("WARNING: Description is short or empty.")
            else:
                print("No jobs found!")
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            page.close()
            browser.close()

if __name__ == "__main__":
    test_snaphunt()
