import requests
import time
import json

BASE_URL = "http://localhost:5000"

def run_test():
    print("Starting PowerToFly scrape test...")
    
    # 1. Start Task
    # Use /api/scrape/start which accepts specific URLs
    resp = requests.post(f"{BASE_URL}/api/scrape/start", json={
        "urls": ["https://powertofly.com/jobs/?keywords=AI"]
    })
    
    if resp.status_code != 200:
        print(f"Failed to start task: {resp.text}")
        return
        
    task_id = resp.json()["task_id"]
    print(f"Task started: {task_id}")
    
    # 2. Approve Task (endpoint is /api/scrape/approve_all/<task_id>)
    time.sleep(2) # Wait for init
    requests.post(f"{BASE_URL}/api/scrape/approve_all/{task_id}", json={})
    print("Task approved")
    
    # 3. Poll Status (endpoint is /api/scrape/status/<task_id>)
    print("Polling for results...")
    max_retries = 100 # Wait up to 100 seconds (since we increased scrolls)
    
    last_count = 0
    for i in range(max_retries):
        status_resp = requests.get(f"{BASE_URL}/api/scrape/status/{task_id}")
        status = status_resp.json()
        
        jobs_count = 0
        if status.get("results"):
            for res in status["results"]:
                if res.get("jobs"):
                    jobs_count += len(res["jobs"])
        
        if jobs_count > last_count:
            print(f"Jobs count: {jobs_count}")
            last_count = jobs_count
            
        if status["status"] in ["completed", "failed"]:
            print(f"Task finished with status: {status['status']}")
            break
            
        time.sleep(2)
        
    print(f"Final Job Count: {jobs_count}")

if __name__ == "__main__":
    run_test()
