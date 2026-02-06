
import logging
import sys
import os
import time
from playwright.sync_api import sync_playwright
from backend.scraper.strategies.builtin import BuiltInStrategy

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_builtin")

def test_builtin():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        strategy = BuiltInStrategy()
        url = "https://builtin.com/jobs/remote/hybrid?search=AI"
        
        print(f"Testing URL: {url}")
        
        def on_jobs(jobs):
            print(f"Found {len(jobs)} jobs")
            if jobs:
                first_job = jobs[0]
                print(f"First Job Title: {first_job.get('title')}")
                print(f"First Job Description Len: {len(first_job.get('description', ''))}")
                print(f"First Job Details Keys: {first_job.get('details', {}).keys()}")
                if not first_job.get('description'):
                    print("WARNING: No description found!")
                else:
                    print("Description sample:", first_job['description'][:100])

        jobs = strategy.scrape(page, url, on_jobs_found=on_jobs)
        
        print(f"Total jobs: {len(jobs)}")
        browser.close()

if __name__ == "__main__":
    test_builtin()
