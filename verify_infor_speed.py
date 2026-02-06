import requests
import time
import json

def test_infor_speed():
    print("Testing Infor scraper speed via API...")
    url = "https://careers.infor.com/en_US/careers/SearchJobs"
    start_time = time.time()
    
    try:
        response = requests.post(
            'http://127.0.0.1:5000/api/scrape/one',
            json={'url': url},
            timeout=300  # 5 minutes timeout
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if response.status_code == 200:
            data = response.json()
            jobs = data.get('jobs', [])
            job_count = len(jobs)
            print(f"\nSUCCESS!")
            print(f"Time taken: {duration:.2f} seconds")
            print(f"Jobs found: {job_count}")
            print(f"Status: {data.get('status')}")
            print("-" * 50)
            
            # Print first few jobs as sample
            if job_count > 0:
                print("Sample jobs:")
                for job in jobs[:3]:
                    print(f" - {job.get('title', 'No Title')} ({job.get('location', 'No Location')})")
            
            if duration < 60:
                print("Speed check: PASSED (Under 60 seconds)")
            else:
                print(f"Speed check: SLOW ({duration:.2f}s)")
                
            if job_count > 10:
                print("Count check: PASSED (Found > 10 jobs, implies multi-page)")
            elif job_count > 0:
                print("Count check: WARNING (Found jobs but <= 10, maybe single page?)")
            else:
                print("Count check: FAILED (No jobs found)")
                
        else:
            print(f"FAILED with status code: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error occurred: {str(e)}")

if __name__ == "__main__":
    test_infor_speed()
