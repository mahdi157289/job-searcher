import sys
import os
import logging

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from scraper.strategies.infor import InforStrategy
from scraper.strategies.snaphunt import SnaphuntStrategy
from playwright.sync_api import sync_playwright

# Setup logging
logging.basicConfig(level=logging.INFO)

def verify():
    print("Starting Job Count Verification...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # 1. Verify Infor
        # print("\n--- Verifying Infor Strategy ---")
        # infor_url = "https://careers.infor.com/en_US/careers/SearchJobs"
        # strategy = InforStrategy()
        # page = browser.new_page()
        # try:
        #     jobs = strategy.scrape(page, infor_url)
        #     print(f"Infor Jobs Found: {len(jobs)}")
        #     if jobs:
        #         print(f"Sample Job 1: {jobs[0]['title']} - {jobs[0]['location']}")
        #         print(f"Has Description: {bool(jobs[0].get('description'))}")
        # except Exception as e:
        #     print(f"Infor Failed: {e}")
        # finally:
        #     page.close()

        # 2. Verify Snaphunt
        print("\n--- Verifying Snaphunt Strategy ---")
        snap_url = "https://odixcity.snaphunt.com"
        strategy = SnaphuntStrategy()
        page = browser.new_page()
        try:
            jobs = strategy.scrape(page, snap_url)
            print(f"Snaphunt Jobs Found: {len(jobs)}")
            if jobs:
                print(f"Sample Job 1: {jobs[0]['title']} - {jobs[0]['location']}")
                print(f"Has Description: {bool(jobs[0].get('description'))}")
        except Exception as e:
            print(f"Snaphunt Failed: {e}")
        finally:
            page.close()
            
        browser.close()

if __name__ == "__main__":
    verify()
