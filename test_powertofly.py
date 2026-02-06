import requests
import time

base_url = "http://127.0.0.1:5000/api/scrape"

print(f"Requesting scrape for https://powertofly.com/jobs/?keywords=AI (timeout=60s)...")
try:
    response = requests.post(f"{base_url}/one", json={"url": "https://powertofly.com/jobs/?keywords=AI"}, timeout=60)
    if response.status_code == 200:
        data = response.json()
        jobs = data.get("jobs", [])
        print(f"Status: {data.get('status')}")
        print(f"Jobs found: {len(jobs)}")
        if len(jobs) > 0:
            print(f"First job: {jobs[0].get('title')} at {jobs[0].get('company')}")
    else:
        print(f"Error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"Exception: {e}")
