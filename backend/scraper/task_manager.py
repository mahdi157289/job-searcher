import uuid
from dataclasses import dataclass, field
from typing import Dict, Any, List
import threading
import logging

logger = logging.getLogger(__name__)

@dataclass
class ScrapingTask:
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "pending"
    progress: int = 0
    total: int = 0
    logs: List[str] = field(default_factory=list)
    results: List[Dict[str, Any]] = field(default_factory=list)
    awaiting_approval: bool = False
    next_url: str = ""
    approve_all: bool = False
    skip_next: bool = False

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, ScrapingTask] = {}
        self.lock = threading.Lock()

    def create_task(self, total_urls: int) -> ScrapingTask:
        with self.lock:
            task = ScrapingTask(total=total_urls)
            self.tasks[task.task_id] = task
            return task

    def get_task(self, task_id: str) -> ScrapingTask:
        with self.lock:
            return self.tasks.get(task_id)

    def update_task_status(self, task_id: str, status: str):
        with self.lock:
            if task := self.tasks.get(task_id):
                task.status = status

    def add_log(self, task_id: str, message: str):
        with self.lock:
            if task := self.tasks.get(task_id):
                task.logs.append(message)

    def add_result(self, task_id: str, result: Dict[str, Any]):
        with self.lock:
            if task := self.tasks.get(task_id):
                # Check if result for this URL already exists (partial update case)
                existing = next((r for r in task.results if r["url"] == result["url"]), None)
                if existing:
                    # Update existing result
                    existing.update(result)
                    if result.get("status") in ["success", "error"]:
                        # Only increment progress if it's a completion update and wasn't already counted?
                        # Actually progress is usually just "count of completed URLs".
                        # If we initialized it earlier, we shouldn't increment again?
                        # Let's handle progress separately or assume add_result is final.
                        pass
                else:
                    task.results.append(result)
                    task.progress += 1

    def init_result(self, task_id: str, url: str):
        with self.lock:
            if task := self.tasks.get(task_id):
                # Add placeholder result
                logger.info(f"[TaskManager] Init result for task {task_id}, url {url}")
                task.results.append({
                    "url": url,
                    "status": "running",
                    "jobs": [],
                    "platform": "Pending...",
                    "total_found": 0
                })
                # We don't increment progress yet, progress is completed URLs

    def update_result_jobs(self, task_id: str, url: str, new_jobs: List[Dict[str, Any]], stats: Dict[str, Any] = None):
        with self.lock:
            if task := self.tasks.get(task_id):
                for res in task.results:
                    if res["url"] == url:
                        # Update stats if provided
                        if stats:
                            res["stats"] = stats
                        
                        # Merge logic: use link as unique key
                        existing_map = {j.get("link"): j for j in res["jobs"] if j.get("link")}
                        added_count = 0
                        
                        for job in new_jobs:
                            link = job.get("link")
                            if link and link in existing_map:
                                # Update existing job
                                existing_map[link].update(job)
                            else:
                                # Add new job
                                res["jobs"].append(job)
                                added_count += 1
                        
                        logger.info(f"[TaskManager] Streamed jobs for task {task_id}. Added: {added_count}, Updated: {len(new_jobs) - added_count}. Total: {len(res['jobs'])}")
                        res["total_found"] = len(res["jobs"])
                        break

    def set_approval(self, task_id: str, awaiting: bool, next_url: str = ""):
        with self.lock:
            if task := self.tasks.get(task_id):
                task.awaiting_approval = awaiting
                task.next_url = next_url

    def set_approve_all(self, task_id: str, value: bool):
        with self.lock:
            if task := self.tasks.get(task_id):
                task.approve_all = value

    def set_skip_next(self, task_id: str, value: bool):
        with self.lock:
            if task := self.tasks.get(task_id):
                task.skip_next = value
