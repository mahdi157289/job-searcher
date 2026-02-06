import React from 'react';
import type { Job } from '../api';
import { ExternalLink, MapPin, Building2 } from 'lucide-react';
import './JobCard.css';

interface JobCardProps {
    job: Job;
}

export const JobCard: React.FC<JobCardProps> = ({ job }) => {
    return (
        <div className="job-card">
            <h3 className="job-title">{job.title}</h3>
            <div className="job-meta">
                <div className="meta-item">
                    <Building2 size={16} />
                    <span>{job.company}</span>
                </div>
                <div className="meta-item">
                    <MapPin size={16} />
                    <span>{job.location}</span>
                </div>
            </div>
            <div className="job-footer">
                <span className="platform-tag">{job.platform}</span>
                <a href={job.link} target="_blank" rel="noopener noreferrer" className="apply-link">
                    Apply <ExternalLink size={14} />
                </a>
            </div>
        </div>
    );
};
