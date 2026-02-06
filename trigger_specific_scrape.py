import requests
import time
import json
import sys

BASE_URL = "http://127.0.0.1:5000"
URLS = [
    "https://careers.infor.com/en_US/careers/SearchJobs",
    "https://odixcity.snaphunt.com"
]

def trigger_scrape():
    print(f"Triggering scrape for {len(URLS)} URLs via API...")
    try:
        resp = requests.post(f"{BASE_URL}/api/scrape/start", json={"urls": URLS})
        resp.raise_for_status()
        data = resp.json()
        task_id = data["task_id"]
        print(f"Task started with ID: {task_id}")
        return task_id
    except Exception as e:
        print(f"Failed to start scrape: {e}")
        sys.exit(1)

def monitor_task(task_id):
    print("Monitoring task...")
    approved = False
    
    while True:
        try:
            resp = requests.get(f"{BASE_URL}/api/scrape/status/{task_id}")
            resp.raise_for_status()
            status_data = resp.json()
            
            status = status_data.get("status")
            total = status_data.get("total", 0)
            current = status_data.get("current", 0)
            results = status_data.get("results", [])
            logs = status_data.get("logs", [])
            
            # Print last log
            if logs:
                print(f"Server Log: {logs[-1]}")
            
            print(f"Status: {status} | Progress: {current}/{total} | Scraped Jobs: {len(results)}")
            
            if status == "pending_approval" and not approved:
                print("Task waiting for approval. Approving all...")
                requests.post(f"{BASE_URL}/api/scrape/approve_all/{task_id}")
                approved = True
            
            if status in ["completed", "failed"]:
                print(f"Task finished with status: {status}")
                return status_data
            
            time.sleep(2)
        except Exception as e:
            print(f"Error monitoring task: {e}")
            time.sleep(2)

if __name__ == "__main__":
    task_id = trigger_scrape()
    final_data = monitor_task(task_id)
    
    print("\n" + "="*50)
    print("FINAL RESULTS")
    print("="*50)
    results = final_data.get("results", [])
    print(f"Total Jobs Scraped: {len(results)}")
    
    by_platform = {}
    for job in results:
        plat = job.get("platform", "Unknown")
        by_platform[plat] = by_platform.get(plat, 0) + 1
        
    for plat, count in by_platform.items():
        print(f"{plat}: {count} jobs")
        
    # Verify Infor specifically
    infor_jobs = [j for j in results if j.get("platform") == "Infor"]
    print(f"\nInfor Jobs: {len(infor_jobs)}")
    if infor_jobs:
        print("Sample Infor Job:", infor_jobs[0].get("title"))
