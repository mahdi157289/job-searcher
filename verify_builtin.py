import sys
import os
import logging
from playwright.sync_api import sync_playwright

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from scraper.strategies.builtin import BuiltInStrategy

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_builtin():
    url = "https://builtin.com/jobs/dev-engineering/python" # Example URL
    # Or use the one from the user's previous request if known, or a generic one.
    # The user said "we used to scrappe 162 jobs from builtin".
    # I'll use a broad search.
    
    print(f"Testing BuiltIn Strategy with URL: {url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        strategy = BuiltInStrategy()
        if strategy.can_handle(url):
            print("Strategy can handle URL.")
            results = strategy.scrape(page, url)
            print(f"Scraped {len(results)} jobs.")
            
            # Check if we got more than 22 jobs (the 'bad' number)
            if len(results) > 22:
                print("SUCCESS: Pagination seems to be working.")
            else:
                print("WARNING: Job count is low. Pagination might not be effective.")
                
            # Print first 3 jobs to verify content
            for i, job in enumerate(results[:3]):
                print(f"Job {i+1}: {job.get('title')} at {job.get('company')}")
        else:
            print("Error: Strategy cannot handle URL.")
            
        browser.close()

if __name__ == "__main__":
    test_builtin()
