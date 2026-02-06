from playwright.sync_api import sync_playwright
from backend.scraper.strategies.builtin import BuiltInStrategy
import logging

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_builtin():
    url = "https://builtin.com/jobs/remote"
    strategy = BuiltInStrategy()
    
    print(f"Testing BuiltInStrategy with URL: {url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            jobs = strategy.scrape(page, url)
            print(f"Total jobs found: {len(jobs)}")
            if jobs:
                print(f"Sample job: {jobs[0]}")
        except Exception as e:
            print(f"Error during scraping: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    test_builtin()
