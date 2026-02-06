from playwright.sync_api import sync_playwright
import logging
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from scraper.strategies.infor import InforStrategy

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_infor_scrape():
    url = "https://careers.infor.com/en_US/careers/SearchJobs"
    print(f"--- Testing Infor Scraper: {url} ---")
    
    with sync_playwright() as p:
        # Launch with extra args to avoid detection/empty page issues
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu'
            ]
        )
        # Create context with user agent
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        
        # Add stealth script
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        strategy = InforStrategy()
        
        try:
            # Run the actual scrape
            jobs = strategy.scrape(page, url)
            
            print(f"\n--- SCRAPE RESULTS ---")
            print(f"Total Jobs Found: {len(jobs)}")
            print(f"Pages Scraped: {strategy.stats.get('pages', 0)}")
            
            if jobs:
                print(f"Sample Job 1: {jobs[0]['title']}")
                print(f"Sample Job Last: {jobs[-1]['title']}")
                
                # Verify unique links
                links = set(j['link'] for j in jobs)
                print(f"Unique Links: {len(links)}")
            else:
                print("No jobs found!")
                
        except Exception as e:
            print(f"Error during scrape: {e}")
            import traceback
            traceback.print_exc()
        finally:
            page.close()
            browser.close()

if __name__ == "__main__":
    test_infor_scrape()
