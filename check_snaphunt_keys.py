from playwright.sync_api import sync_playwright
import json
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("Navigating to Snaphunt...")
        
        def handle_response(response):
            if "api.snaphunt.com/jobs/recruiters" in response.url and response.status == 200:
                print(f"Intercepted API: {response.url}")
                try:
                    data = response.json()
                    if "body" in data and "statusCode" in data:
                        if isinstance(data["body"], str):
                            data = json.loads(data["body"])
                        else:
                            data = data["body"]
                    
                    jobs = []
                    if isinstance(data, list):
                        jobs = data
                    elif isinstance(data, dict):
                        jobs = data.get("jobs", data.get("data", data.get("list", [])))
                        
                    if jobs:
                        print(f"Found {len(jobs)} jobs.")
                        first_job = jobs[0]
                        print("KEYS of first job:")
                        print(json.dumps(list(first_job.keys()), indent=2))
                        print("SAMPLE DATA of first job:")
                        print(json.dumps(first_job, indent=2))
                except Exception as e:
                    print(f"Error: {e}")

        page.on("response", handle_response)
        
        page.goto("https://odixcity.snaphunt.com", wait_until="networkidle")
        time.sleep(5)
        
        browser.close()

if __name__ == "__main__":
    run()
