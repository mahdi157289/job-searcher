import { useState, useEffect, useRef } from 'react'
import { getScrapePlan, startScrapeTask, getTaskStatus, approveAllTask } from './api'
import type { Job, ScrapeResult, ScrapePlanItem } from './api'
import { Play, AlertCircle, RefreshCw } from 'lucide-react'
import './App.css'
import { SiteCard } from './components/SiteCard'
import { Sidebar } from './components/Sidebar'
import { JobDetailsModal } from './components/JobDetailsModal'

function App() {
  const [loading, setLoading] = useState(false) // Global loading (e.g. initial fetch)
  const [scraping, setScraping] = useState(false) // Scraping active state
  const [plan, setPlan] = useState<ScrapePlanItem[]>([])
  const [jobs, setJobs] = useState<Job[]>([])
  const [error, setError] = useState<string | null>(null)
  
  // Sidebar & Modal State
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [selectedJob, setSelectedJob] = useState<Job | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  
  // Task Management
  const [taskId, setTaskId] = useState<string | null>(null)
  const pollingRef = useRef<number | null>(null)

  useEffect(() => {
    loadPlan()
    return () => stopPolling()
  }, [])

  const loadPlan = async () => {
    try {
      const response = await getScrapePlan()
      setPlan(response.plan)
    } catch (err) {
      console.error("Failed to load plan:", err)
      setError("Failed to load scraping plan. Is the backend running?")
    }
  }

  const stopPolling = () => {
    if (pollingRef.current) {
      window.clearInterval(pollingRef.current)
      pollingRef.current = null
    }
  }

  const handleRun = async (url?: string) => {
    if (scraping) return
    
    setScraping(true)
    setError(null)
    setJobs([])
    setIsSidebarOpen(true)
    
    try {
      const urls = url ? [url] : []
      const { task_id } = await startScrapeTask(urls)
      setTaskId(task_id)
      
      // Auto-approve all
      await approveAllTask(task_id)
      
      // Start polling
      pollingRef.current = window.setInterval(async () => {
        try {
          const status = await getTaskStatus(task_id)
          
          // Collect all jobs from results
          const allJobs: Job[] = []
          status.results.forEach(res => {
            if (res.jobs) {
                // Debug log for first job of each result to check structure
                if (res.jobs.length > 0) {
                    console.log(`Jobs from ${res.url} (Platform: ${res.platform}):`, res.jobs[0]);
                }
                allJobs.push(...res.jobs)
            }
          })
          setJobs(allJobs)
          
          if (status.status === 'completed' || status.status === 'failed') {
            stopPolling()
            setScraping(false)
          }
        } catch (e) {
          console.error("Polling error", e)
          stopPolling()
          setScraping(false)
          setError("Connection lost to scraping task.")
        }
      }, 1000)
      
    } catch (err) {
      console.error("Failed to start scrape:", err)
      setError("Failed to start scraping task.")
      setScraping(false)
    }
  }

  // Sync selectedJob with jobs updates
  useEffect(() => {
    if (selectedJob) {
      const updated = jobs.find(j => j.link === selectedJob.link)
      if (updated && updated !== selectedJob) {
        setSelectedJob(updated)
      }
    }
  }, [jobs, selectedJob])

  const handleViewJob = (job: Job) => {
    setSelectedJob(job)
    setIsModalOpen(true)
  }

  const handleStop = () => {
    stopPolling()
    setScraping(false)
  }

  return (
    <div className="app-container min-h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100 p-6">
      <header className="max-w-7xl mx-auto mb-8 flex justify-between items-center border-b border-gray-200 dark:border-gray-800 pb-6">
        <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent">Job Scraper</h1>
            <p className="text-gray-500 dark:text-gray-400 mt-1">Manage and run your job scraping tasks</p>
        </div>
        <button 
          onClick={() => handleRun()} 
          disabled={scraping}
          className={`flex items-center gap-2 px-6 py-3 rounded-lg font-semibold shadow-lg transition-all ${
              scraping 
              ? 'bg-gray-400 cursor-not-allowed' 
              : 'bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white transform hover:scale-105'
          }`}
        >
          {scraping ? (
             <>
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Scraping in progress...
             </>
          ) : (
            <>
              <Play size={20} fill="currentColor" /> Run All Scrapers
            </>
          )}
        </button>
      </header>

      {error && (
        <div className="max-w-7xl mx-auto mb-6 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-4 rounded-lg flex items-center gap-3 border border-red-100 dark:border-red-900/30">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      <main className="max-w-7xl mx-auto">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            Available Platforms 
            <span className="text-sm font-normal text-gray-500 bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded-full">{plan.length}</span>
        </h2>
        
        {plan.length === 0 ? (
            <div className="text-center py-20 text-gray-500">
                <RefreshCw className="mx-auto mb-4 animate-spin text-gray-300" size={40} />
                <p>Loading platforms...</p>
            </div>
        ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {plan.map((item, idx) => (
                <SiteCard 
                    key={idx} 
                    item={item} 
                    onRun={handleRun}
                    isRunning={scraping}
                />
            ))}
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
  )
}

export default App
