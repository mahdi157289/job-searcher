import { useState, useEffect, useRef } from 'react';
import type { Route } from "./+types/home";
import { getScrapePlan, startScrapeTask, getTaskStatus, approveAllTask } from '../api';
import type { Job, ScrapeResult, ScrapePlanItem } from '../api';
import { Play, AlertCircle, RefreshCw } from 'lucide-react';
import { SiteCard } from '../components/SiteCard';
import { Sidebar } from '../components/Sidebar';
import { JobDetailsModal } from '../components/JobDetailsModal';

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Job Scraper Dashboard" },
    { name: "description", content: "Manage your job scraping tasks" },
  ];
}

export default function Home() {
  const [loading, setLoading] = useState(false); // Global loading (e.g. initial fetch)
  const [scraping, setScraping] = useState(false); // Scraping active state
  const [plan, setPlan] = useState<ScrapePlanItem[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [error, setError] = useState<string | null>(null);
  
  // Sidebar & Modal State
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  // Task Management
  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskResults, setTaskResults] = useState<ScrapeResult[]>([]);
  const pollingRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    loadPlan();
    return () => stopPolling();
  }, []);

  useEffect(() => {
    if (selectedJob) {
      const updated = jobs.find(j => j.link === selectedJob.link);
      if (updated && updated !== selectedJob) {
        console.log("Syncing selectedJob with updated data");
        setSelectedJob(updated);
      }
    }
  }, [jobs, selectedJob]);

  const loadPlan = async () => {
    try {
      const response = await getScrapePlan();
      setPlan(response.plan);
    } catch (err) {
      console.error("Failed to load plan:", err);
      setError("Failed to load scraping plan. Is the backend running?");
    }
  };

  const stopPolling = () => {
    if (pollingRef.current) {
      clearTimeout(pollingRef.current);
      pollingRef.current = null;
    }
  };

  const pollTask = async (tid: string) => {
    try {
      const status = await getTaskStatus(tid);
      console.log(`[Polling] Task ${tid} status: ${status.status}, results: ${status.results?.length}`);
      
      if (status.results) {
        setTaskResults(status.results);
      }

      // Collect all jobs from results
      const allJobs: Job[] = [];
      status.results.forEach(res => {
        if (res.jobs) {
            console.log(`[Polling] Result for ${res.url}: ${res.jobs.length} jobs`);
            allJobs.push(...res.jobs);
        }
      });
      console.log(`[Polling] Total jobs collected: ${allJobs.length}`);
      
      // Debug log for description
      if (allJobs.length > 0) {
        const firstJob = allJobs[0];
        console.log(`[Debug] First Job: ${firstJob.title}`);
        console.log(`[Debug] Description len: ${firstJob.description?.length}`);
        console.log(`[Debug] Description content: ${firstJob.description?.substring(0, 50)}...`);
      }

      setJobs(allJobs);
      
      if (status.status === 'completed' || status.status === 'failed') {
        console.log(`[Polling] Task finished with status ${status.status}`);
        setScraping(false);
      } else {
        // Schedule next poll
        pollingRef.current = setTimeout(() => pollTask(tid), 1000);
      }
    } catch (e) {
      console.error("Polling error", e);
      stopPolling();
      setScraping(false);
      setError("Connection lost to scraping task.");
    }
  };

  const handleRun = async (url?: string) => {
    if (scraping) return;
    
    setScraping(true);
    setError(null);
    setJobs([]);
    setIsSidebarOpen(true);
    
    try {
      const urls = url ? [url] : [];
      const { task_id } = await startScrapeTask(urls);
      setTaskId(task_id);
      
      // Auto-approve all
      await approveAllTask(task_id);
      
      // Start polling
      pollTask(task_id);
      
    } catch (err) {
      console.error(err);
      setError('Failed to start scraping.');
      setScraping(false);
    }
  };

  const handleViewJob = (job: Job) => {
    setSelectedJob(job);
    setIsModalOpen(true);
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400">
                Job Scraper Dashboard
            </h1>
        </div>
        
        <div className="flex gap-3">
            <button 
                onClick={loadPlan}
                className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
                title="Refresh Plan"
            >
                <RefreshCw size={20} />
            </button>
            <button 
                onClick={() => handleRun()} 
                disabled={scraping}
                className={`scrape-button ${scraping ? 'opacity-75 cursor-not-allowed' : ''}`}
            >
                {scraping ? 'Scraping...' : (
                    <>
                        <Play size={18} fill="currentColor" /> Run All Scrapers
                    </>
                )}
            </button>
        </div>
      </header>

      {error && (
        <div className="error-banner">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      <main>
        {plan.length === 0 ? (
            <div className="text-center py-20 text-gray-500 dark:text-gray-400">
                <p>No platforms configured or failed to load plan.</p>
            </div>
        ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                {plan.map((item, idx) => {
                    const result = taskResults.find(r => r.url === item.url);
                    return (
                        <SiteCard 
                            key={idx} 
                            item={item} 
                            result={result}
                            onRun={handleRun}
                            isRunning={scraping}
                        />
                    );
                })}
            </div>
        )}
      </main>

      <Sidebar 
          isOpen={isSidebarOpen} 
          onClose={() => setIsSidebarOpen(false)} 
          jobs={jobs}
          onViewJob={handleViewJob}
          loading={scraping}
      />

      <JobDetailsModal 
          job={selectedJob} 
          isOpen={isModalOpen} 
          onClose={() => setIsModalOpen(false)} 
      />
    </div>
  );
}
