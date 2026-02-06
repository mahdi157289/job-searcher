import time
from scraper.engine import ScraperEngine
from scraper.task_manager import TaskManager

def test_scraper():
    task_manager = TaskManager()
    engine = ScraperEngine(task_manager=task_manager)
    test_urls = [
        "https://jobs.ashbyhq.com/The-Flex",
        "https://my.greenhouse.io/jobs",
        "https://builtin.com/jobs/remote"
    ]
    task_id = engine.start_scraping_task(test_urls)
    task_manager.set_approve_all(task_id, True)
    engine.approve_next(task_id)
    while True:
        task = task_manager.get_task(task_id)
        if task and task.status in ("completed", "failed"):
            break
        time.sleep(0.3)
    task = task_manager.get_task(task_id)
    if not task:
        print("Task not found")
        return
    print(f"Status: {task.status}")
    print(f"Total URLs: {task.total}")
    print(f"Scraped count: {len(task.results)}")
    for r in task.results:
        print(f"{r.get('platform','N/A')} - {r.get('url')} - jobs: {len(r.get('jobs',[]))}")

if __name__ == "__main__":
    test_scraper()
