
import React, { useState, useRef, useCallback, useEffect } from 'react';
import type { LogMessage, TransferProgress } from '../types';
import { TransferStatus } from '../types';
import { FileIcon, UploadIcon } from '../constants';
import { LogView } from './LogView';
import { TransferDisplay } from './TransferDisplay';
import { SIMULATION_CHUNK_SIZE, SIMULATION_INTERVAL } from '../constants';

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const SenderView: React.FC = () => {
  const [files, setFiles] = useState<File[]>([]);
  const [transferCode, setTransferCode] = useState('');
  const [status, setStatus] = useState<TransferStatus>(TransferStatus.IDLE);
  const [logs, setLogs] = useState<LogMessage[]>([]);
  const [progress, setProgress] = useState<TransferProgress>({
    percentage: 0, speed: 0, sentBytes: 0, totalBytes: 0, eta: 0
  });

  const fileInputRef = useRef<HTMLInputElement>(null);
  const transferIntervalRef = useRef<number | null>(null);

  const addLog = useCallback((message: string, type: 'info' | 'success' | 'error' = 'info') => {
    setLogs(prev => [
      ...prev,
      { id: Date.now(), type, message, timestamp: new Date().toLocaleTimeString() }
    ]);
  }, []);

  useEffect(() => {
    return () => {
      if (transferIntervalRef.current) {
        clearInterval(transferIntervalRef.current);
      }
    };
  }, []);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      const selectedFiles = Array.from(event.target.files);
      setFiles(selectedFiles);
      addLog(`Selected ${selectedFiles.length} file(s) for transfer.`);
    }
  };

  const handleStartTransfer = () => {
    if (files.length === 0) {
      addLog('No files selected for transfer.', 'error');
      return;
    }

    const totalBytes = files.reduce((acc, file) => acc + file.size, 0);
    const code = Math.random().toString(36).substring(2, 8).toUpperCase();
    setTransferCode(code);
    setStatus(TransferStatus.TRANSFERRING);
    setProgress({ percentage: 0, speed: 0, sentBytes: 0, totalBytes, eta: Infinity });
    addLog(`Starting transfer with code: ${code}`);

    let sentBytes = 0;
    const startTime = Date.now();

    transferIntervalRef.current = window.setInterval(() => {
      const elapsedSeconds = (Date.now() - startTime) / 1000;
      sentBytes += SIMULATION_CHUNK_SIZE * (0.8 + Math.random() * 0.4); // a bit of variation
      sentBytes = Math.min(sentBytes, totalBytes);
      
      const percentage = (sentBytes / totalBytes) * 100;
      const speed = elapsedSeconds > 0 ? (sentBytes / elapsedSeconds) / (1024 * 1024) : 0;
      const remainingBytes = totalBytes - sentBytes;
      const eta = speed > 0 ? remainingBytes / (speed * 1024 * 1024) : Infinity;

      setProgress({ percentage, speed, sentBytes, totalBytes, eta });

      if (sentBytes >= totalBytes) {
        if (transferIntervalRef.current) clearInterval(transferIntervalRef.current);
        setStatus(TransferStatus.COMPLETE);
        addLog('File transfer complete!', 'success');
      }
    }, SIMULATION_INTERVAL);
  };
  
  const handleStopTransfer = () => {
    if (transferIntervalRef.current) {
        clearInterval(transferIntervalRef.current);
        transferIntervalRef.current = null;
    }
    setStatus(TransferStatus.STOPPED);
    addLog('Transfer stopped by user.', 'error');
  };

  const resetState = () => {
    setFiles([]);
    setTransferCode('');
    setStatus(TransferStatus.IDLE);
    setLogs([]);
    setProgress({ percentage: 0, speed: 0, sentBytes: 0, totalBytes: 0, eta: 0 });
    if(fileInputRef.current) fileInputRef.current.value = "";
  };


  const isTransmitting = status === TransferStatus.TRANSFERRING;
  const isFinished = status === TransferStatus.COMPLETE || status === TransferStatus.FAILED || status === TransferStatus.STOPPED;

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-200 mb-6">Send Files</h2>

      {!isTransmitting && !isFinished && (
        <div className="border-2 border-dashed border-gray-600 rounded-lg p-8 text-center bg-gray-800/50">
          <input
            type="file"
            multiple
            ref={fileInputRef}
            onChange={handleFileChange}
            className="hidden"
          />
          <UploadIcon />
          <p className="mt-2 text-gray-400">Drag & drop files here, or</p>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="mt-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
          >
            Browse Files
          </button>
        </div>
      )}

      {files.length > 0 && !isTransmitting && !isFinished && (
        <div className="mt-6">
          <h3 className="font-semibold text-lg mb-2">Selected Files:</h3>
          <ul className="space-y-2 max-h-48 overflow-y-auto bg-gray-900 p-3 rounded-md">
            {files.map((file, index) => (
              <li key={index} className="flex items-center gap-3 bg-gray-700 p-2 rounded">
                <FileIcon />
                <span className="text-gray-300 truncate flex-grow">{file.name}</span>
                <span className="text-gray-400 text-sm font-mono whitespace-nowrap">{formatFileSize(file.size)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {(isTransmitting || isFinished) ? (
        <TransferDisplay 
            status={status} 
            progress={progress} 
            transferCode={transferCode}
            files={files}
            isSender={true}
        />
      ) : null}

      <div className="mt-8 flex justify-center gap-4">
        {!isTransmitting && !isFinished && (
            <button
                onClick={handleStartTransfer}
                disabled={files.length === 0}
                className="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-8 rounded-lg disabled:bg-gray-500 disabled:cursor-not-allowed transition-colors text-lg"
            >
                Start Transfer
            </button>
        )}
        {isTransmitting && (
            <button
                onClick={handleStopTransfer}
                className="bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-8 rounded-lg transition-colors text-lg"
            >
                Stop Transfer
            </button>
        )}
        {isFinished && (
             <button
                onClick={resetState}
                className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-8 rounded-lg transition-colors text-lg"
            >
                Send New Files
            </button>
        )}
      </div>

      <LogView logs={logs} />
    </div>
  );
};
