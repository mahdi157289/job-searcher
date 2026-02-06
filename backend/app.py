from flask import Flask, jsonify, send_from_directory, abort
from flask import request
from flask_cors import CORS
from scraper.engine import ScraperEngine
from scraper.task_manager import TaskManager
from scraper.utils import parse_platforms_file
from scraper.strategies import plan_strategies
import os
import sys
print("STARTING APP FROM CWD:", os.getcwd())
print("SYS PATH:", sys.path)
import logging
import uuid
import threading
import atexit
from dataclasses import asdict
import time

app = Flask(__name__, static_folder='static')
CORS(app)

task_manager = TaskManager()
scraper_engine = ScraperEngine(task_manager=task_manager)

# Ensure the scraper engine is stopped when the app exits
atexit.register(scraper_engine.stop)

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/api/scrape/start', methods=['POST'])
def start_scraping():
    data = request.get_json(silent=True) or {}
    urls = data.get("urls")
    if not urls:
        file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'job platforms.txt')
        urls = parse_platforms_file(file_path)
    
    task_id = scraper_engine.start_scraping_task(urls)
    return jsonify({"task_id": task_id})

@app.route('/api/scrape/status/<task_id>', methods=['GET'])
def get_status(task_id: str):
    task = task_manager.get_task(task_id)
    if not task:
        abort(404, description="Task not found")
    return jsonify(asdict(task))

@app.route('/api/scrape/approve/<task_id>', methods=['POST'])
def approve_next(task_id: str):
    task = task_manager.get_task(task_id)
    if not task:
        abort(404, description="Task not found")
    scraper_engine.approve_next(task_id)
    return jsonify({"status": "ok", "message": "Approved next URL"})

@app.route('/api/scrape/approve_all/<task_id>', methods=['POST'])
def approve_all(task_id: str):
    task = task_manager.get_task(task_id)
    if not task:
        abort(404, description="Task not found")
    task_manager.set_approve_all(task_id, True)
    scraper_engine.approve_next(task_id)
    return jsonify({"status": "ok", "message": "Approved all remaining URLs"})

@app.route('/api/scrape/skip/<task_id>', methods=['POST'])
def skip_next(task_id: str):
    task = task_manager.get_task(task_id)
    if not task:
        abort(404, description="Task not found")
    task_manager.set_skip_next(task_id, True)
    return jsonify({"status": "ok", "message": "Skipped current URL"})

@app.route('/api/scrape', methods=['POST'])
def scrape_aggregate():
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'job platforms.txt')
    urls = parse_platforms_file(file_path)
    task_id = scraper_engine.start_scraping_task(urls)
    task_manager.set_approve_all(task_id, True)
    scraper_engine.approve_next(task_id)
    while True:
        task = task_manager.get_task(task_id)
        if task and task.status in ("completed", "failed"):
            break
        time.sleep(0.3)
    task = task_manager.get_task(task_id)
    if not task:
        return jsonify({"status": "error", "message": "Task not found"}), 500
    return jsonify({
        "status": task.status,
        "total_urls": task.total,
        "scraped_count": len(task.results),
        "results": task.results
    })

@app.route('/api/scrape/plan', methods=['GET'])
def scrape_plan():
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'job platforms.txt')
    urls = parse_platforms_file(file_path)
    # Return both the plan and the raw list for the UI
    plan = plan_strategies(urls)
    # plan is a list of dicts: [{"url": "...", "strategy": "..."}]
    # We ensure "platform" key exists for the UI
    for item in plan:
        if "platform" not in item:
            item["platform"] = item.get("strategy", "Unknown")
            
    return jsonify({"total_urls": len(urls), "plan": plan})


@app.route('/api/scrape/one', methods=['POST'])
def scrape_one():
    data = request.get_json(silent=True) or {}
    url = data.get("url")
    if not url:
        abort(400, description="Missing 'url' in request body")
    task_id = scraper_engine.start_scraping_task([url])
    task_manager.set_approve_all(task_id, True)
    scraper_engine.approve_next(task_id)
    while True:
        task = task_manager.get_task(task_id)
        if task and task.status in ("completed", "failed"):
            break
        time.sleep(0.3)
    task = task_manager.get_task(task_id)
    if not task:
        return jsonify({"status": "error", "message": "Task not found"}), 500
    result = task.results[-1] if task.results else {"url": url, "status": "error", "jobs": []}
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=False)
