from playwright.sync_api import sync_playwright
import logging
import inspect
from typing import List, Dict, Any
import threading
from .strategies import get_strategy
from .task_manager import TaskManager
from .utils import filter_jobs_by_date

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScraperEngine:
    def __init__(self, task_manager: TaskManager):
        self.task_manager = task_manager
        self.approvals: Dict[str, threading.Event] = {}

    def stop(self):
        return

    def _scrape_url(self, browser, url: str, task_id: str) -> Dict[str, Any]:
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True
        )
        page = context.new_page()
        
        # Anti-detection script
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        try:
            self.task_manager.add_log(task_id, f"Starting to scrape {url}")
            try:
                page.goto(url, timeout=45000, wait_until="domcontentloaded")
            except Exception as nav_err:
                self.task_manager.add_log(task_id, f"Initial navigation failed for {url}: {nav_err}. Retrying with longer timeout.")
                try:
                    page.goto(url, timeout=70000, wait_until="domcontentloaded")
                except Exception as retry_err:
                    self.task_manager.add_log(task_id, f"Retry navigation failed: {retry_err}. Proceeding with partial page.")
            
            strategy = get_strategy(url)
            self.task_manager.add_log(task_id, f"Using {strategy.__class__.__name__} for {url}")
            import inspect
            try:
                self.task_manager.add_log(task_id, f"Strategy file: {inspect.getfile(strategy.__class__)}")
            except:
                pass
            
            # Initialize streaming result
            self.task_manager.init_result(task_id, url)

            def _json_safe(items):
                safe = []
                for it in items:
                    ni = {}
                    for k, v in it.items():
                        if isinstance(v, dict):
                            ni[k] = v
                        elif hasattr(v, "isoformat"):
                            try:
                                ni[k] = v.isoformat()
                            except Exception:
                                ni[k] = str(v)
                        else:
                            ni[k] = v
                    safe.append(ni)
                return safe

            def on_jobs_found(new_jobs, stats=None):
                if not new_jobs: return
                logger.info(f"[Engine] on_jobs_found called with {len(new_jobs)} jobs")
                # Relaxed filtering to 30 days to ensure we see more jobs during development
                filtered = filter_jobs_by_date(new_jobs, hours_back=720, require_date=False)
                safe_jobs = _json_safe(filtered)
                self.task_manager.update_result_jobs(task_id, url, safe_jobs, stats=stats)
                self.task_manager.add_log(task_id, f"Streamed {len(safe_jobs)} new jobs from {url}")

            sig = inspect.signature(strategy.scrape)
            if "on_jobs_found" in sig.parameters:
                jobs = strategy.scrape(page, url, on_jobs_found=on_jobs_found)
            else:
                jobs = strategy.scrape(page, url)
            
            # Retrieve stats from strategy if available
            strategy_stats = getattr(strategy, "stats", {})
            
            # Relaxed require_date to False and increased window to 30 days
            filtered_jobs = filter_jobs_by_date(jobs, hours_back=720, require_date=False)
            filtered_jobs_json = _json_safe(filtered_jobs)
            jobs_json = _json_safe(jobs)
            try:
                page_title = page.title()
            except Exception:
                page_title = ""
            result = {
                "url": url,
                "title": page_title,
                "status": "success",
                "jobs": filtered_jobs_json, # Note: this will duplicate if we blindly append in add_result
                "platform": strategy.__class__.__name__.replace('Strategy', ''),
                "total_found": len(jobs),
                "filtered_count": len(filtered_jobs),
                "jobs_unfiltered": jobs_json,
                "stats": strategy_stats
            }
            self.task_manager.add_log(task_id, f"Successfully scraped {len(jobs)} jobs from {url}, filtered to {len(filtered_jobs)} recent jobs")
            return result
        except Exception as e:
            error_message = f"Error scraping {url}: {e}"
            logger.error(error_message)
            self.task_manager.add_log(task_id, error_message)
            return {
                "url": url,
                "status": "error",
                "error": str(e),
                "jobs": []
            }
        finally:
            page.close()
            context.close()

    def _run_task(self, task_id: str, urls: List[str]) -> None:
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-setuid-sandbox'
                    ]
                )
                try:
                    for i, url in enumerate(urls):
                        self.task_manager.add_log(task_id, f"Ready to scrape site {i+1}/{len(urls)}: {url}. Awaiting approval.")
                        self.task_manager.set_approval(task_id, True, url)
                        evt = self.approvals.get(task_id)
                        skip_current = False
                        if evt:
                            evt.clear()
                            while True:
                                task = self.task_manager.get_task(task_id)
                                if task and task.approve_all:
                                    break
                                if task and task.skip_next:
                                    self.task_manager.add_log(task_id, f"Skipped site {i+1}/{len(urls)}: {url}")
                                    self.task_manager.add_result(task_id, {
                                        "url": url,
                                        "status": "skipped",
                                        "jobs": [],
                                        "platform": get_strategy(url).__class__.__name__.replace('Strategy', '')
                                    })
                                    self.task_manager.set_skip_next(task_id, False)
                                    self.task_manager.set_approval(task_id, False, "")
                                    skip_current = True
                                    break
                                if evt.wait(timeout=0.5):
                                    break
                        if skip_current:
                            continue
                        self.task_manager.set_approval(task_id, False, "")
                        self.task_manager.add_log(task_id, f"Approval received. Processing site {i+1}/{len(urls)}: {url}")
                        result = self._scrape_url(browser, url, task_id)
                        self.task_manager.add_result(task_id, result)
                finally:
                    browser.close()
        except Exception as e:
            logger.error(f"Task failed: {e}")
            self.task_manager.add_log(task_id, f"Task failed: {e}")
        finally:
            self.task_manager.update_task_status(task_id, "completed")
            # Cleanup approval event
            if task_id in self.approvals:
                del self.approvals[task_id]

    def start_scraping_task(self, urls: List[str]) -> str:
        task = self.task_manager.create_task(total_urls=len(urls))
        self.task_manager.update_task_status(task.task_id, "running")
        # Create approval event for this task
        self.approvals[task.task_id] = threading.Event()

        thread = threading.Thread(target=self._run_task, args=(task.task_id, urls), daemon=True)
        thread.start()
        return task.task_id

    def approve_next(self, task_id: str):
        evt = self.approvals.get(task_id)
        if evt:
            evt.set()
            self.task_manager.set_approval(task_id, False, "")
