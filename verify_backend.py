import requests
import time
import json

BASE_URL = "http://127.0.0.1:5000"

def verify_backend():
    print("Triggering scrape for Infor and Snaphunt...")
    
    payload = {
        "urls": [
            "https://careers.infor.com/en_US/careers/SearchJobs",
            "https://odixcity.snaphunt.com"
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/scrape/start", json=payload)
        response.raise_for_status()
        data = response.json()
        task_id = data["task_id"]
        print(f"Task started with ID: {task_id}")
        
        seen_logs = 0
        
        while True:
            status_resp = requests.get(f"{BASE_URL}/api/scrape/status/{task_id}")
            status_resp.raise_for_status()
            status_data = status_resp.json()
            
            status = status_data.get("status")
            results = status_data.get("results", [])
            logs = status_data.get("logs", [])
            awaiting = status_data.get("awaiting_approval", False)
            
            # Print new logs
            if len(logs) > seen_logs:
                for log in logs[seen_logs:]:
                    print(f"LOG: {log}")
                seen_logs = len(logs)
            
            if awaiting:
                print("Task awaiting approval. Sending approve...")
                requests.post(f"{BASE_URL}/api/scrape/approve/{task_id}")
            
            if status in ["completed", "failed", "stopped"]:
                # Final Report
                print(f"\nTask Finished with status: {status}")
                if isinstance(results, list):
                     for res in results:
                         url = res.get("url", "unknown")
                         jobs = res.get("jobs", [])
                         platform = "Unknown"
                         if "infor" in url: platform = "Infor"
                         elif "snaphunt" in url: platform = "Snaphunt"
                         
                         has_desc = sum(1 for j in jobs if j.get("description") and len(j.get("description")) > 100)
                         print(f"  {platform}: {len(jobs)} jobs found. {has_desc} have descriptions > 100 chars.")
                         if has_desc == 0 and len(jobs) > 0:
                             print("    WARNING: No descriptions found for this platform!")
                         elif len(jobs) > 0:
                             print(f"    Sample Description: {jobs[0]['description'][:50]}...")
                break
                
            time.sleep(2)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_backend()
