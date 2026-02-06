import React, { useRef, useEffect } from 'react';
import type { Job } from '../api';
import { X, Eye, ExternalLink, Building2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface SidebarProps {
    isOpen: boolean;
    onClose: () => void;
    jobs: Job[];
    onViewJob: (job: Job) => void;
    loading: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose, jobs, onViewJob, loading }) => {
    const listRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom when new jobs arrive
    useEffect(() => {
        if (listRef.current) {
            listRef.current.scrollTop = listRef.current.scrollHeight;
        }
    }, [jobs.length]);

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 0.5 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="fixed inset-0 bg-black z-40"
                    />
                    
                    {/* Drawer */}
                    <motion.div
                        initial={{ x: '100%' }}
                        animate={{ x: 0 }}
                        exit={{ x: '100%' }}
                        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                        className="fixed top-0 right-0 h-full w-full max-w-md bg-white dark:bg-gray-900 shadow-2xl z-50 flex flex-col border-l border-gray-200 dark:border-gray-800"
                    >
                        {/* Header */}
                        <div className="p-4 border-b border-gray-200 dark:border-gray-800 flex justify-between items-center bg-gray-50 dark:bg-gray-800">
                            <div>
                                <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100">Live Results</h2>
                                <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                                    {loading && <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />}
                                    <span>{jobs.length} jobs found</span>
                                </div>
                            </div>
                            <button onClick={onClose} className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-full transition-colors">
                                <X size={20} className="text-gray-600 dark:text-gray-300" />
                            </button>
                        </div>

                        {/* List */}
                        <div className="flex-1 overflow-y-auto p-4 space-y-3" ref={listRef}>
                            {jobs.length === 0 && loading && (
                                <div className="text-center py-10 text-gray-500">
                                    <div className="loader mx-auto mb-4"></div>
                                    <p>Waiting for jobs...</p>
                                </div>
                            )}
                            
                            {jobs.map((job, index) => (
                                <motion.div
                                    key={`${job.link}-${index}`}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="bg-white dark:bg-gray-800 p-3 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm hover:shadow-md transition-shadow"
                                >
                                    <h3 className="font-semibold text-gray-800 dark:text-gray-200 mb-1 line-clamp-1">{job.title}</h3>
                                    <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 mb-2">
                                        <Building2 size={14} />
                                        <span className="truncate max-w-[150px]">{job.company}</span>
                                    </div>
                                    
                                    <div className="flex justify-between items-center mt-2 pt-2 border-t border-gray-100 dark:border-gray-700">
                                        <span className="text-xs px-2 py-1 bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-300 rounded">
                                            {job.platform}
                                        </span>
                                        <div className="flex gap-2">
                                            <a 
                                                href={job.link} 
                                                target="_blank" 
                                                rel="noopener noreferrer"
                                                className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded text-gray-500 dark:text-gray-400"
                                                title="Open Link"
                                            >
                                                <ExternalLink size={16} />
                                            </a>
                                            <button 
                                                onClick={() => onViewJob(job)}
                                                className="p-1.5 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded text-blue-600 dark:text-blue-400"
                                                title="View Details"
                                            >
                                                <Eye size={16} />
                                            </button>
                                        </div>
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
};
