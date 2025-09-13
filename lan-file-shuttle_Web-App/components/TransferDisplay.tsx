
import React from 'react';
import type { TransferProgress } from '../types';
import { TransferStatus } from '../types';
import { FileIcon } from '../constants';

interface TransferDisplayProps {
    status: TransferStatus;
    progress: TransferProgress;
    transferCode: string;
    files: File[];
    isSender: boolean;
}

const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const formatEta = (seconds: number): string => {
    if (seconds === Infinity || seconds < 0) return '...';
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
};


export const TransferDisplay: React.FC<TransferDisplayProps> = ({ status, progress, transferCode, files, isSender }) => {
    
    const getStatusText = () => {
        switch(status) {
            case TransferStatus.CONNECTING: return 'Connecting...';
            case TransferStatus.TRANSFERRING: return isSender ? 'Sending...' : 'Receiving...';
            case TransferStatus.COMPLETE: return 'Transfer Complete!';
            case TransferStatus.FAILED: return 'Transfer Failed!';
            case TransferStatus.STOPPED: return 'Transfer Stopped.';
            default: return 'Waiting...';
        }
    };

    const progressColor = status === TransferStatus.COMPLETE ? 'bg-green-500' : 'bg-blue-500';

    return (
        <div className="mt-6 bg-gray-900/50 p-6 rounded-lg border border-gray-700">
            <div className="flex justify-between items-center mb-4">
                <h3 className="font-semibold text-lg text-gray-300">{getStatusText()}</h3>
                <div className="text-right">
                    <span className="text-gray-400 text-sm">Transfer Code</span>
                    <p className="font-mono text-2xl text-cyan-400 tracking-widest">{transferCode}</p>
                </div>
            </div>
            
            <div className="w-full bg-gray-700 rounded-full h-4 mb-2 overflow-hidden">
                <div 
                    className={`h-4 rounded-full transition-all duration-300 ease-linear ${progressColor}`} 
                    style={{ width: `${progress.percentage}%` }}
                ></div>
            </div>
            
            <div className="flex justify-between text-sm font-medium text-gray-400">
                <span>{progress.percentage.toFixed(1)}%</span>
                <span>{formatFileSize(progress.sentBytes)} / {formatFileSize(progress.totalBytes)}</span>
                <span>{progress.speed.toFixed(2)} MB/s</span>
                <span>ETA: {formatEta(progress.eta)}</span>
            </div>

            <div className="mt-6">
                <h4 className="font-semibold text-gray-400 mb-2">{isSender ? "Sending Files:" : "Receiving Files:"}</h4>
                <ul className="space-y-2 max-h-40 overflow-y-auto bg-gray-800 p-3 rounded-md">
                    {files.map((file, index) => (
                        <li key={index} className="flex items-center gap-3 bg-gray-700/50 p-2 rounded">
                            <FileIcon />
                            <span className="text-gray-300 truncate flex-grow">{file.name}</span>
                            <span className="text-gray-400 text-sm font-mono whitespace-nowrap">{formatFileSize(file.size)}</span>
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );
};
