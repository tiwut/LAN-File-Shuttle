
export type AppView = 'home' | 'sender' | 'receiver';

export enum TransferStatus {
  IDLE = 'idle',
  CONNECTING = 'connecting',
  TRANSFERRING = 'transferring',
  COMPLETE = 'complete',
  FAILED = 'failed',
  STOPPED = 'stopped'
}

export interface LogMessage {
  id: number;
  type: 'info' | 'success' | 'error';
  message: string;
  timestamp: string;
}

export interface TransferProgress {
    percentage: number;
    speed: number; // in MB/s
    sentBytes: number;
    totalBytes: number;
    eta: number; // in seconds
}
