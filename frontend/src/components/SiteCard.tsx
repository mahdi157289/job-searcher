import React from 'react';
import { Play } from 'lucide-react';
import { ScrapePlanItem } from '../api';

interface SiteCardProps {
    item: ScrapePlanItem;
    onRun: (url: string) => void;
    isRunning?: boolean;
}

export const SiteCard: React.FC<SiteCardProps> = ({ item, onRun, isRunning }) => {
    return (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 border border-gray-200 dark:border-gray-700 flex flex-col justify-between h-full hover:shadow-lg transition-shadow">
            <div>
                <h3 className="font-bold text-lg text-gray-800 dark:text-gray-100 mb-1">{item.platform}</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 break-all mb-4 truncate" title={item.url}>{item.url}</p>
                <div className="text-xs font-mono text-gray-400 dark:text-gray-500 mb-4">{item.strategy}</div>
            </div>
            
            <button
                onClick={() => onRun(item.url)}
                disabled={isRunning}
                className={`w-full flex items-center justify-center gap-2 py-2 px-4 rounded-md font-medium transition-colors ${
                    isRunning 
                    ? 'bg-gray-300 dark:bg-gray-700 cursor-not-allowed text-gray-500' 
                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                }`}
            >
                {isRunning ? (
                    'Queued...'
                ) : (
                    <>
                        <Play size={16} fill="currentColor" /> Run Scraper
                    </>
                )}
            </button>
        </div>
    );
};
