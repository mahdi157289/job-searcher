import React from 'react';
import { Job } from '../api';
import { X, ExternalLink, MapPin, Building2, Calendar, Clock } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface JobDetailsModalProps {
    job: Job | null;
    isOpen: boolean;
    onClose: () => void;
}

export const JobDetailsModal: React.FC<JobDetailsModalProps> = ({ job, isOpen, onClose }) => {
    // Debug logging
    React.useEffect(() => {
        if (isOpen && job) {
            console.log("JobDetailsModal received job:", job);
            console.log("Job Description length:", job.description?.length);
            console.log("Job Details keys:", job.details ? Object.keys(job.details) : "none");
        }
    }, [isOpen, job]);

    if (!job) return null;

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 0.5 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="fixed inset-0 bg-black z-50"
                    />
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none"
                    >
                        <div className="bg-white dark:bg-gray-900 rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col pointer-events-auto border border-gray-200 dark:border-gray-700">
                            {/* Header */}
                            <div className="p-6 border-b border-gray-200 dark:border-gray-800 flex justify-between items-start">
                                <div>
                                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">{job.title}</h2>
                                    <div className="flex flex-wrap gap-4 text-gray-600 dark:text-gray-300">
                                        <div className="flex items-center gap-2">
                                            <Building2 size={18} className="text-gray-400" />
                                            {job.company}
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <MapPin size={18} className="text-gray-400" />
                                            {job.location}
                                        </div>
                                    </div>
                                </div>
                                <button onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full transition-colors">
                                    <X size={24} className="text-gray-500" />
                                </button>
                            </div>

                            {/* Body */}
                            <div className="flex-1 overflow-y-auto p-6">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                                    <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                                        <span className="text-sm text-gray-500 dark:text-gray-400 block mb-1">Platform</span>
                                        <span className="font-medium text-gray-900 dark:text-gray-100">{job.platform}</span>
                                    </div>
                                    <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                                        <span className="text-sm text-gray-500 dark:text-gray-400 block mb-1">Posted</span>
                                        <span className="font-medium text-gray-900 dark:text-gray-100 flex items-center gap-2">
                                            <Calendar size={16} />
                                            {job.age_text || (job.posted_at ? new Date(job.posted_at).toLocaleDateString() : 'Unknown')}
                                        </span>
                                    </div>
                                </div>

                                {job.description && (
                                    <div className="mb-6">
                                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Description</h3>
                                        <div className="prose dark:prose-invert max-w-none text-gray-600 dark:text-gray-300 whitespace-pre-wrap">
                                            {job.description}
                                        </div>
                                    </div>
                                )}

                                {job.details && Object.keys(job.details).length > 0 && (
                                    <div className="space-y-6">
                                        {Object.entries(job.details).map(([key, value]) => (
                                            <div key={key}>
                                                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2 capitalize">
                                                    {key.replace(/_/g, ' ')}
                                                </h3>
                                                <div className="prose dark:prose-invert max-w-none text-gray-600 dark:text-gray-300 whitespace-pre-wrap">
                                                    {value}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                                
                                {(!job.details || Object.keys(job.details).length === 0) && !job.description && (
                                    <div className="text-center py-8 text-gray-500">
                                        No additional details available for this job.
                                    </div>
                                )}
                            </div>

                            {/* Footer */}
                            <div className="p-6 border-t border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-800/50 flex justify-end">
                                <a 
                                    href={job.link} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2.5 rounded-lg font-medium flex items-center gap-2 transition-colors"
                                >
                                    Apply Now <ExternalLink size={18} />
                                </a>
                            </div>
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
};
