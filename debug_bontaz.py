from playwright.sync_api import sync_playwright
import sys
import os

# Ensure backend modules can be imported
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.scraper.strategies import get_strategy
from backend.scraper.strategies.generic import GenericStrategy

def test_bontaz():
    url = "https://bontaz-career.talent-soft.com/accueil.aspx?LCID=1036"
    print(f"--- Testing Bontaz Scraper: {url} ---")
    
    strategy = get_strategy(url)
    print(f"Strategy: {strategy.__class__.__name__}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            print(f"Navigating to {url}...")
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)
        except Exception as e:
            print(f"Navigation warning: {e}")

        jobs = strategy.scrape(page, url)
        
        print(f"\n--- SCRAPE RESULTS ---")
        print(f"Total Jobs Found: {len(jobs)}")
        if jobs:
            print(f"Platform: {jobs[0].get('platform')}")
            print(f"First Job: {jobs[0]}")
        else:
            print("No jobs found!")
            
        browser.close()

if __name__ == "__main__":
    test_bontaz()
