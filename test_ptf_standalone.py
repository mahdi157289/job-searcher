
import logging
from backend.scraper.strategies.powertofly import PowerToFlyStrategy
from playwright.sync_api import sync_playwright

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_ptf():
    strategy = PowerToFlyStrategy()
    url = "https://powertofly.com/jobs/?keywords=AI"
    
    print(f"Testing PowerToFly strategy with URL: {url}")
    
    def on_jobs_found(jobs):
        print(f"Callback: Found {len(jobs)} jobs")
        if jobs:
            print(f"Sample job: {jobs[0].get('title')} - Link: {jobs[0].get('link')}")
            if 'description' in jobs[0]:
                 print(f"Desc Len: {len(jobs[0]['description'])}")
            else:
                 print("No description field")
            
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        jobs = strategy.scrape(page, url, on_jobs_found=on_jobs_found)
        print(f"Total jobs returned: {len(jobs)}")
        
        if jobs:
            print("First job details:")
            print(jobs[0])
            
        browser.close()

if __name__ == "__main__":
    test_ptf()
