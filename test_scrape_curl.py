
import requests
import time
import json

def test_scrape_api():
    url = "http://127.0.0.1:5000/api/scrape/start"
    payload = {"urls": ["https://powertofly.com/jobs/?keywords=AI"]}
    
    print(f"Starting scrape for {payload['urls'][0]}")
    resp = requests.post(url, json=payload)
    if resp.status_code != 200:
        print(f"Error starting scrape: {resp.text}")
        return
        
    task_id = resp.json().get("task_id")
    print(f"Task ID: {task_id}")
    
    # Wait for task to be awaiting approval
    print("Waiting for task to request approval...")
    for _ in range(30):
        resp = requests.get(f"http://127.0.0.1:5000/api/scrape/status/{task_id}")
        data = resp.json()
        if data.get("awaiting_approval"):
            print("Task is awaiting approval.")
            break
        time.sleep(1)
    else:
        print("Timed out waiting for approval request.")
        return
    
    # Approve it
    print("Approving next URL...")
    requests.post(f"http://127.0.0.1:5000/api/scrape/approve/{task_id}")
    
    print("Polling for results...")
    for i in range(20):
        resp = requests.get(f"http://127.0.0.1:5000/api/scrape/status/{task_id}")
        data = resp.json()
        
        print(f"Poll {i} Status: {data.get('status')} - Logs: {len(data.get('logs', []))}")
        if data.get('logs'):
            print(f"Last Log: {data['logs'][-1]}")
            
        results = data.get("results", [])
        if results:
            jobs = results[0].get("jobs", [])
            print(f"Poll {i}: Found {len(jobs)} jobs")
            
            # Check for description
            jobs_with_desc = [j for j in jobs if j.get("description") and j.get("description") != "Loading details..."]
            print(f"Jobs with real description: {len(jobs_with_desc)}")
            
            if jobs_with_desc:
                print("SUCCESS: Found job with description!")
                print(f"Sample desc len: {len(jobs_with_desc[0]['description'])}")
                print(f"Content: {jobs_with_desc[0]['description'][:200]}")
                # print(jobs_with_desc[0]['description'][:100])
                return
                
        if data.get("status") in ["completed", "failed"]:
            print(f"Task finished with status: {data.get('status')}")
            break
            
        time.sleep(2)

if __name__ == "__main__":
    test_scrape_api()
