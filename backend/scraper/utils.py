import re
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def parse_platforms_file(file_path: str) -> List[str]:
    urls = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                # Find all content within parentheses in this line
                matches = re.findall(r'\((https?://[^)]+)\)', line)
                urls.extend(matches)
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
    return urls

def filter_jobs_by_date(jobs: List[Dict[str, Any]], hours_back: int = 24, require_date: bool = False) -> List[Dict[str, Any]]:
    if not jobs:
        return jobs
    
    cutoff_time = datetime.now() - timedelta(hours=hours_back)
    filtered_jobs = []
    
    for job in jobs:
        job_date = None

        for key in ("posted_at", "posted", "date", "age", "age_text"):
            value = job.get(key)
            if not value:
                continue
            if isinstance(value, datetime):
                job_date = value
                break
            if isinstance(value, str):
                job_date = _parse_posted_time(value)
                if job_date:
                    break

        if job_date is None:
            if not require_date:
                filtered_jobs.append(job)
            continue

        if job_date >= cutoff_time:
            filtered_jobs.append(job)
    
    return filtered_jobs

def is_recent_job(job_text: str, hours_back: int = 24) -> bool:
    recent_keywords = ['just posted', 'new', 'today', 'this week', 'recently posted']
    job_text_lower = job_text.lower()
    
    for keyword in recent_keywords:
        if keyword in job_text_lower:
            return True
    
    dt = _parse_posted_time(job_text_lower)
    if dt is None:
        return False
    return dt >= (datetime.now() - timedelta(hours=hours_back))

def _parse_posted_time(text: str):
    if not text:
        return None
    t = text.strip().lower()

    if "just posted" in t:
        return datetime.now()
    if "today" in t:
        return datetime.now()
    if "yesterday" in t:
        return datetime.now() - timedelta(days=1)

    m = re.search(r'(\d+)\s*(minute|minutes|hour|hours|day|days)\s*ago', t)
    if m:
        amount = int(m.group(1))
        unit = m.group(2)
        if unit.startswith("minute"):
            return datetime.now() - timedelta(minutes=amount)
        if unit.startswith("hour"):
            return datetime.now() - timedelta(hours=amount)
        if unit.startswith("day"):
            return datetime.now() - timedelta(days=amount)

    m = re.search(r'(\d+)\s*(minute|minutes|hour|hours|day|days)', t)
    if m and any(w in t for w in ("posted", "ago", "since", "updated")):
        amount = int(m.group(1))
        unit = m.group(2)
        if unit.startswith("minute"):
            return datetime.now() - timedelta(minutes=amount)
        if unit.startswith("hour"):
            return datetime.now() - timedelta(hours=amount)
        if unit.startswith("day"):
            return datetime.now() - timedelta(days=amount)

    return None
