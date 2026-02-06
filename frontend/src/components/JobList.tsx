import React from 'react';
import type { Job } from '../api';
import { JobCard } from './JobCard';
import './JobList.css';

interface JobListProps {
    jobs: Job[];
    loading: boolean;
}

export const JobList: React.FC<JobListProps> = ({ jobs, loading }) => {
    if (loading) {
        return (
            <div className="loading-state">
                <div className="loader"></div>
                <p>Scraping jobs... This might take a minute.</p>
            </div>
        );
    }

    if (jobs.length === 0) {
        return (
            <div className="empty-state">
                <p>No jobs found yet. Click "Start Scraping" to begin.</p>
            </div>
        );
    }

    return (
        <div className="job-grid">
            {jobs.map((job, index) => (
                <JobCard key={`${job.platform}-${index}`} job={job} />
            ))}
        </div>
    );
};
