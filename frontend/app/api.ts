import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '/api'; // Use env var or relative path

export interface Job {
    title: string;
    company: string;
    location: string;
    link: string;
    platform: string;
    posted_at?: string;
    age_text?: string;
    description?: string;
    details?: Record<string, string>;
}

export interface ScrapeResult {
    url: string;
    title: string;
    status: 'pending' | 'running' | 'success' | 'failed' | 'skipped';
    jobs: Job[];
    platform: string;
    total_found: number;
    filtered_count?: number;
    stats?: {
        pages?: number;
        [key: string]: any;
    };
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
