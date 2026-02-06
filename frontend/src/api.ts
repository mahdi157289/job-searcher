import axios from 'axios';

const API_URL = '/api'; // Use relative path to leverage Vite proxy

export interface Job {
    title: string;
    company: string;
    location: string;
    link: string;
    platform: string;
    posted_at?: string;
    age_text?: string;
    details?: Record<string, string>;
    description?: string;
}

export interface ScrapeResult {
    url: string;
    status: string;
    jobs: Job[];
    error?: string;
    platform?: string;
}

export interface ScrapeResponse {
    status: string;
    total_urls: number;
    scraped_count: number;
    results: ScrapeResult[];
}

export interface ScrapePlanItem {
    url: string;
    strategy: string;
    platform: string;
}

export interface ScrapePlanResponse {
    total_urls: number;
    plan: ScrapePlanItem[];
}

export interface TaskStatusResponse {
    task_id: string;
    status: string;
    progress: number;
    total: number;
    results: ScrapeResult[];
    logs: string[];
}

export const scrapeJobs = async (): Promise<ScrapeResponse> => {
    const response = await axios.post<ScrapeResponse>(`${API_URL}/scrape`);
    return response.data;
};

export const getScrapePlan = async (): Promise<ScrapePlanResponse> => {
    const response = await axios.get<ScrapePlanResponse>(`${API_URL}/scrape/plan`);
    return response.data;
};

export const startScrapeTask = async (urls: string[]): Promise<{ task_id: string }> => {
    // We can't easily pass URLs to /api/scrape/start because it reads from file on backend.
    // However, looking at app.py, scrape_one takes a URL. 
    // But start_scraping reads from file. 
    // We need a way to start a task with specific URLs or rely on backend file.
    // For now, let's use the existing start_scraping for "Run All".
    // For single site, we might need a new endpoint or use scrape_one (but scrape_one is synchronous/blocking in app.py).
    
    // Actually, looking at app.py:
    // start_scraping reads from file.
    // scrape_one starts a task with [url] but then waits for it.
    
    // To support non-blocking single site, we should probably add an endpoint or modify start to accept URLs.
    // But I cannot modify backend easily without ensuring I don't break things.
    // Let's stick to what we have:
    // If urls is provided, we might need to use scrape_one (blocking) or we can just accept blocking for single site.
    // But user wants "sidebar drops", so blocking is bad.
    
    // Wait, I can modify app.py safely.
    // Let's modify start_scraping to accept optional list of URLs.
    
    const response = await axios.post<{ task_id: string }>(`${API_URL}/scrape/start`, { urls });
    return response.data;
};

export const approveAllTask = async (taskId: string): Promise<void> => {
    await axios.post(`${API_URL}/scrape/approve_all/${taskId}`);
};

export const getTaskStatus = async (taskId: string): Promise<TaskStatusResponse> => {
    const response = await axios.get<TaskStatusResponse>(`${API_URL}/scrape/status/${taskId}`);
    return response.data;
};
