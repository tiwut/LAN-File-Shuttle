
import React, { useState, useCallback, useRef, useEffect } from 'react';
import type { LogMessage, TransferProgress } from '../types';
import { TransferStatus } from '../types';
import { LogView } from './LogView';
import { TransferDisplay } from './TransferDisplay';
import { SIMULATION_CHUNK_SIZE, SIMULATION_INTERVAL } from '../constants';

// Mock file data for receiver simulation
const MOCK_FILES: File[] = [
    new File(["data"], "project-alpha.zip", { type: "application/zip" }),
    new File(["data"], "meeting-notes.docx", { type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document" }),
    new File(["data"], "design-mockup-v3.png", { type: "image/png" }),
];
// Manually setting sizes as File constructor doesn't allow it directly
Object.defineProperty(MOCK_FILES[0], 'size', { value: 157286400 }); // 150 MB
Object.defineProperty(MOCK_FILES[1], 'size', { value: 2097152 }); // 2 MB
Object.defineProperty(MOCK_FILES[2], 'size', { value: 5242880 }); // 5 MB

export const ReceiverView: React.FC = () => {
    const [transferCode, setTransferCode] = useState('');
    const [status, setStatus] = useState<TransferStatus>(TransferStatus.IDLE);
    const [logs, setLogs] = useState<LogMessage[]>([]);
    const [progress, setProgress] = useState<TransferProgress>({
        percentage: 0, speed: 0, sentBytes: 0, totalBytes: 0, eta: 0
    });
    
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

    const handleConnect = () => {
        if (!/^[A-Z0-9]{6}$/.test(transferCode)) {
            addLog('Invalid transfer code. Must be 6 uppercase letters/numbers.', 'error');
            return;
        }
        addLog(`Attempting to connect with code: ${transferCode}...`);
        setStatus(TransferStatus.CONNECTING);

        setTimeout(() => {
            addLog('Connection established. Preparing to receive files.');
            startReceiving();
        }, 1500);
    };

    const startReceiving = () => {
        setStatus(TransferStatus.TRANSFERRING);
        const totalBytes = MOCK_FILES.reduce((acc, file) => acc + file.size, 0);
        setProgress({ percentage: 0, speed: 0, sentBytes: 0, totalBytes, eta: Infinity });
        addLog(`Receiving ${MOCK_FILES.length} files (${(totalBytes / (1024 * 1024)).toFixed(2)} MB)...`);
        
        let receivedBytes = 0;
        const startTime = Date.now();

        transferIntervalRef.current = window.setInterval(() => {
            const elapsedSeconds = (Date.now() - startTime) / 1000;
            receivedBytes += SIMULATION_CHUNK_SIZE * (0.8 + Math.random() * 0.4);
            receivedBytes = Math.min(receivedBytes, totalBytes);

            const percentage = (receivedBytes / totalBytes) * 100;
            const speed = elapsedSeconds > 0 ? (receivedBytes / elapsedSeconds) / (1024 * 1024) : 0;
            const remainingBytes = totalBytes - receivedBytes;
            const eta = speed > 0 ? remainingBytes / (speed * 1024 * 1024) : Infinity;

            setProgress({ percentage, speed, sentBytes: receivedBytes, totalBytes, eta });

            if (receivedBytes >= totalBytes) {
                if (transferIntervalRef.current) clearInterval(transferIntervalRef.current);
                setStatus(TransferStatus.COMPLETE);
                addLog('File reception complete!', 'success');
            }
        }, SIMULATION_INTERVAL);
    };
    
    const handleStopTransfer = () => {
        if (transferIntervalRef.current) {
            clearInterval(transferIntervalRef.current);
            transferIntervalRef.current = null;
        }
        setStatus(TransferStatus.STOPPED);
        addLog('Reception stopped by user.', 'error');
    };

    const resetState = () => {
        setTransferCode('');
        setStatus(TransferStatus.IDLE);
        setLogs([]);
        setProgress({ percentage: 0, speed: 0, sentBytes: 0, totalBytes: 0, eta: 0 });
    };

    const isTransmitting = status === TransferStatus.TRANSFERRING || status === TransferStatus.CONNECTING;
    const isFinished = status === TransferStatus.COMPLETE || status === TransferStatus.FAILED || status === TransferStatus.STOPPED;

    return (
        <div>
            <h2 className="text-2xl font-bold text-gray-200 mb-6">Receive Files</h2>

            {!isTransmitting && !isFinished && (
                <div className="flex flex-col sm:flex-row items-center gap-4">
                    <input
                        type="text"
                        value={transferCode}
                        onChange={(e) => setTransferCode(e.target.value.toUpperCase())}
                        placeholder="Enter 6-digit code"
                        maxLength={6}
                        className="w-full sm:w-auto flex-grow text-center font-mono text-2xl tracking-widest bg-gray-900 border-2 border-gray-600 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    />
                    <button
                        onClick={handleConnect}
                        disabled={transferCode.length !== 6}
                        className="w-full sm:w-auto bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-8 rounded-lg disabled:bg-gray-500 disabled:cursor-not-allowed transition-colors text-lg"
                    >
                        Connect
                    </button>
                </div>
            )}
            
            {(isTransmitting || isFinished) && (
                <TransferDisplay 
                    status={status} 
                    progress={progress} 
                    transferCode={transferCode}
                    files={MOCK_FILES}
                    isSender={false}
                />
            )}

            {isTransmitting && !isFinished && status !== TransferStatus.CONNECTING && (
                <div className="mt-8 flex justify-center">
                    <button
                        onClick={handleStopTransfer}
                        className="bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-8 rounded-lg transition-colors text-lg"
                    >
                        Stop Transfer
                    </button>
                </div>
            )}

            {isFinished && (
                 <div className="mt-8 flex justify-center">
                    <button
                        onClick={resetState}
                        className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-8 rounded-lg transition-colors text-lg"
                    >
                        Receive New Files
                    </button>
                </div>
            )}

            <LogView logs={logs} />
        </div>
    );
};
