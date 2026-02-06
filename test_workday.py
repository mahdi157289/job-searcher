from playwright.sync_api import sync_playwright
import logging
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from scraper.strategies.workday import WorkdayStrategy

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_workday():
    url = "https://fina.wd103.myworkdayjobs.com/en-US/DeloitteRecrute"
    print(f"--- Testing Workday Scraper: {url} ---")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = context.new_page()
        
        strategy = WorkdayStrategy()
        
        try:
            print("Navigating...")
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000) # Wait for initial load
            
            print("Starting scrape...")
            jobs = strategy.scrape(page, url)
            
            print(f"\n--- SCRAPE RESULTS ---")
            print(f"Total Jobs Found: {len(jobs)}")
            
            if jobs:
                print(f"Sample Job 1: {jobs[0]['title']}")
                print(f"Sample Job Link: {jobs[0]['link']}")
                desc = jobs[0].get('description', '')
                print(f"Sample Description Length: {len(desc)}")
                if len(desc) < 50:
                    print("WARNING: Description is missing or short.")
            else:
                print("No jobs found!")
                
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    test_workday()
