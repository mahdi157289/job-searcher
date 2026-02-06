from playwright.sync_api import sync_playwright
import json
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("Navigating to Snaphunt...", flush=True)
        
        captured_jobs = []
        api_calls = 0

        def handle_response(response):
            nonlocal api_calls
            if "api.snaphunt.com" in response.url and "jobs" in response.url:
                try:
                    if "application/json" not in response.headers.get("content-type", ""):
                        return

                    data = response.json()
                    if "body" in data and "statusCode" in data:
                        if isinstance(data["body"], str):
                            data = json.loads(data["body"])
                        else:
                            data = data["body"]
                    
                    # Print root keys to find 'total'
                    if isinstance(data, dict):
                        print(f"API Root Keys: {list(data.keys())}", flush=True)
                        print(f"Total in root: {data.get('total')}", flush=True)
                        print(f"Count in root: {data.get('count')}", flush=True)

                    jobs_batch = []
                    if isinstance(data, list):
                        jobs_batch = data
                    elif isinstance(data, dict):
                        jobs_batch = data.get("jobs", data.get("data", data.get("list", [])))
                    
                    if jobs_batch:
                        api_calls += 1
                        captured_jobs.extend(jobs_batch)
                        if api_calls == 1:
                            # Check keys of first job again just to be sure
                            print(f"Job Keys: {list(jobs_batch[0].keys())}", flush=True)

                except Exception as e:
                    pass

        page.on("response", handle_response)
        
        try:
            page.goto("https://odixcity.snaphunt.com", wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(5000)
            
            # Check for Load More button
            print("\n--- CHECKING PAGINATION CONTROLS ---", flush=True)
            more_btn = page.query_selector("button:has-text('Load more'), button:has-text('Show more'), div:has-text('Show more')")
            if more_btn:
                print(f"Found 'Load/Show More' button: {more_btn.inner_text()}", flush=True)
                print("Clicking button...", flush=True)
                more_btn.click()
                page.wait_for_timeout(3000)
            else:
                print("No 'Load More' or 'Show More' button found.", flush=True)
            
            print(f"Total jobs captured: {len(captured_jobs)}", flush=True)
            
        except Exception as e:
            print(f"Error: {e}", flush=True)
        
        browser.close()

if __name__ == "__main__":
    run()
