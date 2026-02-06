from playwright.sync_api import sync_playwright
import logging
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from scraper.strategies.infor import InforStrategy

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_infor_pagination():
    url = "https://careers.infor.com/en_US/careers/SearchJobs"
    print(f"--- Testing Infor Pagination (Target: 4 pages) ---")
    
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
        
        strategy = InforStrategy()
        
        try:
            print("Starting scrape...")
            jobs = strategy.scrape(page, url)
            
            print(f"\n--- PAGINATION RESULTS ---")
            print(f"Total Pages Scraped: {strategy.stats.get('pages', 0)}")
            print(f"Total Jobs Found: {len(jobs)}")
            
            # Group jobs by page logic (approximate since we don't store page num in job)
            # But we can check if we found significantly more jobs than 6
            
            if strategy.stats.get('pages', 0) >= 4:
                print("SUCCESS: Reached page 4 limit.")
            else:
                print(f"FAILURE: Only reached page {strategy.stats.get('pages', 0)}")
                
            if len(jobs) > 10:
                print("SUCCESS: Found more than 10 jobs (implies multiple pages).")
            else:
                print("WARNING: Found 10 or fewer jobs. Pagination might be failing.")
                
        except Exception as e:
            print(f"Error: {e}")
        finally:
            page.close()
            browser.close()

if __name__ == "__main__":
    test_infor_pagination()
