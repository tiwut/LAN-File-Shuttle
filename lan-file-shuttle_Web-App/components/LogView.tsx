
import React, { useRef, useEffect } from 'react';
import type { LogMessage } from '../types';
import { InfoIcon, SuccessIcon, ErrorIcon } from '../constants';

interface LogViewProps {
  logs: LogMessage[];
}

const logIcons = {
    info: <InfoIcon />,
    success: <SuccessIcon />,
    error: <ErrorIcon />
};

const logColors = {
    info: 'text-gray-300',
    success: 'text-green-300',
    error: 'text-red-300'
};

export const LogView: React.FC<LogViewProps> = ({ logs }) => {
  const logContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  if (logs.length === 0) return null;

  return (
    <div className="mt-8">
      <h3 className="font-semibold text-lg mb-2 text-gray-400">Status Log</h3>
      <div
        ref={logContainerRef}
        className="bg-gray-900 rounded-lg p-4 h-48 overflow-y-auto font-mono text-sm space-y-2 border border-gray-700"
      >
        {logs.map((log) => (
          <div key={log.id} className={`flex items-start gap-3 ${logColors[log.type]}`}>
            <div className="mt-0.5">{logIcons[log.type]}</div>
            <div className="flex-grow">
              <span className="text-gray-500 mr-2">{log.timestamp}</span>
              <span>{log.message}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
